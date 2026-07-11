"""Tests for design rule trigger helpers."""

from __future__ import annotations

import json
from pathlib import Path

from multi_agent_code_factory.profile_config import load_profile
from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.schemas.prd import PrdArtifact
from multi_agent_code_factory.validators.design_rules import validate_design_rules
from multi_agent_code_factory.validators.design_triggers import (
    design_has_cross_module_collaboration,
    is_stateless_design,
    requires_flow_section,
    requires_table_schemas,
    requires_transaction_constraints,
    spec_has_nonlinear_us,
)

from tests.conftest import load_snippet_json


def _load_design(name: str) -> DesignArtifact:
    fixture = Path(__file__).parent / "fixtures" / name
    return DesignArtifact.model_validate(
        json.loads(fixture.read_text(encoding="utf-8"))
    )


def test_stateless_calculator_skips_des_013_014(snippets_dir: Path) -> None:
    spec = PrdArtifact.model_validate(
        load_snippet_json(snippets_dir, "spec-calculator-stateless.json")
    )
    design = _load_design("design-calculator-stateless-min.json")
    assert is_stateless_design(design, spec) is True
    assert requires_table_schemas(design, spec) is False
    assert requires_transaction_constraints(design, spec) is False

    profile = load_profile("python")
    violations, _ = validate_design_rules(design, profile, spec)
    rule_ids = {v.rule_id for v in violations}
    assert "DES-013" not in rule_ids
    assert "DES-014" not in rule_ids


def test_todo_fixture_still_requires_table_schemas(snippets_dir: Path) -> None:
    spec = PrdArtifact.model_validate(
        load_snippet_json(snippets_dir, "prd-default.json")
    )
    design = _load_design("design-todo-valid.json")
    assert requires_table_schemas(design, spec) is True
    assert requires_transaction_constraints(design, spec) is (
        spec.consistency_profile.multi_writer
    )


def test_filesystem_dep_does_not_require_transaction_constraints(
    snippets_dir: Path,
) -> None:
    spec = PrdArtifact.model_validate(
        load_snippet_json(snippets_dir, "spec-calculator-stateless.json")
    )
    payload = json.loads(
        (
            Path(__file__).parent / "fixtures" / "design-calculator-stateless-min.json"
        ).read_text(encoding="utf-8")
    )
    payload["external_dependencies"] = [
        {
            "name": "out.txt",
            "kind": "filesystem",
            "code_domain": "CLI",
            "purpose": "optional output",
        }
    ]
    design = DesignArtifact.model_validate(payload)
    assert requires_transaction_constraints(design, spec) is False


def test_stateless_calculator_skips_flow_section(snippets_dir: Path) -> None:
    spec = PrdArtifact.model_validate(
        load_snippet_json(snippets_dir, "spec-calculator-stateless.json")
    )
    design = _load_design("design-calculator-stateless-min.json")
    assert design_has_cross_module_collaboration(design, spec) is False
    assert requires_flow_section(design, spec) is False


def test_todo_requires_flow_section(snippets_dir: Path) -> None:
    spec = PrdArtifact.model_validate(
        load_snippet_json(snippets_dir, "prd-default.json")
    )
    design = _load_design("design-todo-valid.json")
    assert design_has_cross_module_collaboration(design, spec) is True
    assert requires_flow_section(design, spec) is True


def test_prd_multi_writer_triggers_nonlinear_us(snippets_dir: Path) -> None:
    raw = load_snippet_json(snippets_dir, "prd-default.json")
    raw["consistency_profile"]["multi_writer"] = True
    spec = PrdArtifact.model_validate(raw)
    assert spec_has_nonlinear_us(spec) is True
