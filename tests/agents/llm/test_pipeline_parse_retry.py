"""Pipeline parse-retry feedback tests."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.llm.errors import LlmParseError
from multi_agent_code_factory.agents.llm.pipeline import StructuredInvokePipeline
from multi_agent_code_factory.agents.llm.types import InvokeRequest, InvokeResult
from multi_agent_code_factory.config import LoopLimits
from multi_agent_code_factory.llm import LlmRuntimeConfig
from multi_agent_code_factory.profile_config import load_profile
from multi_agent_code_factory.tools.run_artifacts import RunArtifactWriter
from pydantic import BaseModel, Field


class _EchoSchema(BaseModel):
    message: str = Field(min_length=1)


def test_pipeline_appends_parse_feedback_on_prompted_json_retry(tmp_path: Path) -> None:
    profile = load_profile("python")
    writer = RunArtifactWriter("pipeline-parse-retry", base_dir=tmp_path)
    writer.init_run_meta(profile, LoopLimits())

    parsed = _EchoSchema(message="ok")
    model = MagicMock()
    system_prompts: list[str] = []

    def fake_invoke(
        _model: object,
        *,
        role_id: AgentRole,
        output_schema: type[BaseModel],
        system_prompt: str,
        user_prompt: str,
    ) -> InvokeResult[_EchoSchema]:
        system_prompts.append(system_prompt)
        if len(system_prompts) == 1:
            raise LlmParseError("JSON did not match _EchoSchema: message")
        return InvokeResult(parsed=parsed, raw_response=SimpleNamespace(content="{}"))

    strategy = MagicMock()
    strategy.invoke.side_effect = fake_invoke

    runtime = LlmRuntimeConfig(
        factory_provider="deepseek",
        model="deepseek-v4-pro",
        api_key_env="DEEPSEEK_API_KEY",
        langchain_provider="deepseek",
        langchain_model_id="deepseek:deepseek-v4-pro",
        base_url=None,
        api_key="sk-test",
        output_mode="prompted_json",
    )
    pipeline = StructuredInvokePipeline(
        writer=writer,
        profile=profile,
        factory_config=None,
        runtime=runtime,
        model=model,
    )
    pipeline._strategy = strategy

    request = InvokeRequest(
        role_id=AgentRole.PM,
        output_schema=_EchoSchema,
        context={"message": "hello"},
    )
    result = pipeline.execute(request)
    assert result.message == "ok"
    assert len(system_prompts) == 2
    assert "Previous JSON output failed" in system_prompts[1]
    assert "message" in system_prompts[1]

    usage = writer.read_llm_usage()
    assert usage is not None
    assert usage.totals.llm_calls == 2
