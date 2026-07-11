"""Coverage 解析器共享类型。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CoverageCommandResult:
    exit_code: int
    stdout: str
    stderr: str
    command: str
