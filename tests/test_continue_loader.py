from __future__ import annotations

from pathlib import Path

from multi_agent_code_factory.artifact_loader import (
    artifact_available,
    hydrate_state,
    is_stale,
)
from multi_agent_code_factory.schemas.prd import PrdArtifact
from multi_agent_code_factory.schemas.run_meta import RunMeta, RunStatus
from multi_agent_code_factory.schemas.test_report import TestReport, TestSummary

from tests.conftest import load_snippet_json


def _write_meta(run_dir: Path, **overrides: object) -> RunMeta:
    meta = RunMeta.model_validate(
        {
            "version": "1",
            "task_id": "hydrate-test",
            "user_request": "build a calc",
            "profile": {"id": "python"},
            "loop_limits": {"max_impl_retries": 3},
            "status": RunStatus.FAILED,
            **overrides,
        }
    )
    (run_dir / "run_meta.json").write_text(
        meta.model_dump_json(indent=2), encoding="utf-8"
    )
    return meta


def test_is_stale() -> None:
    meta = RunMeta.model_validate(
        {
            "version": "1",
            "task_id": "x",
            "profile": {},
            "loop_limits": {},
            "stale_artifacts": ["test_report.json"],
        }
    )
    assert is_stale("test_report.json", meta)
    assert not is_stale("prd.json", meta)


def test_hydrate_skips_stale_test_report(
    tmp_path: Path,
    snippets_dir: Path,
) -> None:
    run_dir = tmp_path
    spec = PrdArtifact.model_validate(
        load_snippet_json(snippets_dir, "prd-default.json")
    )
    (run_dir / "prd.json").write_text(spec.model_dump_json(indent=2), encoding="utf-8")
    report = TestReport(
        version="1",
        passed=False,
        exit_code=1,
        summary=TestSummary(total=1, passed=0, failed=1, skipped=0),
        failures=[],
        duration_sec=0.0,
        command="pytest",
        parser="junit_xml",
    )
    (run_dir / "test_report.json").write_text(
        report.model_dump_json(), encoding="utf-8"
    )
    meta = _write_meta(run_dir, stale_artifacts=["test_report.json"])
    state = hydrate_state(run_dir, meta)
    assert state.prd is not None
    assert state.test_report is None
    assert state.user_request == "build a calc"
    assert not artifact_available(run_dir, "test_report.json", meta)


def test_hydrate_user_request_fallback_from_spec(
    tmp_path: Path,
    snippets_dir: Path,
) -> None:
    run_dir = tmp_path
    spec = PrdArtifact.model_validate(
        load_snippet_json(snippets_dir, "prd-default.json")
    )
    (run_dir / "prd.json").write_text(spec.model_dump_json(indent=2), encoding="utf-8")
    meta = _write_meta(run_dir, user_request=None)
    state = hydrate_state(run_dir, meta)
    assert "Todo" in state.user_request or state.user_request
