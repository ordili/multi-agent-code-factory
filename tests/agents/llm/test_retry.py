"""Retry policy and executor tests."""

from __future__ import annotations

import pytest
from multi_agent_code_factory.agents.llm.retry.executor import RetryExecutor
from multi_agent_code_factory.agents.llm.retry.policy import (
    RetryPolicy,
    default_retry_policy,
    is_transient_llm_error,
)


def test_is_transient_llm_error_detects_connection_issues() -> None:
    assert is_transient_llm_error(ConnectionError("refused")) is True
    assert is_transient_llm_error(RuntimeError("HTTP 502 bad gateway")) is True
    assert is_transient_llm_error(ValueError("bad schema")) is False


def test_default_retry_policy_differs_by_output_mode() -> None:
    assert default_retry_policy("prompted_json").max_attempts == 2
    assert default_retry_policy("native_structured").max_attempts == 3


def test_default_retry_policy_honors_env_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FACTORY_LLM_MAX_RETRIES", "5")
    assert default_retry_policy("prompted_json").max_attempts == 5
    assert default_retry_policy("native_structured").max_attempts == 5


def test_retry_executor_retries_transient_errors() -> None:
    calls: list[int] = []

    def attempt_fn(attempt: int) -> str:
        calls.append(attempt)
        if attempt < 2:
            raise ConnectionError("temporary")
        return "ok"

    policy = RetryPolicy(max_attempts=3, backoff_base_sec=0)
    result = RetryExecutor(policy).run(attempt_fn)
    assert result == "ok"
    assert calls == [1, 2]


def test_retry_executor_does_not_retry_permanent_errors() -> None:
    policy = RetryPolicy(max_attempts=3, backoff_base_sec=0)

    def attempt_fn(_attempt: int) -> str:
        raise ValueError("permanent")

    with pytest.raises(ValueError, match="permanent"):
        RetryExecutor(policy).run(attempt_fn)
