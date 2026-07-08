"""条件路由决策：下一节点、状态补丁与过期产物标记。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from multi_agent_code_factory.config import LoopLimits
from multi_agent_code_factory.pipeline_nodes import PipelineNode
from multi_agent_code_factory.log import get_logger
from multi_agent_code_factory.profile_config import ProfileConfig, ValidationBlockOn
from multi_agent_code_factory.schemas.review import ReviewNextStage
from multi_agent_code_factory.state import PipelineState

IMPL_STALE_FILES = ["test_report.json", "review.json"]
DESIGN_ESCALATION_STALE_FILES = [*IMPL_STALE_FILES, "dev_manifest.json"]
SPEC_ESCALATION_STALE_FILES = [
    *DESIGN_ESCALATION_STALE_FILES,
    "design.json",
    "design_validation.json",
    "flow.mmd",
]

logger = get_logger("graph.routing")

N = PipelineNode


@dataclass
class RouteDecision:
    """路由结果：目标节点、状态更新与需标记为过期的产物文件。"""

    next_node: PipelineNode
    state_updates: dict[str, Any] = field(default_factory=dict)
    stale_artifacts: list[str] = field(default_factory=list)

    def apply(self, state: PipelineState) -> dict[str, Any]:
        patch = dict(self.state_updates)
        patch["pipeline_route"] = self.next_node
        for key, value in self.state_updates.items():
            setattr(state, key, value)
        state.pipeline_route = self.next_node
        return patch


def _limit_route(limits: LoopLimits) -> PipelineNode:
    return PipelineNode(limits.on_limit_exceeded.value)


def decide_after_spec_validate(
    state: PipelineState,
    profile: ProfileConfig,
    limits: LoopLimits,
) -> RouteDecision:
    """规格校验后路由：重试 PM、进入 spec HITL 或 Architect。"""
    validation = state.spec_validation
    if (
        validation is not None
        and not validation.passed
        and profile.validation.spec.block_on == ValidationBlockOn.ERROR
    ):
        if state.spec_revision_count >= limits.max_spec_revisions:
            logger.error(
                "spec validation loop limit reached revisions=%s max=%s",
                state.spec_revision_count,
                limits.max_spec_revisions,
            )
            return RouteDecision(_limit_route(limits))
        logger.warning(
            "spec validation failed; retry pm revision=%s/%s",
            state.spec_revision_count + 1,
            limits.max_spec_revisions,
        )
        return RouteDecision(
            N.PM,
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
        logger.info("spec validation passed; route spec_hitl")
        return RouteDecision(N.SPEC_HITL)
    logger.info("spec validation passed; route architect")
    return RouteDecision(N.ARCHITECT)


def decide_after_design_validate(
    state: PipelineState,
    profile: ProfileConfig,
    limits: LoopLimits,
) -> RouteDecision:
    """设计校验后路由：重试 Architect、进入 design HITL 或 Developer。"""
    validation = state.design_validation
    if (
        validation is not None
        and not validation.passed
        and profile.validation.design.block_on == ValidationBlockOn.ERROR
    ):
        if state.design_revision_count >= limits.max_design_revisions:
            logger.error(
                "design validation loop limit reached revisions=%s max=%s",
                state.design_revision_count,
                limits.max_design_revisions,
            )
            return RouteDecision(_limit_route(limits))
        logger.warning(
            "design validation failed; retry architect revision=%s/%s",
            state.design_revision_count + 1,
            limits.max_design_revisions,
        )
        return RouteDecision(
            N.ARCHITECT,
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
        logger.info("design validation passed; route design_hitl")
        return RouteDecision(N.DESIGN_HITL)
    logger.info("design validation passed; route developer")
    return RouteDecision(N.DEVELOPER)


def decide_after_test(state: PipelineState, limits: LoopLimits) -> RouteDecision:
    """QA 测试后路由：通过则 Reviewer，失败则重试 Developer 或升环。"""
    report = state.test_report
    if report is not None and report.passed:
        logger.info("qa passed; route reviewer")
        return RouteDecision(N.REVIEWER)
    if state.impl_retry_count >= limits.max_impl_retries:
        logger.error(
            "implementation loop limit reached retries=%s max=%s",
            state.impl_retry_count,
            limits.max_impl_retries,
        )
        return RouteDecision(_limit_route(limits))
    logger.warning(
        "qa failed; retry developer attempt=%s/%s",
        state.impl_retry_count + 1,
        limits.max_impl_retries,
    )
    return RouteDecision(
        N.DEVELOPER,
        state_updates={"impl_retry_count": state.impl_retry_count + 1},
    )


def decide_after_review(state: PipelineState, limits: LoopLimits) -> RouteDecision:
    """评审后路由：按 next_stage 回退、升环或进入 deploy HITL。"""
    review = state.review
    if review is None:
        msg = "decide_after_review requires review"
        raise ValueError(msg)

    stage = review.next_stage

    if stage == ReviewNextStage.DEPLOY:
        if not review.approved:
            if state.impl_retry_count >= limits.max_impl_retries:
                logger.error(
                    "review rejected deploy; implementation loop limit reached retries=%s max=%s",
                    state.impl_retry_count,
                    limits.max_impl_retries,
                )
                return RouteDecision(_limit_route(limits))
            logger.warning("review rejected deploy; retry developer")
            return RouteDecision(
                N.DEVELOPER,
                state_updates={"impl_retry_count": state.impl_retry_count + 1},
            )
        logger.info("review approved; route deploy_hitl")
        return RouteDecision(N.DEPLOY_HITL)

    if stage == ReviewNextStage.DEVELOPER:
        if state.impl_retry_count >= limits.max_impl_retries:
            logger.error(
                "review escalated developer; implementation loop limit reached retries=%s max=%s",
                state.impl_retry_count,
                limits.max_impl_retries,
            )
            return RouteDecision(_limit_route(limits))
        logger.warning("review escalated developer; retry developer")
        return RouteDecision(
            N.DEVELOPER,
            state_updates={"impl_retry_count": state.impl_retry_count + 1},
        )

    if stage == ReviewNextStage.ARCHITECT:
        if state.design_revision_count >= limits.max_design_revisions:
            logger.error(
                "review escalated architect; design loop limit reached revisions=%s max=%s",
                state.design_revision_count,
                limits.max_design_revisions,
            )
            return RouteDecision(_limit_route(limits))
        logger.warning("review escalated architect; retry architect")
        return RouteDecision(
            N.ARCHITECT,
            state_updates={
                "design_revision_count": state.design_revision_count + 1,
                "test_report": None,
                "review": None,
                "dev_manifest": None,
            },
            stale_artifacts=DESIGN_ESCALATION_STALE_FILES,
        )

    if stage == ReviewNextStage.PM:
        if state.spec_revision_count >= limits.max_spec_revisions:
            logger.error(
                "review escalated pm; spec loop limit reached revisions=%s max=%s",
                state.spec_revision_count,
                limits.max_spec_revisions,
            )
            return RouteDecision(_limit_route(limits))
        logger.warning("review escalated pm; retry pm")
        return RouteDecision(
            N.PM,
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

    return RouteDecision(PipelineNode(stage.value))


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
