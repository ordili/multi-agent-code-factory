"""Load optional `.env` from the repository root into process environment.

Only runtime secrets and environment-specific overrides belong in ``.env``.
Stack defaults (language, toolchain, validation) belong in Profile YAML.
See docs/design/pipeline/profiles.md §0.
"""

from __future__ import annotations

import os
from pathlib import Path

from multi_agent_code_factory._paths import repo_root

_ENV_LOADED = False


def env_file_path(*, root: Path | None = None) -> Path:
    return (root or repo_root()) / ".env"


def load_env_file(*, root: Path | None = None, override: bool = False) -> bool:
    """Load ``.env`` if present. Existing env vars win unless ``override`` is True."""
    global _ENV_LOADED
    if _ENV_LOADED:
        return False

    path = env_file_path(root=root)
    if not path.is_file():
        _ENV_LOADED = True
        return False

    try:
        from dotenv import load_dotenv
    except ImportError:
        msg = (
            f"found {path} but python-dotenv is not installed; "
            "reinstall the package or set environment variables manually"
        )
        raise RuntimeError(msg) from None

    load_dotenv(dotenv_path=path, override=override)
    _ENV_LOADED = True
    return True


def reset_env_loaded_for_tests() -> None:
    """Allow tests to reload `.env` after changing cwd or env file contents."""
    global _ENV_LOADED
    _ENV_LOADED = False
