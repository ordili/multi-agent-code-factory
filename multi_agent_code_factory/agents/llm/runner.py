"""结构化 LLM 调用编排：prompt、invoke、预算与重试。"""

from __future__ import annotations

import time
from typing import Any, TypeVar

from pydantic import BaseModel

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.llm.budget import check_llm_budget, record_llm_call
from multi_agent_code_factory.agents.llm.invoke import (
    invoke_langchain_structured,
    invoke_prompted_json,
    is_transient_llm_error,
    ollama_invoke_hint,
    uses_prompted_json,
)
from multi_agent_code_factory.agents.llm.prompt import build_llm_messages, load_role_prompt
from multi_agent_code_factory.agents.llm.usage import (
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
from multi_agent_code_factory.tools.write_artifact import RunArtifactWriter

T = TypeVar("T", bound=BaseModel)

logger = get_logger("agents.llm.runner")


class LlmRunner:
    """按角色调用 LLM 并解析结构化输出，同时更新 run_meta 预算。"""

    def __init__(
        self,
        writer: RunArtifactWriter,
        profile: ProfileConfig,
        *,
        factory_config: FactoryConfig | None = None,
    ) -> None:
        """初始化 runner：绑定产物写入器、Profile 与可选的工厂级预算配置。"""
        self.writer = writer
        self.profile = profile
        self.factory_config = factory_config
        self._runtime = resolve_llm_runtime_config()
        self._model = create_chat_model()

    def load_role_prompt(self, role_id: AgentRole) -> str:
        """加载角色 system prompt（委托 ``prompt.load_role_prompt``）。"""
        return load_role_prompt(self.profile, role_id)

    def _persist_usage(self, call: LlmCallUsage) -> None:
        """追加单次 LLM 调用明细到 run 目录下的 usage 审计文件。"""
        self.writer.record_llm_usage(
            call,
            provider=self._runtime.factory_provider,
            model=self._runtime.model,
        )

    def _log_usage(self, call: LlmCallUsage) -> None:
        """记录单次调用的 token 与耗时日志。"""
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

    def _build_call_usage(
        self,
        *,
        role_id: AgentRole,
        schema: type[BaseModel],
        attempt: int,
        duration_ms: int,
        raw_response: Any | None,
    ) -> LlmCallUsage:
        """从原始响应提取 token 用量并构造 ``LlmCallUsage`` 记录。"""
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
        role_id: AgentRole,
        schema: type[T],
        context: dict[str, Any],
        extra_system: str | None = None,
    ) -> T:
        """调用 LLM 并解析为指定 Pydantic schema；超预算或全部重试失败则抛错。

        根据 provider 选择 structured output 或 prompted JSON 路径；
        瞬态错误会指数退避重试（Ollama/DeepSeek 2 次，其它 3 次）。
        """
        check_llm_budget(self.writer, self.factory_config)
        system_prompt, user_prompt = build_llm_messages(
            self.profile,
            role_id=role_id,
            context=context,
            extra_system=extra_system,
        )
        logger.info("llm invoke start role=%s schema=%s", role_id, schema.__name__)

        use_prompted_json = uses_prompted_json(self._runtime.factory_provider)
        attempts = 2 if use_prompted_json else 3
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):
            started = time.perf_counter()
            try:
                if use_prompted_json:
                    result, raw = invoke_prompted_json(
                        self._model,
                        role_id=role_id,
                        schema=schema,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                    )
                else:
                    result, raw = invoke_langchain_structured(
                        self._model,
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
                record_llm_call(self.writer, self.factory_config, call)
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
                if attempt < attempts and is_transient_llm_error(exc):
                    time.sleep(1.5 * attempt)
                    continue
                break

        assert last_error is not None
        if use_prompted_json:
            msg = f"{ollama_invoke_hint(self._runtime.model)}\nOriginal error: {last_error}"
            raise LlmInvokeError(msg) from last_error
        logger.exception(
            "llm invoke failed role=%s schema=%s", role_id, schema.__name__
        )
        raise last_error
