"""结构化 LLM 调用封装，含预算追踪与重试。"""

from __future__ import annotations

import json
import re
import time
from typing import Any, TypeVar

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, ValidationError

from multi_agent_code_factory.agents.base import (
    default_stub_fixtures,
    load_json_fixture,
)
from multi_agent_code_factory.agents.llm_usage import (
    LlmCallUsage,
    TokenUsage,
    extract_token_usage,
)
from multi_agent_code_factory.config import FactoryConfig
from multi_agent_code_factory.llm import (
    LlmInvokeError,
    create_chat_model,
    resolve_llm_runtime_config,
)
from multi_agent_code_factory.log import get_logger
from multi_agent_code_factory.profiles import ProfileConfig
from multi_agent_code_factory.schemas.run_meta import BudgetUsage
from multi_agent_code_factory.tools.write_artifact import RunArtifactWriter

T = TypeVar("T", bound=BaseModel)

logger = get_logger("agents.llm_runner")

_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)
_TRANSIENT_ERROR_NAMES = frozenset(
    {
        "ResponseError",
        "ReadError",
        "RemoteProtocolError",
        "ConnectionError",
        "TimeoutError",
    }
)


def extract_json_text(raw: str) -> str:
    """去除模型输出中的 markdown 围栏与首尾空白。"""
    text = raw.strip()
    if text.startswith("```"):
        text = _JSON_FENCE_RE.sub("", text).strip()
    return text


def _is_transient_llm_error(exc: BaseException) -> bool:
    name = type(exc).__name__
    if name in _TRANSIENT_ERROR_NAMES:
        return True
    message = str(exc).lower()
    return "502" in message or "503" in message or "connection" in message


_PROMPTED_JSON_PROVIDERS = frozenset({"ollama", "deepseek"})


def _uses_prompted_json(provider: str) -> bool:
    """不支持 LangChain ``with_structured_output`` 的 provider 需走提示词 JSON 模式。"""
    return provider in _PROMPTED_JSON_PROVIDERS


def _ollama_invoke_hint(model: str) -> str:
    return (
        f"LLM call failed for model {model!r}. "
        "For Ollama: restart the server and prefer qwen3.5:9b for large JSON specs. "
        "For DeepSeek: use deepseek-chat or deepseek-v4-pro with prompted JSON mode. "
        "Or switch FACTORY_LLM_PROVIDER=ollama."
    )


def _resolved_call_tokens(call: LlmCallUsage) -> int:
    if call.total_tokens is not None:
        return call.total_tokens
    return (call.prompt_tokens or 0) + (call.completion_tokens or 0)


class LlmRunner:
    """按角色调用 LLM 并解析结构化输出，同时更新 run_meta 预算。"""

    def __init__(
        self,
        writer: RunArtifactWriter,
        profile: ProfileConfig,
        *,
        factory_config: FactoryConfig | None = None,
    ) -> None:
        self.writer = writer
        self.profile = profile
        self.factory_config = factory_config
        self._runtime = resolve_llm_runtime_config()
        self._model = create_chat_model()

    def load_role_prompt(self, role_id: str) -> str:
        path = self.profile.prompts_dir / f"{role_id}.txt"
        if path.is_file():
            return path.read_text(encoding="utf-8")
        fallback = self.profile.prompts_dir / "python-style-snippet.txt"
        if fallback.is_file():
            return fallback.read_text(encoding="utf-8")
        return (
            f"You are the {role_id} agent. Output must match the requested JSON schema."
        )

    def _check_budget(self) -> None:
        if self.factory_config is None or self.factory_config.budget is None:
            return
        meta = self.writer.read_meta()
        if meta is None or meta.budget is None:
            return
        budget = meta.budget
        max_calls = budget.max_llm_calls
        used_calls = budget.used_llm_calls or 0
        if max_calls is not None and used_calls >= max_calls:
            msg = f"LLM call budget exceeded ({used_calls}/{max_calls})"
            raise RuntimeError(msg)
        max_tokens = budget.max_tokens
        used_tokens = budget.used_tokens or 0
        if max_tokens is not None and used_tokens >= max_tokens:
            msg = f"LLM token budget exceeded ({used_tokens}/{max_tokens})"
            raise RuntimeError(msg)

    def _record_call(self, call: LlmCallUsage) -> None:
        meta = self.writer.read_meta()
        if meta is None:
            return
        budget = meta.budget
        if budget is None and self.factory_config and self.factory_config.budget:
            budget = BudgetUsage(
                max_llm_calls=self.factory_config.budget.max_llm_calls,
                max_tokens=self.factory_config.budget.max_tokens,
                used_llm_calls=0,
                used_tokens=0,
            )
        tokens = _resolved_call_tokens(call)
        if budget is None:
            budget = BudgetUsage(used_llm_calls=1, used_tokens=tokens)
        else:
            budget = budget.model_copy(
                update={
                    "used_llm_calls": (budget.used_llm_calls or 0) + 1,
                    "used_tokens": (budget.used_tokens or 0) + tokens,
                }
            )
        self.writer.update_meta(budget=budget)

    def _persist_usage(self, call: LlmCallUsage) -> None:
        self.writer.record_llm_usage(
            call,
            provider=self._runtime.factory_provider,
            model=self._runtime.model,
        )

    def _log_usage(self, call: LlmCallUsage) -> None:
        logger.info(
            "llm usage role=%s schema=%s attempt=%s prompt_tokens=%s "
            "completion_tokens=%s total_tokens=%s duration_ms=%s",
            call.role_id,
            call.schema_name,
            call.attempt,
            call.prompt_tokens,
            call.completion_tokens,
            call.total_tokens,
            call.duration_ms,
        )

    def _example_json_for_schema(self, schema: type[BaseModel]) -> str | None:
        fixtures = default_stub_fixtures()
        mapping: dict[str, Any] = {
            "SpecArtifact": fixtures.spec,
            "DesignArtifact": fixtures.design,
        }
        path = mapping.get(schema.__name__)
        if path is None:
            return None
        return json.dumps(load_json_fixture(path), ensure_ascii=False, indent=2)

    def _build_messages(
        self,
        *,
        role_id: str,
        context: dict[str, Any],
        extra_system: str | None,
    ) -> tuple[str, str]:
        system_parts = [self.load_role_prompt(role_id)]
        style = self.profile.prompts_dir / "python-style-snippet.txt"
        if role_id in {"developer", "architect", "pm"} and style.is_file():
            system_parts.append(style.read_text(encoding="utf-8"))
        if extra_system:
            system_parts.append(extra_system)
        system_prompt = "\n\n".join(
            part.strip() for part in system_parts if part.strip()
        )
        user_prompt = json.dumps(context, ensure_ascii=False, indent=2)
        return system_prompt, user_prompt

    def _invoke_langchain_structured(
        self,
        *,
        role_id: str,
        schema: type[T],
        system_prompt: str,
        user_prompt: str,
    ) -> tuple[T, Any | None]:
        structured = self._model.with_structured_output(schema, include_raw=True)
        payload = structured.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )
        raw: Any | None = None
        if isinstance(payload, dict):
            raw = payload.get("raw")
            parsed = payload.get("parsed")
        else:
            parsed = payload
        if not isinstance(parsed, schema):
            parsed = schema.model_validate(parsed)
        return parsed, raw

    def _invoke_ollama_json(
        self,
        *,
        role_id: str,
        schema: type[T],
        system_prompt: str,
        user_prompt: str,
    ) -> tuple[T, Any]:
        example = self._example_json_for_schema(schema)
        json_rules = (
            "Output ONLY one JSON object. No markdown fences, no commentary.\n"
            "Match field names and nested object shapes exactly."
        )
        if example:
            json_rules += f"\n\nExample JSON shape:\n{example}"
        else:
            json_rules += (
                f"\n\nJSON schema (follow types strictly):\n"
                f"{json.dumps(schema.model_json_schema(), ensure_ascii=False, indent=2)}"
            )
        messages = [
            SystemMessage(content=f"{system_prompt}\n\n{json_rules}"),
            HumanMessage(content=user_prompt),
        ]
        response = self._model.invoke(messages)
        content = getattr(response, "content", response)
        if not isinstance(content, str) or not content.strip():
            msg = f"Ollama returned empty content for role={role_id} schema={schema.__name__}"
            raise LlmInvokeError(msg)
        try:
            payload = json.loads(extract_json_text(content))
        except json.JSONDecodeError as exc:
            msg = (
                f"Ollama JSON parse failed for role={role_id} schema={schema.__name__}: {exc}\n"
                f"Raw output (first 800 chars): {content[:800]}"
            )
            raise LlmInvokeError(msg) from exc
        try:
            return schema.model_validate(payload), response
        except ValidationError as exc:
            msg = f"Ollama JSON did not match schema {schema.__name__} for role={role_id}: {exc}"
            raise LlmInvokeError(msg) from exc

    def _build_call_usage(
        self,
        *,
        role_id: str,
        schema: type[BaseModel],
        attempt: int,
        duration_ms: int,
        raw_response: Any | None,
    ) -> LlmCallUsage:
        usage = (
            extract_token_usage(raw_response)
            if raw_response is not None
            else TokenUsage()
        )
        total = usage.resolved_total()
        return LlmCallUsage(
            role_id=role_id,
            schema_name=schema.__name__,
            attempt=attempt,
            duration_ms=duration_ms,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=total if total > 0 else None,
        )

    def invoke_structured(
        self,
        *,
        role_id: str,
        schema: type[T],
        context: dict[str, Any],
        extra_system: str | None = None,
    ) -> T:
        """调用 LLM 并解析为指定 Pydantic schema；超预算或全部重试失败则抛错。"""
        self._check_budget()
        system_prompt, user_prompt = self._build_messages(
            role_id=role_id,
            context=context,
            extra_system=extra_system,
        )
        logger.info("llm invoke start role=%s schema=%s", role_id, schema.__name__)

        use_prompted_json = _uses_prompted_json(self._runtime.factory_provider)
        attempts = 2 if use_prompted_json else 3
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):
            started = time.perf_counter()
            try:
                if use_prompted_json:
                    result, raw = self._invoke_ollama_json(
                        role_id=role_id,
                        schema=schema,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                    )
                else:
                    result, raw = self._invoke_langchain_structured(
                        role_id=role_id,
                        schema=schema,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                    )
                duration_ms = int((time.perf_counter() - started) * 1000)
                call = self._build_call_usage(
                    role_id=role_id,
                    schema=schema,
                    attempt=attempt,
                    duration_ms=duration_ms,
                    raw_response=raw,
                )
                self._record_call(call)
                self._persist_usage(call)
                self._log_usage(call)
                logger.info(
                    "llm invoke done role=%s schema=%s", role_id, schema.__name__
                )
                return result
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "llm invoke attempt %s/%s failed role=%s schema=%s: %s",
                    attempt,
                    attempts,
                    role_id,
                    schema.__name__,
                    exc,
                )
                # 瞬态错误可退避重试
                if attempt < attempts and _is_transient_llm_error(exc):
                    time.sleep(1.5 * attempt)
                    continue
                break

        assert last_error is not None
        if use_prompted_json:
            msg = f"{_ollama_invoke_hint(self._runtime.model)}\nOriginal error: {last_error}"
            raise LlmInvokeError(msg) from last_error
        logger.exception(
            "llm invoke failed role=%s schema=%s", role_id, schema.__name__
        )
        raise last_error
