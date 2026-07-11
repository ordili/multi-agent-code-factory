"""PRD AC ↔ design.test_cases ↔ QA 工具链结果的自动追溯。"""

from __future__ import annotations

from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.schemas.prd import PrdArtifact
from multi_agent_code_factory.schemas.test_report import AcceptanceTraceItem


def _ac_test_case_map(design: DesignArtifact) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for tc in design.test_cases:
        for ref in tc.covers or []:
            if not ref.startswith("AC-"):
                continue
            mapping.setdefault(ref, [])
            if tc.id not in mapping[ref]:
                mapping[ref].append(tc.id)
    return mapping


def compute_acceptance_traceability(
    prd: PrdArtifact,
    design: DesignArtifact,
    *,
    toolchain_ok: bool,
) -> list[AcceptanceTraceItem]:
    """生成 AC 追溯项：designed=有 test_cases.covers；met=designed 且工具链绿。"""
    tc_map = _ac_test_case_map(design)
    items: list[AcceptanceTraceItem] = []

    for ac in prd.acceptance_criteria:
        test_case_ids = tc_map.get(ac.id, [])
        designed = bool(test_case_ids)
        if not designed:
            items.append(
                AcceptanceTraceItem(
                    id=ac.id,
                    designed=False,
                    test_case_ids=[],
                    met=False,
                    note="no test_cases.covers for this acceptance criterion",
                )
            )
            continue
        if toolchain_ok:
            items.append(
                AcceptanceTraceItem(
                    id=ac.id,
                    designed=True,
                    test_case_ids=test_case_ids,
                    met=True,
                    note=None,
                )
            )
        else:
            items.append(
                AcceptanceTraceItem(
                    id=ac.id,
                    designed=True,
                    test_case_ids=test_case_ids,
                    met=False,
                    note="toolchain tests failed or errored",
                )
            )

    return items


def traceability_blocks_pass(
    items: list[AcceptanceTraceItem],
    *,
    block_on: bool,
) -> bool:
    """block_on 时：任一 designed 但未 met 的 AC 应阻断 passed。"""
    if not block_on:
        return False
    return any(item.designed and not item.met for item in items)
