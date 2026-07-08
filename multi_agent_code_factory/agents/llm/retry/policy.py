"""Retry policy configuration."""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass, replace

from multi_agent_code_factory.llm import LlmOutputMode

_TRANSIENT_ERROR_NAMES = frozenset(
    {
        "ResponseError",
        "ReadError",
        "RemoteProtocolError",
        "ConnectionError",
        "TimeoutError",
    }
)


def is_transient_llm_error(exc: BaseException) -> bool:
    """Return True when the error is likely transient and worth retrying."""
    name = type(exc).__name__
    if name in _TRANSIENT_ERROR_NAMES:
        return True
    message = str(exc).lower()
    return "502" in message or "503" in message or "connection" in message


@dataclass(frozen=True)
class RetryPolicy:
    """Retry attempts and linear backoff for LLM invokes."""

    max_attempts: int = 3
    backoff_base_sec: float = 1.5
    backoff_multiplier: float = 1.0
    is_retryable: Callable[[BaseException], bool] = is_transient_llm_error

    def backoff_sec(self, attempt: int) -> float:
        return self.backoff_base_sec * attempt * self.backoff_multiplier


_DEFAULT_POLICIES: dict[LlmOutputMode, RetryPolicy] = {
    "native_structured": RetryPolicy(max_attempts=3),
    "prompted_json": RetryPolicy(max_attempts=2),
}


def _env_max_retries() -> int | None:
    raw = os.environ.get("FACTORY_LLM_MAX_RETRIES")
    if raw is None or not raw.strip():
        return None
    try:
        value = int(raw.strip())
    except ValueError:
        return None
    return value if value >= 1 else None


def default_retry_policy(output_mode: LlmOutputMode) -> RetryPolicy:
    policy = _DEFAULT_POLICIES[output_mode]
    override = _env_max_retries()
    if override is None:
        return policy
    return replace(policy, max_attempts=override)
