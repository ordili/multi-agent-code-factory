"""LangGraph pipeline state."""

from __future__ import annotations

from dataclasses import dataclass

from multi_agent_code_factory.config import LoopLimits
from multi_agent_code_factory.profiles import ProfileConfig
from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.schemas.dev_manifest import DevManifest
from multi_agent_code_factory.schemas.hitl import HitlDecision
from multi_agent_code_factory.schemas.review import ReviewReport
from multi_agent_code_factory.schemas.spec import SpecArtifact
from multi_agent_code_factory.schemas.test_report import TestReport
from multi_agent_code_factory.schemas.validation_report import ValidationReport


@dataclass
class PipelineState:
    task_id: str = ""
    user_request: str = ""
    profile: ProfileConfig | None = None
    loop_limits: LoopLimits | None = None
    spec: SpecArtifact | None = None
    spec_validation: ValidationReport | None = None
    design: DesignArtifact | None = None
    design_validation: ValidationReport | None = None
    dev_manifest: DevManifest | None = None
    test_report: TestReport | None = None
    review: ReviewReport | None = None
    hitl: HitlDecision | None = None
    impl_retry_count: int = 0
    design_revision_count: int = 0
    spec_revision_count: int = 0

    def copy_with_counters(
        self,
        *,
        impl_retry_count: int | None = None,
        design_revision_count: int | None = None,
        spec_revision_count: int | None = None,
    ) -> PipelineState:
        return PipelineState(
            task_id=self.task_id,
            user_request=self.user_request,
            profile=self.profile,
            loop_limits=self.loop_limits,
            spec=self.spec,
            spec_validation=self.spec_validation,
            design=self.design,
            design_validation=self.design_validation,
            dev_manifest=self.dev_manifest,
            test_report=self.test_report,
            review=self.review,
            hitl=self.hitl,
            impl_retry_count=(
                self.impl_retry_count if impl_retry_count is None else impl_retry_count
            ),
            design_revision_count=(
                self.design_revision_count
                if design_revision_count is None
                else design_revision_count
            ),
            spec_revision_count=(
                self.spec_revision_count
                if spec_revision_count is None
                else spec_revision_count
            ),
        )
