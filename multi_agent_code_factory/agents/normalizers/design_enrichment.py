"""Design 产物校验前补全与默认值生成。"""

from __future__ import annotations

from multi_agent_code_factory.schemas.design import (
    ArchitectureOverview,
    CodeDelta,
    ContextView,
    DesignArtifact,
    DevTask,
    TraceRow,
)
from multi_agent_code_factory.schemas.prd import FeaturePriority, PrdArtifact


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


def _normalize_traceability_rows(rows: list[TraceRow]) -> list[TraceRow]:
    normalized: list[TraceRow] = []
    for row in rows:
        if row.spec_ref_id or not row.feature_id:
            normalized.append(row)
            continue
        normalized.append(
            row.model_copy(
                update={
                    "spec_ref_id": row.feature_id,
                    "spec_ref_kind": row.spec_ref_kind or "FEAT",
                }
            )
        )
    return normalized


def _default_non_goals(spec: PrdArtifact | None) -> list[str]:
    if spec is not None and spec.scope_out:
        return list(spec.scope_out)
    return [
        "Web UI and browser-based interfaces",
        "Multi-user or server deployment",
        "External network services",
    ]


def _default_context_view(design: DesignArtifact) -> ContextView:
    actors = [module.name for module in design.modules if module.name.strip()]
    if not actors:
        actors = ["User", "Application"]
    return ContextView(actors=actors)


def _default_design_goals(spec: PrdArtifact | None) -> list[str]:
    if spec is None:
        return ["Deliver scoped features with automated test coverage"]
    goals: list[str] = []
    for feature in spec.features:
        if feature.priority == FeaturePriority.P0:
            goals.append(f"{feature.id}: {feature.description}")
    if goals:
        return goals
    return [spec.summary] if spec.summary.strip() else [spec.title]


def _default_architecture(
    design: DesignArtifact,
    spec: PrdArtifact | None,
) -> ArchitectureOverview:
    strategy = design.summary
    if not strategy and spec is not None:
        strategy = spec.summary or spec.title
    if not strategy:
        strategy = "Layered modules with dev_tasks mapped to file paths"
    return ArchitectureOverview(
        solution_strategy=strategy,
        code_delta=CodeDelta(summary="空仓库"),
    )


def _ensure_code_delta(design: DesignArtifact) -> ArchitectureOverview | None:
    architecture = design.architecture
    if architecture is None:
        return None
    if architecture.code_delta and architecture.code_delta.summary.strip():
        return None
    return architecture.model_copy(update={"code_delta": CodeDelta(summary="空仓库")})


def enrich_design_for_validation(
    design: DesignArtifact,
    *,
    spec: PrdArtifact | None,
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

    if not any(str(goal).strip() for goal in design.design_goals):
        updates["design_goals"] = _default_design_goals(spec)

    if not design.context_view:
        updates["context_view"] = _default_context_view(design)

    architecture = design.architecture
    solution_strategy = architecture.solution_strategy if architecture else None
    if not isinstance(solution_strategy, str) or not solution_strategy.strip():
        updates["architecture"] = _default_architecture(design, spec)
    else:
        patched = _ensure_code_delta(design)
        if patched is not None:
            updates["architecture"] = patched

    if design.cross_cutting is None:
        updates["cross_cutting"] = {}

    if not updates:
        return design
    return design.model_copy(update=updates)
