"""Route decisions with state patches and stale artifact tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from multi_agent_code_factory.config import LoopLimits
from multi_agent_code_factory.profiles import ProfileConfig
from multi_agent_code_factory.state import PipelineState

IMPL_STALE_FILES = ["test_report.json", "review.json"]
DESIGN_ESCALATION_STALE_FILES = [*IMPL_STALE_FILES, "dev_manifest.json"]
SPEC_ESCALATION_STALE_FILES = [
    *DESIGN_ESCALATION_STALE_FILES,
    "design.json",
    "design_validation.json",
    "flow.mmd",
]


@dataclass
class RouteDecision:
    next_node: str
    state_updates: dict[str, Any] = field(default_factory=dict)
    stale_artifacts: list[str] = field(default_factory=list)

    def apply(self, state: PipelineState) -> dict[str, Any]:
        patch = dict(self.state_updates)
        patch["pipeline_route"] = self.next_node
        for key, value in self.state_updates.items():
            setattr(state, key, value)
        state.pipeline_route = self.next_node
        return patch


def _limit_route(limits: LoopLimits) -> str:
    return limits.on_limit_exceeded.value


def decide_after_spec_validate(
    state: PipelineState,
    profile: ProfileConfig,
    limits: LoopLimits,
) -> RouteDecision:
    validation = state.spec_validation
    if (
        validation is not None
        and not validation.passed
        and profile.validation.spec.block_on == "error"
    ):
        if state.spec_revision_count >= limits.max_spec_revisions:
            return RouteDecision(_limit_route(limits))
        return RouteDecision(
            "pm",
            state_updates={
                "spec_revision_count": state.spec_revision_count + 1,
                "design": None,
                "design_validation": None,
                "dev_manifest": None,
                "test_report": None,
                "review": None,
            },
            stale_artifacts=SPEC_ESCALATION_STALE_FILES,
        )
    if profile.validation.spec.require_hitl:
        return RouteDecision("spec_hitl")
    return RouteDecision("architect")


def decide_after_design_validate(
    state: PipelineState,
    profile: ProfileConfig,
    limits: LoopLimits,
) -> RouteDecision:
    validation = state.design_validation
    if (
        validation is not None
        and not validation.passed
        and profile.validation.design.block_on == "error"
    ):
        if state.design_revision_count >= limits.max_design_revisions:
            return RouteDecision(_limit_route(limits))
        return RouteDecision(
            "architect",
            state_updates={
                "design_revision_count": state.design_revision_count + 1,
                "dev_manifest": None,
                "test_report": None,
                "review": None,
            },
            stale_artifacts=DESIGN_ESCALATION_STALE_FILES,
        )
    if profile.validation.design.require_hitl or (
        validation is not None and validation.require_hitl
    ):
        return RouteDecision("design_hitl")
    return RouteDecision("developer")


def decide_after_test(state: PipelineState, limits: LoopLimits) -> RouteDecision:
    report = state.test_report
    if report is not None and report.passed:
        return RouteDecision("reviewer")
    if state.impl_retry_count >= limits.max_impl_retries:
        return RouteDecision(_limit_route(limits))
    return RouteDecision(
        "developer",
        state_updates={"impl_retry_count": state.impl_retry_count + 1},
    )


def decide_after_review(state: PipelineState, limits: LoopLimits) -> RouteDecision:
    review = state.review
    if review is None:
        msg = "decide_after_review requires review"
        raise ValueError(msg)

    stage = review.next_stage.value

    if stage == "deploy":
        if not review.approved:
            if state.impl_retry_count >= limits.max_impl_retries:
                return RouteDecision(_limit_route(limits))
            return RouteDecision(
                "developer",
                state_updates={"impl_retry_count": state.impl_retry_count + 1},
            )
        return RouteDecision("deploy_hitl")

    if stage == "developer":
        if state.impl_retry_count >= limits.max_impl_retries:
            return RouteDecision(_limit_route(limits))
        return RouteDecision(
            "developer",
            state_updates={"impl_retry_count": state.impl_retry_count + 1},
        )

    if stage == "architect":
        if state.design_revision_count >= limits.max_design_revisions:
            return RouteDecision(_limit_route(limits))
        return RouteDecision(
            "architect",
            state_updates={
                "design_revision_count": state.design_revision_count + 1,
                "test_report": None,
                "review": None,
                "dev_manifest": None,
            },
            stale_artifacts=DESIGN_ESCALATION_STALE_FILES,
        )

    if stage == "pm":
        if state.spec_revision_count >= limits.max_spec_revisions:
            return RouteDecision(_limit_route(limits))
        return RouteDecision(
            "pm",
            state_updates={
                "spec_revision_count": state.spec_revision_count + 1,
                "design": None,
                "design_validation": None,
                "dev_manifest": None,
                "test_report": None,
                "review": None,
            },
            stale_artifacts=SPEC_ESCALATION_STALE_FILES,
        )

    return RouteDecision(stage)


def route_after_spec_validate(
    state: PipelineState,
    profile: ProfileConfig,
    limits: LoopLimits,
) -> str:
    decision = decide_after_spec_validate(state, profile, limits)
    decision.apply(state)
    return decision.next_node


def route_after_design_validate(
    state: PipelineState,
    profile: ProfileConfig,
    limits: LoopLimits,
) -> str:
    decision = decide_after_design_validate(state, profile, limits)
    decision.apply(state)
    return decision.next_node


def route_after_test(state: PipelineState, limits: LoopLimits) -> str:
    decision = decide_after_test(state, limits)
    decision.apply(state)
    return decision.next_node


def route_after_review(state: PipelineState, limits: LoopLimits) -> str:
    decision = decide_after_review(state, limits)
    decision.apply(state)
    return decision.next_node
