"""fit_task_batch_context_to_input_budget 与相关裁剪。"""

from __future__ import annotations

from typing import Any

from multi_agent_code_factory.context_lines import count_context_lines


def _slim_test_cases(cases: list[Any]) -> list[dict[str, Any]]:
    slim: list[dict[str, Any]] = []
    for item in cases:
        if not isinstance(item, dict):
            continue
        entry: dict[str, Any] = {}
        if item.get("id") is not None:
            entry["id"] = item["id"]
        if item.get("title") is not None:
            entry["title"] = item["title"]
        if entry:
            slim.append(entry)
    return slim


def fit_task_batch_context_to_input_budget(
    context: dict[str, Any],
    max_lines: int,
) -> dict[str, Any]:
    """§9.1.2：超 input 预算时渐进裁剪，仍超限则交由 ``input_budget`` 门禁失败。"""
    if count_context_lines(context) <= max_lines:
        return context

    result = dict(context)
    design = result.get("design")
    if isinstance(design, dict):
        trimmed = dict(design)
        trimmed.pop("diagrams", None)
        trimmed.pop("context_view", None)
        architecture = trimmed.get("architecture")
        if isinstance(architecture, dict):
            trimmed["architecture"] = {
                key: architecture[key]
                for key in ("summary", "solution_strategy")
                if key in architecture
            }
        result["design"] = trimmed

    if count_context_lines(result) <= max_lines:
        return result

    impl_batch = result.get("impl_batch")
    if isinstance(impl_batch, dict):
        batch_copy = dict(impl_batch)
        cases = batch_copy.get("relevant_test_cases")
        if isinstance(cases, list):
            slim = _slim_test_cases(cases)
            batch_copy["relevant_test_cases"] = slim
            result["impl_batch"] = batch_copy
            design = result.get("design")
            if isinstance(design, dict):
                design_copy = dict(design)
                if isinstance(design_copy.get("test_cases"), list):
                    design_copy["test_cases"] = slim
                result["design"] = design_copy

    return result
