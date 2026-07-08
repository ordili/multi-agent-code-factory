"""Structured LLM runner facade."""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.llm.pipeline import StructuredInvokePipeline
from multi_agent_code_factory.agents.llm.prompt.loader import load_role_prompt
from multi_agent_code_factory.agents.llm.types import InvokeRequest
from multi_agent_code_factory.config import FactoryConfig
from multi_agent_code_factory.llm import LlmRuntimeConfig, create_chat_model, resolve_llm_runtime_config
from multi_agent_code_factory.profiles import ProfileConfig
from multi_agent_code_factory.tools.write_artifact import RunArtifactWriter

T = TypeVar("T", bound=BaseModel)


class LlmRunner:
    """Invoke LLM by role and parse structured output; update run budget and usage."""

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
        """Load role system prompt."""
        return load_role_prompt(self.profile, role_id)

    def invoke_structured(
        self,
        *,
        role_id: AgentRole,
        schema: type[T],
        context: dict[str, Any],
        extra_system: str | None = None,
    ) -> T:
        """Call LLM and parse to the given Pydantic schema."""
        request = InvokeRequest(
            role_id=role_id,
            schema=schema,
            context=context,
            extra_system=extra_system,
        )
        return self._pipeline.execute(request)
