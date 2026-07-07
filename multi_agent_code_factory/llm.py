"""LLM client configuration (provider-agnostic via LangChain init_chat_model).

Vendor selection is driven solely by ``FACTORY_LLM_PROVIDER`` (see ``PROVIDER_SPECS``).
``FACTORY_LLM_MODEL`` is only the model id/tag; it must not select the provider.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from langchain_core.language_models.chat_models import BaseChatModel

DEFAULT_FACTORY_LLM_PROVIDER = "deepseek"
DEFAULT_FACTORY_LLM_MODEL = "deepseek-chat"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"


@dataclass(frozen=True)
class LlmProviderSpec:
    """Maps ``FACTORY_LLM_PROVIDER`` id → API key env and LangChain wiring."""

    api_key_env: str
    langchain_provider: str
    base_url: str | None = None
    base_url_env: str | None = None
    api_key_required: bool = True


PROVIDER_SPECS: dict[str, LlmProviderSpec] = {
    "deepseek": LlmProviderSpec(
        api_key_env="DEEPSEEK_API_KEY",
        langchain_provider="openai",
        base_url="https://api.deepseek.com",
    ),
    "openai": LlmProviderSpec(
        api_key_env="OPENAI_API_KEY",
        langchain_provider="openai",
    ),
    "anthropic": LlmProviderSpec(
        api_key_env="ANTHROPIC_API_KEY",
        langchain_provider="anthropic",
    ),
    "ollama": LlmProviderSpec(
        api_key_env="OLLAMA_API_KEY",
        langchain_provider="ollama",
        base_url=DEFAULT_OLLAMA_BASE_URL,
        base_url_env="OLLAMA_BASE_URL",
        api_key_required=False,
    ),
}


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


class LlmConfigError(RuntimeError):
    """Raised when LLM configuration is missing or invalid."""


def list_factory_llm_providers() -> tuple[str, ...]:
    return tuple(PROVIDER_SPECS)


def resolve_factory_llm_provider(*, provider: str | None = None) -> str:
    """Return active vendor id from ``FACTORY_LLM_PROVIDER`` (factory provider registry)."""
    raw = provider or os.environ.get("FACTORY_LLM_PROVIDER", DEFAULT_FACTORY_LLM_PROVIDER)
    if not raw or not raw.strip():
        return DEFAULT_FACTORY_LLM_PROVIDER
    normalized = raw.strip().lower()
    if normalized not in PROVIDER_SPECS:
        supported = ", ".join(sorted(PROVIDER_SPECS))
        msg = f"unsupported FACTORY_LLM_PROVIDER={raw!r} (supported: {supported})"
        raise LlmConfigError(msg)
    return normalized


def resolve_factory_llm_model(*, model: str | None = None) -> str:
    raw = model or os.environ.get("FACTORY_LLM_MODEL", DEFAULT_FACTORY_LLM_MODEL)
    if not raw or not raw.strip():
        msg = "FACTORY_LLM_MODEL must not be empty"
        raise LlmConfigError(msg)
    return raw.strip()


def provider_spec(provider_id: str) -> LlmProviderSpec:
    try:
        return PROVIDER_SPECS[provider_id]
    except KeyError as exc:
        supported = ", ".join(sorted(PROVIDER_SPECS))
        msg = f"unsupported LLM provider {provider_id!r} (supported: {supported})"
        raise LlmConfigError(msg) from exc


def _read_env_secret(name: str) -> str | None:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return None
    return raw.strip()


def resolve_provider_base_url(provider_id: str) -> str | None:
    spec = provider_spec(provider_id)
    if spec.base_url_env:
        explicit = _read_env_secret(spec.base_url_env)
        if explicit:
            return explicit
    return spec.base_url


def api_key_for_provider(provider_id: str) -> str | None:
    spec = provider_spec(provider_id)
    return _read_env_secret(spec.api_key_env)


def resolve_chat_model_id(
    *,
    provider: str | None = None,
    model: str | None = None,
) -> str:
    """Build ``langchain_provider:model`` from ``FACTORY_LLM_PROVIDER`` + ``FACTORY_LLM_MODEL``."""
    provider_id = resolve_factory_llm_provider(provider=provider)
    model_name = resolve_factory_llm_model(model=model)
    spec = provider_spec(provider_id)
    return f"{spec.langchain_provider}:{model_name}"


def resolve_llm_runtime_config(
    *,
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> LlmRuntimeConfig:
    provider_id = resolve_factory_llm_provider(provider=provider)
    spec = provider_spec(provider_id)
    model_name = resolve_factory_llm_model(model=model)
    resolved_key = api_key if api_key is not None else require_llm_api_key(provider=provider_id)
    resolved_base_url = base_url if base_url is not None else resolve_provider_base_url(
        provider_id
    )
    return LlmRuntimeConfig(
        factory_provider=provider_id,
        model=model_name,
        api_key_env=spec.api_key_env,
        langchain_provider=spec.langchain_provider,
        langchain_model_id=f"{spec.langchain_provider}:{model_name}",
        base_url=resolved_base_url,
        api_key=resolved_key,
    )


def llm_available(*, provider: str | None = None) -> bool:
    provider_id = resolve_factory_llm_provider(provider=provider)
    spec = provider_spec(provider_id)
    if not spec.api_key_required:
        return True
    return api_key_for_provider(provider_id) is not None


def require_llm_api_key(*, provider: str | None = None) -> str:
    provider_id = resolve_factory_llm_provider(provider=provider)
    spec = provider_spec(provider_id)
    if not spec.api_key_required:
        return api_key_for_provider(provider_id) or ""
    key = api_key_for_provider(provider_id)
    if key is None:
        msg = (
            f"{spec.api_key_env} is required when FACTORY_LLM_PROVIDER={provider_id!r}"
        )
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
    provider: str | None = None,
    model: str | None = None,
    temperature: float = 0.0,
    api_key: str | None = None,
    base_url: str | None = None,
) -> BaseChatModel:
    """Create a chat model via LangChain ``init_chat_model`` (1.x unified API)."""
    runtime = resolve_llm_runtime_config(
        provider=provider,
        model=model,
        api_key=api_key,
        base_url=base_url,
    )
    try:
        from langchain.chat_models import init_chat_model
    except ImportError as exc:
        msg = (
            "langchain is required for live mode; "
            "install with: pip install 'multi-agent-code-factory[llm]'"
        )
        raise LlmConfigError(msg) from exc

    kwargs: dict[str, Any] = {"temperature": temperature}
    if runtime.api_key:
        kwargs["api_key"] = runtime.api_key
    if runtime.base_url:
        kwargs["base_url"] = runtime.base_url

    chat_model = init_chat_model(runtime.langchain_model_id, **kwargs)
    return cast("BaseChatModel", chat_model)
