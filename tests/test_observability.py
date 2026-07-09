from __future__ import annotations

import os

import pytest
from multi_agent_code_factory.observability.langsmith import (
    build_run_config,
    configure_tracing_env,
    is_tracing_enabled,
)


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


def test_build_run_config_includes_task_id() -> None:
    config = build_run_config(task_id="todo-cli", profile_id="python")
    assert config["run_name"] == "todo-cli"
    assert config["metadata"]["task_id"] == "todo-cli"
    assert config["metadata"]["profile_id"] == "python"
    assert "task_id:todo-cli" in config["tags"]
