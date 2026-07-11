from __future__ import annotations

from pathlib import Path

import pytest
from multi_agent_code_factory.agents.llm.schemas import ArchitectLLMOutput
from multi_agent_code_factory.schemas import (
    DesignArtifact,
    DevManifest,
    HitlDecision,
    PrdArtifact,
    ReviewReport,
    RunMeta,
    ValidationReport,
)
from multi_agent_code_factory.schemas.dev_manifest import ChangeType
from multi_agent_code_factory.schemas.hitl import HitlStage
from multi_agent_code_factory.schemas.review import ReviewNextStage
from multi_agent_code_factory.schemas.run_meta import DeployStatus
from multi_agent_code_factory.schemas.test_report import (
    TestReport as TestReportArtifact,
)
from multi_agent_code_factory.schemas.validation_report import (
    ValidationTarget,
)
from pydantic import ValidationError

from tests.conftest import load_snippet_json


def test_prd_default_fixture(snippets_dir: Path) -> None:
    data = load_snippet_json(snippets_dir, "prd-default.json")
    spec = PrdArtifact.model_validate(data)
    assert spec.profile == "python"
    assert spec.context["language"] == "python"


def test_prd_rejects_missing_title(snippets_dir: Path) -> None:
    data = load_snippet_json(snippets_dir, "prd-default.json")
    data.pop("title")
    with pytest.raises(ValidationError):
        PrdArtifact.model_validate(data)


def test_prd_coerces_llm_simplified_shapes() -> None:
    """LLM often returns strings/dicts that differ from the strict schema."""
    spec = PrdArtifact.model_validate(
        {
            "version": "1",
            "title": "Calculator CLI",
            "summary": "Divide two numbers safely",
            "success_metrics": [
                {
                    "id": "KPI-1",
                    "name": "Tests pass",
                    "description": "pytest green",
                    "target": "all pass",
                    "verifiable_by": "automated_test",
                }
            ],
            "features": [
                {
                    "id": "FEAT-1",
                    "name": "Division",
                    "description": "Safe divide",
                    "priority": "P0",
                }
            ],
            "user_stories": [
                "As a user, I want to divide two numbers safely "
                "if the divisor is zero.",
            ],
            "requirement_pool": {
                "functional": ["Support division", "Reject zero divisor"],
                "non_functional": ["No hardcoded secrets"],
            },
            "scope_in": ["CLI divide command"],
            "operational_profile": {
                "user_scale": "personal",
                "deployment": "local_dev_and_run",
            },
            "consistency_profile": "local_only",
            "acceptance_criteria": [
                {
                    "id": "AC-1",
                    "description": "pytest passes",
                    "verifiable_by": "automated_test",
                }
            ],
        }
    )
    assert spec.profile == "unknown"
    assert spec.revision == 1
    assert spec.user_stories[0].want.startswith("to divide")
    assert len(spec.requirement_pool) == 3
    assert spec.operational_profile.high_concurrency is False
    assert spec.operational_profile.performance.tier.value == "best_effort"
    assert spec.consistency_profile.consistency_model.value == "local_only"


def test_design_todo_excerpt_fixture(snippets_dir: Path) -> None:
    data = load_snippet_json(snippets_dir, "design-todo-excerpt.json")
    design = DesignArtifact.model_validate(data)
    assert design.spec_ref == "CLI Todo App"
    assert len(design.modules) == 2


def test_design_rejects_bad_version(snippets_dir: Path) -> None:
    data = load_snippet_json(snippets_dir, "design-todo-excerpt.json")
    data["version"] = "2"
    with pytest.raises(ValidationError):
        DesignArtifact.model_validate(data)


def test_design_coerces_traceability_dict_to_list() -> None:
    design = DesignArtifact.model_validate(
        {
            "spec_ref": "Hello module",
            "traceability": {
                "spec_ref_id": "FEAT-1",
                "spec_ref_kind": "FEAT",
            },
        }
    )
    assert len(design.traceability) == 1
    assert design.traceability[0].spec_ref_id == "FEAT-1"


def test_design_coerces_error_catalog_error_code_alias() -> None:
    design = DesignArtifact.model_validate(
        {
            "spec_ref": "Hello module",
            "error_catalog": [
                {
                    "error_code": "ERR-HELLO-001",
                    "when": "import fails",
                    "message": "Module not found",
                }
            ],
        }
    )
    assert design.error_catalog[0].code == "ERR-HELLO-001"


def test_design_coerces_diagram_mermaid_kind_aliases() -> None:
    design = DesignArtifact.model_validate(
        {
            "spec_ref": "Hello module",
            "diagrams": [
                {"path": "flow.mmd", "kind": "sequenceDiagram"},
                {"path": "architecture.mmd", "kind": "flowchart LR"},
            ],
        }
    )
    assert design.diagrams[0].kind == "sequence"
    assert design.diagrams[1].kind == "flowchart"


def test_design_coerces_top_level_field_aliases() -> None:
    design = DesignArtifact.model_validate(
        {
            "spec_ref": "Todo",
            "decisions": [{"option": "JSON", "decision": "accepted"}],
            "code_delta": {"summary": "greenfield"},
            "test_strategy": {"approach": "pytest", "paths": ["tests/"]},
            "cross_cutting": {"configuration": "./data"},
        }
    )
    assert design.architecture is not None
    assert design.architecture.decisions[0].option == "JSON"
    assert design.architecture.code_delta is not None
    assert design.architecture.code_delta.summary == "greenfield"
    assert design.cross_cutting is not None
    assert design.cross_cutting["test_strategy"]["approach"] == "pytest"
    assert design.cross_cutting["configuration"] == "./data"


def test_architect_llm_output_accepts_coerced_design_traceability() -> None:
    output = ArchitectLLMOutput.model_validate(
        {
            "design": {
                "spec_ref": "Hello module",
                "traceability": {
                    "spec_ref_id": "FEAT-1",
                    "spec_ref_kind": "FEAT",
                },
            }
        }
    )
    assert output.design.traceability[0].spec_ref_kind == "FEAT"


def test_test_report_example() -> None:
    report = TestReportArtifact.model_validate(
        {
            "version": "1",
            "passed": False,
            "exit_code": 1,
            "summary": {"total": 12, "passed": 11, "failed": 1, "skipped": 0},
            "failures": [
                {
                    "test_id": "tests.test_todo.TestAdd::test_add",
                    "file": "tests/test_todo.py",
                    "line": 14,
                    "message": "AssertionError: expected 2 items",
                }
            ],
            "duration_sec": 1.23,
            "command": "pytest -q --junitxml=reports/junit.xml",
            "parser": "junit_xml",
            "language": "python",
        }
    )
    assert report.failures[0].line == 14


def test_test_report_rejects_negative_duration() -> None:
    with pytest.raises(ValidationError):
        TestReportArtifact.model_validate(
            {
                "version": "1",
                "passed": True,
                "exit_code": 0,
                "summary": {"total": 0, "passed": 0, "failed": 0, "skipped": 0},
                "duration_sec": -1,
                "command": "true",
                "parser": "exit_code_only",
            }
        )


def test_validation_report_example() -> None:
    report = ValidationReport.model_validate(
        {
            "version": "1",
            "target": "design",
            "passed": False,
            "error_count": 1,
            "warn_count": 0,
            "violations": [
                {
                    "rule_id": "DES-005",
                    "severity": "error",
                    "message": "dev_tasks dependency cycle",
                    "path": "/dev_tasks",
                }
            ],
        }
    )
    assert report.target == ValidationTarget.DESIGN


def test_review_report_example() -> None:
    review = ReviewReport.model_validate(
        {
            "version": "1",
            "approved": True,
            "next_stage": "deploy",
            "summary": "AC met",
            "acceptance_coverage": [{"id": "AC-1", "met": True}],
        }
    )
    assert review.next_stage == ReviewNextStage.DEPLOY


def test_dev_manifest_example() -> None:
    manifest = DevManifest.model_validate(
        {
            "version": "1",
            "tasks_completed": ["T1"],
            "changed_files": [{"path": "src/todo_store.py", "change_type": "create"}],
            "reflection": {
                "attempt": 2,
                "hypothesis": "flush missing",
                "next_action": "fsync after save",
            },
        }
    )
    assert manifest.changed_files[0].change_type == ChangeType.CREATE


def test_hitl_decision_example() -> None:
    hitl = HitlDecision.model_validate(
        {
            "version": "1",
            "stage": "design",
            "required": True,
            "reason": ["validation.design.require_hitl"],
            "approved": True,
        }
    )
    assert hitl.stage == HitlStage.DESIGN


def test_run_meta_example() -> None:
    meta = RunMeta.model_validate(
        {
            "version": "1",
            "task_id": "todo-cli",
            "profile": {"id": "python", "language": "python"},
            "loop_limits": {
                "max_impl_retries": 3,
                "max_design_revisions": 2,
                "max_prd_revisions": 1,
            },
            "deploy_status": "skipped",
        }
    )
    assert meta.deploy_status == DeployStatus.SKIPPED


def test_run_meta_rejects_invalid_deploy_status() -> None:
    with pytest.raises(ValidationError):
        RunMeta.model_validate(
            {
                "version": "1",
                "task_id": "x",
                "profile": {},
                "loop_limits": {},
                "deploy_status": "unknown",
            }
        )
