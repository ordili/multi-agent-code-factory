from __future__ import annotations

import pytest
from multi_agent_code_factory.config import LoopLimits, OnLimitExceeded
from multi_agent_code_factory.graph_routing import (
    route_after_design_validate,
    route_after_prd_validate,
    route_after_review,
    route_after_test,
)
from multi_agent_code_factory.profile_config import (
    ProfileConfig,
    ValidationConfig,
    ValidationGateConfig,
    load_profile,
)
from multi_agent_code_factory.schemas.review import ReviewNextStage, ReviewReport
from multi_agent_code_factory.schemas.test_report import (
    TestReport as TestReportArtifact,
)
from multi_agent_code_factory.schemas.test_report import (
    TestSummary as TestSummaryModel,
)
from multi_agent_code_factory.schemas.validation_report import (
    ValidationReport,
    ValidationTarget,
)
from multi_agent_code_factory.state import PipelineState


@pytest.fixture
def limits() -> LoopLimits:
    return LoopLimits(
        max_impl_retries=3,
        max_design_revisions=2,
        max_prd_revisions=1,
    )


@pytest.fixture
def default_profile() -> ProfileConfig:
    return load_profile("python")


def _failed_validation(target: ValidationTarget) -> ValidationReport:
    return ValidationReport(
        version="1",
        target=target,
        passed=False,
        error_count=1,
        warn_count=0,
    )


def _passed_test_report() -> TestReportArtifact:
    return TestReportArtifact(
        version="1",
        passed=True,
        exit_code=0,
        summary=TestSummaryModel(total=1, passed=1, failed=0, skipped=0),
        duration_sec=0.1,
        command="pytest",
        parser="junit_xml",
    )


def _failed_test_report() -> TestReportArtifact:
    return TestReportArtifact(
        version="1",
        passed=False,
        exit_code=1,
        summary=TestSummaryModel(total=1, passed=0, failed=1, skipped=0),
        duration_sec=0.1,
        command="pytest",
        parser="junit_xml",
    )


def test_route_after_prd_validate_passes_to_architect(
    default_profile: ProfileConfig,
    limits: LoopLimits,
) -> None:
    state = PipelineState(
        prd_validation=ValidationReport(
            version="1",
            target=ValidationTarget.PRD,
            passed=True,
            error_count=0,
            warn_count=0,
        )
    )
    assert route_after_prd_validate(state, default_profile, limits) == "architect"


def test_route_after_prd_validate_failure_returns_pm(
    default_profile: ProfileConfig,
    limits: LoopLimits,
) -> None:
    state = PipelineState(prd_validation=_failed_validation(ValidationTarget.PRD))
    assert route_after_prd_validate(state, default_profile, limits) == "pm"
    assert state.prd_revision_count == 1


def test_route_after_prd_validate_limit_exceeded(
    default_profile: ProfileConfig,
    limits: LoopLimits,
) -> None:
    state = PipelineState(
        prd_validation=_failed_validation(ValidationTarget.PRD),
        prd_revision_count=limits.max_prd_revisions,
    )
    assert route_after_prd_validate(state, default_profile, limits) == "fail"


def test_route_after_prd_validate_require_hitl(
    limits: LoopLimits,
) -> None:
    profile = load_profile("python")
    profile = profile.model_copy(
        update={
            "validation": ValidationConfig(
                spec=ValidationGateConfig(require_hitl=True),
                design=profile.validation.design,
            )
        }
    )
    state = PipelineState(
        prd_validation=ValidationReport(
            version="1",
            target=ValidationTarget.PRD,
            passed=True,
            error_count=0,
            warn_count=0,
        )
    )
    assert route_after_prd_validate(state, profile, limits) == "prd_hitl"


def test_route_after_design_validate_failure_returns_architect(
    default_profile: ProfileConfig,
    limits: LoopLimits,
) -> None:
    state = PipelineState(design_validation=_failed_validation(ValidationTarget.DESIGN))
    assert route_after_design_validate(state, default_profile, limits) == "architect"
    assert state.design_revision_count == 1


def test_route_after_design_validate_require_hitl_from_report(
    default_profile: ProfileConfig,
    limits: LoopLimits,
) -> None:
    state = PipelineState(
        design_validation=ValidationReport(
            version="1",
            target=ValidationTarget.DESIGN,
            passed=True,
            error_count=0,
            warn_count=0,
            require_hitl=True,
        )
    )
    assert route_after_design_validate(state, default_profile, limits) == "design_hitl"


def test_route_after_test_pass_to_reviewer(limits: LoopLimits) -> None:
    state = PipelineState(test_report=_passed_test_report())
    assert route_after_test(state, limits) == "reviewer"


def test_route_after_test_fail_increments_impl_retry(limits: LoopLimits) -> None:
    state = PipelineState(test_report=_failed_test_report())
    assert route_after_test(state, limits) == "developer"
    assert state.impl_retry_count == 1


def test_route_after_test_limit_exceeded(limits: LoopLimits) -> None:
    state = PipelineState(
        test_report=_failed_test_report(),
        impl_retry_count=limits.max_impl_retries,
    )
    assert route_after_test(state, limits) == "fail"


def test_route_after_review_deploy_approved_goes_to_deploy_hitl(
    limits: LoopLimits,
) -> None:
    state = PipelineState(
        review=ReviewReport(
            version="1",
            approved=True,
            next_stage=ReviewNextStage.DEPLOY,
            summary="ok",
        )
    )
    assert route_after_review(state, limits) == "deploy_hitl"


def test_route_after_review_deploy_not_approved_returns_developer(
    limits: LoopLimits,
) -> None:
    state = PipelineState(
        review=ReviewReport(
            version="1",
            approved=False,
            next_stage=ReviewNextStage.DEPLOY,
            summary="contradiction",
        )
    )
    assert route_after_review(state, limits) == "developer"
    assert state.impl_retry_count == 1


def test_route_after_review_developer_stage(limits: LoopLimits) -> None:
    state = PipelineState(
        review=ReviewReport(
            version="1",
            approved=False,
            next_stage=ReviewNextStage.DEVELOPER,
            summary="fix tests",
        )
    )
    assert route_after_review(state, limits) == "developer"
    assert state.impl_retry_count == 1


def test_route_after_review_architect_stage(limits: LoopLimits) -> None:
    state = PipelineState(
        review=ReviewReport(
            version="1",
            approved=False,
            next_stage=ReviewNextStage.ARCHITECT,
            summary="redesign",
        )
    )
    assert route_after_review(state, limits) == "architect"
    assert state.design_revision_count == 1


def test_route_after_review_pm_stage(limits: LoopLimits) -> None:
    state = PipelineState(
        review=ReviewReport(
            version="1",
            approved=False,
            next_stage=ReviewNextStage.PM,
            summary="scope issue",
        )
    )
    assert route_after_review(state, limits) == "pm"
    assert state.prd_revision_count == 1


def test_route_after_review_escalation_on_limit() -> None:
    limits = LoopLimits(
        max_impl_retries=0,
        max_design_revisions=0,
        max_prd_revisions=0,
        on_limit_exceeded=OnLimitExceeded.ESCALATION_HITL,
    )
    state = PipelineState(
        review=ReviewReport(
            version="1",
            approved=False,
            next_stage=ReviewNextStage.DEVELOPER,
            summary="fix",
        )
    )
    assert route_after_review(state, limits) == "escalation_hitl"
