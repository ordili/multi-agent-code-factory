"""SPEC-001-016 validation rules (MVP whitelist)."""

from __future__ import annotations

from typing import Any

from multi_agent_code_factory.profiles import ProfileConfig
from multi_agent_code_factory.schemas.spec import (
    ConsistencyModel,
    SpecArtifact,
)
from multi_agent_code_factory.schemas.validation_report import Violation
from multi_agent_code_factory.validators._report import error


def _duplicate_ids(items: list[Any], id_attr: str = "id") -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for item in items:
        value = getattr(item, id_attr, None)
        if not isinstance(value, str):
            continue
        if value in seen:
            duplicates.append(value)
        seen.add(value)
    return duplicates


def _validate_context_schema(
    context: dict[str, Any],
    schema: dict[str, Any],
) -> list[Violation]:
    violations: list[Violation] = []
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        return violations
    for key, rule in properties.items():
        if not isinstance(rule, dict):
            continue
        if key not in context:
            continue
        value = context[key]
        if "const" in rule and value != rule["const"]:
            violations.append(
                error(
                    "SPEC-007",
                    f"context.{key} must be {rule['const']!r}",
                    path=f"/context/{key}",
                    field=key,
                )
            )
        enum = rule.get("enum")
        if isinstance(enum, list) and value not in enum:
            violations.append(
                error(
                    "SPEC-007",
                    f"context.{key} must be one of {enum}",
                    path=f"/context/{key}",
                    field=key,
                )
            )
    return violations


def validate_spec_rules(
    spec: SpecArtifact,
    profile: ProfileConfig,
) -> list[Violation]:
    violations: list[Violation] = []

    if not spec.acceptance_criteria:
        violations.append(
            error(
                "SPEC-001",
                "acceptance_criteria must not be empty",
                field="acceptance_criteria",
            )
        )
    ac_dupes = _duplicate_ids(spec.acceptance_criteria)
    for ac_id in ac_dupes:
        violations.append(
            error(
                "SPEC-002",
                f"duplicate acceptance criterion id: {ac_id}",
                field="acceptance_criteria",
            )
        )

    if not spec.scope_in:
        violations.append(
            error("SPEC-003", "scope_in must not be empty", field="scope_in")
        )

    if not spec.title.strip():
        violations.append(error("SPEC-004", "title must not be empty", field="title"))
    if not spec.summary.strip():
        violations.append(
            error("SPEC-004", "summary must not be empty", field="summary")
        )

    if spec.profile != profile.id:
        violations.append(
            error(
                "SPEC-005",
                f"spec.profile {spec.profile!r} does not match "
                f"CLI profile {profile.id!r}",
                field="profile",
            )
        )

    if profile.language:
        context_language = spec.context.get("language")
        if context_language != profile.language:
            violations.append(
                error(
                    "SPEC-006",
                    (
                        f"context.language {context_language!r} must match "
                        f"profile language {profile.language!r}"
                    ),
                    path="/context/language",
                    field="language",
                )
            )

    if profile.context_schema:
        violations.extend(
            _validate_context_schema(spec.context, profile.context_schema)
        )

    id_buckets: dict[str, list[str]] = {
        "user_stories": [story.id for story in spec.user_stories],
        "requirement_pool": [item.id for item in spec.requirement_pool],
        "features": [feature.id for feature in spec.features],
        "success_metrics": [metric.id for metric in spec.success_metrics],
    }
    for bucket, ids in id_buckets.items():
        dupes = {item for item in ids if ids.count(item) > 1}
        for dup in dupes:
            violations.append(
                error("SPEC-008", f"duplicate id in {bucket}: {dup}", field=bucket)
            )

    if not spec.features:
        violations.append(
            error("SPEC-009", "features must not be empty", field="features")
        )
    for feature_id in _duplicate_ids(spec.features):
        violations.append(
            error("SPEC-010", f"duplicate feature id: {feature_id}", field="features")
        )

    if not spec.success_metrics:
        violations.append(
            error(
                "SPEC-011", "success_metrics must not be empty", field="success_metrics"
            )
        )
    for metric_id in _duplicate_ids(spec.success_metrics):
        violations.append(
            error(
                "SPEC-012",
                f"duplicate success metric id: {metric_id}",
                field="success_metrics",
            )
        )
    for metric in spec.success_metrics:
        if not metric.target.strip():
            violations.append(
                error(
                    "SPEC-012",
                    f"success_metrics[{metric.id}].target must not be empty",
                    field="success_metrics",
                )
            )

    if spec.operational_profile is None:
        violations.append(
            error(
                "SPEC-013",
                "operational_profile is required",
                field="operational_profile",
            )
        )
    else:
        if not spec.operational_profile.user_scale:
            violations.append(
                error("SPEC-014", "operational_profile.user_scale is required")
            )
        if spec.operational_profile.performance.tier is None:
            violations.append(
                error("SPEC-014", "operational_profile.performance.tier is required")
            )

    if spec.consistency_profile is None:
        violations.append(
            error(
                "SPEC-015",
                "consistency_profile is required",
                field="consistency_profile",
            )
        )
    else:
        cp = spec.consistency_profile
        if not cp.consistency_model:
            violations.append(error("SPEC-016", "consistency_model is required"))
        if not cp.delivery:
            violations.append(error("SPEC-016", "delivery is required"))
        if cp.multi_writer is None:
            violations.append(error("SPEC-016", "multi_writer is required"))
        if cp.idempotency_required is None:
            violations.append(error("SPEC-016", "idempotency_required is required"))
        if (
            cp.consistency_model == ConsistencyModel.CUSTOM
            and not (cp.notes or "").strip()
        ):
            violations.append(
                error(
                    "SPEC-016",
                    "consistency_profile.notes required when consistency_model=custom",
                    field="consistency_profile.notes",
                )
            )

    return violations
