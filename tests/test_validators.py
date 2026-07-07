from __future__ import annotations

from pathlib import Path

import pytest
from multi_agent_code_factory.config import LoopLimits
from multi_agent_code_factory.graph_routing import route_after_spec_validate
from multi_agent_code_factory.nodes.design_validate import run_design_validate
from multi_agent_code_factory.nodes.spec_validate import run_spec_validate
from multi_agent_code_factory.profiles import load_profile
from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.schemas.spec import SpecArtifact
from multi_agent_code_factory.state import PipelineState

from tests.conftest import load_snippet_json


@pytest.fixture
def default_profile():
    return load_profile("python")


@pytest.fixture
def limits() -> LoopLimits:
    return LoopLimits()


def test_spec_default_passes_validate(default_profile, snippets_dir: Path) -> None:
    spec = SpecArtifact.model_validate(
        load_snippet_json(snippets_dir, "spec-default.json")
    )
    report = run_spec_validate(spec, default_profile)
    assert report.passed is True
    assert report.error_count == 0


def test_spec_missing_acceptance_criteria_fails(
    default_profile, snippets_dir: Path
) -> None:
    data = load_snippet_json(snippets_dir, "spec-default.json")
    data["acceptance_criteria"] = []
    spec = SpecArtifact.model_validate(data)
    report = run_spec_validate(spec, default_profile)
    assert report.passed is False
    assert any(v.rule_id == "SPEC-001" for v in report.violations)


def test_spec_wrong_profile_fails(default_profile, snippets_dir: Path) -> None:
    data = load_snippet_json(snippets_dir, "spec-default.json")
    data["profile"] = "other"
    spec = SpecArtifact.model_validate(data)
    report = run_spec_validate(spec, default_profile)
    assert any(v.rule_id == "SPEC-005" for v in report.violations)


def test_spec_validate_failure_routes_to_pm(
    default_profile, limits, snippets_dir: Path
) -> None:
    data = load_snippet_json(snippets_dir, "spec-default.json")
    data["acceptance_criteria"] = []
    spec = SpecArtifact.model_validate(data)
    report = run_spec_validate(spec, default_profile)
    state = PipelineState(spec_validation=report)
    assert route_after_spec_validate(state, default_profile, limits) == "pm"


def test_design_todo_valid_passes(default_profile, snippets_dir: Path) -> None:
    spec = SpecArtifact.model_validate(
        load_snippet_json(snippets_dir, "spec-default.json")
    )
    design = DesignArtifact.model_validate(
        load_snippet_json(Path(__file__).parent / "fixtures", "design-todo-valid.json")
    )
    report = run_design_validate(design, default_profile, spec=spec)
    assert report.passed is True


def test_design_excerpt_fails_mvp_rules(default_profile, snippets_dir: Path) -> None:
    design = DesignArtifact.model_validate(
        load_snippet_json(snippets_dir, "design-todo-excerpt.json")
    )
    report = run_design_validate(design, default_profile)
    assert report.passed is False
    rule_ids = {v.rule_id for v in report.violations}
    assert "DES-008" in rule_ids


def test_design_dev_task_cycle_detected(default_profile) -> None:
    design = DesignArtifact.model_validate(
        {
            "version": "1",
            "spec_ref": "x",
            "revision": 1,
            "non_goals": ["n"],
            "context_view": {"a": 1},
            "architecture": {"solution_strategy": "s"},
            "cross_cutting": {},
            "modules": [
                {
                    "name": "M",
                    "path": "src/m.py",
                    "responsibility": "r",
                    "code_domain": "M",
                }
            ],
            "traceability": [{"spec_ref_id": "F", "spec_ref_kind": "FEAT"}],
            "dev_tasks": [
                {
                    "id": "T1",
                    "path": "a.py",
                    "description": "a",
                    "depends_on": ["T2"],
                },
                {
                    "id": "T2",
                    "path": "b.py",
                    "description": "b",
                    "depends_on": ["T1"],
                },
            ],
        }
    )
    report = run_design_validate(design, default_profile)
    assert any(v.rule_id == "DES-005" for v in report.violations)


def test_design_hitl_flags_set_require_hitl(default_profile) -> None:
    profile = default_profile.model_copy(
        update={
            "hitl": default_profile.hitl.model_copy(
                update={"flags": ["touches_production"]}
            )
        }
    )
    design = DesignArtifact.model_validate(
        {
            "version": "1",
            "spec_ref": "x",
            "revision": 1,
            "non_goals": ["n"],
            "context_view": {"a": 1},
            "architecture": {"solution_strategy": "s"},
            "cross_cutting": {},
            "modules": [
                {
                    "name": "M",
                    "path": "src/m.py",
                    "responsibility": "r",
                    "code_domain": "M",
                }
            ],
            "traceability": [{"spec_ref_id": "F", "spec_ref_kind": "FEAT"}],
            "dev_tasks": [
                {"id": "T1", "path": "a.py", "description": "a", "depends_on": []}
            ],
            "hitl_flags": ["touches_production"],
        }
    )
    report = run_design_validate(design, profile)
    assert report.require_hitl is True
