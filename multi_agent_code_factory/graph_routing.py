"""Conditional routing after validate, test, and review nodes."""

from __future__ import annotations

from multi_agent_code_factory.config import LoopLimits
from multi_agent_code_factory.profiles import ProfileConfig
from multi_agent_code_factory.state import PipelineState


def _limit_route(limits: LoopLimits) -> str:
    return limits.on_limit_exceeded.value


def route_after_spec_validate(
    state: PipelineState,
    profile: ProfileConfig,
    limits: LoopLimits,
) -> str:
    validation = state.spec_validation
    if (
        validation is not None
        and not validation.passed
        and profile.validation.spec.block_on == "error"
    ):
        if state.spec_revision_count >= limits.max_spec_revisions:
            return _limit_route(limits)
        state.spec_revision_count += 1
        return "pm"
    if profile.validation.spec.require_hitl:
        return "spec_hitl"
    return "architect"


def route_after_design_validate(
    state: PipelineState,
    profile: ProfileConfig,
    limits: LoopLimits,
) -> str:
    validation = state.design_validation
    if (
        validation is not None
        and not validation.passed
        and profile.validation.design.block_on == "error"
    ):
        if state.design_revision_count >= limits.max_design_revisions:
            return _limit_route(limits)
        state.design_revision_count += 1
        return "architect"
    if profile.validation.design.require_hitl or (
        validation is not None and validation.require_hitl
    ):
        return "design_hitl"
    return "developer"


def route_after_test(state: PipelineState, limits: LoopLimits) -> str:
    report = state.test_report
    if report is not None and report.passed:
        return "reviewer"
    if state.impl_retry_count >= limits.max_impl_retries:
        return _limit_route(limits)
    state.impl_retry_count += 1
    return "developer"


def route_after_review(state: PipelineState, limits: LoopLimits) -> str:
    review = state.review
    if review is None:
        msg = "route_after_review requires review"
        raise ValueError(msg)

    stage = review.next_stage.value

    if stage == "deploy":
        if not review.approved:
            if state.impl_retry_count >= limits.max_impl_retries:
                return _limit_route(limits)
            state.impl_retry_count += 1
            return "developer"
        return "deploy_hitl"

    if stage == "developer":
        if state.impl_retry_count >= limits.max_impl_retries:
            return _limit_route(limits)
        state.impl_retry_count += 1
        return "developer"

    if stage == "architect":
        if state.design_revision_count >= limits.max_design_revisions:
            return _limit_route(limits)
        state.design_revision_count += 1
        return "architect"

    if stage == "pm":
        if state.spec_revision_count >= limits.max_spec_revisions:
            return _limit_route(limits)
        state.spec_revision_count += 1
        return "pm"

    return stage
