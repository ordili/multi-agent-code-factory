from __future__ import annotations

from pathlib import Path

import pytest
from multi_agent_code_factory.agents.stub.fixtures import StubScenario
from multi_agent_code_factory.config import FactoryConfig, LoopLimits
from multi_agent_code_factory.graph import run_pipeline
from multi_agent_code_factory.profile_config import load_profile
from multi_agent_code_factory.schemas.run_meta import RunMeta, RunStatus


@pytest.fixture
def default_profile():
    return load_profile("python")


def _read_meta(run_dir: Path) -> RunMeta:
    return RunMeta.model_validate_json(
        (run_dir / "run_meta.json").read_text(encoding="utf-8")
    )


def test_qa_fail_then_pass_completes(tmp_path: Path, default_profile) -> None:
    result = run_pipeline(
        task_id="loop-qa-retry",
        user_request="todo",
        profile=default_profile,
        factory_config=FactoryConfig(),
        run_dir=tmp_path / "loop-qa-retry",
        stub_scenario=StubScenario.QA_FAIL_THEN_PASS,
    )
    assert result.status == RunStatus.COMPLETED
    assert result.state.impl_retry_count == 1
    meta = _read_meta(result.run_dir)
    assert meta.impl_retry_count == 1


def test_qa_always_fail_hits_limit(tmp_path: Path, default_profile) -> None:
    result = run_pipeline(
        task_id="loop-qa-fail",
        user_request="todo",
        profile=default_profile,
        factory_config=FactoryConfig(
            loop_limits=LoopLimits(max_impl_retries=1, max_design_revisions=2)
        ),
        run_dir=tmp_path / "loop-qa-fail",
        stub_scenario=StubScenario.QA_ALWAYS_FAIL,
    )
    assert result.status == RunStatus.FAILED
    assert result.state.impl_retry_count == 1


def test_reviewer_escalate_architect_completes(tmp_path: Path, default_profile) -> None:
    result = run_pipeline(
        task_id="loop-review-architect",
        user_request="todo",
        profile=default_profile,
        factory_config=FactoryConfig(),
        run_dir=tmp_path / "loop-review-architect",
        stub_scenario=StubScenario.REVIEWER_ESCALATE_ARCHITECT,
    )
    assert result.status == RunStatus.COMPLETED
    assert result.state.design_revision_count == 1
    meta = _read_meta(result.run_dir)
    assert "test_report.json" in (meta.stale_artifacts or [])
    assert "review.json" in (meta.stale_artifacts or [])


def test_reviewer_escalate_pm_completes(tmp_path: Path, default_profile) -> None:
    result = run_pipeline(
        task_id="loop-review-pm",
        user_request="todo",
        profile=default_profile,
        factory_config=FactoryConfig(),
        run_dir=tmp_path / "loop-review-pm",
        stub_scenario=StubScenario.REVIEWER_ESCALATE_PM,
    )
    assert result.status == RunStatus.COMPLETED
    assert result.state.spec_revision_count == 1
    meta = _read_meta(result.run_dir)
    assert "design.json" in (meta.stale_artifacts or [])


def test_spec_validate_retry_completes(tmp_path: Path, default_profile) -> None:
    result = run_pipeline(
        task_id="loop-spec-validate",
        user_request="todo",
        profile=default_profile,
        factory_config=FactoryConfig(),
        run_dir=tmp_path / "loop-spec-validate",
        stub_scenario=StubScenario.SPEC_VALIDATE_RETRY,
    )
    assert result.status == RunStatus.COMPLETED
    assert result.state.spec_revision_count == 1


def test_design_validate_retry_completes(tmp_path: Path, default_profile) -> None:
    result = run_pipeline(
        task_id="loop-design-validate",
        user_request="todo",
        profile=default_profile,
        factory_config=FactoryConfig(),
        run_dir=tmp_path / "loop-design-validate",
        stub_scenario=StubScenario.DESIGN_VALIDATE_RETRY,
    )
    assert result.status == RunStatus.COMPLETED
    assert result.state.design_revision_count == 1
