"""按 ``LlmRuntimeConfig.output_mode`` 选择的调用策略。

- ``native_structured`` → ``native_structured.py``（openai、anthropic）
- ``prompted_json`` → ``prompted_json.py``（deepseek、ollama）

provider → output_mode 映射由 ``llm.PROVIDER_SPECS`` 推导，见 ``modes.py``。
"""

from multi_agent_code_factory.agents.llm.strategies.modes import (
    NATIVE_STRUCTURED_PROVIDERS,
    PROMPTED_JSON_PROVIDERS,
    providers_for_output_mode,
)
from multi_agent_code_factory.agents.llm.strategies.native_structured import (
    NativeStructuredStrategy,
)
from multi_agent_code_factory.agents.llm.strategies.prompted_json import (
    PromptedJsonStrategy,
    extract_json_text,
)

__all__ = [
    "NATIVE_STRUCTURED_PROVIDERS",
    "PROMPTED_JSON_PROVIDERS",
    "NativeStructuredStrategy",
    "PromptedJsonStrategy",
    "extract_json_text",
    "providers_for_output_mode",
]
