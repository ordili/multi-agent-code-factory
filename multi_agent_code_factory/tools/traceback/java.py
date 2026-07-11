"""Java JUnit / Surefire 栈解析。"""

from __future__ import annotations

import re
from pathlib import Path

from multi_agent_code_factory.schemas.retry_context import StackFrame, StackFrameRole
from multi_agent_code_factory.tools.traceback._paths import (
    is_framework_path,
    normalize_code_path,
)

# at com.example.CalcTest.testAdd(CalcTest.java:42)
_JAVA_AT_RE = re.compile(
    r"^\s*at\s+(?:(?:[\w.$]+\.)*[\w$]+)\((?P<file>[^:)]+):(?P<line>\d+)\)",
    re.MULTILINE,
)


def parse_java_traceback(
    text: str,
    *,
    code_root: Path,
) -> list[StackFrame]:
    raw_frames: list[tuple[str, int, None]] = []
    for match in _JAVA_AT_RE.finditer(text):
        rel = normalize_code_path(match.group("file"), code_root=code_root)
        if rel is None or is_framework_path(rel):
            continue
        raw_frames.append((rel, int(match.group("line")), None))

    if not raw_frames:
        return []

    count = len(raw_frames)
    result: list[StackFrame] = []
    for order, (file_path, line, _) in enumerate(reversed(raw_frames)):
        if order == 0:
            role = StackFrameRole.ROOT_CAUSE
        elif order == count - 1:
            role = StackFrameRole.TEST
        else:
            role = StackFrameRole.CALLER
        result.append(
            StackFrame(order=order, role=role, file=file_path, line=line, function=None)
        )
    return result
