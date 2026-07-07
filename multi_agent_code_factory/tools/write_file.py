"""Write a file relative to code_root."""

from __future__ import annotations

from pathlib import Path

from multi_agent_code_factory.tools._paths import resolve_in_root


def write_file(
    code_root: Path,
    relative_path: str,
    content: str,
    *,
    encoding: str = "utf-8",
) -> Path:
    path = resolve_in_root(code_root, relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=encoding)
    return path
