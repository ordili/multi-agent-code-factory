"""LLM 调用错误辅助函数。"""

from __future__ import annotations

from pydantic import ValidationError

from multi_agent_code_factory.llm import LlmInvokeError, LlmRuntimeConfig


class LlmParseError(LlmInvokeError):
    """LLM 响应后的 JSON 或 schema 校验失败。"""


def provider_failure_hint(runtime: LlmRuntimeConfig) -> str:
    """构造 Live 模式调用失败时的运维排查提示。"""
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
    """将最终失败统一包装为 ``LlmInvokeError``。"""
    if isinstance(exc, LlmInvokeError):
        return exc
    message = f"{provider_failure_hint(runtime)}\nOriginal error: {exc}"
    if isinstance(exc, (ValidationError, ValueError)):
        return LlmParseError(message)
    return LlmInvokeError(message)
