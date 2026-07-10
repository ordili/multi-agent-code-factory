"""SPEC-101 至 SPEC-114、SPEC-201–202 可测性与一致性规则。"""

from __future__ import annotations

from multi_agent_code_factory.schemas.spec import (
    ConsistencyModel,
    FeaturePriority,
    PerformanceTier,
    SpecArtifact,
    VerifiableBy,
)
from multi_agent_code_factory.schemas.validation_report import Violation
from multi_agent_code_factory.validators._report import error, warn


def _text_refs_id(text: str, ref_id: str) -> bool:
    return ref_id.lower() in text.lower()


def _p0_user_story_ids(spec: SpecArtifact) -> set[str]:
    valid_ids = {story.id for story in spec.user_stories}
    story_ids: set[str] = set()
    for feature in spec.features:
        if feature.priority != FeaturePriority.P0:
            continue
        if feature.user_story_ids:
            story_ids.update(sid for sid in feature.user_story_ids if sid in valid_ids)
    if not story_ids and any(
        feature.priority == FeaturePriority.P0 for feature in spec.features
    ):
        story_ids = valid_ids
    return story_ids


def _story_covered_by_ac_or_manual_kpi(spec: SpecArtifact, story_id: str) -> bool:
    for ac in spec.acceptance_criteria:
        if _text_refs_id(ac.description, story_id):
            return True
    for metric in spec.success_metrics:
        if metric.verifiable_by != VerifiableBy.MANUAL:
            continue
        if _text_refs_id(metric.description, story_id) or _text_refs_id(
            metric.target, story_id
        ):
            return True
    return False


def validate_spec_extended_rules(spec: SpecArtifact) -> list[Violation]:
    """SPEC-101 至 SPEC-114、SPEC-201–202 扩展规则。"""
    violations: list[Violation] = []

    storage = spec.context.get("storage")
    if not isinstance(storage, str) or not storage.strip():
        violations.append(
            error(
                "SPEC-017",
                "context.storage is required (e.g. none, local_file, json_file)",
                path="/context/storage",
                field="storage",
            )
        )

    feature_ids = {feature.id for feature in spec.features}
    for req in spec.requirement_pool:
        if req.feature_id and req.feature_id not in feature_ids:
            violations.append(
                error(
                    "SPEC-105",
                    f"requirement_pool {req.id} references unknown feature "
                    f"{req.feature_id!r}",
                    field="requirement_pool",
                )
            )

    scope_in_lower = {item.lower() for item in spec.scope_in}
    for item in spec.scope_out:
        if item.lower() in scope_in_lower:
            violations.append(
                warn(
                    "SPEC-103",
                    f"scope_out item {item!r} also appears in scope_in",
                    field="scope_out",
                )
            )

    if spec.constraints:
        for constraint in spec.constraints:
            if not str(constraint).strip():
                violations.append(
                    warn(
                        "SPEC-104",
                        "constraints must not contain empty entries",
                        field="constraints",
                    )
                )

    ac_ids = {ac.id for ac in spec.acceptance_criteria}
    kpi_ids = {metric.id for metric in spec.success_metrics}
    covered_refs: set[str] = ac_ids | kpi_ids
    for feature in spec.features:
        if feature.priority != FeaturePriority.P0:
            continue
        feature_covered = feature.id in covered_refs or any(
            ac.id in covered_refs for ac in spec.acceptance_criteria
        )
        if not feature_covered:
            violations.append(
                warn(
                    "SPEC-106",
                    f"P0 feature {feature.id} lacks AC or KPI trace",
                    field="features",
                )
            )

    for req in spec.requirement_pool:
        for feature in spec.features:
            if (
                req.description.strip().lower() == feature.description.strip().lower()
                or req.description.strip().lower() == feature.name.strip().lower()
            ):
                violations.append(
                    warn(
                        "SPEC-107",
                        f"requirement_pool {req.id} duplicates feature {feature.id}",
                        field="requirement_pool",
                    )
                )

    op = spec.operational_profile
    if op.high_concurrency and op.performance.tier == PerformanceTier.BEST_EFFORT:
        violations.append(
            warn(
                "SPEC-108",
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
                "SPEC-109",
                "performance.tier=custom requires performance.notes",
                field="operational_profile.performance.notes",
            )
        )

    cp = spec.consistency_profile
    if cp.consistency_model == ConsistencyModel.CUSTOM and not (cp.notes or "").strip():
        violations.append(
            error(
                "SPEC-111",
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
                "SPEC-110",
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
                "SPEC-112",
                "multi_writer=true should not use conflict_strategy=not_applicable",
                field="consistency_profile.conflict_strategy",
            )
        )

    if cp.idempotency_required and cp.delivery.value == "at_least_once":
        idempotency_covered = any(
            "幂等" in ac.description or "retry" in ac.description.lower()
            for ac in spec.acceptance_criteria
        ) or any(
            "幂等" in metric.description or "retry" in metric.description.lower()
            for metric in spec.success_metrics
        )
        if not idempotency_covered:
            violations.append(
                warn(
                    "SPEC-113",
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
                "SPEC-114",
                "spec stage operational/consistency numeric fields should be empty",
                field="operational_profile",
            )
        )

    has_automated = any(
        ac.verifiable_by == VerifiableBy.AUTOMATED_TEST
        for ac in spec.acceptance_criteria
    )
    if not has_automated:
        violations.append(
            warn(
                "SPEC-201",
                "acceptance_criteria should include automated_test entry",
                field="acceptance_criteria",
            )
        )

    if spec.revision < 1:
        violations.append(
            warn(
                "SPEC-202",
                f"revision {spec.revision} should be >= 1",
                field="revision",
            )
        )

    for ac in spec.acceptance_criteria:
        if not ac.description.strip():
            violations.append(
                error(
                    "SPEC-101",
                    f"acceptance criterion {ac.id} description must be non-empty",
                    field="acceptance_criteria",
                )
            )

    glossary = spec.context.get("glossary")
    if isinstance(glossary, list):
        for index, item in enumerate(glossary):
            if not isinstance(item, dict):
                violations.append(
                    warn(
                        "SPEC-118",
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
                        "SPEC-118",
                        f"context.glossary[{index}].term must be non-empty",
                        field="context.glossary",
                    )
                )
            if not isinstance(definition, str) or not definition.strip():
                violations.append(
                    warn(
                        "SPEC-118",
                        f"context.glossary[{index}].definition must be non-empty",
                        field="context.glossary",
                    )
                )

    for story_id in sorted(_p0_user_story_ids(spec)):
        if not _story_covered_by_ac_or_manual_kpi(spec, story_id):
            violations.append(
                warn(
                    "SPEC-102",
                    f"P0 user story {story_id} should be covered by AC or manual KPI",
                    field="acceptance_criteria",
                )
            )

    return violations
