"""PRD-101 至 PRD-114、PRD-201–202 可测性与一致性规则。"""

from __future__ import annotations

from multi_agent_code_factory.schemas.prd import (
    ConsistencyModel,
    FeaturePriority,
    PerformanceTier,
    PrdArtifact,
    VerifiableBy,
)
from multi_agent_code_factory.schemas.validation_report import Violation
from multi_agent_code_factory.validators._report import error, warn


def _text_refs_id(text: str, ref_id: str) -> bool:
    return ref_id.lower() in text.lower()


def _p0_user_story_ids(prd: PrdArtifact) -> set[str]:
    valid_ids = {story.id for story in prd.user_stories}
    story_ids: set[str] = set()
    for feature in prd.features:
        if feature.priority != FeaturePriority.P0:
            continue
        if feature.user_story_ids:
            story_ids.update(sid for sid in feature.user_story_ids if sid in valid_ids)
    if not story_ids and any(
        feature.priority == FeaturePriority.P0 for feature in prd.features
    ):
        story_ids = valid_ids
    return story_ids


def _story_covered_by_ac_or_manual_kpi(prd: PrdArtifact, story_id: str) -> bool:
    for ac in prd.acceptance_criteria:
        if _text_refs_id(ac.description, story_id):
            return True
    for metric in prd.success_metrics:
        if metric.verifiable_by != VerifiableBy.MANUAL:
            continue
        if _text_refs_id(metric.description, story_id) or _text_refs_id(
            metric.target, story_id
        ):
            return True
    return False


def validate_prd_extended_rules(prd: PrdArtifact) -> list[Violation]:
    """PRD-101 至 PRD-114、PRD-201–202 扩展规则。"""
    violations: list[Violation] = []

    storage = prd.context.get("storage")
    if not isinstance(storage, str) or not storage.strip():
        violations.append(
            error(
                "PRD-017",
                "context.storage is required (e.g. none, local_file, json_file)",
                path="/context/storage",
                field="storage",
            )
        )

    feature_ids = {feature.id for feature in prd.features}
    for req in prd.requirement_pool:
        if req.feature_id and req.feature_id not in feature_ids:
            violations.append(
                error(
                    "PRD-105",
                    f"requirement_pool {req.id} references unknown feature "
                    f"{req.feature_id!r}",
                    field="requirement_pool",
                )
            )

    scope_in_lower = {item.lower() for item in prd.scope_in}
    for item in prd.scope_out:
        if item.lower() in scope_in_lower:
            violations.append(
                warn(
                    "PRD-103",
                    f"scope_out item {item!r} also appears in scope_in",
                    field="scope_out",
                )
            )

    if prd.constraints:
        for constraint in prd.constraints:
            if not str(constraint).strip():
                violations.append(
                    warn(
                        "PRD-104",
                        "constraints must not contain empty entries",
                        field="constraints",
                    )
                )

    ac_ids = {ac.id for ac in prd.acceptance_criteria}
    kpi_ids = {metric.id for metric in prd.success_metrics}
    covered_refs: set[str] = ac_ids | kpi_ids
    for feature in prd.features:
        if feature.priority != FeaturePriority.P0:
            continue
        feature_covered = feature.id in covered_refs or any(
            ac.id in covered_refs for ac in prd.acceptance_criteria
        )
        if not feature_covered:
            violations.append(
                warn(
                    "PRD-106",
                    f"P0 feature {feature.id} lacks AC or KPI trace",
                    field="features",
                )
            )

    for req in prd.requirement_pool:
        for feature in prd.features:
            if (
                req.description.strip().lower() == feature.description.strip().lower()
                or req.description.strip().lower() == feature.name.strip().lower()
            ):
                violations.append(
                    warn(
                        "PRD-107",
                        f"requirement_pool {req.id} duplicates feature {feature.id}",
                        field="requirement_pool",
                    )
                )

    op = prd.operational_profile
    if op.high_concurrency and op.performance.tier == PerformanceTier.BEST_EFFORT:
        violations.append(
            warn(
                "PRD-108",
                "high_concurrency=true with performance.tier=best_effort",
                field="operational_profile",
            )
        )
    if (
        op.performance.tier == PerformanceTier.CUSTOM
        and not (op.performance.notes or "").strip()
    ):
        violations.append(
            warn(
                "PRD-109",
                "performance.tier=custom requires performance.notes",
                field="operational_profile.performance.notes",
            )
        )

    cp = prd.consistency_profile
    if cp.consistency_model == ConsistencyModel.CUSTOM and not (cp.notes or "").strip():
        violations.append(
            error(
                "PRD-111",
                "consistency_profile.notes required when consistency_model=custom",
                field="consistency_profile.notes",
            )
        )
    if (
        cp.consistency_model == ConsistencyModel.EVENTUAL
        and not (cp.notes or "").strip()
    ):
        violations.append(
            warn(
                "PRD-110",
                "consistency_model=eventual should include qualitative notes",
                field="consistency_profile.notes",
            )
        )
    if (
        cp.multi_writer
        and cp.conflict_strategy
        and cp.conflict_strategy.value == "not_applicable"
    ):
        violations.append(
            warn(
                "PRD-112",
                "multi_writer=true should not use conflict_strategy=not_applicable",
                field="consistency_profile.conflict_strategy",
            )
        )

    if cp.idempotency_required and cp.delivery.value == "at_least_once":
        idempotency_covered = any(
            "幂等" in ac.description or "retry" in ac.description.lower()
            for ac in prd.acceptance_criteria
        ) or any(
            "幂等" in metric.description or "retry" in metric.description.lower()
            for metric in prd.success_metrics
        )
        if not idempotency_covered:
            violations.append(
                warn(
                    "PRD-113",
                    "idempotency_required with at_least_once delivery should "
                    "trace to AC or KPI",
                    field="consistency_profile",
                )
            )

    numeric_fields = [
        op.performance.latency,
        op.performance.throughput,
        op.performance.availability,
        cp.staleness_bound,
    ]
    if cp.recovery:
        numeric_fields.extend(str(v) for v in cp.recovery.values() if v)
    if any(str(field).strip() for field in numeric_fields if field):
        violations.append(
            warn(
                "PRD-114",
                "spec stage operational/consistency numeric fields should be empty",
                field="operational_profile",
            )
        )

    has_automated = any(
        ac.verifiable_by == VerifiableBy.AUTOMATED_TEST
        for ac in prd.acceptance_criteria
    )
    if not has_automated:
        violations.append(
            warn(
                "PRD-201",
                "acceptance_criteria should include automated_test entry",
                field="acceptance_criteria",
            )
        )

    if prd.revision < 1:
        violations.append(
            warn(
                "PRD-202",
                f"revision {prd.revision} should be >= 1",
                field="revision",
            )
        )

    for ac in prd.acceptance_criteria:
        if not ac.description.strip():
            violations.append(
                error(
                    "PRD-101",
                    f"acceptance criterion {ac.id} description must be non-empty",
                    field="acceptance_criteria",
                )
            )

    background = prd.context.get("background")
    if not isinstance(background, str) or not background.strip():
        violations.append(
            warn(
                "PRD-119",
                "context.background must be non-empty narrative for prd.md §3",
                field="context.background",
            )
        )

    glossary = prd.context.get("glossary")
    if isinstance(glossary, list):
        for index, item in enumerate(glossary):
            if not isinstance(item, dict):
                violations.append(
                    warn(
                        "PRD-118",
                        f"context.glossary[{index}] must be an object",
                        field="context.glossary",
                    )
                )
                continue
            term = item.get("term")
            definition = item.get("definition")
            if not isinstance(term, str) or not term.strip():
                violations.append(
                    warn(
                        "PRD-118",
                        f"context.glossary[{index}].term must be non-empty",
                        field="context.glossary",
                    )
                )
            if not isinstance(definition, str) or not definition.strip():
                violations.append(
                    warn(
                        "PRD-118",
                        f"context.glossary[{index}].definition must be non-empty",
                        field="context.glossary",
                    )
                )

    for story_id in sorted(_p0_user_story_ids(prd)):
        if not _story_covered_by_ac_or_manual_kpi(prd, story_id):
            violations.append(
                warn(
                    "PRD-102",
                    f"P0 user story {story_id} should be covered by AC or manual KPI",
                    field="acceptance_criteria",
                )
            )

    return violations
