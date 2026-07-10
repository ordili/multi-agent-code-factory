"""将校验 / 解析失败格式化为 LLM 重试时的 extra_system 提示。"""

from __future__ import annotations

from multi_agent_code_factory.agents.llm.errors import LlmParseError
from multi_agent_code_factory.schemas.validation_report import (
    ValidationReport,
    Violation,
    ViolationSeverity,
)
from multi_agent_code_factory.state import PipelineState

_SEVERITY_ORDER = {
    ViolationSeverity.ERROR: 0,
    ViolationSeverity.WARN: 1,
    ViolationSeverity.INFO: 2,
}


def _format_violation_line(item: Violation) -> str:
    """单条 violation 的可读行（含 severity / field / path）。"""
    meta: list[str] = [f"({item.severity})"]
    if item.field:
        meta.append(f"field={item.field}")
    if item.path:
        meta.append(f"path={item.path}")
    meta_text = " ".join(meta)
    return f"- [{item.rule_id}] {meta_text}: {item.message}"


def _format_validation_failure_feedback(
    report: ValidationReport | None,
    *,
    headline: str,
    footer: str | None = None,
) -> str | None:
    """将 ValidationReport 失败项格式化为 extra_system 文本（全量 violations）。"""
    if report is None or report.passed or not report.violations:
        return None
    ordered = sorted(
        report.violations,
        key=lambda item: _SEVERITY_ORDER.get(item.severity, 99),
    )
    lines = [headline, *(_format_violation_line(item) for item in ordered)]
    if footer:
        lines.append(footer)
    return "\n".join(lines)


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


def format_spec_validation_feedback(state: PipelineState) -> str | None:
    """将上次 spec 校验失败项格式化为 PM 重试时的 extra_system 提示。"""
    footer = None
    if state.spec is not None:
        footer = "Keep valid spec fields; only patch items listed above."
    return _format_validation_failure_feedback(
        state.spec_validation,
        headline="Previous spec failed validation. Fix every item before resubmitting:",
        footer=footer,
    )


def format_design_validation_feedback(state: PipelineState) -> str | None:
    """将上次 design 校验失败项格式化为 Architect 重试时的 extra_system 提示。"""
    footer = None
    if state.design is not None:
        footer = "Keep valid modules/dev_tasks/traceability; only patch failing fields."
    return _format_validation_failure_feedback(
        state.design_validation,
        headline=(
            "Previous design failed validation. Fix every item before resubmitting:"
        ),
        footer=footer,
    )
