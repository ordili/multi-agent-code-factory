"""重试循环执行器。"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

from multi_agent_code_factory.agents.llm.retry.policy import RetryPolicy

T = TypeVar("T")


class RetryExecutor:
    """按配置对可调用对象执行重试，可选失败回调。"""

    def __init__(self, policy: RetryPolicy) -> None:
        self._policy = policy

    @property
    def max_attempts(self) -> int:
        return self._policy.max_attempts

    def run(
        self,
        attempt_fn: Callable[[int], T],
        *,
        on_attempt_failure: Callable[[int, BaseException], None] | None = None,
    ) -> T:
        last_error: BaseException | None = None
        for attempt in range(1, self._policy.max_attempts + 1):
            try:
                return attempt_fn(attempt)
            except BaseException as exc:
                last_error = exc
                if on_attempt_failure is not None:
                    on_attempt_failure(attempt, exc)
                if attempt < self._policy.max_attempts and self._policy.is_retryable(
                    exc
                ):
                    time.sleep(self._policy.backoff_sec(attempt))
                    continue
                raise
        assert last_error is not None
        raise last_error
