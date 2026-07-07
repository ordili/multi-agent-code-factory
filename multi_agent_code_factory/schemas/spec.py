"""SpecArtifact — PM output."""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from multi_agent_code_factory.schemas._base import ARTIFACT_VERSION

_USER_STORY_RE = re.compile(
    r"^As an?\s+(?P<as_a>.+?),\s+I want\s+(?P<want>.+?)(?:\s+so that\s+(?P<so_that>.+))?\.$",
    re.IGNORECASE | re.DOTALL,
)


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


def _parse_user_story_text(text: str, index: int) -> dict[str, str]:
    stripped = text.strip()
    match = _USER_STORY_RE.match(stripped)
    if match:
        return {
            "id": f"US-{index}",
            "as_a": match.group("as_a").strip(),
            "want": match.group("want").strip(),
            "so_that": (match.group("so_that") or "deliver the requested behavior").strip(),
        }
    return {
        "id": f"US-{index}",
        "as_a": "user",
        "want": stripped,
        "so_that": "deliver the requested behavior",
    }


def _coerce_user_stories(value: Any) -> list[Any]:
    if not isinstance(value, list):
        return []
    coerced: list[Any] = []
    for index, item in enumerate(value, start=1):
        if isinstance(item, str):
            coerced.append(_parse_user_story_text(item, index))
        else:
            coerced.append(item)
    return coerced


def _coerce_requirement_pool(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if not isinstance(value, dict):
        return []
    items: list[Any] = []
    counter = 1
    for descriptions in value.values():
        if isinstance(descriptions, str):
            descriptions = [descriptions]
        if not isinstance(descriptions, list):
            continue
        for description in descriptions:
            if isinstance(description, str):
                items.append(
                    {
                        "id": f"REQ-{counter}",
                        "description": description,
                        "priority": "P0",
                    }
                )
                counter += 1
            elif isinstance(description, dict):
                items.append(description)
    return items


def _coerce_operational_profile(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        value = {}
    profile = dict(value)
    profile.setdefault("user_scale", "personal")
    profile.setdefault("high_concurrency", False)
    performance = profile.get("performance")
    if isinstance(performance, str):
        profile["performance"] = {"tier": performance}
    elif not isinstance(performance, dict):
        profile["performance"] = {
            "tier": "best_effort",
            "notes": "coerced default for local CLI",
        }
    else:
        performance = dict(performance)
        performance.setdefault("tier", "best_effort")
        profile["performance"] = performance
    return profile


def _coerce_consistency_profile(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        return {
            "consistency_model": value,
            "delivery": "best_effort",
            "multi_writer": False,
            "idempotency_required": False,
            "conflict_strategy": "not_applicable",
        }
    if not isinstance(value, dict):
        return {
            "consistency_model": "local_only",
            "delivery": "best_effort",
            "multi_writer": False,
            "idempotency_required": False,
            "conflict_strategy": "not_applicable",
        }
    profile = dict(value)
    profile.setdefault("consistency_model", "local_only")
    profile.setdefault("delivery", "best_effort")
    profile.setdefault("multi_writer", False)
    profile.setdefault("idempotency_required", False)
    profile.setdefault("conflict_strategy", "not_applicable")
    return profile


def coerce_spec_payload(data: Any) -> Any:
    """Normalize common LLM JSON shapes before SpecArtifact validation."""
    if not isinstance(data, dict):
        return data
    payload = dict(data)
    payload.setdefault("version", "1")
    payload.setdefault("profile", "unknown")
    payload.setdefault("revision", 1)
    if "user_stories" in payload:
        payload["user_stories"] = _coerce_user_stories(payload["user_stories"])
    if "requirement_pool" in payload:
        payload["requirement_pool"] = _coerce_requirement_pool(payload["requirement_pool"])
    if "operational_profile" in payload:
        payload["operational_profile"] = _coerce_operational_profile(
            payload["operational_profile"]
        )
    if "consistency_profile" in payload:
        payload["consistency_profile"] = _coerce_consistency_profile(
            payload["consistency_profile"]
        )
    return payload


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

    @model_validator(mode="before")
    @classmethod
    def _coerce_llm_payload(cls, data: Any) -> Any:
        return coerce_spec_payload(data)
