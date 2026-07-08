"""LLM invoke error helpers."""

from __future__ import annotations

from pydantic import ValidationError

from multi_agent_code_factory.llm import LlmInvokeError, LlmRuntimeConfig


class LlmParseError(LlmInvokeError):
    """JSON or schema validation failed after an LLM response."""


def provider_failure_hint(runtime: LlmRuntimeConfig) -> str:
    """Build operator hints when a live LLM call fails."""
    if runtime.output_mode == "prompted_json":
        return (
            f"LLM call failed for provider={runtime.factory_provider!r} "
            f"model={runtime.model!r}. "
            "For Ollama: restart the server and prefer qwen3.5:9b for large JSON specs. "
            "For DeepSeek: use deepseek-chat or deepseek-v4-pro with prompted JSON mode. "
            "Or switch FACTORY_LLM_PROVIDER=openai."
        )
    return (
        f"LLM call failed for provider={runtime.factory_provider!r} "
        f"model={runtime.model!r}. "
        "Check API key, model id, and provider status."
    )


def wrap_invoke_failure(
    exc: BaseException,
    *,
    runtime: LlmRuntimeConfig,
) -> LlmInvokeError:
    """Normalize terminal invoke failures to ``LlmInvokeError``."""
    if isinstance(exc, LlmInvokeError):
        return exc
    message = f"{provider_failure_hint(runtime)}\nOriginal error: {exc}"
    if isinstance(exc, (ValidationError, ValueError)):
        return LlmParseError(message)
    return LlmInvokeError(message)
