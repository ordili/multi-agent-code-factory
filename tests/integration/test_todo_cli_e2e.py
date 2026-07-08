"""Live LLM end-to-end test for python Todo CLI profile."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from multi_agent_code_factory.config import FactoryConfig, LoopLimits
from multi_agent_code_factory.graph import run_pipeline
from multi_agent_code_factory.llm import (
    llm_available,
    provider_spec,
    resolve_factory_llm_provider,
)
from multi_agent_code_factory.profile_config import load_profile
from multi_agent_code_factory.schemas.run_meta import RunMeta, RunStatus
from multi_agent_code_factory.schemas.test_report import TestReport

pytestmark = pytest.mark.integration


@pytest.fixture
def live_profile(tmp_path: Path):
    code_root = tmp_path / "generated" / "python"
    code_root.mkdir(parents=True)
    return load_profile("python", code_root_override=code_root)


def _skip_unless_live_llm_ready() -> None:
    provider_id = resolve_factory_llm_provider()
    if provider_id == "ollama":
        if os.environ.get("RUN_OLLAMA_E2E") != "1":
            pytest.skip("Ollama e2e disabled; set RUN_OLLAMA_E2E=1 to enable")
        pytest.importorskip("langchain_ollama")
        return
    if not llm_available():
        pytest.skip("LLM API key not set for current FACTORY_LLM_PROVIDER")
    langchain_provider = provider_spec(provider_id).langchain_provider
    if langchain_provider == "openai":
        pytest.importorskip("langchain_openai")
    elif langchain_provider == "anthropic":
        pytest.importorskip("langchain_anthropic")


def test_todo_cli_live_e2e(tmp_path: Path, live_profile) -> None:
    _skip_unless_live_llm_ready()

    run_dir = tmp_path / "runs" / "todo-e2e"
    result = run_pipeline(
        task_id="todo-e2e",
        user_request=(
            "实现命令行 Todo: add/list/done 子命令, JSON 文件持久化, 带 pytest"
        ),
        profile=live_profile,
        factory_config=FactoryConfig(
            loop_limits=LoopLimits(
                max_impl_retries=2,
                max_design_revisions=2,
                max_spec_revisions=1,
            )
        ),
        run_dir=run_dir,
        stub=False,
    )

    assert result.status == RunStatus.COMPLETED, (
        f"pipeline failed; see {run_dir / 'run_meta.json'}"
    )
    assert (run_dir / "spec.json").is_file()
    assert (run_dir / "design.json").is_file()
    assert (run_dir / "dev_manifest.json").is_file()
    assert (run_dir / "test_report.json").is_file()
    assert (run_dir / "review.json").is_file()

    report = TestReport.model_validate_json(
        (run_dir / "test_report.json").read_text(encoding="utf-8")
    )
    assert report.passed is True
    if report.failures:
        for failure in report.failures:
            assert failure.test_id
            assert failure.file

    meta = RunMeta.model_validate_json(
        (run_dir / "run_meta.json").read_text(encoding="utf-8")
    )
    assert meta.profile.get("id") == "python"
    assert meta.loop_limits.get("max_impl_retries") == 2
    assert meta.budget is None or (meta.budget.used_llm_calls or 0) > 0

    assert live_profile.code_root.is_dir()
    assert any(live_profile.code_root.rglob("*.py"))
