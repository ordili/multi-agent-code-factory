"""测试解析器共享类型定义。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandResult:
    """Shell 命令执行结果。"""

    exit_code: int
    stdout: str
    stderr: str
    duration_sec: float
    command: str
