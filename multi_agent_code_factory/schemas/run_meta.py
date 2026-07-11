"""单次运行元数据的 Pydantic 模型。"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from multi_agent_code_factory.schemas._base import ARTIFACT_VERSION


class RunStatus(StrEnum):
    RUNNING = "running"
    FAILED = "failed"
    COMPLETED = "completed"


class DeployStatus(StrEnum):
    SKIPPED = "skipped"
    SUCCESS = "success"
    FAILED = "failed"


class BudgetUsage(BaseModel):
    max_llm_calls: int | None = None
    max_tokens: int | None = None
    used_llm_calls: int | None = Field(default=None, ge=0)
    used_tokens: int | None = Field(default=None, ge=0)


class RunMeta(BaseModel):
    version: ARTIFACT_VERSION
    task_id: str
    user_request: str | None = None
    profile: dict[str, Any]
    loop_limits: dict[str, Any]
    impl_retry_count: int = Field(default=0, ge=0)
    design_revision_count: int = Field(default=0, ge=0)
    prd_revision_count: int = Field(default=0, ge=0)
    budget: BudgetUsage | None = None
    checkpoint_id: str | None = None
    deploy_status: DeployStatus = DeployStatus.SKIPPED
    status: RunStatus | None = None
    hitl_history: list[dict[str, Any]] | None = None
    stale_artifacts: list[str] | None = None
    artifact_layout: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    last_continue_at: str | None = None
    last_reentry_node: str | None = None
