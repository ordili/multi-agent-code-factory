from __future__ import annotations

import json
from pathlib import Path

from multi_agent_code_factory.profile_config import load_profile
from multi_agent_code_factory.renderers.design_md import render_design_md
from multi_agent_code_factory.renderers.spec_md import render_spec_md
from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.schemas.spec import SpecArtifact
from multi_agent_code_factory.schemas.validation_report import ValidationTarget
from multi_agent_code_factory.validators._report import build_validation_report
from multi_agent_code_factory.validators.design_md_rules import validate_design_md_rules
from multi_agent_code_factory.validators.design_rules import validate_design_rules
from multi_agent_code_factory.validators.mermaid import (
    detect_mermaid_kinds,
    validate_mermaid_files,
)
from multi_agent_code_factory.validators.spec_md_rules import validate_spec_md_rules
from multi_agent_code_factory.validators.spec_rules import validate_spec_rules

from tests.conftest import load_snippet_json


def test_detect_mermaid_kinds_flow_todo(snippets_dir: Path) -> None:
    text = (snippets_dir / "flow-todo.mmd").read_text(encoding="utf-8")
    kinds = detect_mermaid_kinds(text)
    assert "sequence" in kinds
    assert "flowchart" in kinds


def test_validate_spec_md_rules_passes_renderer_output(snippets_dir: Path) -> None:
    spec = SpecArtifact.model_validate(
        load_snippet_json(snippets_dir, "spec-default.json")
    )
    md = render_spec_md(spec)
    violations = validate_spec_md_rules(spec, md)
    assert not violations


def test_validate_design_md_rules_passes_renderer_output() -> None:
    fixture = Path(__file__).parent / "fixtures" / "design-todo-valid.json"
    design = DesignArtifact.model_validate(
        json.loads(fixture.read_text(encoding="utf-8"))
    )
    md = render_design_md(design)
    violations = validate_design_md_rules(design, md)
    assert not [v for v in violations if v.rule_id == "DES-208"]


def test_validate_mermaid_files_with_fixture(
    snippets_dir: Path, tmp_path: Path
) -> None:
    fixture = Path(__file__).parent / "fixtures" / "design-todo-valid.json"
    design = DesignArtifact.model_validate(
        json.loads(fixture.read_text(encoding="utf-8"))
    )
    (tmp_path / "flow.mmd").write_text(
        (snippets_dir / "flow-todo.mmd").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    violations = validate_mermaid_files(design, tmp_path, strict=True)
    assert not [v for v in violations if v.severity.value == "error"]


def test_design_todo_valid_passes_extended_rules(
    snippets_dir: Path,
) -> None:
    profile = load_profile("python")
    spec = SpecArtifact.model_validate(
        load_snippet_json(snippets_dir, "spec-default.json")
    )
    design = DesignArtifact.model_validate(
        json.loads(
            (Path(__file__).parent / "fixtures" / "design-todo-valid.json").read_text(
                encoding="utf-8"
            )
        )
    )
    violations, _ = validate_design_rules(design, profile, spec)
    report = build_validation_report(ValidationTarget.DESIGN, violations)
    assert report.passed is True


def test_spec_default_passes_extended_rules(snippets_dir: Path) -> None:
    profile = load_profile("python")
    spec = SpecArtifact.model_validate(
        load_snippet_json(snippets_dir, "spec-default.json")
    )
    violations = validate_spec_rules(spec, profile)
    report = build_validation_report(ValidationTarget.SPEC, violations)
    assert report.passed is True
