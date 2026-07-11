"""Design semantic rule tests."""

from __future__ import annotations

from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.schemas.prd import PrdArtifact
from multi_agent_code_factory.validators.design_semantic_rules import (
    validate_design_semantic_rules,
)


def _prd_with_sem() -> PrdArtifact:
    return PrdArtifact.model_validate(
        {
            "version": "1",
            "profile": "python",
            "revision": 1,
            "title": "Calc",
            "summary": "Calc",
            "context": {"language": "python", "interface": "cli", "storage": "none"},
            "success_metrics": [],
            "features": [
                {
                    "id": "FEAT-1",
                    "name": "Calc",
                    "description": "parse",
                    "priority": "P0",
                }
            ],
            "scope_in": ["CLI"],
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
                    "description": "SEM-IN-1 passes",
                    "verifiable_by": "automated_test",
                }
            ],
            "semantic_constraints": [
                {
                    "id": "SEM-IN-1",
                    "source_ref": "US-1",
                    "source_kind": "US",
                    "kind": "input_shape",
                    "summary": "binary input",
                    "dimensions": {
                        "operand_count": "exactly:2",
                        "operator_set": "one_of:+, -, *, /",
                    },
                    "excludes": [
                        {
                            "id": "EX-CHAIN",
                            "dimension": "operand_count",
                            "rule": "gte:3",
                            "summary": "chained operands",
                        }
                    ],
                }
            ],
        }
    )


def test_des_rules_skip_when_prd_has_no_sem() -> None:
    design = DesignArtifact.model_validate({"spec_ref": "Calc"})
    prd = _prd_with_sem().model_copy(update={"semantic_constraints": []})
    assert validate_design_semantic_rules(design, prd) == []


def test_des_s01_missing_equivalence_classes() -> None:
    design = DesignArtifact.model_validate(
        {
            "spec_ref": "Calc",
            "test_cases": [
                {
                    "id": "TC-HAP-CALC-001",
                    "kind": "happy",
                    "description": 'input: "1+2"',
                    "covers": ["AC-1", "SEM-IN-1"],
                    "semantic_evidence": {
                        "constraint_ref": "SEM-IN-1",
                        "equivalence_class": "plus",
                        "proves_dimensions": ["operand_count", "operator_set"],
                    },
                }
            ],
        }
    )
    violations = validate_design_semantic_rules(design, _prd_with_sem())
    assert any(item.rule_id == "DES-S01" for item in violations)


def test_des_s04_requires_sem_in_covers() -> None:
    design = DesignArtifact.model_validate(
        {
            "spec_ref": "Calc",
            "test_cases": [
                {
                    "id": "TC-HAP-CALC-001",
                    "kind": "happy",
                    "description": 'input: "1+2"',
                    "covers": ["AC-1"],
                }
            ],
        }
    )
    violations = validate_design_semantic_rules(design, _prd_with_sem())
    assert any(item.rule_id == "DES-S04" for item in violations)
