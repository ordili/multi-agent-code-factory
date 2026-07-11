"""裁剪 prompt 上下文 payload，降低 LLM token 消耗。"""

from __future__ import annotations

import json
from pathlib import PurePosixPath
from typing import Any

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.dev_task_scheduler import file_plan_aux_paths
from multi_agent_code_factory.schemas.design import DevTask, FilePlanItem
from multi_agent_code_factory.schemas.task_batch import TaskBatch

MAX_SNIPPET_LINES = 500
MAX_SNIPPET_FILES = 3
MAX_FAILURE_ITEMS = 10
MAX_VIOLATION_ITEMS = 20
MAX_FINDING_ITEMS = 20
MAX_HEAVY_LIST_ITEMS = 30
MAX_TEXT_CHARS = 800
MAX_FAILURE_OUTPUT_CHARS = 500
MAX_FAILURE_MESSAGE_CHARS = 300

_TEST_CASE_KEEP = (
    "id",
    "kind",
    "title",
    "description",
    "expected",
    "covers",
    "semantic_evidence",
    "steps",
)


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


def _trim_test_case_item(item: Any) -> Any:
    if not isinstance(item, dict):
        return item
    return {key: item[key] for key in _TEST_CASE_KEEP if key in item}


def _cap_test_cases(items: list[Any]) -> tuple[list[Any], int | None]:
    trimmed = [_trim_test_case_item(item) for item in items]
    return _cap_list_items(trimmed, MAX_HEAVY_LIST_ITEMS)


def trim_prd(payload: dict[str, Any]) -> dict[str, Any]:
    """保留下游 Agent 使用的 prd 字段（含语义契约）。"""
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
        "semantic_constraints",
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
            "test_cases",
        )
        result = {key: payload[key] for key in keep if key in payload}
        test_cases = result.get("test_cases")
        if isinstance(test_cases, list):
            capped, extra = _cap_test_cases(test_cases)
            result["test_cases"] = capped
            if extra:
                result["test_cases_truncated_count"] = extra
        return result

    result = dict(payload)
    for key in ("test_cases", "table_schemas", "traceability", "file_plan"):
        value = result.get(key)
        if isinstance(value, list):
            if key == "test_cases":
                capped, extra = _cap_test_cases(value)
            else:
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
    coverage = payload.get("coverage")
    if isinstance(coverage, dict):
        result["coverage"] = {
            key: coverage[key]
            for key in (
                "tool",
                "command",
                "parser",
                "line_percent",
                "branch_percent",
                "lines_covered",
                "lines_total",
                "thresholds",
                "passed",
                "violations",
                "raw_summary_path",
            )
            if key in coverage
        }
    trace = payload.get("acceptance_traceability")
    if isinstance(trace, list):
        result["acceptance_traceability"] = trace
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
    """压缩 Developer 重试包（snippet 已在提取阶段预算化，不再头截断）。"""
    result = dict(payload)
    test_report = result.get("test_report")
    if isinstance(test_report, dict):
        result["test_report"] = trim_test_report(test_report)
    dev_manifest = result.get("dev_manifest")
    if isinstance(dev_manifest, dict):
        result["dev_manifest"] = trim_dev_manifest(dev_manifest)
    review_feedback = result.get("review_feedback")
    if isinstance(review_feedback, dict):
        findings = review_feedback.get("findings")
        if isinstance(findings, list):
            capped, extra = _cap_list_items(findings, MAX_FINDING_ITEMS)
            review_feedback = dict(review_feedback)
            review_feedback["findings"] = capped
            if extra:
                review_feedback["findings_truncated_count"] = extra
            summary = review_feedback.get("summary")
            if isinstance(summary, str):
                review_feedback["summary"] = _truncate_text(summary, MAX_TEXT_CHARS)
            result["review_feedback"] = review_feedback
    return result


def _module_prefix(path: str) -> str:
    normalized = path.replace("\\", "/")
    parent = PurePosixPath(normalized).parent
    if str(parent) == ".":
        return normalized
    return str(parent)


def _task_mentioned(text: str, needle: str) -> bool:
    return needle.lower() in text.lower()


def trim_design_for_task_batch(
    payload: dict[str, Any],
    batch: TaskBatch,
    active_tasks: list[DevTask],
    *,
    completed_task_ids: list[str] | None = None,
) -> dict[str, Any]:
    """按批过滤 design（§9.1.1）。"""
    base = trim_design(payload, compact=True)
    active_ids = {task.id for task in active_tasks}
    completed_ids = set(completed_task_ids or [])

    dev_tasks_raw = base.get("dev_tasks")
    if isinstance(dev_tasks_raw, list):
        kept: list[Any] = []
        for item in dev_tasks_raw:
            if not isinstance(item, dict):
                continue
            task_id = item.get("id")
            if task_id in active_ids or task_id in completed_ids:
                kept.append(
                    {
                        key: item[key]
                        for key in (
                            "id",
                            "path",
                            "description",
                            "depends_on",
                            "covers",
                        )
                        if key in item
                    }
                )
        base["dev_tasks"] = kept

    active_paths = [task.path for task in active_tasks]
    prefixes = {_module_prefix(path) for path in active_paths}

    modules = base.get("modules")
    if isinstance(modules, list):
        filtered_modules: list[Any] = []
        for item in modules:
            if not isinstance(item, dict):
                continue
            mod_path = str(item.get("path", ""))
            if any(
                mod_path == prefix or mod_path.startswith(f"{prefix}/")
                for prefix in prefixes
            ):
                filtered_modules.append(item)
        base["modules"] = filtered_modules

    case_ids = set(batch.relevant_test_case_ids)
    test_cases = base.get("test_cases")
    if isinstance(test_cases, list):
        filtered_cases = [
            _trim_test_case_item(item)
            for item in test_cases
            if isinstance(item, dict) and item.get("id") in case_ids
        ]
        capped, extra = _cap_test_cases(filtered_cases)
        base["test_cases"] = capped
        if extra:
            base["test_cases_truncated_count"] = extra

    aux_paths: set[str] = set()
    file_plan_raw = base.get("file_plan")
    file_plan_items: list[FilePlanItem] = []
    if isinstance(file_plan_raw, list):
        for item in file_plan_raw:
            if isinstance(item, dict) and item.get("path"):
                file_plan_items.append(FilePlanItem.model_validate(item))
    for task in active_tasks:
        aux_paths.update(file_plan_aux_paths(task, file_plan_items))
    required = set(batch.required_paths)

    if isinstance(file_plan_raw, list):
        base["file_plan"] = [
            item
            for item in file_plan_raw
            if isinstance(item, dict)
            and (item.get("path") in required or item.get("path") in aux_paths)
        ]

    interfaces = base.get("interfaces")
    if isinstance(interfaces, list):
        filtered_ifaces: list[Any] = []
        for item in interfaces:
            if not isinstance(item, dict):
                continue
            blob = json.dumps(item, ensure_ascii=False)
            if any(_task_mentioned(blob, task.id) for task in active_tasks):
                filtered_ifaces.append(item)
                continue
            mod_path = str(item.get("file", ""))
            if any(
                mod_path == prefix or mod_path.startswith(f"{prefix}/")
                for prefix in prefixes
            ):
                filtered_ifaces.append(item)
        base["interfaces"] = filtered_ifaces

    return base


def trim_dev_manifest_for_batch(payload: dict[str, Any]) -> dict[str, Any]:
    """task-batch 仅注入 tasks_completed + changed_files 摘要。"""
    return {
        "version": payload.get("version"),
        "tasks_completed": payload.get("tasks_completed", []),
        "changed_files": payload.get("changed_files", []),
        "notes": payload.get("notes"),
    }


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
