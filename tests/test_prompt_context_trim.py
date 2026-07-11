"""Prompt context trimming tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.profile_config import load_profile
from multi_agent_code_factory.prompt_context import build_prompt_context
from multi_agent_code_factory.prompt_context_trim import (
    trim_design,
    trim_prd,
    trim_retry_bundle,
    trim_test_report,
)
from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.schemas.dev_manifest import (
    ChangedFile,
    ChangeType,
    DevManifest,
)
from multi_agent_code_factory.schemas.prd import PrdArtifact
from multi_agent_code_factory.schemas.test_report import (
    TestFailure as TestCaseFailure,
)
from multi_agent_code_factory.schemas.test_report import (
    TestReport,
    TestSummary,
)
from multi_agent_code_factory.schemas.validation_report import (
    ValidationReport,
    ValidationTarget,
    Violation,
    ViolationSeverity,
)
from multi_agent_code_factory.state import PipelineState

from tests.conftest import load_snippet_json


@pytest.fixture
def default_profile():
    return load_profile("python")


def test_trim_design_caps_heavy_lists() -> None:
    payload = {
        "version": "1",
        "spec_ref": "demo",
        "revision": 1,
        "test_cases": [{"id": f"TC-{index}"} for index in range(40)],
    }
    trimmed = trim_design(payload)
    assert len(trimmed["test_cases"]) == 30
    assert trimmed["test_cases_truncated_count"] == 10


def test_trim_design_compact_keeps_test_cases() -> None:
    payload = {
        "version": "1",
        "spec_ref": "demo",
        "revision": 1,
        "modules": [{"id": "m1"}],
        "test_cases": [
            {
                "id": "TC-HAP-CALC-001",
                "kind": "happy",
                "title": "compact",
                "description": 'input: "1*2"',
                "expected": "2",
                "covers": ["AC-1", "SEM-IN-1"],
                "semantic_evidence": {
                    "constraint_ref": "SEM-IN-1",
                    "equivalence_class": "multiply-compact",
                    "proves_dimensions": ["operand_count"],
                },
                "notes": "drop me",
            }
        ],
        "traceability": [{"id": "row-1"}],
    }
    trimmed = trim_design(payload, compact=True)
    assert "test_cases" in trimmed
    assert trimmed["test_cases"][0]["description"] == 'input: "1*2"'
    assert trimmed["test_cases"][0]["semantic_evidence"]["constraint_ref"] == "SEM-IN-1"
    assert "notes" not in trimmed["test_cases"][0]
    assert "traceability" not in trimmed


def test_trim_prd_keeps_semantic_constraints() -> None:
    payload = {
        "title": "Demo",
        "semantic_constraints": [{"id": "SEM-IN-1", "kind": "input_shape"}],
        "noise": "drop",
    }
    trimmed = trim_prd(payload)
    assert trimmed["semantic_constraints"][0]["id"] == "SEM-IN-1"
    assert "noise" not in trimmed


def test_trim_test_report_caps_failures_and_output() -> None:
    payload = {
        "version": "1",
        "passed": False,
        "exit_code": 1,
        "summary": {"total": 2, "passed": 0, "failed": 2, "skipped": 0},
        "command": "pytest",
        "duration_sec": 1.0,
        "parser": "junit_xml",
        "failures": [
            {
                "test_id": f"t{index}",
                "message": "x" * 400,
                "output": "y" * 900,
            }
            for index in range(12)
        ],
    }
    trimmed = trim_test_report(payload)
    assert len(trimmed["failures"]) == 10
    assert trimmed["failures_truncated_count"] == 2
    assert len(trimmed["failures"][0]["message"]) <= 300
    assert len(trimmed["failures"][0]["output"]) <= 500


def test_trim_test_report_keeps_tests_missing() -> None:
    payload = {
        "version": "1",
        "passed": False,
        "exit_code": 0,
        "summary": {"total": 1, "passed": 1, "failed": 0, "skipped": 0},
        "command": "pytest",
        "duration_sec": 0.1,
        "parser": "junit_xml",
        "tests_missing": ["src/cli.py"],
    }
    trimmed = trim_test_report(payload)
    assert trimmed["tests_missing"] == ["src/cli.py"]


def test_trim_test_report_keeps_coverage_summary() -> None:
    payload = {
        "version": "1",
        "passed": True,
        "exit_code": 0,
        "summary": {"total": 1, "passed": 1, "failed": 0, "skipped": 0},
        "command": "pytest",
        "duration_sec": 0.1,
        "parser": "junit_xml",
        "coverage": {
            "tool": "pytest-cov",
            "command": "pytest --cov",
            "parser": "pytest_cov_json",
            "line_percent": 84.2,
            "passed": True,
            "violations": [],
        },
    }
    trimmed = trim_test_report(payload)
    assert trimmed["coverage"]["line_percent"] == 84.2


def test_trim_retry_bundle_truncates_code_snippets() -> None:
    payload = {
        "prd": PrdArtifact.model_validate(
            {
                "version": "1",
                "profile": "python",
                "revision": 1,
                "title": "Demo",
                "summary": "demo",
                "success_metrics": [],
                "features": [],
                "scope_in": ["a"],
                "operational_profile": {
                    "user_scale": "personal",
                    "high_concurrency": False,
                    "performance": {"tier": "best_effort"},
                },
                "consistency_profile": {
                    "consistency_model": "local_only",
                    "delivery": "best_effort",
                    "multi_writer": False,
                    "idempotency_required": False,
                },
                "acceptance_criteria": [],
            }
        ).model_dump(mode="json"),
        "design": DesignArtifact.model_validate(
            {
                "version": "1",
                "spec_ref": "Demo",
                "revision": 1,
            }
        ).model_dump(mode="json"),
        "test_report": {
            "version": "1",
            "passed": False,
            "exit_code": 1,
            "summary": {"total": 1, "passed": 0, "failed": 1, "skipped": 0},
            "failures": [],
            "duration_sec": 0.1,
            "command": "pytest",
            "parser": "junit_xml",
        },
        "dev_manifest": DevManifest(version="1").model_dump(mode="json"),
        "code_snippets": [
            {
                "path": f"src/f{index}.py",
                "content": "\n".join(f"line {line}" for line in range(200)),
            }
            for index in range(5)
        ],
    }
    trimmed = trim_retry_bundle(payload)
    assert len(trimmed["code_snippets"]) == 3
    assert trimmed["code_snippets_truncated_count"] == 2
    assert trimmed["code_snippets"][0]["content"].endswith("... (已截断)")


def test_build_prompt_context_is_trimmed(
    default_profile,
    snippets_dir: Path,
) -> None:
    spec = PrdArtifact.model_validate(
        load_snippet_json(snippets_dir, "prd-default.json")
    )
    design = DesignArtifact.model_validate(
        load_snippet_json(Path(__file__).parent / "fixtures", "design-todo-valid.json")
    )
    report = TestReport(
        version="1",
        passed=False,
        exit_code=1,
        summary=TestSummary(total=1, passed=0, failed=1, skipped=0),
        failures=[
            TestCaseFailure(
                test_id="t1",
                message="m" * 400,
                output="o" * 900,
            )
        ],
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
        prd=spec,
        design=design,
        test_report=report,
        dev_manifest=manifest,
        impl_retry_count=1,
    )
    ctx = build_prompt_context(AgentRole.DEVELOPER, state, default_profile)
    assert "retry_bundle" in ctx
    assert len(ctx["retry_bundle"]["test_report"]["failures"][0]["message"]) <= 300
    assert "test_cases" in ctx["design"]


def test_build_prompt_context_injects_semantic_advisories(default_profile) -> None:
    state = PipelineState(
        task_id="t",
        user_request="calc",
        prd_validation=ValidationReport(
            version="1",
            target=ValidationTarget.PRD,
            passed=True,
            error_count=0,
            warn_count=1,
            violations=[
                Violation(
                    rule_id="PRD-S01",
                    severity=ViolationSeverity.WARN,
                    message="missing semantic_constraints",
                )
            ],
        ),
        design_validation=ValidationReport(
            version="1",
            target=ValidationTarget.DESIGN,
            passed=True,
            error_count=0,
            warn_count=1,
            violations=[
                Violation(
                    rule_id="DES-S02",
                    severity=ViolationSeverity.WARN,
                    message="error message too literal",
                )
            ],
        ),
    )
    dev_ctx = build_prompt_context(AgentRole.DEVELOPER, state, default_profile)
    assert "semantic_advisories_prd" in dev_ctx
    assert "PRD-S01" in dev_ctx["semantic_advisories_prd"]
    assert "semantic_advisories_design" in dev_ctx
    assert "DES-S02" in dev_ctx["semantic_advisories_design"]

    arch_ctx = build_prompt_context(AgentRole.ARCHITECT, state, default_profile)
    assert "semantic_advisories_prd" in arch_ctx
    assert "semantic_advisories_design" not in arch_ctx
