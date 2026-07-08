"""评审报告（Reviewer 输出）的 Pydantic 模型。"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from multi_agent_code_factory.schemas._base import ARTIFACT_VERSION


class ReviewNextStage(StrEnum):
    DEVELOPER = "developer"
    ARCHITECT = "architect"
    PM = "pm"
    DEPLOY = "deploy"


class FindingSeverity(StrEnum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"


class FindingCategory(StrEnum):
    SECURITY = "security"
    PERFORMANCE = "performance"
    CORRECTNESS = "correctness"
    STYLE = "style"


class FindingRouting(StrEnum):
    DEVELOPER_FIX = "developer_fix"
    ARCHITECT_REDESIGN = "architect_redesign"
    PM_SCOPE_CHANGE = "pm_scope_change"


class Finding(BaseModel):
    id: str
    severity: FindingSeverity
    category: FindingCategory
    message: str
    blocking: bool = False
    file: str | None = None
    routing: FindingRouting | None = None


class AcceptanceCoverageItem(BaseModel):
    id: str
    met: bool
    note: str | None = None


class ReviewReport(BaseModel):
    version: ARTIFACT_VERSION
    approved: bool
    next_stage: ReviewNextStage
    summary: str
    findings: list[Finding] = Field(default_factory=list)
    acceptance_coverage: list[AcceptanceCoverageItem] = Field(default_factory=list)
