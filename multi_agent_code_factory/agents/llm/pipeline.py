"""结构化 LLM 调用流水线编排。"""

from __future__ import annotations

import time
from typing import Any, TypeVar

from pydantic import BaseModel

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.llm.budget.guard import check_llm_budget
from multi_agent_code_factory.agents.llm.errors import wrap_invoke_failure
from multi_agent_code_factory.agents.llm.prompt.builder import build_llm_messages
from multi_agent_code_factory.agents.llm.retry.executor import RetryExecutor
from multi_agent_code_factory.agents.llm.retry.policy import default_retry_policy
from multi_agent_code_factory.agents.llm.strategies.base import InvokeStrategy
from multi_agent_code_factory.agents.llm.strategies.native_structured import NativeStructuredStrategy
from multi_agent_code_factory.agents.llm.strategies.prompted_json import PromptedJsonStrategy
from multi_agent_code_factory.agents.llm.types import InvokeRequest
from multi_agent_code_factory.agents.llm.usage.recorder import UsageRecorder
from multi_agent_code_factory.config import FactoryConfig
from multi_agent_code_factory.llm import LlmOutputMode, LlmRuntimeConfig
from multi_agent_code_factory.log import get_logger
from multi_agent_code_factory.profiles import ProfileConfig
from multi_agent_code_factory.tools.write_artifact import RunArtifactWriter

T = TypeVar("T", bound=BaseModel)

logger = get_logger("agents.llm.pipeline")

_STRATEGIES: dict[LlmOutputMode, InvokeStrategy[Any]] = {
    # openai、anthropic — LangChain with_structured_output
    "native_structured": NativeStructuredStrategy(),
    # deepseek、ollama — 提示词 + 手动 JSON 解析
    "prompted_json": PromptedJsonStrategy(),
}


class StructuredInvokePipeline:
    """编排一次结构化 LLM 调用：预算、prompt、重试、策略、用量。"""

    def __init__(
        self,
        *,
        writer: RunArtifactWriter,
        profile: ProfileConfig,
        factory_config: FactoryConfig | None,
        runtime: LlmRuntimeConfig,
        model: Any,
    ) -> None:
        self._writer = writer
        self._profile = profile
        self._factory_config = factory_config
        self._runtime = runtime
        self._model = model
        self._strategy = _STRATEGIES[runtime.output_mode]
        self._retry = RetryExecutor(default_retry_policy(runtime.output_mode))
        self._usage = UsageRecorder(writer, factory_config, runtime)

    def execute(self, request: InvokeRequest[T]) -> T:
        check_llm_budget(self._writer, self._factory_config)

        system_prompt, user_prompt = build_llm_messages(
            self._profile,
            role_id=request.role_id,
            context=request.context,
            extra_system=request.extra_system,
        )

        output_schema_name = request.output_schema.__name__
        logger.info(
            "llm invoke start role=%s output_schema=%s mode=%s",
            request.role_id,
            output_schema_name,
            self._runtime.output_mode,
        )

        def attempt_fn(attempt: int) -> T:
            started = time.perf_counter()
            try:
                result = self._strategy.invoke(
                    self._model,
                    role_id=request.role_id,
                    output_schema=request.output_schema,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )
            except BaseException as exc:
                duration_ms = int((time.perf_counter() - started) * 1000)
                call = self._usage.build_call(
                    role_id=request.role_id,
                    output_schema=request.output_schema,
                    attempt=attempt,
                    duration_ms=duration_ms,
                    raw_response=None,
                    success=False,
                    error=exc,
                )
                self._usage.record_failure(call)
                logger.warning(
                    "llm invoke attempt %s/%s failed role=%s output_schema=%s: %s",
                    attempt,
                    self._retry.max_attempts,
                    request.role_id,
                    output_schema_name,
                    exc,
                )
                raise

            duration_ms = int((time.perf_counter() - started) * 1000)
            call = self._usage.build_call(
                role_id=request.role_id,
                output_schema=request.output_schema,
                attempt=attempt,
                duration_ms=duration_ms,
                raw_response=result.raw_response,
                success=True,
            )
            self._usage.record_success(call)
            logger.info(
                "llm invoke done role=%s output_schema=%s",
                request.role_id,
                output_schema_name,
            )
            return result.parsed

        try:
            return self._retry.run(attempt_fn)
        except BaseException as exc:
            wrapped = wrap_invoke_failure(exc, runtime=self._runtime)
            if wrapped is exc:
                raise
            raise wrapped from exc
