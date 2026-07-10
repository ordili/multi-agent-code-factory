"""将校验 / 解析失败格式化为 LLM 重试时的 extra_system 提示。"""

from __future__ import annotations

from multi_agent_code_factory.agents.llm.errors import LlmParseError
from multi_agent_code_factory.state import PipelineState


def format_llm_parse_retry_feedback(exc: LlmParseError) -> str:
    """将上次 JSON 解析或 schema 校验失败格式化为重试 system 追加段。"""
    message = str(exc).strip()
    if len(message) > 1200:
        message = message[:1200] + "..."
    return (
        "Previous JSON output failed parsing or schema validation. "
        "Fix every issue and resubmit one corrected JSON object:\n"
        f"{message}"
    )


def format_design_validation_feedback(state: PipelineState) -> str | None:
    """将上次 design 校验失败项格式化为 Architect 重试时的 extra_system 提示。"""
    validation = state.design_validation
    if validation is None or validation.passed:
        return None
    lines = [
        "Previous design failed validation. Fix every item before resubmitting:",
    ]
    for item in validation.violations:
        field = f" ({item.field})" if item.field else ""
        lines.append(f"- [{item.rule_id}]{field}: {item.message}")
    if state.design is not None:
        lines.append(
            "Keep valid modules/dev_tasks/traceability; only patch failing fields."
        )
    return "\n".join(lines)
