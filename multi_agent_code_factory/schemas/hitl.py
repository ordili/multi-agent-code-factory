"""HitlDecision — human-in-the-loop approval record."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from multi_agent_code_factory.schemas._base import ARTIFACT_VERSION


class HitlStage(StrEnum):
    SPEC = "spec"
    DESIGN = "design"
    DEPLOY = "deploy"
    ESCALATION = "escalation"


class HitlDecision(BaseModel):
    version: ARTIFACT_VERSION
    stage: HitlStage
    required: bool
    reason: list[str] = Field(default_factory=list)
    approved: bool | None = None
    reviewer: str | None = None
    comment: str | None = None
