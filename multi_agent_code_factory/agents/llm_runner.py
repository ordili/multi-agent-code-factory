"""Structured LLM invocation with budget tracking."""

from __future__ import annotations

import json
import re
import time
from typing import Any, TypeVar

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, ValidationError

from multi_agent_code_factory.agents.base import default_stub_fixtures, load_json_fixture
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
    {"ResponseError", "ReadError", "RemoteProtocolError", "ConnectionError", "TimeoutError"}
)


def extract_json_text(raw: str) -> str:
    """Strip markdown fences and surrounding whitespace from model output."""
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


def _ollama_invoke_hint(model: str) -> str:
    return (
        f"Ollama call failed for model {model!r}. "
        "Restart Ollama, prefer qwen2.5:7b over deepseek-r1:1.5b for SpecArtifact JSON, "
        "or switch to FACTORY_LLM_PROVIDER=deepseek."
    )


class LlmRunner:
    """Invoke role prompts with structured output and run_meta budget updates."""

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
        max_calls = meta.budget.max_llm_calls
        used = meta.budget.used_llm_calls or 0
        if max_calls is not None and used >= max_calls:
            msg = f"LLM call budget exceeded ({used}/{max_calls})"
            raise RuntimeError(msg)

    def _record_call(self) -> None:
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
        if budget is None:
            budget = BudgetUsage(used_llm_calls=1, used_tokens=0)
        else:
            budget = budget.model_copy(
                update={"used_llm_calls": (budget.used_llm_calls or 0) + 1}
            )
        self.writer.update_meta(budget=budget)

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
    ) -> T:
        structured = self._model.with_structured_output(schema)
        result = structured.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )
        if not isinstance(result, schema):
            result = schema.model_validate(result)
        return result

    def _invoke_ollama_json(
        self,
        *,
        role_id: str,
        schema: type[T],
        system_prompt: str,
        user_prompt: str,
    ) -> T:
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
            return schema.model_validate(payload)
        except ValidationError as exc:
            msg = (
                f"Ollama JSON did not match schema {schema.__name__} for role={role_id}: {exc}"
            )
            raise LlmInvokeError(msg) from exc

    def invoke_structured(
        self,
        *,
        role_id: str,
        schema: type[T],
        context: dict[str, Any],
        extra_system: str | None = None,
    ) -> T:
        self._check_budget()
        system_prompt, user_prompt = self._build_messages(
            role_id=role_id,
            context=context,
            extra_system=extra_system,
        )
        logger.info("llm invoke start role=%s schema=%s", role_id, schema.__name__)

        use_ollama_json = self._runtime.factory_provider == "ollama"
        attempts = 2 if use_ollama_json else 3
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):
            try:
                if use_ollama_json:
                    result = self._invoke_ollama_json(
                        role_id=role_id,
                        schema=schema,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                    )
                else:
                    result = self._invoke_langchain_structured(
                        role_id=role_id,
                        schema=schema,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                    )
                self._record_call()
                logger.info("llm invoke done role=%s schema=%s", role_id, schema.__name__)
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
                if attempt < attempts and _is_transient_llm_error(exc):
                    time.sleep(1.5 * attempt)
                    continue
                break

        assert last_error is not None
        if use_ollama_json:
            msg = f"{_ollama_invoke_hint(self._runtime.model)}\nOriginal error: {last_error}"
            raise LlmInvokeError(msg) from last_error
        logger.exception(
            "llm invoke failed role=%s schema=%s", role_id, schema.__name__
        )
        raise last_error
