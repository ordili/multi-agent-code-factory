"""从仓库根目录加载可选 ``.env`` 到进程环境（密钥与运行时覆盖）。"""

from __future__ import annotations

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
    try:
        from multi_agent_code_factory.observability import configure_tracing_env

        configure_tracing_env()
    except ImportError:
        pass
    return True


def reset_env_loaded_for_tests() -> None:
    """Allow tests to reload `.env` after changing cwd or env file contents."""
    global _ENV_LOADED
    _ENV_LOADED = False
