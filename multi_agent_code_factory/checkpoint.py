"""产物续跑：再入点推断与 checkpointer 工厂。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from multi_agent_code_factory.artifact_loader import (
    artifact_available,
    load_artifact_json,
)
from multi_agent_code_factory.config import LoopLimits
from multi_agent_code_factory.log import get_logger
from multi_agent_code_factory.pipeline_nodes import PipelineNode
from multi_agent_code_factory.schemas.review import ReviewNextStage, ReviewReport
from multi_agent_code_factory.schemas.run_meta import RunMeta, RunStatus
from multi_agent_code_factory.schemas.validation_report import ValidationReport
from multi_agent_code_factory.state import PipelineState

logger = get_logger("checkpoint")

GATE_REENTRY_NODES = frozenset(
    {
        PipelineNode.SPEC_VALIDATE,
        PipelineNode.DESIGN_VALIDATE,
        PipelineNode.QA,
    }
)


class ContinueError(Exception):
    """产物续跑无法继续时抛出。"""


def sqlite_checkpointer(db_path: Path) -> Any:
    """返回 SqliteSaver 上下文管理器（须 ``with`` 包裹续跑 invoke）。"""
    from langgraph.checkpoint.sqlite import SqliteSaver

    db_path.parent.mkdir(parents=True, exist_ok=True)
    return SqliteSaver.from_conn_string(str(db_path))


def build_sqlite_checkpointer(db_path: Path) -> Any:
    """兼容别名；优先使用 ``sqlite_checkpointer``。"""
    return sqlite_checkpointer(db_path)


def _load_validation(
    run_dir: Path,
    filename: str,
    meta: RunMeta,
) -> ValidationReport | None:
    if not artifact_available(run_dir, filename, meta):
        return None
    return load_artifact_json(run_dir, filename, ValidationReport)


def _impl_retry_at_limit(meta: RunMeta) -> bool:
    limits = LoopLimits.model_validate(meta.loop_limits)
    return meta.impl_retry_count >= limits.max_impl_retries


def infer_reentry_node(
    run_dir: Path,
    meta: RunMeta,
    *,
    explicit: str | None = None,
) -> PipelineNode:
    """按设计文档优先级推断再入点；``explicit`` 覆盖自动推断。"""
    if explicit is not None:
        try:
            return PipelineNode(explicit)
        except ValueError as exc:
            msg = f"invalid --reenter value: {explicit!r}"
            raise ContinueError(msg) from exc

    if meta.status == RunStatus.COMPLETED:
        msg = (
            f"task {meta.task_id!r} already completed; "
            "use a new task_id or run --force-new"
        )
        raise ContinueError(msg)

    if artifact_available(run_dir, "review.json", meta):
        review = load_artifact_json(run_dir, "review.json", ReviewReport)
        if review is not None:
            stage = review.next_stage
            if stage == ReviewNextStage.PM:
                return PipelineNode.SPEC_VALIDATE
            if stage == ReviewNextStage.ARCHITECT:
                return PipelineNode.DESIGN_VALIDATE
            if stage == ReviewNextStage.DEVELOPER:
                return PipelineNode.QA

    spec_val = _load_validation(run_dir, "spec_validation.json", meta)
    if spec_val is not None and not spec_val.passed:
        return PipelineNode.SPEC_VALIDATE

    design_val = _load_validation(run_dir, "design_validation.json", meta)
    if design_val is not None and not design_val.passed:
        return PipelineNode.DESIGN_VALIDATE

    if artifact_available(run_dir, "test_report.json", meta):
        from multi_agent_code_factory.schemas.test_report import TestReport

        report = load_artifact_json(run_dir, "test_report.json", TestReport)
        if report is not None and (not report.passed or bool(report.tests_missing)):
            return PipelineNode.QA

    if (
        meta.status == RunStatus.FAILED
        and _impl_retry_at_limit(meta)
        and artifact_available(run_dir, "dev_manifest.json", meta)
    ):
        return PipelineNode.QA

    if artifact_available(run_dir, "design.json", meta) and not artifact_available(
        run_dir, "dev_manifest.json", meta
    ):
        return PipelineNode.DESIGN_VALIDATE

    if artifact_available(run_dir, "spec.json", meta):
        spec_validation = _load_validation(run_dir, "spec_validation.json", meta)
        if (
            spec_validation is not None
            and spec_validation.passed
            and not (run_dir / "design.json").is_file()
        ):
            return PipelineNode.ARCHITECT

    msg = (
        f"cannot infer reentry node for task {meta.task_id!r}; "
        "use --reenter or run --force-new"
    )
    raise ContinueError(msg)


def validate_reentry_preconditions(
    state: PipelineState,
    reentry: PipelineNode,
) -> None:
    """校验水合 state 是否满足再入点前置条件。"""
    if reentry == PipelineNode.SPEC_VALIDATE and state.spec is None:
        msg = "continue at spec_validate requires spec.json"
        raise ContinueError(msg)
    if reentry == PipelineNode.DESIGN_VALIDATE and state.design is None:
        msg = "continue at design_validate requires design.json"
        raise ContinueError(msg)
    if reentry == PipelineNode.QA and (
        state.design is None or state.dev_manifest is None
    ):
        msg = "continue at qa requires design.json and dev_manifest.json"
        raise ContinueError(msg)
    if reentry == PipelineNode.ARCHITECT:
        if state.spec is None:
            msg = "continue at architect requires spec.json"
            raise ContinueError(msg)
        if state.spec_validation is not None and not state.spec_validation.passed:
            msg = "continue at architect requires spec_validation.passed=true"
            raise ContinueError(msg)


def save_checkpoint(*_args: Any, **_kwargs: Any) -> None:
    raise NotImplementedError("crash resume is planned; use continue for now")


def resume_run(*_args: Any, **_kwargs: Any) -> None:
    raise NotImplementedError("crash resume is planned; use continue for now")
