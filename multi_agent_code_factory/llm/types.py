"""LLM 配置类型与异常。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

LlmOutputMode = Literal["native_structured", "prompted_json"]


@dataclass(frozen=True)
class LlmProviderSpec:
    """Maps ``FACTORY_LLM_PROVIDER`` id → API key env and LangChain wiring."""

    api_key_env: str
    langchain_provider: str
    # 厂商默认 API 地址；OpenAI/Anthropic 为 ``None`` 时用 SDK 默认域名。
    base_url: str | None = None
    # 用 ``.env`` 覆盖 ``base_url``，适配本机/VM/Docker 等不同部署地址。
    base_url_override_env: str | None = None
    # ``False``：本地 Ollama 等无需 Key 即可联调；云端厂商保持 ``True``。
    api_key_required: bool = True
    output_mode: LlmOutputMode = "native_structured"


@dataclass(frozen=True)
class LlmRuntimeConfig:
    """Resolved live LLM settings from ``FACTORY_LLM_PROVIDER`` + ``FACTORY_LLM_MODEL``."""

    factory_provider: str
    model: str
    api_key_env: str
    langchain_provider: str
    langchain_model_id: str
    base_url: str | None
    api_key: str
    output_mode: LlmOutputMode


class LlmConfigError(RuntimeError):
    """Raised when LLM configuration is missing or invalid."""


class LlmInvokeError(RuntimeError):
    """Raised when a live LLM call fails (HTTP, Ollama crash, parse errors)."""
