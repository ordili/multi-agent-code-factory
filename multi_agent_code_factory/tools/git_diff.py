"""在 code_root 下获取 git 工作区 diff，供 Reviewer 审查实现变更。"""

from __future__ import annotations

import subprocess
from pathlib import Path

_DIFF_CHAR_LIMIT = 12_000


def _truncate(text: str, limit: int = _DIFF_CHAR_LIMIT) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 24] + "\n... (diff truncated)"


def git_diff(
    code_root: Path,
    *,
    paths: list[str] | None = None,
) -> str:
    """返回 ``code_root`` 内未提交变更的 unified diff；非 git 仓库时返回空字符串。"""
    root = code_root.resolve()
    if not (root / ".git").is_dir():
        return ""

    command = ["git", "diff", "--no-color", "HEAD"]
    if paths:
        command.extend(paths)

    completed = subprocess.run(
        command,
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return ""

    diff = completed.stdout.strip()
    if not diff:
        untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if untracked.returncode == 0 and untracked.stdout.strip():
            lines = untracked.stdout.strip().splitlines()
            if paths:
                allowed = {_normalize_path(path) for path in paths}
                lines = [line for line in lines if _normalize_path(line) in allowed]
            if lines:
                return _truncate(
                    "Untracked files (no staged diff):\n"
                    + "\n".join(f"+ {line}" for line in lines)
                )
        return ""

    return _truncate(diff)


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/")
