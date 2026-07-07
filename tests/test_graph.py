from __future__ import annotations

from pathlib import Path

import pytest
from multi_agent_code_factory.config import FactoryConfig
from multi_agent_code_factory.context import (
    DEFAULT_WATCH,
    build_node_context,
    build_retry_bundle,
    resolve_watch,
)
from multi_agent_code_factory.graph import run_pipeline
from multi_agent_code_factory.profiles import load_profile
from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.schemas.dev_manifest import (
    ChangedFile,
    ChangeType,
    DevManifest,
)
from multi_agent_code_factory.schemas.review import ReviewNextStage, ReviewReport
from multi_agent_code_factory.schemas.run_meta import RunStatus
from multi_agent_code_factory.schemas.spec import SpecArtifact
from multi_agent_code_factory.schemas.test_report import TestReport, TestSummary
from multi_agent_code_factory.state import PipelineState

from tests.conftest import load_snippet_json


@pytest.fixture
def default_profile():
    return load_profile("default")


def test_resolve_watch_uses_defaults(default_profile) -> None:
    assert "spec" in resolve_watch("architect", default_profile)
    assert resolve_watch("architect", default_profile) == DEFAULT_WATCH["architect"]


def test_build_retry_bundle_when_retrying(default_profile, snippets_dir: Path) -> None:
    spec = SpecArtifact.model_validate(
        load_snippet_json(snippets_dir, "spec-default.json")
    )
    design = DesignArtifact.model_validate(
        load_snippet_json(Path(__file__).parent / "fixtures", "design-todo-valid.json")
    )
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
    manifest = DevManifest(
        version="1",
        changed_files=[ChangedFile(path="src/cli.py", change_type=ChangeType.MODIFY)],
    )
    state = PipelineState(
        task_id="t",
        user_request="todo",
        profile=default_profile,
        spec=spec,
        design=design,
        test_report=report,
        dev_manifest=manifest,
        impl_retry_count=1,
    )
    bundle = build_retry_bundle(state)
    assert bundle is not None
    assert bundle.spec.title == spec.title
    ctx = build_node_context("developer", state, default_profile)
    assert "retry_bundle" in ctx


def test_stub_pipeline_happy_path(tmp_path: Path, default_profile) -> None:
    result = run_pipeline(
        task_id="todo-cli-test",
        user_request="实现命令行 Todo",
        profile=default_profile,
        factory_config=FactoryConfig(),
        run_dir=tmp_path / "runs" / "todo-cli-test",
        stub=True,
    )
    assert result.status == RunStatus.COMPLETED
    run_dir = result.run_dir
    assert (run_dir / "spec.json").is_file()
    assert (run_dir / "spec.md").is_file()
    assert (run_dir / "design.json").is_file()
    assert (run_dir / "flow.mmd").is_file()
    assert (run_dir / "dev_manifest.json").is_file()
    assert (run_dir / "test_report.json").is_file()
    assert (run_dir / "review.json").is_file()
    assert (run_dir / "spec_validation.json").is_file()
    assert (run_dir / "design_validation.json").is_file()
    assert (run_dir / "run_meta.json").is_file()

    review = ReviewReport.model_validate_json(
        (run_dir / "review.json").read_text(encoding="utf-8")
    )
    assert review.next_stage == ReviewNextStage.DEPLOY
