"""在 code_root 下写入文件。"""

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
    """将内容写入 code_root 下的相对路径文件，必要时创建父目录。"""
    path = resolve_in_root(code_root, relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=encoding)
    return path
