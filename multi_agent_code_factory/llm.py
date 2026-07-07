"""LLM client configuration (DeepSeek via OpenAI-compatible API)."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from langchain_core.language_models.chat_models import BaseChatModel

DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_DEEPSEEK_MODEL = "deepseek-chat"


class LlmConfigError(RuntimeError):
    """Raised when LLM configuration is missing or invalid."""


def deepseek_api_key() -> str | None:
    raw = os.environ.get("DEEPSEEK_API_KEY")
    if raw is None or not raw.strip():
        return None
    return raw.strip()


def llm_available() -> bool:
    return deepseek_api_key() is not None


def require_llm_api_key() -> str:
    key = deepseek_api_key()
    if key is None:
        msg = "DEEPSEEK_API_KEY is required for live LLM mode"
        raise LlmConfigError(msg)
    return key


def resolve_stub_mode(*, stub: bool, live: bool) -> bool:
    if stub and live:
        msg = "cannot use both --stub and --live"
        raise ValueError(msg)
    if live:
        require_llm_api_key()
        return False
    if stub:
        return True
    return True


def create_chat_model(
    *,
    model: str | None = None,
    temperature: float = 0.0,
    api_key: str | None = None,
    base_url: str | None = None,
) -> BaseChatModel:
    require_llm_api_key()
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:
        msg = (
            "langchain-openai is required for live mode; "
            "install with: pip install 'multi-agent-code-factory[llm]'"
        )
        raise LlmConfigError(msg) from exc

    kwargs: dict[str, Any] = {
        "model": model or os.environ.get("DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL),
        "temperature": temperature,
        "api_key": api_key or require_llm_api_key(),
        "base_url": base_url
        or os.environ.get("DEEPSEEK_BASE_URL", DEFAULT_DEEPSEEK_BASE_URL),
    }
    return ChatOpenAI(**kwargs)
