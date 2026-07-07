"""SpecArtifact — PM output."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from multi_agent_code_factory.schemas._base import ARTIFACT_VERSION


class VerifiableBy(StrEnum):
    AUTOMATED_TEST = "automated_test"
    MANUAL = "manual"
    DEPLOY_CHECK = "deploy_check"
    LINT = "lint"


class FeaturePriority(StrEnum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


class UserScale(StrEnum):
    PERSONAL = "personal"
    TEAM = "team"
    MULTI_TENANT = "multi_tenant"
    INTERNET = "internet"


class PerformanceTier(StrEnum):
    BEST_EFFORT = "best_effort"
    INTERACTIVE = "interactive"
    LOW_LATENCY = "low_latency"
    CUSTOM = "custom"


class ConsistencyModel(StrEnum):
    LOCAL_ONLY = "local_only"
    STRONG = "strong"
    EVENTUAL = "eventual"
    SESSION = "session"
    CUSTOM = "custom"


class DeliverySemantics(StrEnum):
    BEST_EFFORT = "best_effort"
    AT_MOST_ONCE = "at_most_once"
    AT_LEAST_ONCE = "at_least_once"
    EXACTLY_ONCE = "exactly_once"


class ConflictStrategy(StrEnum):
    NOT_APPLICABLE = "not_applicable"
    SINGLE_WRITER = "single_writer"
    LAST_WRITE_WINS = "last_write_wins"
    VERSIONED_MERGE = "versioned_merge"
    MANUAL = "manual"


class SuccessMetric(BaseModel):
    id: str
    name: str
    description: str
    target: str
    verifiable_by: VerifiableBy


class FeatureItem(BaseModel):
    id: str
    name: str
    description: str
    priority: FeaturePriority
    user_story_ids: list[str] | None = None


class UserStory(BaseModel):
    id: str
    as_a: str
    want: str
    so_that: str


class RequirementItem(BaseModel):
    id: str
    description: str
    priority: FeaturePriority | str
    feature_id: str | None = None


class AcceptanceCriterion(BaseModel):
    id: str
    description: str
    verifiable_by: VerifiableBy


class PerformanceSpec(BaseModel):
    tier: PerformanceTier
    latency: str | None = None
    throughput: str | None = None
    availability: str | None = None
    notes: str | None = None


class OperationalProfile(BaseModel):
    user_scale: UserScale
    user_scale_notes: str | None = None
    high_concurrency: bool
    performance: PerformanceSpec


class ConsistencyProfile(BaseModel):
    consistency_model: ConsistencyModel
    delivery: DeliverySemantics
    multi_writer: bool
    idempotency_required: bool
    conflict_strategy: ConflictStrategy | None = None
    staleness_bound: str | None = None
    recovery: dict[str, Any] | None = None
    notes: str | None = None


class SpecArtifact(BaseModel):
    version: ARTIFACT_VERSION
    profile: str
    revision: int = Field(ge=1)
    parent_task_id: str | None = None
    title: str
    summary: str
    context: dict[str, Any] = Field(default_factory=dict)
    success_metrics: list[SuccessMetric]
    features: list[FeatureItem]
    user_stories: list[UserStory] = Field(default_factory=list)
    requirement_pool: list[RequirementItem] = Field(default_factory=list)
    scope_in: list[str]
    scope_out: list[str] = Field(default_factory=list)
    operational_profile: OperationalProfile
    consistency_profile: ConsistencyProfile
    acceptance_criteria: list[AcceptanceCriterion]
    constraints: list[str] = Field(default_factory=list)
