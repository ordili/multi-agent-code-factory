"""Read a file relative to code_root."""

from __future__ import annotations

from pathlib import Path

from multi_agent_code_factory.tools._paths import resolve_in_root


def read_file(code_root: Path, relative_path: str, *, encoding: str = "utf-8") -> str:
    path = resolve_in_root(code_root, relative_path)
    return path.read_text(encoding=encoding)
