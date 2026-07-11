from __future__ import annotations

from pathlib import Path

import pytest
from multi_agent_code_factory.agents.stub.fixtures import StubScenario
from multi_agent_code_factory.config import FactoryConfig, LoopLimits
from multi_agent_code_factory.graph import continue_pipeline, run_pipeline
from multi_agent_code_factory.profile_config import load_profile
from multi_agent_code_factory.schemas.prd import PrdArtifact
from multi_agent_code_factory.schemas.run_meta import RunMeta, RunStatus
from multi_agent_code_factory.schemas.validation_report import (
    ValidationReport,
    ValidationTarget,
)
from multi_agent_code_factory.tools.run_artifacts import RunArtifactWriter

from tests.conftest import load_snippet_json


@pytest.fixture
def default_profile():
    return load_profile("python")


def test_continue_after_qa_limit_completes(tmp_path: Path, default_profile) -> None:
    run_dir = tmp_path / "continue-qa"
    first = run_pipeline(
        task_id="continue-qa",
        user_request="todo",
        profile=default_profile,
        factory_config=FactoryConfig(
            loop_limits=LoopLimits(max_impl_retries=1, max_design_revisions=2)
        ),
        run_dir=run_dir,
        stub_scenario=StubScenario.QA_ALWAYS_FAIL,
    )
    assert first.status == RunStatus.FAILED
    meta = RunMeta.model_validate_json(
        (run_dir / "run_meta.json").read_text(encoding="utf-8")
    )
    assert meta.impl_retry_count >= 1

    spec_text = (run_dir / "prd.json").read_text(encoding="utf-8")

    second = continue_pipeline(
        task_id="continue-qa",
        run_dir=run_dir,
        stub_scenario=StubScenario.HAPPY,
    )
    assert second.status == RunStatus.COMPLETED
    assert (run_dir / "prd.json").read_text(encoding="utf-8") == spec_text
    final_meta = RunMeta.model_validate_json(
        (run_dir / "run_meta.json").read_text(encoding="utf-8")
    )
    assert final_meta.last_reentry_node == "qa"
    if final_meta.budget is not None:
        assert final_meta.budget.used_llm_calls == 0


def test_prepare_continue_resets_budget(tmp_path: Path, default_profile) -> None:
    run_dir = tmp_path / "budget-reset"
    run_pipeline(
        task_id="budget-reset",
        user_request="todo",
        profile=default_profile,
        factory_config=FactoryConfig(),
        run_dir=run_dir,
        stub=True,
    )
    writer = RunArtifactWriter("budget-reset", base_dir=run_dir)
    writer.update_meta(
        status=RunStatus.FAILED,
        budget={
            "max_llm_calls": None,
            "max_tokens": None,
            "used_llm_calls": 9,
            "used_tokens": 1000,
        },
    )
    updated = writer.prepare_continue(reentry_node="qa", reset_loops=True)
    assert updated.budget is not None
    assert updated.budget.used_llm_calls == 0
    assert updated.budget.used_tokens == 0


def test_run_meta_stores_user_request(tmp_path: Path, default_profile) -> None:
    run_dir = tmp_path / "user-req"
    run_pipeline(
        task_id="user-req",
        user_request="my custom request",
        profile=default_profile,
        factory_config=FactoryConfig(),
        run_dir=run_dir,
        stub=True,
    )
    meta = RunMeta.model_validate_json(
        (run_dir / "run_meta.json").read_text(encoding="utf-8")
    )
    assert meta.user_request == "my custom request"


def _seed_architect_continue_run(
    run_dir: Path,
    *,
    task_id: str,
    profile,
    snippets_dir: Path,
) -> None:
    writer = RunArtifactWriter(task_id, base_dir=run_dir)
    writer.init_run_meta(
        profile,
        LoopLimits(),
        factory_config=FactoryConfig(),
        user_request="todo",
    )
    writer.update_meta(status=RunStatus.FAILED)
    spec = PrdArtifact.model_validate(
        load_snippet_json(snippets_dir, "prd-default.json")
    )
    writer.write_model("prd.json", spec)
    writer.write_model(
        "prd_validation.json",
        ValidationReport(
            version="1",
            target=ValidationTarget.PRD,
            passed=True,
            error_count=0,
            warn_count=0,
            violations=[],
        ),
    )


def test_continue_architect_reentry_passes_design_validate(
    tmp_path: Path,
    default_profile,
    snippets_dir: Path,
) -> None:
    """Regression: checkpoint dict state must survive architect → design_validate."""
    run_dir = tmp_path / "continue-architect"
    task_id = "continue-architect"
    _seed_architect_continue_run(
        run_dir,
        task_id=task_id,
        profile=default_profile,
        snippets_dir=snippets_dir,
    )

    result = continue_pipeline(
        task_id=task_id,
        run_dir=run_dir,
        reenter="architect",
        stub_scenario=StubScenario.HAPPY,
    )

    assert result.status == RunStatus.COMPLETED
    assert result.state.design is not None
    assert result.state.design_validation is not None
    assert result.state.design_validation.passed is True
    assert (run_dir / "design.json").is_file()
    assert (run_dir / "design_validation.json").is_file()
    meta = RunMeta.model_validate_json(
        (run_dir / "run_meta.json").read_text(encoding="utf-8")
    )
    assert meta.last_reentry_node == "architect"
