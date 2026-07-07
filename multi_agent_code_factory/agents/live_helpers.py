"""Post-processing helpers for live LLM agent outputs."""

from __future__ import annotations

from multi_agent_code_factory.profiles import ProfileConfig
from multi_agent_code_factory.schemas.design import DesignArtifact, DevTask
from multi_agent_code_factory.schemas.spec import SpecArtifact
from multi_agent_code_factory.state import PipelineState


def normalize_spec(
    spec: SpecArtifact,
    profile: ProfileConfig,
    state: PipelineState,
) -> SpecArtifact:
    revision = state.spec.revision + 1 if state.spec is not None else 1
    if state.spec_revision_count > 0:
        revision = max(revision, state.spec_revision_count + 1)
    context = dict(spec.context)
    if profile.language:
        context["language"] = profile.language
    return spec.model_copy(
        update={
            "profile": profile.id,
            "revision": revision,
            "context": context,
        }
    )


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
    """Fill common MVP validation gaps when the LLM omits optional-but-required fields."""
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


def normalize_design(
    design: DesignArtifact,
    state: PipelineState,
) -> DesignArtifact:
    spec_title = state.spec.title if state.spec is not None else design.spec_ref
    revision = state.design.revision + 1 if state.design is not None else 1
    if state.design_revision_count > 0:
        revision = max(revision, state.design_revision_count + 1)
    enriched = enrich_design_for_validation(design, spec=state.spec)
    return enriched.model_copy(
        update={
            "spec_ref": spec_title,
            "revision": revision,
        }
    )


def format_design_validation_feedback(state: PipelineState) -> str | None:
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
