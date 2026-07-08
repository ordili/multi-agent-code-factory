"""开发清单（Developer 输出）的 Pydantic 模型。"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from multi_agent_code_factory.schemas._base import ARTIFACT_VERSION


class ChangeType(StrEnum):
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"


class ChangedFile(BaseModel):
    path: str
    change_type: ChangeType


class DevReflection(BaseModel):
    attempt: int = Field(ge=1)
    hypothesis: str
    next_action: str


class DevManifest(BaseModel):
    version: ARTIFACT_VERSION
    tasks_completed: list[str] = Field(default_factory=list)
    changed_files: list[ChangedFile] = Field(default_factory=list)
    lint_passed: bool | None = None
    needs_architect: bool = False
    escalation_note: str | None = None
    reflection: DevReflection | None = None
    incremental_plan: str | None = None
    notes: str | None = None
