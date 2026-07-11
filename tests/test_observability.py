from __future__ import annotations

import os

import pytest
from multi_agent_code_factory.observability.langsmith import (
    build_continue_invoke_input,
    build_run_config,
    build_trace_inputs,
    build_trace_output,
    configure_tracing_env,
    is_tracing_enabled,
)
from multi_agent_code_factory.schemas.run_meta import RunStatus
from multi_agent_code_factory.state import PipelineState


@pytest.fixture(autouse=True)
def _clear_tracing_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "LANGSMITH_TRACING",
        "LANGCHAIN_TRACING_V2",
        "LANGSMITH_API_KEY",
        "LANGCHAIN_API_KEY",
        "LANGSMITH_PROJECT",
        "LANGCHAIN_PROJECT",
        "LANGSMITH_ENDPOINT",
        "LANGCHAIN_ENDPOINT",
    ):
        monkeypatch.delenv(key, raising=False)


def test_is_tracing_enabled_reads_langsmith_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert is_tracing_enabled() is False
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    assert is_tracing_enabled() is True


def test_configure_tracing_env_syncs_langchain_vars(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.setenv("LANGSMITH_API_KEY", "ls_test")
    monkeypatch.setenv("LANGSMITH_PROJECT", "factory-tests")

    assert configure_tracing_env() is True
    assert os.environ["LANGCHAIN_TRACING_V2"] == "true"
    assert os.environ["LANGCHAIN_API_KEY"] == "ls_test"
    assert os.environ["LANGCHAIN_PROJECT"] == "factory-tests"


def test_build_run_config_includes_trace_metadata() -> None:
    config = build_run_config(
        task_id="arbitrage",
        profile_id="rust",
        pipeline_mode="continue",
        agent_mode="live",
        user_request="Monitor BSC DEX arbitrage opportunities",
        reentry="architect",
    )
    assert config["run_name"] == "arbitrage"
    assert config["metadata"]["pipeline_mode"] == "continue"
    assert config["metadata"]["reentry"] == "architect"
    assert config["metadata"]["user_request_preview"].startswith("Monitor BSC")
    assert "pipeline_mode:continue" in config["tags"]
    assert "reentry:architect" in config["tags"]


def test_build_trace_inputs_truncates_long_user_request() -> None:
    long_request = "x" * 400
    payload = build_trace_inputs(
        task_id="arbitrage",
        profile_id="rust",
        pipeline_mode="continue",
        agent_mode="live",
        user_request=long_request,
        reentry="architect",
    )
    assert payload["task_id"] == "arbitrage"
    assert payload["reentry"] == "architect"
    assert len(payload["user_request"]) == 300
    assert payload["user_request"].endswith("…")


def test_build_continue_invoke_input_preserves_full_user_request() -> None:
    state = PipelineState(
        task_id="arbitrage",
        user_request="full original user request text",
    )
    payload = build_continue_invoke_input(state)
    assert payload == {
        "task_id": "arbitrage",
        "user_request": "full original user request text",
    }


def test_build_trace_output_summarizes_final_state() -> None:
    state = PipelineState(
        task_id="arbitrage",
        user_request="todo",
        design_revision_count=1,
        impl_retry_count=0,
        pipeline_route="design_validate",
    )
    output = build_trace_output(state, status=RunStatus.COMPLETED)
    assert output["status"] == "completed"
    assert output["task_id"] == "arbitrage"
    assert output["design_revision_count"] == 1
    assert output["pipeline_route"] == "design_validate"
