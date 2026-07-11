"""Tests for semantic gate validation report building."""

from __future__ import annotations

from multi_agent_code_factory.profile_config import ValidationBlockOn
from multi_agent_code_factory.schemas.validation_report import ValidationTarget
from multi_agent_code_factory.validators._report import error, warn
from multi_agent_code_factory.validators._semantic_report import (
    apply_semantic_block_on,
    build_gate_validation_report,
)


def test_semantic_blocking_error_fails_when_semantic_block_on_error() -> None:
    violations = [
        error("PRD-S01", "missing semantic_constraints", field="semantic_constraints"),
    ]
    report = build_gate_validation_report(
        ValidationTarget.PRD,
        violations,
        block_on=ValidationBlockOn.ERROR,
        semantic_block_on=ValidationBlockOn.ERROR,
    )
    assert report.passed is False
    assert any(item.rule_id == "PRD-S01" for item in report.violations)


def test_semantic_blocking_downgraded_when_semantic_block_on_warn() -> None:
    violations = [
        error("PRD-S01", "missing semantic_constraints", field="semantic_constraints"),
    ]
    report = build_gate_validation_report(
        ValidationTarget.PRD,
        violations,
        block_on=ValidationBlockOn.ERROR,
        semantic_block_on=ValidationBlockOn.WARN,
    )
    assert report.passed is True
    assert report.violations[0].severity.value == "warn"


def test_advisory_semantic_warn_does_not_fail_gate() -> None:
    violations = [
        warn("PRD-S04", "FEAT wider than US", field="description"),
    ]
    report = build_gate_validation_report(
        ValidationTarget.PRD,
        violations,
        block_on=ValidationBlockOn.ERROR,
        semantic_block_on=ValidationBlockOn.ERROR,
    )
    assert report.passed is True


def test_format_error_still_fails_when_semantic_warn_only() -> None:
    violations = [
        error("PRD-001", "missing title", field="title"),
        warn("PRD-S05", "SEM not referenced", field="semantic_constraints"),
    ]
    report = build_gate_validation_report(
        ValidationTarget.PRD,
        violations,
        block_on=ValidationBlockOn.ERROR,
        semantic_block_on=ValidationBlockOn.WARN,
    )
    assert report.passed is False


def test_semantic_block_on_defaults_to_block_on() -> None:
    violations = [
        error("DES-S04", "missing SEM in covers", field="test_cases"),
    ]
    report = build_gate_validation_report(
        ValidationTarget.DESIGN,
        violations,
        block_on=ValidationBlockOn.ERROR,
        semantic_block_on=None,
    )
    assert report.passed is False


def test_apply_semantic_block_on_leaves_non_semantic_errors() -> None:
    violations = [
        error("PRD-001", "missing title", field="title"),
        error("PRD-S02", "bad source_ref", field="source_ref"),
    ]
    adjusted = apply_semantic_block_on(violations, ValidationBlockOn.WARN)
    assert adjusted[0].severity.value == "error"
    assert adjusted[1].severity.value == "warn"
