"""结构化 LLM 调用门面（LlmRunner）。"""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.llm.pipeline import StructuredInvokePipeline
from multi_agent_code_factory.agents.llm.prompt.loader import load_role_prompt
from multi_agent_code_factory.agents.llm.types import InvokeRequest
from multi_agent_code_factory.config import FactoryConfig
from multi_agent_code_factory.llm import (
    LlmRuntimeConfig,
    create_chat_model,
    resolve_llm_runtime_config,
)
from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.tools.run_artifacts import RunArtifactWriter

T = TypeVar("T", bound=BaseModel)


class LlmRunner:
    """按角色调用 LLM 并解析结构化输出，同时更新 run 预算与用量。"""

    def __init__(
        self,
        writer: RunArtifactWriter,
        profile: ProfileConfig,
        *,
        factory_config: FactoryConfig | None = None,
        model: Any | None = None,
        runtime: LlmRuntimeConfig | None = None,
        pipeline: StructuredInvokePipeline | None = None,
    ) -> None:
        self.writer = writer
        self.profile = profile
        self.factory_config = factory_config
        self._runtime = runtime or resolve_llm_runtime_config()
        self._model = model if model is not None else create_chat_model()
        self._pipeline = pipeline or StructuredInvokePipeline(
            writer=writer,
            profile=profile,
            factory_config=factory_config,
            runtime=self._runtime,
            model=self._model,
        )

    def load_role_prompt(self, role_id: AgentRole) -> str:
        """加载角色 system prompt。"""
        return load_role_prompt(self.profile, role_id)

    def invoke_structured(
        self,
        *,
        role_id: AgentRole,
        output_schema: type[T],
        context: dict[str, Any],
        extra_system: str | None = None,
    ) -> T:
        """调用 LLM 并解析为指定 Pydantic 输出模型。"""
        request = InvokeRequest(
            role_id=role_id,
            output_schema=output_schema,
            context=context,
            extra_system=extra_system,
        )
        return self._pipeline.execute(request)
