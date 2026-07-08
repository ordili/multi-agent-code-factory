"""Design 产物校验前补全与默认值生成。"""

from __future__ import annotations

from multi_agent_code_factory.schemas.design import DesignArtifact, DevTask
from multi_agent_code_factory.schemas.spec import SpecArtifact


def _dedupe_dev_tasks_by_path(tasks: list[DevTask]) -> list[DevTask]:
    by_path: dict[str, DevTask] = {}
    for task in tasks:
        existing = by_path.get(task.path)
        if existing is None:
            by_path[task.path] = task
            continue
        merged_covers = list(dict.fromkeys([*existing.covers, *task.covers]))
        merged_deps = list(dict.fromkeys([*existing.depends_on, *task.depends_on]))
        description = (
            task.description
            if len(task.description) > len(existing.description)
            else existing.description
        )
        by_path[task.path] = existing.model_copy(
            update={
                "covers": merged_covers,
                "depends_on": merged_deps,
                "description": description,
            }
        )
    return list(by_path.values())


def _normalize_traceability_rows(
    rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for row in rows:
        patched = dict(row)
        spec_ref_id = patched.get("spec_ref_id")
        feature_id = patched.get("feature_id")
        if not spec_ref_id and isinstance(feature_id, str):
            patched["spec_ref_id"] = feature_id
            patched.setdefault("spec_ref_kind", "FEAT")
        normalized.append(patched)
    return normalized


def _default_non_goals(spec: SpecArtifact | None) -> list[str]:
    if spec is not None and spec.scope_out:
        return list(spec.scope_out)
    return [
        "Web UI and browser-based interfaces",
        "Multi-user or server deployment",
        "External network services",
    ]


def _default_context_view(design: DesignArtifact) -> dict[str, object]:
    actors = [module.name for module in design.modules if module.name.strip()]
    if not actors:
        actors = ["User", "Application"]
    return {"actors": actors}


def _default_architecture(
    design: DesignArtifact,
    spec: SpecArtifact | None,
) -> dict[str, object]:
    strategy = design.summary
    if not strategy and spec is not None:
        strategy = spec.summary or spec.title
    if not strategy:
        strategy = "Layered modules with dev_tasks mapped to file paths"
    return {"solution_strategy": strategy}


def enrich_design_for_validation(
    design: DesignArtifact,
    *,
    spec: SpecArtifact | None,
) -> DesignArtifact:
    """在 LLM 遗漏可选字段时补全 MVP 校验所需的设计字段。"""
    updates: dict[str, object] = {}

    dev_tasks = _dedupe_dev_tasks_by_path(design.dev_tasks)
    if dev_tasks != design.dev_tasks:
        updates["dev_tasks"] = dev_tasks

    if design.traceability:
        traceability = _normalize_traceability_rows(design.traceability)
        if traceability != design.traceability:
            updates["traceability"] = traceability

    if not design.non_goals:
        updates["non_goals"] = _default_non_goals(spec)

    if not design.context_view:
        updates["context_view"] = _default_context_view(design)

    architecture = design.architecture or {}
    solution_strategy = architecture.get("solution_strategy")
    if not isinstance(solution_strategy, str) or not solution_strategy.strip():
        updates["architecture"] = _default_architecture(design, spec)

    if design.cross_cutting is None:
        updates["cross_cutting"] = {}

    if not updates:
        return design
    return design.model_copy(update=updates)
