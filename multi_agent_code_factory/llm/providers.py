"""LLM 厂商注册表与默认常量。"""

from __future__ import annotations

from multi_agent_code_factory.llm.types import LlmConfigError, LlmProviderSpec

DEFAULT_FACTORY_LLM_PROVIDER = "deepseek"
DEFAULT_FACTORY_LLM_MODEL = "deepseek-chat"
# Use IPv4 loopback: on Windows, ``localhost`` often resolves to ::1 while Ollama
# listens on 127.0.0.1 only, which surfaces as HTTP 502 from LangChain invoke.
DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"

PROVIDER_SPECS: dict[str, LlmProviderSpec] = {
    "deepseek": LlmProviderSpec(
        api_key_env="DEEPSEEK_API_KEY",
        langchain_provider="openai",
        base_url="https://api.deepseek.com",
        output_mode="prompted_json",
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
        base_url_override_env="OLLAMA_BASE_URL",
        api_key_required=False,
        output_mode="prompted_json",
    ),
}


def list_factory_llm_providers() -> tuple[str, ...]:
    return tuple(PROVIDER_SPECS)


def provider_spec(provider_id: str) -> LlmProviderSpec:
    try:
        return PROVIDER_SPECS[provider_id]
    except KeyError as exc:
        supported = ", ".join(sorted(PROVIDER_SPECS))
        msg = f"unsupported LLM provider {provider_id!r} (supported: {supported})"
        raise LlmConfigError(msg) from exc
