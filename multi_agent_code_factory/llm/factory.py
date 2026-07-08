"""LangChain ChatModel 工厂。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from multi_agent_code_factory.llm._env import read_env_bool, read_env_int
from multi_agent_code_factory.llm.config import resolve_llm_runtime_config
from multi_agent_code_factory.llm.types import LlmConfigError

if TYPE_CHECKING:
    from langchain_core.language_models.chat_models import BaseChatModel


def _ollama_performance_kwargs() -> dict[str, Any]:
    """Optional Ollama inference tuning via env (see ``.env.example``)."""
    kwargs: dict[str, Any] = {}
    num_ctx = read_env_int("OLLAMA_NUM_CTX")
    if num_ctx is not None:
        kwargs["num_ctx"] = num_ctx
    num_predict = read_env_int("OLLAMA_NUM_PREDICT")
    if num_predict is not None:
        kwargs["num_predict"] = num_predict
    num_gpu = read_env_int("OLLAMA_NUM_GPU")
    if num_gpu is not None:
        kwargs["num_gpu"] = num_gpu
    reasoning = read_env_bool("OLLAMA_REASONING")
    if reasoning is not None:
        kwargs["reasoning"] = reasoning
    return kwargs


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
    if runtime.factory_provider == "ollama":
        kwargs.update(_ollama_performance_kwargs())

    chat_model = init_chat_model(runtime.langchain_model_id, **kwargs)
    return cast("BaseChatModel", chat_model)
