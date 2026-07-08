"""llm_usage.json 审计日志。"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from pydantic import BaseModel

from multi_agent_code_factory.agents.llm.usage import (
    LlmCallUsage,
    LlmUsageLog,
    LlmUsageTotals,
    merge_usage_totals,
)


class LlmUsageStore:
    """追加并读取 LLM 调用用量审计。"""

    def __init__(
        self,
        directory: Path,
        *,
        write_model: Callable[[str, BaseModel], Path],
    ) -> None:
        self._directory = directory
        self._write_model = write_model
        self._path = directory / "llm_usage.json"

    @property
    def path(self) -> Path:
        return self._path

    def read(self) -> LlmUsageLog | None:
        """读取 llm_usage.json，不存在时返回 None。"""
        if not self._path.is_file():
            return None
        data = json.loads(self._path.read_text(encoding="utf-8"))
        return LlmUsageLog.model_validate(data)

    def record(
        self,
        call: LlmCallUsage,
        *,
        provider: str,
        model: str,
    ) -> LlmUsageLog:
        """追加一次 LLM 调用记录并更新累计用量。"""
        existing = self.read()
        if existing is None:
            log = LlmUsageLog(
                version="1",
                provider=provider,
                model=model,
                calls=[call],
                totals=merge_usage_totals(LlmUsageTotals(), call),
            )
        else:
            log = existing.model_copy(
                update={
                    "provider": provider,
                    "model": model,
                    "calls": [*existing.calls, call],
                    "totals": merge_usage_totals(existing.totals, call),
                }
            )
        self._write_model("llm_usage.json", log)
        return log
