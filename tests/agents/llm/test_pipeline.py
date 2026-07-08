"""Structured invoke pipeline tests."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel, Field

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.llm.pipeline import StructuredInvokePipeline
from multi_agent_code_factory.agents.llm.types import InvokeRequest
from multi_agent_code_factory.config import LoopLimits
from multi_agent_code_factory.llm import LlmInvokeError, LlmRuntimeConfig
from multi_agent_code_factory.profile_config import load_profile
from multi_agent_code_factory.tools.run_artifacts import RunArtifactWriter


class _EchoSchema(BaseModel):
    message: str = Field(min_length=1)


def test_pipeline_records_success_and_returns_parsed(tmp_path: Path) -> None:
    profile = load_profile("python")
    writer = RunArtifactWriter("pipeline-success", base_dir=tmp_path)
    writer.init_run_meta(profile, LoopLimits())

    parsed = _EchoSchema(message="hello")
    model = MagicMock()
    structured = MagicMock()
    structured.invoke.return_value = {
        "parsed": parsed,
        "raw": SimpleNamespace(
            usage_metadata={"input_tokens": 5, "output_tokens": 3, "total_tokens": 8}
        ),
    }
    model.with_structured_output.return_value = structured

    runtime = LlmRuntimeConfig(
        factory_provider="openai",
        model="gpt-4o-mini",
        api_key_env="OPENAI_API_KEY",
        langchain_provider="openai",
        langchain_model_id="openai:gpt-4o-mini",
        base_url=None,
        api_key="sk-test",
        output_mode="native_structured",
    )
    pipeline = StructuredInvokePipeline(
        writer=writer,
        profile=profile,
        factory_config=None,
        runtime=runtime,
        model=model,
    )
    request = InvokeRequest(
        role_id=AgentRole.PM,
        output_schema=_EchoSchema,
        context={"message": "hello"},
    )
    result = pipeline.execute(request)
    assert result.message == "hello"

    usage = writer.read_llm_usage()
    assert usage is not None
    assert usage.totals.llm_calls == 1
    assert usage.totals.total_tokens == 8
    assert usage.calls[0].success is True

    meta = writer.read_meta()
    assert meta is not None
    assert meta.budget is not None
    assert meta.budget.used_llm_calls == 1


def test_pipeline_records_failed_attempts(tmp_path: Path) -> None:
    profile = load_profile("python")
    writer = RunArtifactWriter("pipeline-failure", base_dir=tmp_path)
    writer.init_run_meta(profile, LoopLimits())

    model = MagicMock()
    structured = MagicMock()
    structured.invoke.side_effect = ValueError("bad output")
    model.with_structured_output.return_value = structured

    runtime = LlmRuntimeConfig(
        factory_provider="openai",
        model="gpt-4o-mini",
        api_key_env="OPENAI_API_KEY",
        langchain_provider="openai",
        langchain_model_id="openai:gpt-4o-mini",
        base_url=None,
        api_key="sk-test",
        output_mode="native_structured",
    )
    pipeline = StructuredInvokePipeline(
        writer=writer,
        profile=profile,
        factory_config=None,
        runtime=runtime,
        model=model,
    )
    request = InvokeRequest(
        role_id=AgentRole.PM,
        output_schema=_EchoSchema,
        context={"message": "hello"},
    )
    with pytest.raises(LlmInvokeError):
        pipeline.execute(request)

    usage = writer.read_llm_usage()
    assert usage is not None
    assert usage.totals.llm_calls == 1
    assert usage.calls[0].success is False
    assert usage.calls[0].error_type == "ValueError"

    meta = writer.read_meta()
    assert meta is not None
    assert meta.budget is None or (meta.budget.used_llm_calls or 0) == 0
