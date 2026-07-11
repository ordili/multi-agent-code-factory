"""PRD semantic rule tests."""

from __future__ import annotations

from multi_agent_code_factory.schemas.prd import PrdArtifact
from multi_agent_code_factory.validators.prd_semantic_rules import (
    validate_prd_semantic_rules,
)
from multi_agent_code_factory.validators.prd_semantic_triggers import (
    prd_requires_semantic_constraints,
)


def _calc_prd_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "version": "1",
        "profile": "python",
        "revision": 1,
        "title": "Calculator CLI",
        "summary": "Parse arithmetic expressions from CLI input",
        "context": {
            "language": "python",
            "interface": "cli",
            "storage": "none",
        },
        "success_metrics": [],
        "features": [
            {
                "id": "FEAT-1",
                "name": "Expression parser",
                "description": "Parse expression input",
                "priority": "P0",
                "user_story_ids": ["US-1"],
            }
        ],
        "user_stories": [
            {
                "id": "US-1",
                "as_a": "user",
                "want": "enter two numbers and one operator",
                "so_that": "I can calculate",
            }
        ],
        "requirement_pool": [],
        "scope_in": ["CLI"],
        "scope_out": ["mixed chained operations"],
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
                "description": "pytest passes",
                "verifiable_by": "automated_test",
            }
        ],
        "semantic_constraints": [],
    }
    payload.update(overrides)
    return payload


def test_narrow_trigger_for_calculator_like_prd() -> None:
    prd = PrdArtifact.model_validate(_calc_prd_payload())
    assert prd_requires_semantic_constraints(prd) is True


def test_todo_cli_subcommand_does_not_trigger() -> None:
    prd = PrdArtifact.model_validate(
        _calc_prd_payload(
            title="Todo CLI",
            summary="Todo add/list/done",
            context={"language": "python", "interface": "cli", "storage": "json_file"},
            features=[
                {
                    "id": "FEAT-1",
                    "name": "Todo CRUD",
                    "description": "add/list/done subcommands",
                    "priority": "P0",
                }
            ],
            user_stories=[
                {
                    "id": "US-1",
                    "as_a": "user",
                    "want": "add todos from CLI",
                    "so_that": "I can track tasks",
                }
            ],
            scope_out=[],
        )
    )
    assert prd_requires_semantic_constraints(prd) is False


def test_prd_s01_missing_semantic_constraints() -> None:
    prd = PrdArtifact.model_validate(_calc_prd_payload())
    violations = validate_prd_semantic_rules(prd)
    assert any(item.rule_id == "PRD-S01" for item in violations)


def test_prd_s02_invalid_source_ref() -> None:
    prd = PrdArtifact.model_validate(
        _calc_prd_payload(
            semantic_constraints=[
                {
                    "id": "SEM-IN-1",
                    "source_ref": "US-99",
                    "source_kind": "US",
                    "kind": "input_shape",
                    "summary": "binary input",
                    "dimensions": {"operand_count": "exactly:2"},
                }
            ]
        )
    )
    violations = validate_prd_semantic_rules(prd)
    assert any(item.rule_id == "PRD-S02" for item in violations)
