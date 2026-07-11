"""按 profile.language 分发 traceback 解析。"""

from __future__ import annotations

from pathlib import Path

from multi_agent_code_factory.schemas.retry_context import StackFrame
from multi_agent_code_factory.tools.traceback.go import parse_go_traceback
from multi_agent_code_factory.tools.traceback.java import parse_java_traceback
from multi_agent_code_factory.tools.traceback.python import parse_python_traceback
from multi_agent_code_factory.tools.traceback.rust import parse_rust_traceback
from multi_agent_code_factory.tools.traceback.solidity import parse_solidity_traceback

_PARSERS = {
    "python": parse_python_traceback,
    "java": parse_java_traceback,
    "rust": parse_rust_traceback,
    "go": parse_go_traceback,
    "solidity": parse_solidity_traceback,
}


def parse_traceback(
    text: str,
    *,
    language: str,
    code_root: Path,
) -> list[StackFrame]:
    parser = _PARSERS.get(language)
    if parser is None:
        return []
    return parser(text, code_root=code_root)
