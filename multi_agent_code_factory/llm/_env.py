"""LLM 相关环境变量读取辅助。"""

from __future__ import annotations

import os

from multi_agent_code_factory.llm.types import LlmConfigError


def read_env_secret(name: str) -> str | None:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return None
    return raw.strip()


def read_env_int(name: str) -> int | None:
    raw = read_env_secret(name)
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError as exc:
        msg = f"{name} must be an integer, got {raw!r}"
        raise LlmConfigError(msg) from exc


def read_env_bool(name: str) -> bool | None:
    raw = read_env_secret(name)
    if raw is None:
        return None
    normalized = raw.lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    msg = f"{name} must be a boolean (true/false), got {raw!r}"
    raise LlmConfigError(msg)
