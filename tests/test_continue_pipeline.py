from __future__ import annotations

from pathlib import Path

import pytest
from multi_agent_code_factory.agents.stub.fixtures import StubScenario
from multi_agent_code_factory.config import FactoryConfig, LoopLimits
from multi_agent_code_factory.graph import continue_pipeline, run_pipeline
from multi_agent_code_factory.profile_config import load_profile
from multi_agent_code_factory.schemas.run_meta import RunMeta, RunStatus
from multi_agent_code_factory.tools.run_artifacts import RunArtifactWriter


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
