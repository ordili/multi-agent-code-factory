"""在 code_root 下读取文件。"""

from __future__ import annotations

from pathlib import Path

from multi_agent_code_factory.tools._paths import resolve_in_root


def read_file(code_root: Path, relative_path: str, *, encoding: str = "utf-8") -> str:
    """读取 code_root 下的相对路径文件，返回文本内容。"""
    path = resolve_in_root(code_root, relative_path)
    return path.read_text(encoding=encoding)
