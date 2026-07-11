"""DES-035 / DES-036 design delivery intent rules."""

from __future__ import annotations

import json
from pathlib import Path

from multi_agent_code_factory.profile_config import load_profile
from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.schemas.prd import PrdArtifact
from multi_agent_code_factory.validators.design_rules import validate_design_rules

from tests.conftest import load_snippet_json


def _load_design(name: str) -> DesignArtifact:
    fixture = Path(__file__).parent / "fixtures" / name
    return DesignArtifact.model_validate(
        json.loads(fixture.read_text(encoding="utf-8"))
    )


def test_todo_fixture_passes_des_035_036(snippets_dir: Path) -> None:
    spec = PrdArtifact.model_validate(
        load_snippet_json(snippets_dir, "prd-default.json")
    )
    design = _load_design("design-todo-valid.json")
    profile = load_profile("python")
    violations, _ = validate_design_rules(design, profile, spec)
    rule_ids = {v.rule_id for v in violations}
    assert "DES-035" not in rule_ids
    assert "DES-036" not in rule_ids


def test_empty_design_goals_triggers_des_035(snippets_dir: Path) -> None:
    spec = PrdArtifact.model_validate(
        load_snippet_json(snippets_dir, "prd-default.json")
    )
    design = _load_design("design-todo-valid.json").model_copy(
        update={"design_goals": []}
    )
    profile = load_profile("python")
    violations, _ = validate_design_rules(design, profile, spec)
    assert any(v.rule_id == "DES-035" for v in violations)


def test_bare_design_goals_trigger_des_037_warn(snippets_dir: Path) -> None:
    spec = PrdArtifact.model_validate(
        load_snippet_json(snippets_dir, "prd-default.json")
    )
    design = _load_design("design-todo-valid.json").model_copy(
        update={"design_goals": ["FEAT-1", "US-1"]}
    )
    profile = load_profile("python")
    violations, _ = validate_design_rules(design, profile, spec)
    des_037 = [v for v in violations if v.rule_id == "DES-037"]
    assert len(des_037) == 2
    assert all(v.severity == "warn" for v in des_037)


def test_missing_code_delta_triggers_des_036(snippets_dir: Path) -> None:
    spec = PrdArtifact.model_validate(
        load_snippet_json(snippets_dir, "prd-default.json")
    )
    design = _load_design("design-todo-valid.json")
    architecture = design.architecture
    assert architecture is not None
    design = design.model_copy(
        update={"architecture": architecture.model_copy(update={"code_delta": None})}
    )
    profile = load_profile("python")
    violations, _ = validate_design_rules(design, profile, spec)
    assert any(v.rule_id == "DES-036" for v in violations)
