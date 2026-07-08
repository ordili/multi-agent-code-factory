"""LLM 客户端配置（经 LangChain init_chat_model，厂商无关）。

厂商由 ``FACTORY_LLM_PROVIDER`` 选择；``FACTORY_LLM_MODEL`` 仅指定模型 id。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, cast

LlmOutputMode = Literal["native_structured", "prompted_json"]

if TYPE_CHECKING:
    from langchain_core.language_models.chat_models import BaseChatModel

DEFAULT_FACTORY_LLM_PROVIDER = "deepseek"
DEFAULT_FACTORY_LLM_MODEL = "deepseek-chat"
# Use IPv4 loopback: on Windows, ``localhost`` often resolves to ::1 while Ollama
# listens on 127.0.0.1 only, which surfaces as HTTP 502 from LangChain invoke.
DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"


@dataclass(frozen=True)
class LlmProviderSpec:
    """Maps ``FACTORY_LLM_PROVIDER`` id → API key env and LangChain wiring."""

    api_key_env: str
    langchain_provider: str
    base_url: str | None = None
    base_url_env: str | None = None
    api_key_required: bool = True
    output_mode: LlmOutputMode = "native_structured"


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
        base_url_env="OLLAMA_BASE_URL",
        api_key_required=False,
        output_mode="prompted_json",
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
    output_mode: LlmOutputMode


class LlmConfigError(RuntimeError):
    """Raised when LLM configuration is missing or invalid."""


class LlmInvokeError(RuntimeError):
    """Raised when a live LLM call fails (HTTP, Ollama crash, parse errors)."""


class LlmBudgetExceededError(LlmInvokeError):
    """Raised when run LLM call or token budget is exhausted."""


def list_factory_llm_providers() -> tuple[str, ...]:
    return tuple(PROVIDER_SPECS)


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
    if spec.base_url_env:
        explicit = _read_env_secret(spec.base_url_env)
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
        output_mode=spec.output_mode,
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
    """解析 stub / live 互斥标志；live 模式要求 API key 可用。"""
    if stub and live:
        msg = "cannot use both --stub and --live"
        raise ValueError(msg)
    if live:
        require_llm_api_key()
        return False
    if stub:
        return True
    return True


def _read_env_int(name: str) -> int | None:
    raw = _read_env_secret(name)
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError as exc:
        msg = f"{name} must be an integer, got {raw!r}"
        raise LlmConfigError(msg) from exc


def _read_env_bool(name: str) -> bool | None:
    raw = _read_env_secret(name)
    if raw is None:
        return None
    normalized = raw.lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    msg = f"{name} must be a boolean (true/false), got {raw!r}"
    raise LlmConfigError(msg)


def _ollama_performance_kwargs() -> dict[str, Any]:
    """Optional Ollama inference tuning via env (see ``.env.example``)."""
    kwargs: dict[str, Any] = {}
    num_ctx = _read_env_int("OLLAMA_NUM_CTX")
    if num_ctx is not None:
        kwargs["num_ctx"] = num_ctx
    num_predict = _read_env_int("OLLAMA_NUM_PREDICT")
    if num_predict is not None:
        kwargs["num_predict"] = num_predict
    num_gpu = _read_env_int("OLLAMA_NUM_GPU")
    if num_gpu is not None:
        kwargs["num_gpu"] = num_gpu
    reasoning = _read_env_bool("OLLAMA_REASONING")
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


def preflight_live_llm(*, timeout_sec: float = 90.0) -> None:
    """流水线启动前探测 live 后端是否可响应，失败则快速报错。"""
    runtime = resolve_llm_runtime_config()
    if runtime.factory_provider != "ollama":
        require_llm_api_key(provider=runtime.factory_provider)
        return

    import urllib.error
    import urllib.request

    base = (runtime.base_url or DEFAULT_OLLAMA_BASE_URL).rstrip("/")
    payload = json.dumps(
        {
            "model": runtime.model,
            "prompt": "Reply with OK only.",
            "stream": False,
            "options": {"num_predict": 8},
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{base}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_sec) as response:
            body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        msg = _ollama_failure_message(runtime, exc, detail)
        raise LlmConfigError(msg) from exc
    except Exception as exc:
        msg = _ollama_failure_message(runtime, exc, "")
        raise LlmConfigError(msg) from exc

    if '"error"' in body.lower():
        msg = _ollama_failure_message(runtime, RuntimeError("ollama returned error payload"), body)
        raise LlmConfigError(msg)


def _ollama_failure_message(
    runtime: LlmRuntimeConfig,
    exc: BaseException,
    detail: str,
) -> str:
    hint = (
        f"Ollama live preflight failed for model {runtime.model!r} at {runtime.base_url}.\n"
        f"Cause: {exc}\n"
        "Fixes to try:\n"
        "  1. Set OLLAMA_BASE_URL=http://127.0.0.1:11434 (not localhost; Windows IPv6 → 502)\n"
        "  2. Restart Ollama (quit tray app, run `ollama serve`)\n"
        "  3. `ollama pull qwen3.5:9b` and match FACTORY_LLM_MODEL\n"
        "  4. Lower OLLAMA_NUM_CTX / set OLLAMA_REASONING=false in .env\n"
        "  5. Or use cloud: FACTORY_LLM_PROVIDER=deepseek + DEEPSEEK_API_KEY\n"
    )
    if detail.strip():
        hint += f"Ollama response: {detail.strip()[:500]}\n"
    return hint
