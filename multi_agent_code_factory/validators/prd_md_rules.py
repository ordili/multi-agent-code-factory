"""PRD-301 至 PRD-316 prd.md 格式规则。"""

from __future__ import annotations

import re
from pathlib import Path

from multi_agent_code_factory.schemas.prd import PrdArtifact
from multi_agent_code_factory.schemas.validation_report import Violation
from multi_agent_code_factory.validators._report import warn

_REQUIRED_SECTIONS = (
    ("PRD-301", "## 概述"),
    ("PRD-302", "## 验收标准"),
    ("PRD-303", "## 范围"),
    ("PRD-306", "## 业务指标"),
    ("PRD-307", "## 功能"),
    ("PRD-308", "## 非功能性需求"),
    ("PRD-309", "## 术语与领域概念"),
    ("PRD-310", "## 背景与上下文"),
    ("PRD-311", "## 用户故事"),
    ("PRD-312", "## 需求池"),
    ("PRD-313", "## 约束"),
)

_AC_ID_RE = re.compile(r"\b(AC-\d+)\b")


def validate_prd_md_rules(
    spec: PrdArtifact,
    md_text: str,
) -> list[Violation]:
    """对照 prd.json 校验 prd.md 中文固定章节与元数据。"""
    violations: list[Violation] = []

    for rule_id, heading in _REQUIRED_SECTIONS:
        if heading not in md_text:
            violations.append(
                warn(
                    rule_id,
                    f"prd.md missing required section: {heading}",
                    field="prd.md",
                )
            )

    if "**本次包含**" not in md_text:
        violations.append(
            warn(
                "PRD-316",
                "prd.md scope section missing **本次包含**",
                field="prd.md",
            )
        )
    if "**明确不做**" not in md_text:
        violations.append(
            warn(
                "PRD-316",
                "prd.md scope section missing **明确不做**",
                field="prd.md",
            )
        )

    if "### 稳定性与性能" not in md_text:
        violations.append(
            warn(
                "PRD-314",
                "prd.md missing ### 稳定性与性能 under NFR",
                field="prd.md",
            )
        )
    if "### 数据一致性" not in md_text:
        violations.append(
            warn(
                "PRD-315",
                "prd.md missing ### 数据一致性 under NFR",
                field="prd.md",
            )
        )

    json_ac_ids = {ac.id for ac in spec.acceptance_criteria}
    md_ac_ids = set(_AC_ID_RE.findall(md_text))
    for ac_id in sorted(md_ac_ids - json_ac_ids):
        violations.append(
            warn(
                "PRD-304",
                f"prd.md references AC id {ac_id} not in prd.json",
                field="prd.md",
            )
        )
    for ac_id in sorted(json_ac_ids - md_ac_ids):
        violations.append(
            warn(
                "PRD-304",
                f"prd.json AC id {ac_id} missing from prd.md",
                field="prd.md",
            )
        )

    if "task_profile:" not in md_text:
        violations.append(
            warn(
                "PRD-305",
                "prd.md footer missing task_profile metadata",
                field="prd.md",
            )
        )
    if "revision:" not in md_text:
        violations.append(
            warn(
                "PRD-305",
                "prd.md footer missing revision metadata",
                field="prd.md",
            )
        )

    return violations


def validate_prd_md_file(
    spec: PrdArtifact,
    run_dir: Path | None,
) -> list[Violation]:
    """读取 run 目录 prd.md 并执行格式校验。"""
    if run_dir is None:
        return []
    spec_path = run_dir / "prd.md"
    if not spec_path.is_file():
        return [
            warn(
                "PRD-301",
                "prd.md not found in run directory",
                field="prd.md",
            )
        ]
    return validate_prd_md_rules(spec, spec_path.read_text(encoding="utf-8"))
