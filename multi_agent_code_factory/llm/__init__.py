"""LLM 客户端配置（经 LangChain init_chat_model，厂商无关）。

厂商由 ``FACTORY_LLM_PROVIDER`` 选择；``FACTORY_LLM_MODEL`` 仅指定模型 id。
"""

from multi_agent_code_factory.llm.config import (
    api_key_for_provider,
    llm_available,
    require_llm_api_key,
    resolve_chat_model_id,
    resolve_factory_llm_model,
    resolve_factory_llm_provider,
    resolve_llm_runtime_config,
    resolve_provider_base_url,
)
from multi_agent_code_factory.llm.factory import create_chat_model
from multi_agent_code_factory.llm.health import preflight_live_llm
from multi_agent_code_factory.llm.providers import (
    DEFAULT_FACTORY_LLM_MODEL,
    DEFAULT_FACTORY_LLM_PROVIDER,
    DEFAULT_OLLAMA_BASE_URL,
    PROVIDER_SPECS,
    provider_spec,
)
from multi_agent_code_factory.llm.types import (
    LlmConfigError,
    LlmInvokeError,
    LlmOutputMode,
    LlmProviderSpec,
    LlmRuntimeConfig,
)

__all__ = [
    "DEFAULT_FACTORY_LLM_MODEL",
    "DEFAULT_FACTORY_LLM_PROVIDER",
    "DEFAULT_OLLAMA_BASE_URL",
    "LlmConfigError",
    "LlmInvokeError",
    "LlmOutputMode",
    "LlmProviderSpec",
    "LlmRuntimeConfig",
    "PROVIDER_SPECS",
    "api_key_for_provider",
    "create_chat_model",
    "llm_available",
    "preflight_live_llm",
    "provider_spec",
    "require_llm_api_key",
    "resolve_chat_model_id",
    "resolve_factory_llm_model",
    "resolve_factory_llm_provider",
    "resolve_llm_runtime_config",
    "resolve_provider_base_url",
]
