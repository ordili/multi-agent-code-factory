"""SPEC-301 至 SPEC-313 spec.md 格式规则。"""

from __future__ import annotations

import re
from pathlib import Path

from multi_agent_code_factory.schemas.spec import SpecArtifact
from multi_agent_code_factory.schemas.validation_report import Violation
from multi_agent_code_factory.validators._report import warn

_REQUIRED_SECTIONS = (
    ("SPEC-301", "## 概述"),
    ("SPEC-302", "## 验收标准"),
    ("SPEC-303", "## 范围"),
    ("SPEC-307", "## 功能"),
    ("SPEC-308", "## 稳定性、性能与数据一致性"),
    ("SPEC-309", "## 术语与领域概念"),
    ("SPEC-310", "## 背景与上下文"),
    ("SPEC-311", "## 用户故事"),
    ("SPEC-312", "## 需求池"),
    ("SPEC-313", "## 约束"),
)

_AC_ID_RE = re.compile(r"\b(AC-\d+)\b")


def validate_spec_md_rules(
    spec: SpecArtifact,
    md_text: str,
) -> list[Violation]:
    """对照 spec.json 校验 spec.md 中文固定章节与元数据。"""
    violations: list[Violation] = []

    for rule_id, heading in _REQUIRED_SECTIONS:
        if heading not in md_text:
            violations.append(
                warn(
                    rule_id,
                    f"spec.md missing required section: {heading}",
                    field="spec.md",
                )
            )

    if spec.success_metrics and "## 业务指标" not in md_text:
        violations.append(
            warn(
                "SPEC-306",
                "spec.md missing ## 业务指标 while success_metrics is non-empty",
                field="spec.md",
            )
        )

    json_ac_ids = {ac.id for ac in spec.acceptance_criteria}
    md_ac_ids = set(_AC_ID_RE.findall(md_text))
    for ac_id in sorted(md_ac_ids - json_ac_ids):
        violations.append(
            warn(
                "SPEC-304",
                f"spec.md references AC id {ac_id} not in spec.json",
                field="spec.md",
            )
        )
    for ac_id in sorted(json_ac_ids - md_ac_ids):
        violations.append(
            warn(
                "SPEC-304",
                f"spec.json AC id {ac_id} missing from spec.md",
                field="spec.md",
            )
        )

    if "task_profile:" not in md_text:
        violations.append(
            warn(
                "SPEC-305",
                "spec.md footer missing task_profile metadata",
                field="spec.md",
            )
        )
    if "revision:" not in md_text:
        violations.append(
            warn(
                "SPEC-305",
                "spec.md footer missing revision metadata",
                field="spec.md",
            )
        )

    return violations


def validate_spec_md_file(
    spec: SpecArtifact,
    run_dir: Path | None,
) -> list[Violation]:
    """读取 run 目录 spec.md 并执行格式校验。"""
    if run_dir is None:
        return []
    spec_path = run_dir / "spec.md"
    if not spec_path.is_file():
        return [
            warn(
                "SPEC-301",
                "spec.md not found in run directory",
                field="spec.md",
            )
        ]
    return validate_spec_md_rules(spec, spec_path.read_text(encoding="utf-8"))
