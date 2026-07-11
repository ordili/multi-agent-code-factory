from __future__ import annotations

from pathlib import Path

import pytest
from multi_agent_code_factory.checkpoint import ContinueError, infer_reentry_node
from multi_agent_code_factory.config import LoopLimits
from multi_agent_code_factory.pipeline_nodes import PipelineNode
from multi_agent_code_factory.schemas.review import ReviewNextStage, ReviewReport
from multi_agent_code_factory.schemas.run_meta import RunMeta, RunStatus
from multi_agent_code_factory.schemas.test_report import TestReport, TestSummary
from multi_agent_code_factory.schemas.validation_report import (
    ValidationReport,
    ValidationTarget,
)
from multi_agent_code_factory.state import (
    PipelineState,
    normalize_pipeline_state,
    state_to_graph_dict,
)

from tests.conftest import load_snippet_json


def _meta(**overrides: object) -> RunMeta:
    base = {
        "version": "1",
        "task_id": "t1",
        "profile": {"id": "python", "code_root": "/tmp/out"},
        "loop_limits": LoopLimits(max_impl_retries=3).model_dump(mode="json"),
        "status": RunStatus.FAILED,
        "impl_retry_count": 3,
    }
    base.update(overrides)
    return RunMeta.model_validate(base)


def test_infer_qa_when_impl_retry_at_limit_and_dev_manifest(
    tmp_path: Path,
    snippets_dir: Path,
) -> None:
    run_dir = tmp_path
    spec = load_snippet_json(snippets_dir, "prd-default.json")
    (run_dir / "prd.json").write_text(__import__("json").dumps(spec), encoding="utf-8")
    (run_dir / "design.json").write_text("{}", encoding="utf-8")
    (run_dir / "dev_manifest.json").write_text(
        '{"version":"1","changed_files":[]}', encoding="utf-8"
    )
    meta = _meta(
        stale_artifacts=["test_report.json"],
        design_revision_count=0,
    )
    node = infer_reentry_node(run_dir, meta)
    assert node == PipelineNode.QA


def test_infer_design_validate_when_validation_failed(tmp_path: Path) -> None:
    run_dir = tmp_path
    (run_dir / "design.json").write_text("{}", encoding="utf-8")
    report = ValidationReport(
        version="1",
        target=ValidationTarget.DESIGN,
        passed=False,
        error_count=1,
        warn_count=0,
        violations=[],
    )
    (run_dir / "design_validation.json").write_text(
        report.model_dump_json(), encoding="utf-8"
    )
    meta = _meta(status=RunStatus.FAILED, impl_retry_count=0)
    assert infer_reentry_node(run_dir, meta) == PipelineNode.DESIGN_VALIDATE


def test_infer_completed_raises(tmp_path: Path) -> None:
    meta = _meta(status=RunStatus.COMPLETED)
    with pytest.raises(ContinueError, match="already completed"):
        infer_reentry_node(tmp_path, meta)


def test_infer_review_escalation_developer(tmp_path: Path) -> None:
    review = ReviewReport(
        version="1",
        approved=False,
        next_stage=ReviewNextStage.DEVELOPER,
        summary="needs fixes",
        findings=[],
        acceptance_coverage=[],
    )
    (tmp_path / "review.json").write_text(review.model_dump_json(), encoding="utf-8")
    meta = _meta(status=RunStatus.FAILED)
    assert infer_reentry_node(tmp_path, meta) == PipelineNode.QA


def test_state_graph_dict_round_trip(snippets_dir: Path) -> None:
    spec = load_snippet_json(snippets_dir, "prd-default.json")
    state = PipelineState(
        task_id="t",
        user_request="build",
        impl_retry_count=2,
        prd=spec,
    )
    restored = normalize_pipeline_state(state_to_graph_dict(state))
    assert restored.task_id == "t"
    assert restored.user_request == "build"
    assert restored.impl_retry_count == 2
    from multi_agent_code_factory.schemas.prd import PrdArtifact

    assert isinstance(restored.prd, PrdArtifact)
    assert restored.prd.title == "CLI Todo App"


def test_normalize_pipeline_state_restores_prd_for_design_validate(
    snippets_dir: Path,
) -> None:
    from multi_agent_code_factory.profile_config import load_profile
    from multi_agent_code_factory.schemas.design import DesignArtifact
    from multi_agent_code_factory.schemas.prd import PrdArtifact
    from multi_agent_code_factory.validators.design_rules import validate_design_rules

    spec_dict = load_snippet_json(snippets_dir, "prd-default.json")
    design = DesignArtifact.model_validate(
        load_snippet_json(snippets_dir, "design-todo-excerpt.json")
    )
    raw_state = state_to_graph_dict(
        PipelineState(task_id="t", user_request="build", prd=spec_dict)
    )
    state = normalize_pipeline_state(raw_state)
    profile = load_profile("python")

    violations, _ = validate_design_rules(design, profile, state.prd)

    assert isinstance(state.prd, PrdArtifact)
    assert isinstance(violations, list)


def test_infer_test_report_failed(tmp_path: Path) -> None:
    report = TestReport(
        version="1",
        passed=False,
        exit_code=1,
        summary=TestSummary(total=1, passed=0, failed=1, skipped=0),
        failures=[],
        duration_sec=0.1,
        command="pytest",
        parser="junit_xml",
    )
    (tmp_path / "test_report.json").write_text(
        report.model_dump_json(), encoding="utf-8"
    )
    meta = _meta(status=RunStatus.FAILED, impl_retry_count=1)
    assert infer_reentry_node(tmp_path, meta) == PipelineNode.QA


def test_infer_does_not_reenter_qa_when_passed_with_tests_missing(
    tmp_path: Path,
) -> None:
    report = TestReport(
        version="1",
        passed=True,
        exit_code=0,
        summary=TestSummary(total=1, passed=1, failed=0, skipped=0),
        failures=[],
        duration_sec=0.1,
        command="cargo test",
        parser="cargo_json",
        tests_missing=["src/calc.rs"],
    )
    (tmp_path / "test_report.json").write_text(
        report.model_dump_json(), encoding="utf-8"
    )
    (tmp_path / "dev_manifest.json").write_text(
        '{"version":"1","changed_files":[]}', encoding="utf-8"
    )
    (tmp_path / "design.json").write_text("{}", encoding="utf-8")
    meta = _meta(status=RunStatus.FAILED, impl_retry_count=0)
    with pytest.raises(ContinueError, match="cannot infer reentry"):
        infer_reentry_node(tmp_path, meta)
