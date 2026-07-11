"""ValidationReport helpers for semantic rule severities."""

from __future__ import annotations

from multi_agent_code_factory.profile_config import ValidationBlockOn
from multi_agent_code_factory.schemas.validation_report import (
    ValidationReport,
    ValidationTarget,
    Violation,
    ViolationSeverity,
)
from multi_agent_code_factory.validators._report import build_validation_report

_SEMANTIC_RULE_PREFIXES = ("PRD-S", "DES-S")


def is_semantic_rule_id(rule_id: str) -> bool:
    return rule_id.startswith(_SEMANTIC_RULE_PREFIXES)


def apply_semantic_block_on(
    violations: list[Violation],
    semantic_block_on: ValidationBlockOn | None,
) -> list[Violation]:
    """Downgrade semantic ERROR violations to WARN when semantic_block_on=warn."""
    if semantic_block_on != ValidationBlockOn.WARN:
        return violations
    adjusted: list[Violation] = []
    for item in violations:
        if (
            is_semantic_rule_id(item.rule_id)
            and item.severity == ViolationSeverity.ERROR
        ):
            adjusted.append(
                item.model_copy(update={"severity": ViolationSeverity.WARN})
            )
        else:
            adjusted.append(item)
    return adjusted


def _gate_passed(
    violations: list[Violation],
    block_on: ValidationBlockOn,
    *,
    semantic_only: bool,
) -> bool:
    subset = [
        item
        for item in violations
        if is_semantic_rule_id(item.rule_id) == semantic_only
    ]
    error_count = sum(1 for item in subset if item.severity == ViolationSeverity.ERROR)
    if block_on == ValidationBlockOn.NEVER:
        return True
    return error_count == 0


def build_gate_validation_report(
    target: ValidationTarget,
    violations: list[Violation],
    *,
    block_on: ValidationBlockOn = ValidationBlockOn.ERROR,
    semantic_block_on: ValidationBlockOn | None = None,
    require_hitl: bool = False,
) -> ValidationReport:
    """Build report with separate format vs semantic pass semantics."""
    effective_semantic = semantic_block_on or block_on
    normalized = apply_semantic_block_on(violations, semantic_block_on)
    report = build_validation_report(
        target,
        normalized,
        require_hitl=require_hitl,
        block_on=block_on,
    )
    passed = _gate_passed(normalized, block_on, semantic_only=False) and _gate_passed(
        normalized, effective_semantic, semantic_only=True
    )
    return report.model_copy(update={"passed": passed})
