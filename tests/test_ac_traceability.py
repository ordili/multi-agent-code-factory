from __future__ import annotations

from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.schemas.prd import PrdArtifact
from multi_agent_code_factory.tools.ac_traceability import (
    compute_acceptance_traceability,
    traceability_blocks_pass,
)


def _prd_and_design() -> tuple[PrdArtifact, DesignArtifact]:
    prd = PrdArtifact.model_validate(
        {
            "version": "1",
            "profile": "python",
            "revision": 1,
            "title": "Calc",
            "summary": "demo",
            "success_metrics": [],
            "features": [],
            "scope_in": ["calc"],
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
                    "description": "add works",
                    "verifiable_by": "automated_test",
                },
                {
                    "id": "AC-2",
                    "description": "divide works",
                    "verifiable_by": "automated_test",
                },
            ],
        }
    )
    design = DesignArtifact.model_validate(
        {
            "version": "1",
            "title": "Calc",
            "spec_ref": "Calc",
            "test_cases": [
                {
                    "id": "TC-HAP-CALC-001",
                    "kind": "happy",
                    "title": "add",
                    "covers": ["AC-1"],
                },
            ],
        }
    )
    return prd, design


def test_compute_acceptance_traceability_when_toolchain_green() -> None:
    prd, design = _prd_and_design()
    items = compute_acceptance_traceability(prd, design, toolchain_ok=True)
    assert len(items) == 2
    ac1 = next(item for item in items if item.id == "AC-1")
    ac2 = next(item for item in items if item.id == "AC-2")
    assert ac1.designed is True
    assert ac1.met is True
    assert ac1.test_case_ids == ["TC-HAP-CALC-001"]
    assert ac2.designed is False
    assert ac2.met is False
    assert ac2.note is not None


def test_compute_acceptance_traceability_when_toolchain_failed() -> None:
    prd, design = _prd_and_design()
    items = compute_acceptance_traceability(prd, design, toolchain_ok=False)
    ac1 = next(item for item in items if item.id == "AC-1")
    assert ac1.designed is True
    assert ac1.met is False
    assert "toolchain" in (ac1.note or "")


def test_traceability_blocks_pass_only_when_designed_unmet() -> None:
    prd, design = _prd_and_design()
    items = compute_acceptance_traceability(prd, design, toolchain_ok=False)
    assert traceability_blocks_pass(items, block_on=True) is True
    assert traceability_blocks_pass(items, block_on=False) is False
    green = compute_acceptance_traceability(prd, design, toolchain_ok=True)
    assert traceability_blocks_pass(green, block_on=True) is False
