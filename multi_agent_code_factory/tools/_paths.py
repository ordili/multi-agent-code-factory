"""工具模块使用的路径辅助函数（限定在 code_root 内操作）。"""

from __future__ import annotations

from pathlib import Path


class PathEscapeError(ValueError):
    """路径解析结果超出允许的根目录时抛出。"""


def resolve_in_root(root: Path, relative_path: str) -> Path:
    """将相对路径解析为绝对路径，并确保不逃逸出 root。"""
    base = root.resolve()
    target = (base / relative_path).resolve()
    # 校验目标路径仍在根目录内
    try:
        target.relative_to(base)
    except ValueError as exc:
        msg = f"path escapes code_root: {relative_path!r} -> {target}"
        raise PathEscapeError(msg) from exc
    return target
