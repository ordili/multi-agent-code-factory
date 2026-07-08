"""仓库与包路径解析（策略、Profile、运行目录等）。"""

from __future__ import annotations

from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PACKAGE_DIR.parent


def package_dir() -> Path:
    return _PACKAGE_DIR


def repo_root() -> Path:
    return _REPO_ROOT


def default_policy_path() -> Path:
    return _REPO_ROOT / "config" / "autonomy_policy.yaml"


def profiles_dir() -> Path:
    return _PACKAGE_DIR / "profiles"


def runs_dir() -> Path:
    return _REPO_ROOT / "docs" / "runs"


def run_dir(task_id: str) -> Path:
    return runs_dir() / task_id
