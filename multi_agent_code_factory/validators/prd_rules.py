"""PRD-001 至 PRD-016 校验规则（MVP 白名单）。"""

from __future__ import annotations

from typing import Any

from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.schemas.prd import (
    PrdArtifact,
)
from multi_agent_code_factory.schemas.validation_report import Violation
from multi_agent_code_factory.validators._report import error
from multi_agent_code_factory.validators.prd_rules_extended import (
    validate_prd_extended_rules,
)


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
                    "PRD-007",
                    f"context.{key} must be {rule['const']!r}",
                    path=f"/context/{key}",
                    field=key,
                )
            )
        enum = rule.get("enum")
        if isinstance(enum, list) and value not in enum:
            violations.append(
                error(
                    "PRD-007",
                    f"context.{key} must be one of {enum}",
                    path=f"/context/{key}",
                    field=key,
                )
            )
    return violations


def validate_prd_rules(
    prd: PrdArtifact,
    profile: ProfileConfig,
) -> list[Violation]:
    """对 PrdArtifact 执行 PRD-001 至 PRD-016 规则校验，返回违规列表。"""
    violations: list[Violation] = []

    # PRD-001 / PRD-002：验收标准
    if not prd.acceptance_criteria:
        violations.append(
            error(
                "PRD-001",
                "acceptance_criteria must not be empty",
                field="acceptance_criteria",
            )
        )
    ac_dupes = _duplicate_ids(prd.acceptance_criteria)
    for ac_id in ac_dupes:
        violations.append(
            error(
                "PRD-002",
                f"duplicate acceptance criterion id: {ac_id}",
                field="acceptance_criteria",
            )
        )

    # PRD-003 / PRD-004：范围与必填字段
    if not prd.scope_in:
        violations.append(
            error("PRD-003", "scope_in must not be empty", field="scope_in")
        )

    if not prd.title.strip():
        violations.append(error("PRD-004", "title must not be empty", field="title"))
    if not prd.summary.strip():
        violations.append(
            error("PRD-004", "summary must not be empty", field="summary")
        )

    # PRD-005 / PRD-006 / PRD-007：Profile 与 context 一致性
    if prd.profile != profile.id:
        violations.append(
            error(
                "PRD-005",
                f"prd.profile {prd.profile!r} does not match "
                f"CLI profile {profile.id!r}",
                field="profile",
            )
        )

    if profile.language:
        context_language = prd.context.get("language")
        if context_language != profile.language:
            violations.append(
                error(
                    "PRD-006",
                    (
                        f"context.language {context_language!r} must match "
                        f"profile language {profile.language!r}"
                    ),
                    path="/context/language",
                    field="language",
                )
            )

    if profile.context_schema:
        violations.extend(_validate_context_schema(prd.context, profile.context_schema))

    # PRD-008 至 PRD-012：ID 唯一性与必填集合
    id_buckets: dict[str, list[str]] = {
        "user_stories": [story.id for story in prd.user_stories],
        "requirement_pool": [item.id for item in prd.requirement_pool],
        "features": [feature.id for feature in prd.features],
        "success_metrics": [metric.id for metric in prd.success_metrics],
    }
    for bucket, ids in id_buckets.items():
        dupes = {item for item in ids if ids.count(item) > 1}
        for dup in dupes:
            violations.append(
                error("PRD-008", f"duplicate id in {bucket}: {dup}", field=bucket)
            )

    if not prd.features:
        violations.append(
            error("PRD-009", "features must not be empty", field="features")
        )
    for feature_id in _duplicate_ids(prd.features):
        violations.append(
            error("PRD-010", f"duplicate feature id: {feature_id}", field="features")
        )

    for metric_id in _duplicate_ids(prd.success_metrics):
        violations.append(
            error(
                "PRD-012",
                f"duplicate success metric id: {metric_id}",
                field="success_metrics",
            )
        )
    for metric in prd.success_metrics:
        if not metric.target.strip():
            violations.append(
                error(
                    "PRD-012",
                    f"success_metrics[{metric.id}].target must not be empty",
                    field="success_metrics",
                )
            )

    # PRD-013 / PRD-014：运行画像
    if prd.operational_profile is None:
        violations.append(
            error(
                "PRD-013",
                "operational_profile is required",
                field="operational_profile",
            )
        )
    else:
        if not prd.operational_profile.user_scale:
            violations.append(
                error("PRD-014", "operational_profile.user_scale is required")
            )
        if prd.operational_profile.performance.tier is None:
            violations.append(
                error("PRD-014", "operational_profile.performance.tier is required")
            )

    # PRD-015 / PRD-016：一致性画像
    if prd.consistency_profile is None:
        violations.append(
            error(
                "PRD-015",
                "consistency_profile is required",
                field="consistency_profile",
            )
        )
    else:
        cp = prd.consistency_profile
        if not cp.consistency_model:
            violations.append(error("PRD-016", "consistency_model is required"))
        if not cp.delivery:
            violations.append(error("PRD-016", "delivery is required"))
        if cp.multi_writer is None:
            violations.append(error("PRD-016", "multi_writer is required"))
        if cp.idempotency_required is None:
            violations.append(error("PRD-016", "idempotency_required is required"))

    violations.extend(validate_prd_extended_rules(prd))

    return violations
