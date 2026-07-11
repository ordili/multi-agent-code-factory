"""裁剪 prompt 上下文 payload，降低 LLM token 消耗。"""

from __future__ import annotations

from typing import Any

from multi_agent_code_factory.agent_roles import AgentRole

MAX_SNIPPET_LINES = 120
MAX_SNIPPET_FILES = 3
MAX_FAILURE_ITEMS = 10
MAX_VIOLATION_ITEMS = 20
MAX_FINDING_ITEMS = 20
MAX_HEAVY_LIST_ITEMS = 30
MAX_TEXT_CHARS = 800
MAX_FAILURE_OUTPUT_CHARS = 500
MAX_FAILURE_MESSAGE_CHARS = 300


def _truncate_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def _truncate_lines(text: str, max_lines: int) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    return "\n".join(lines[:max_lines]) + "\n... (已截断)"


def _cap_list_items(items: list[Any], max_items: int) -> tuple[list[Any], int | None]:
    if len(items) <= max_items:
        return items, None
    return items[:max_items], len(items) - max_items


def trim_prd(payload: dict[str, Any]) -> dict[str, Any]:
    """保留下游 Agent 使用的 spec 字段。"""
    keep = (
        "version",
        "profile",
        "revision",
        "parent_task_id",
        "title",
        "summary",
        "context",
        "success_metrics",
        "features",
        "user_stories",
        "requirement_pool",
        "scope_in",
        "scope_out",
        "operational_profile",
        "consistency_profile",
        "acceptance_criteria",
        "constraints",
    )
    return {key: payload[key] for key in keep if key in payload}


def trim_design(payload: dict[str, Any], *, compact: bool = False) -> dict[str, Any]:
    """裁剪 design 中的大数组；compact 模式仅保留实现相关字段。"""
    if compact:
        keep = (
            "version",
            "spec_ref",
            "revision",
            "summary",
            "design_goals",
            "non_goals",
            "modules",
            "dev_tasks",
            "external_dependencies",
            "error_catalog",
            "architecture",
            "context_view",
            "diagrams",
            "interfaces",
            "file_plan",
        )
        return {key: payload[key] for key in keep if key in payload}

    result = dict(payload)
    for key in ("test_cases", "table_schemas", "traceability", "file_plan"):
        value = result.get(key)
        if isinstance(value, list):
            capped, extra = _cap_list_items(value, MAX_HEAVY_LIST_ITEMS)
            result[key] = capped
            if extra:
                result[f"{key}_truncated_count"] = extra
    if isinstance(result.get("notes"), str):
        result["notes"] = _truncate_text(result["notes"], MAX_TEXT_CHARS)
    return result


def trim_test_report(payload: dict[str, Any]) -> dict[str, Any]:
    """保留 summary 与限量的 failure 详情。"""
    result: dict[str, Any] = {
        "version": payload.get("version"),
        "passed": payload.get("passed"),
        "exit_code": payload.get("exit_code"),
        "summary": payload.get("summary"),
        "command": payload.get("command"),
        "duration_sec": payload.get("duration_sec"),
        "parser": payload.get("parser"),
    }
    failures = payload.get("failures")
    if isinstance(failures, list):
        trimmed: list[Any] = []
        for item in failures[:MAX_FAILURE_ITEMS]:
            if not isinstance(item, dict):
                trimmed.append(item)
                continue
            failure = dict(item)
            message = failure.get("message")
            if isinstance(message, str):
                failure["message"] = _truncate_text(message, MAX_FAILURE_MESSAGE_CHARS)
            output = failure.get("output")
            if isinstance(output, str):
                failure["output"] = _truncate_text(output, MAX_FAILURE_OUTPUT_CHARS)
            trimmed.append(failure)
        result["failures"] = trimmed
        if len(failures) > MAX_FAILURE_ITEMS:
            result["failures_truncated_count"] = len(failures) - MAX_FAILURE_ITEMS
    raw_tail = payload.get("raw_output_tail")
    if isinstance(raw_tail, str):
        result["raw_output_tail"] = _truncate_text(raw_tail, MAX_TEXT_CHARS)
    tests_missing = payload.get("tests_missing")
    if isinstance(tests_missing, list):
        result["tests_missing"] = tests_missing
    return result


def trim_review(payload: dict[str, Any]) -> dict[str, Any]:
    """保留评审结论字段并限制 findings 数量。"""
    result: dict[str, Any] = {
        "version": payload.get("version"),
        "approved": payload.get("approved"),
        "next_stage": payload.get("next_stage"),
        "summary": payload.get("summary"),
        "acceptance_coverage": payload.get("acceptance_coverage"),
    }
    findings = payload.get("findings")
    if isinstance(findings, list):
        capped, extra = _cap_list_items(findings, MAX_FINDING_ITEMS)
        result["findings"] = capped
        if extra:
            result["findings_truncated_count"] = extra
    summary = result.get("summary")
    if isinstance(summary, str):
        result["summary"] = _truncate_text(summary, MAX_TEXT_CHARS)
    return result


def trim_validation(payload: dict[str, Any]) -> dict[str, Any]:
    """保留校验状态并限制 violations 数量。"""
    result: dict[str, Any] = {
        "version": payload.get("version"),
        "target": payload.get("target"),
        "passed": payload.get("passed"),
        "error_count": payload.get("error_count"),
        "warn_count": payload.get("warn_count"),
        "require_hitl": payload.get("require_hitl"),
    }
    violations = payload.get("violations")
    if isinstance(violations, list):
        capped, extra = _cap_list_items(violations, MAX_VIOLATION_ITEMS)
        result["violations"] = capped
        if extra:
            result["violations_truncated_count"] = extra
    return result


def trim_dev_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    """保留 manifest 摘要字段，截断过长 notes。"""
    result = dict(payload)
    for key in ("notes", "incremental_plan", "escalation_note"):
        value = result.get(key)
        if isinstance(value, str):
            result[key] = _truncate_text(value, MAX_TEXT_CHARS)
    reflection = result.get("reflection")
    if isinstance(reflection, dict):
        reflection_copy = dict(reflection)
        for key in ("hypothesis", "next_action"):
            value = reflection_copy.get(key)
            if isinstance(value, str):
                reflection_copy[key] = _truncate_text(value, MAX_TEXT_CHARS)
        result["reflection"] = reflection_copy
    return result


def trim_retry_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    """压缩 Developer 重试包并限制 code snippet 数量与行数。"""
    result = dict(payload)
    prd = result.get("prd")
    if isinstance(prd, dict):
        result["prd"] = trim_prd(prd)
    design = result.get("design")
    if isinstance(design, dict):
        result["design"] = trim_design(design, compact=True)
    test_report = result.get("test_report")
    if isinstance(test_report, dict):
        result["test_report"] = trim_test_report(test_report)
    dev_manifest = result.get("dev_manifest")
    if isinstance(dev_manifest, dict):
        result["dev_manifest"] = trim_dev_manifest(dev_manifest)

    snippets = result.get("code_snippets")
    if isinstance(snippets, list):
        trimmed: list[Any] = []
        for item in snippets[:MAX_SNIPPET_FILES]:
            if isinstance(item, dict) and isinstance(item.get("content"), str):
                item = dict(item)
                item["content"] = _truncate_lines(item["content"], MAX_SNIPPET_LINES)
            trimmed.append(item)
        result["code_snippets"] = trimmed
        if len(snippets) > MAX_SNIPPET_FILES:
            result["code_snippets_truncated_count"] = len(snippets) - MAX_SNIPPET_FILES
    return result


def trim_context_for_role(
    role_id: AgentRole,
    context: dict[str, Any],
) -> dict[str, Any]:
    """按角色对组装好的 prompt 上下文做裁剪。"""
    result = dict(context)

    prd = result.get("prd")
    if isinstance(prd, dict):
        result["prd"] = trim_prd(prd)

    design = result.get("design")
    if isinstance(design, dict):
        compact_design = role_id in {AgentRole.DEVELOPER, AgentRole.QA}
        result["design"] = trim_design(design, compact=compact_design)

    test_report = result.get("test_report")
    if isinstance(test_report, dict):
        result["test_report"] = trim_test_report(test_report)

    review = result.get("review")
    if isinstance(review, dict):
        result["review"] = trim_review(review)

    for key in ("prd_validation", "design_validation"):
        value = result.get(key)
        if isinstance(value, dict):
            result[key] = trim_validation(value)

    dev_manifest = result.get("dev_manifest")
    if isinstance(dev_manifest, dict):
        result["dev_manifest"] = trim_dev_manifest(dev_manifest)

    retry_bundle = result.get("retry_bundle")
    if isinstance(retry_bundle, dict):
        result["retry_bundle"] = trim_retry_bundle(retry_bundle)

    return result
