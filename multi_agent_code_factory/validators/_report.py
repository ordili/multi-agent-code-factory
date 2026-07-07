"""Shared validation helpers."""

from __future__ import annotations

from datetime import UTC, datetime

from multi_agent_code_factory.schemas.validation_report import (
    ValidationReport,
    ValidationTarget,
    Violation,
    ViolationSeverity,
)


def iso_now() -> str:
    return datetime.now(tz=UTC).isoformat()


def build_validation_report(
    target: ValidationTarget,
    violations: list[Violation],
    *,
    require_hitl: bool = False,
    block_on: str = "error",
) -> ValidationReport:
    error_count = sum(
        1 for item in violations if item.severity == ViolationSeverity.ERROR
    )
    warn_count = sum(
        1 for item in violations if item.severity == ViolationSeverity.WARN
    )
    if block_on == "never":
        passed = True
    elif block_on == "warn":
        passed = error_count == 0
    else:
        passed = error_count == 0
    return ValidationReport(
        version="1",
        target=target,
        passed=passed,
        error_count=error_count,
        warn_count=warn_count,
        violations=violations,
        require_hitl=require_hitl,
        validated_at=iso_now(),
    )


def error(
    rule_id: str,
    message: str,
    *,
    path: str | None = None,
    field: str | None = None,
) -> Violation:
    return Violation(
        rule_id=rule_id,
        severity=ViolationSeverity.ERROR,
        message=message,
        path=path,
        field=field,
    )


def warn(
    rule_id: str,
    message: str,
    *,
    path: str | None = None,
    field: str | None = None,
) -> Violation:
    return Violation(
        rule_id=rule_id,
        severity=ViolationSeverity.WARN,
        message=message,
        path=path,
        field=field,
    )
