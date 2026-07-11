"""Run 目录产物路径规范化。"""

from __future__ import annotations

from pathlib import PurePosixPath


class InvalidRunMmdPathError(ValueError):
    """Mermaid 产物路径不符合 Run 根目录扁平 *.mmd 约定。"""


def normalize_run_mmd_path(path: str) -> str:
    """将 LLM 输出的 path 规范为 Run 目录下的单个 ``*.mmd`` 文件名。

    ``docs/design.mmd`` → ``design.mmd``；禁止 ``..`` 与绝对路径。
    """
    stripped = path.strip()
    if not stripped:
        msg = "mmd path must not be empty"
        raise InvalidRunMmdPathError(msg)

    pure = PurePosixPath(stripped.replace("\\", "/"))
    if pure.is_absolute():
        msg = f"absolute mmd path not allowed: {path!r}"
        raise InvalidRunMmdPathError(msg)
    if ".." in pure.parts:
        msg = f"path traversal not allowed: {path!r}"
        raise InvalidRunMmdPathError(msg)

    name = pure.name
    if not name.endswith(".mmd"):
        msg = f"mmd path must end with .mmd: {path!r}"
        raise InvalidRunMmdPathError(msg)
    return name
