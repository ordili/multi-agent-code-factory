"""ValidationReport — spec_validate / design_validate output."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from multi_agent_code_factory.schemas._base import ARTIFACT_VERSION


class ValidationTarget(StrEnum):
    SPEC = "spec"
    DESIGN = "design"


class ViolationSeverity(StrEnum):
    ERROR = "error"
    WARN = "warn"
    INFO = "info"


class Violation(BaseModel):
    rule_id: str
    severity: ViolationSeverity
    message: str
    path: str | None = None
    field: str | None = None


class ValidationReport(BaseModel):
    version: ARTIFACT_VERSION
    target: ValidationTarget
    passed: bool
    error_count: int = Field(ge=0)
    warn_count: int = Field(ge=0)
    violations: list[Violation] = Field(default_factory=list)
    require_hitl: bool = False
    validated_at: str | None = None
