"""栈帧路径过滤与相对路径规范化。"""

from __future__ import annotations

from pathlib import Path, PurePosixPath

_FRAMEWORK_MARKERS = (
    "site-packages",
    "dist-packages",
    "node_modules",
    "/target/debug/",
    "/target/release/",
    "vendor/",
    ".venv/",
    "\\site-packages\\",
    "\\target\\debug\\",
    "\\target\\release\\",
)


def is_framework_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    return any(marker.replace("\\", "/") in normalized for marker in _FRAMEWORK_MARKERS)


def normalize_code_path(path: str, *, code_root: Path) -> str | None:
    """将栈中的路径规范为相对 code_root 的 POSIX 路径。"""
    raw = path.strip().replace("\\", "/")
    if not raw or ".." in PurePosixPath(raw).parts:
        return None
    candidate = Path(raw)
    if candidate.is_absolute():
        try:
            rel = candidate.resolve().relative_to(code_root.resolve())
        except ValueError:
            return None
        return rel.as_posix()
    return PurePosixPath(raw).as_posix()
