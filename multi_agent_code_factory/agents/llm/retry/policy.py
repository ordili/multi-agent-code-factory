"""LLM 重试策略配置。"""

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
    """判断异常是否为可重试的瞬态 LLM/网络错误。"""
    name = type(exc).__name__
    if name in _TRANSIENT_ERROR_NAMES:
        return True
    message = str(exc).lower()
    return "502" in message or "503" in message or "connection" in message


def is_retryable_prompted_json_error(exc: BaseException) -> bool:
    """prompted_json 模式：网络瞬态错误与 schema 解析失败均可重试。"""
    if is_transient_llm_error(exc):
        return True
    # Local import avoids import cycle with agents.llm.errors.
    from multi_agent_code_factory.agents.llm.errors import LlmParseError

    return isinstance(exc, LlmParseError)


@dataclass(frozen=True)
class RetryPolicy:
    """LLM 调用的重试次数与线性退避配置。"""

    max_attempts: int = 3
    backoff_base_sec: float = 1.5
    backoff_multiplier: float = 1.0
    is_retryable: Callable[[BaseException], bool] = is_transient_llm_error

    def backoff_sec(self, attempt: int) -> float:
        return self.backoff_base_sec * attempt * self.backoff_multiplier


_DEFAULT_POLICIES: dict[LlmOutputMode, RetryPolicy] = {
    "native_structured": RetryPolicy(max_attempts=3),
    "prompted_json": RetryPolicy(
        max_attempts=2,
        is_retryable=is_retryable_prompted_json_error,
    ),
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
