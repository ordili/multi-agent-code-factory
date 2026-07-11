"""Solidity / Foundry revert 文本解析（Tier C）。"""

from __future__ import annotations

import re
from pathlib import Path

from multi_agent_code_factory.schemas.retry_context import StackFrame, StackFrameRole
from multi_agent_code_factory.tools.traceback._paths import (
    is_framework_path,
    normalize_code_path,
)

_SOL_LINE_RE = re.compile(
    r"(?P<file>[\w./\\-]+\.sol):(?P<line>\d+)",
)


def parse_solidity_traceback(
    text: str,
    *,
    code_root: Path,
) -> list[StackFrame]:
    seen: set[tuple[str, int]] = set()
    raw_frames: list[tuple[str, int, None]] = []
    for match in _SOL_LINE_RE.finditer(text):
        rel = normalize_code_path(match.group("file"), code_root=code_root)
        if rel is None or is_framework_path(rel):
            continue
        key = (rel, int(match.group("line")))
        if key in seen:
            continue
        seen.add(key)
        raw_frames.append((rel, key[1], None))

    if not raw_frames:
        return []

    result: list[StackFrame] = []
    for order, (file_path, line, _) in enumerate(reversed(raw_frames)):
        role = StackFrameRole.ROOT_CAUSE if order == 0 else StackFrameRole.CALLER
        result.append(
            StackFrame(order=order, role=role, file=file_path, line=line, function=None)
        )
    return result
