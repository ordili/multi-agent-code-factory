"""调用策略与 provider output_mode 的映射辅助。"""

from __future__ import annotations

from multi_agent_code_factory.llm import LlmOutputMode, PROVIDER_SPECS


def providers_for_output_mode(mode: LlmOutputMode) -> tuple[str, ...]:
    """返回配置了指定 output_mode 的 ``FACTORY_LLM_PROVIDER`` id 列表。"""
    return tuple(
        provider_id
        for provider_id, spec in sorted(PROVIDER_SPECS.items())
        if spec.output_mode == mode
    )


NATIVE_STRUCTURED_PROVIDERS = providers_for_output_mode("native_structured")
PROMPTED_JSON_PROVIDERS = providers_for_output_mode("prompted_json")
