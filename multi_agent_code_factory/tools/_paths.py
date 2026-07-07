"""Path helpers for tools operating under code_root."""

from __future__ import annotations

from pathlib import Path


class PathEscapeError(ValueError):
    """Raised when a path resolves outside the allowed root."""


def resolve_in_root(root: Path, relative_path: str) -> Path:
    base = root.resolve()
    target = (base / relative_path).resolve()
    try:
        target.relative_to(base)
    except ValueError as exc:
        msg = f"path escapes code_root: {relative_path!r} -> {target}"
        raise PathEscapeError(msg) from exc
    return target
