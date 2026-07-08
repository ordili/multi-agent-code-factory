"""LLM 用量统一记录（budget + 审计文件 + 日志）。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.llm.budget.ledger import record_llm_call
from multi_agent_code_factory.agents.llm.usage.extract import extract_token_usage
from multi_agent_code_factory.agents.llm.usage.models import LlmCallUsage, TokenUsage
from multi_agent_code_factory.config import FactoryConfig
from multi_agent_code_factory.llm import LlmRuntimeConfig
from multi_agent_code_factory.log import get_logger
from multi_agent_code_factory.tools.write_artifact import RunArtifactWriter

logger = get_logger("agents.llm.usage.recorder")


class UsageRecorder:
    """将成功/失败的 LLM 调用写入 budget、审计产物与日志。"""

    def __init__(
        self,
        writer: RunArtifactWriter,
        factory_config: FactoryConfig | None,
        runtime: LlmRuntimeConfig,
    ) -> None:
        self._writer = writer
        self._factory_config = factory_config
        self._runtime = runtime

    def build_call(
        self,
        *,
        role_id: AgentRole,
        output_schema: type[BaseModel],
        attempt: int,
        duration_ms: int,
        raw_response: Any | None,
        success: bool,
        error: BaseException | None = None,
    ) -> LlmCallUsage:
        usage = (
            extract_token_usage(raw_response)
            if raw_response is not None
            else TokenUsage()
        )
        total = usage.resolved_total()
        return LlmCallUsage(
            role_id=role_id,
            schema_name=output_schema.__name__,
            attempt=attempt,
            duration_ms=duration_ms,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=total if total > 0 else None,
            success=success,
            error_type=type(error).__name__ if error is not None else None,
        )

    def record_success(self, call: LlmCallUsage) -> None:
        record_llm_call(self._writer, self._factory_config, call)
        self._writer.record_llm_usage(
            call,
            provider=self._runtime.factory_provider,
            model=self._runtime.model,
        )
        self._log_call(call)

    def record_failure(self, call: LlmCallUsage) -> None:
        self._writer.record_llm_usage(
            call,
            provider=self._runtime.factory_provider,
            model=self._runtime.model,
        )
        self._log_call(call)

    def _log_call(self, call: LlmCallUsage) -> None:
        level = logger.info if call.success else logger.warning
        level(
            "llm usage role=%s output_schema=%s attempt=%s success=%s error_type=%s "
            "prompt_tokens=%s completion_tokens=%s total_tokens=%s duration_ms=%s",
            call.role_id,
            call.schema_name,
            call.attempt,
            call.success,
            call.error_type,
            call.prompt_tokens,
            call.completion_tokens,
            call.total_tokens,
            call.duration_ms,
        )
