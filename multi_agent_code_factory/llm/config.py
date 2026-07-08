"""从环境变量解析 LLM 运行时配置。"""

from __future__ import annotations

import os

from multi_agent_code_factory.llm._env import read_env_secret
from multi_agent_code_factory.llm.providers import (
    DEFAULT_FACTORY_LLM_MODEL,
    DEFAULT_FACTORY_LLM_PROVIDER,
    PROVIDER_SPECS,
    provider_spec,
)
from multi_agent_code_factory.llm.types import LlmConfigError, LlmRuntimeConfig


def resolve_factory_llm_provider(*, provider: str | None = None) -> str:
    """从 ``FACTORY_LLM_PROVIDER`` 解析并校验活跃厂商 id。"""
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


def _normalize_ollama_base_url(base_url: str | None) -> str | None:
    if not base_url:
        return base_url
    normalized = base_url.strip()
    for host in ("http://localhost:", "https://localhost:"):
        if host in normalized:
            return normalized.replace(host, host.replace("localhost", "127.0.0.1"), 1)
    return normalized


def resolve_provider_base_url(provider_id: str) -> str | None:
    spec = provider_spec(provider_id)
    if spec.base_url_override_env:
        explicit = read_env_secret(spec.base_url_override_env)
        if explicit:
            base_url = explicit
        else:
            base_url = spec.base_url
    else:
        base_url = spec.base_url
    if provider_id == "ollama":
        return _normalize_ollama_base_url(base_url)
    return base_url


def api_key_for_provider(provider_id: str) -> str | None:
    spec = provider_spec(provider_id)
    return read_env_secret(spec.api_key_env)


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
        langchain_model_id=resolve_chat_model_id(provider=provider_id, model=model_name),
        base_url=resolved_base_url,
        api_key=resolved_key,
        output_mode=spec.output_mode,
    )


def llm_available(*, provider: str | None = None) -> bool:
    provider_id = resolve_factory_llm_provider(provider=provider)
    spec = provider_spec(provider_id)
    if not spec.api_key_required:
        return True
    return api_key_for_provider(provider_id) is not None
