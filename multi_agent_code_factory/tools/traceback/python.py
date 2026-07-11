"""Python pytest traceback 解析。"""

from __future__ import annotations

import re
from pathlib import Path

from multi_agent_code_factory.schemas.retry_context import StackFrame, StackFrameRole
from multi_agent_code_factory.tools.traceback._paths import (
    is_framework_path,
    normalize_code_path,
)

_FILE_LINE_RE = re.compile(
    r'^\s*File "(?P<file>[^"]+)", line (?P<line>\d+)(?:, in (?P<func>[^"]+))?',
    re.MULTILINE,
)


def parse_python_traceback(
    text: str,
    *,
    code_root: Path,
) -> list[StackFrame]:
    raw_frames: list[tuple[str, int, str | None]] = []
    for match in _FILE_LINE_RE.finditer(text):
        rel = normalize_code_path(match.group("file"), code_root=code_root)
        if rel is None or is_framework_path(rel):
            continue
        raw_frames.append((rel, int(match.group("line")), match.group("func")))

    if not raw_frames:
        return []

    user_frames = list(raw_frames)
    count = len(user_frames)
    result: list[StackFrame] = []
    for order, (file_path, line, func) in enumerate(reversed(user_frames)):
        if order == 0:
            role = StackFrameRole.ROOT_CAUSE
        elif order == count - 1:
            role = StackFrameRole.TEST
        else:
            role = StackFrameRole.CALLER
        result.append(
            StackFrame(
                order=order,
                role=role,
                file=file_path,
                line=line,
                function=func,
            )
        )
    return result
