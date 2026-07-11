from __future__ import annotations

from pathlib import Path

from multi_agent_code_factory.schemas.prd import PrdArtifact
from multi_agent_code_factory.validators.prd_rules_extended import (
    validate_prd_extended_rules,
)

from tests.conftest import load_snippet_json


def _minimal_spec(**overrides: object) -> PrdArtifact:
    base = {
        "version": "1",
        "profile": "python",
        "revision": 1,
        "title": "Test",
        "summary": "summary",
        "context": {"language": "python", "storage": "none"},
        "success_metrics": [],
        "features": [
            {
                "id": "FEAT-1",
                "name": "Core",
                "description": "core",
                "priority": "P0",
                "user_story_ids": ["US-1"],
            }
        ],
        "user_stories": [
            {"id": "US-1", "as_a": "user", "want": "do thing", "so_that": "value"}
        ],
        "requirement_pool": [],
        "scope_in": ["cli"],
        "scope_out": [],
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
        "acceptance_criteria": [
            {
                "id": "AC-1",
                "description": "covers US-1 via automated test",
                "verifiable_by": "automated_test",
            }
        ],
        "constraints": [],
    }
    base.update(overrides)
    return PrdArtifact.model_validate(base)


def test_prd_101_empty_ac_description_is_error() -> None:
    spec = _minimal_spec(
        acceptance_criteria=[
            {"id": "AC-1", "description": "  ", "verifiable_by": "automated_test"}
        ]
    )
    violations = validate_prd_extended_rules(spec)
    assert any(
        v.rule_id == "PRD-101" and v.severity.value == "error" for v in violations
    )


def test_prd_102_warns_when_p0_us_not_covered() -> None:
    spec = _minimal_spec(
        acceptance_criteria=[
            {
                "id": "AC-1",
                "description": "unrelated check",
                "verifiable_by": "automated_test",
            }
        ]
    )
    violations = validate_prd_extended_rules(spec)
    assert any(v.rule_id == "PRD-102" for v in violations)


def test_prd_111_custom_consistency_requires_notes() -> None:
    spec = _minimal_spec(
        consistency_profile={
            "consistency_model": "custom",
            "delivery": "best_effort",
            "multi_writer": False,
            "idempotency_required": False,
            "notes": "",
        }
    )
    violations = validate_prd_extended_rules(spec)
    assert any(
        v.rule_id == "PRD-111" and v.severity.value == "error" for v in violations
    )


def test_prd_017_requires_context_storage(snippets_dir: Path) -> None:
    data = load_snippet_json(snippets_dir, "prd-default.json")
    data["context"].pop("storage")
    spec = PrdArtifact.model_validate(data)
    violations = validate_prd_extended_rules(spec)
    assert any(
        v.rule_id == "PRD-017" and v.severity.value == "error" for v in violations
    )


def test_prd_default_passes_spec_102(snippets_dir: Path) -> None:
    spec = PrdArtifact.model_validate(
        load_snippet_json(snippets_dir, "prd-default.json")
    )
    violations = validate_prd_extended_rules(spec)
    assert not [v for v in violations if v.rule_id == "PRD-102"]


def test_prd_118_warns_on_empty_glossary_term() -> None:
    spec = _minimal_spec(
        context={
            "language": "python",
            "storage": "none",
            "glossary": [{"term": "  ", "definition": "ok"}],
        }
    )
    violations = validate_prd_extended_rules(spec)
    assert any(v.rule_id == "PRD-118" for v in violations)
