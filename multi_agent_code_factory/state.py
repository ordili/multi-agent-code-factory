"""LangGraph 流水线图状态（节点间传递的 dataclass）。"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import fields as dataclass_fields
from typing import Any

from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.schemas.dev_manifest import DevManifest
from multi_agent_code_factory.schemas.hitl import HitlDecision
from multi_agent_code_factory.schemas.prd import PrdArtifact
from multi_agent_code_factory.schemas.review import ReviewReport
from multi_agent_code_factory.schemas.test_report import TestReport
from multi_agent_code_factory.schemas.validation_report import ValidationReport


@dataclass
class PipelineState:
    """单次 run 在图内流转的可变状态。"""

    task_id: str = ""
    user_request: str = ""
    prd: PrdArtifact | None = None
    prd_validation: ValidationReport | None = None
    design: DesignArtifact | None = None
    design_validation: ValidationReport | None = None
    dev_manifest: DevManifest | None = None
    test_report: TestReport | None = None
    review: ReviewReport | None = None
    hitl: HitlDecision | None = None
    impl_retry_count: int = 0
    design_revision_count: int = 0
    prd_revision_count: int = 0
    pipeline_route: str = ""

    def copy_with_counters(
        self,
        *,
        impl_retry_count: int | None = None,
        design_revision_count: int | None = None,
        prd_revision_count: int | None = None,
    ) -> PipelineState:
        """升环重试时复制 state 并更新计数器。"""
        return PipelineState(
            task_id=self.task_id,
            user_request=self.user_request,
            prd=self.prd,
            prd_validation=self.prd_validation,
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
            prd_revision_count=(
                self.prd_revision_count
                if prd_revision_count is None
                else prd_revision_count
            ),
            pipeline_route=self.pipeline_route,
        )


def _serialize_state_value(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value


def state_to_graph_dict(state: PipelineState) -> dict[str, Any]:
    """将 PipelineState 转为 LangGraph checkpoint / update_state 可用的 dict。"""
    return {
        field.name: _serialize_state_value(getattr(state, field.name))
        for field in dataclass_fields(PipelineState)
    }


def normalize_pipeline_state(state: PipelineState | dict[str, Any]) -> PipelineState:
    """将 checkpoint 反序列化后的 dict 嵌套字段还原为 Pydantic 模型。"""
    from multi_agent_code_factory.artifact_loader import ARTIFACT_MODEL_BY_FIELD

    raw: dict[str, Any]
    if isinstance(state, dict):
        raw = state
    else:
        raw = {
            field.name: getattr(state, field.name)
            for field in dataclass_fields(PipelineState)
        }

    kwargs: dict[str, Any] = {}
    for field in dataclass_fields(PipelineState):
        value = raw.get(field.name)
        if value is None:
            kwargs[field.name] = None
            continue
        model_cls = ARTIFACT_MODEL_BY_FIELD.get(field.name)
        if model_cls is not None and isinstance(value, dict):
            kwargs[field.name] = model_cls.model_validate(value)
        else:
            kwargs[field.name] = value
    return PipelineState(**kwargs)
