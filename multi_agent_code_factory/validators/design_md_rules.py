"""DES-201 至 DES-224 design.md 格式规则（定稿 §1–§6 + 附录 A–D）。"""

from __future__ import annotations

import re
from pathlib import Path

from multi_agent_code_factory.schemas.design import DesignArtifact, DiagramKind
from multi_agent_code_factory.schemas.spec import SpecArtifact
from multi_agent_code_factory.schemas.validation_report import Violation
from multi_agent_code_factory.validators._report import warn
from multi_agent_code_factory.validators.design_triggers import (
    requires_table_schemas,
    requires_transaction_constraints,
    spec_requires_non_functional,
)

_REQUIRED_SECTIONS = (
    ("DES-201", "## 1. 背景与上下文"),
    ("DES-201", "## 2. 设计目标"),
    ("DES-201", "## 3. 非目标"),
    ("DES-201", "## 4. 方案设计"),
    ("DES-201", "## 6. 测试用例列表"),
)

_APPENDIX_SECTIONS = (
    ("DES-202", "## 附录 A. 需求追溯"),
    ("DES-202", "## 附录 B. 文件变更计划"),
    ("DES-202", "## 附录 C. 开发任务分解"),
    ("DES-207", "## 附录 D. 与现有代码对照"),
)

_REMOVED_SECTIONS = (
    "## 5. 方案对比",
    "## 6. 横切关注点",
    "## 7. 性能与可靠性",
    "## 8. 测试计划",
    "## 9. 监控与告警",
    "## 10. 待澄清项",
    "## 附录 E.",
)

_ROLLOUT_RE = re.compile(r"##\s*9\.\s*Rollout|Rollout\s*&\s*Deployment", re.I)


def _has_real_external_deps(design: DesignArtifact) -> bool:
    return any(dep.kind != "none" for dep in design.external_dependencies)


def _has_flow_diagrams(design: DesignArtifact) -> bool:
    flow_kinds = {DiagramKind.SEQUENCE.value, DiagramKind.FLOWCHART.value}
    return any(
        (d.kind.value if hasattr(d.kind, "value") else d.kind) in flow_kinds
        for d in design.diagrams
    )


def validate_design_md_rules(
    design: DesignArtifact,
    md_text: str,
    spec: SpecArtifact | None = None,
) -> list[Violation]:
    """对照 design.json 与定稿模板校验 design.md 章节。"""
    violations: list[Violation] = []

    seen_rules: set[str] = set()
    for rule_id, heading in _REQUIRED_SECTIONS:
        if heading not in md_text and rule_id not in seen_rules:
            violations.append(
                warn(
                    rule_id,
                    f"design.md missing required section: {heading}",
                    field="design.md",
                )
            )
            seen_rules.add(rule_id)

    for rule_id, heading in _APPENDIX_SECTIONS:
        if heading not in md_text:
            violations.append(
                warn(
                    rule_id,
                    f"design.md missing appendix: {heading}",
                    field="design.md",
                )
            )

    for removed in _REMOVED_SECTIONS:
        if removed in md_text:
            violations.append(
                warn(
                    "DES-208",
                    f"design.md contains removed section: {removed}",
                    field="design.md",
                )
            )

    if _ROLLOUT_RE.search(md_text):
        violations.append(
            warn(
                "DES-208",
                "design.md must not contain Rollout & Deployment section",
                field="design.md",
            )
        )

    if design.modules and (
        "### 4.3 模块划分" not in md_text or "code_domain" not in md_text
    ):
        violations.append(
            warn(
                "DES-220",
                "design.md missing ### 4.3 模块划分 with code_domain column",
                field="design.md",
            )
        )

    if _has_real_external_deps(design) and "### 4.4 外部依赖" not in md_text:
        violations.append(
            warn(
                "DES-212",
                "design.md missing ### 4.4 外部依赖",
                field="design.md",
            )
        )

    if design.interfaces and "### 4.5 接口定义" not in md_text:
        violations.append(
            warn(
                "DES-221",
                "design.md missing ### 4.5 接口定义",
                field="design.md",
            )
        )

    if requires_table_schemas(design, spec) and "### 4.6 存储结构" not in md_text:
        violations.append(
            warn(
                "DES-213",
                "design.md missing ### 4.6 存储结构",
                field="design.md",
            )
        )

    if requires_transaction_constraints(design, spec) and "一致性与事务" not in md_text:
        violations.append(
            warn(
                "DES-216",
                "design.md §4.6 should include 一致性与事务",
                field="design.md",
            )
        )

    if _has_flow_diagrams(design):
        if "### 4.7 流程与时序" not in md_text:
            violations.append(
                warn(
                    "DES-206",
                    "design.md missing ### 4.7 流程与时序",
                    field="design.md",
                )
            )
        elif ".mmd" not in md_text:
            violations.append(
                warn(
                    "DES-217",
                    "design.md §4.7 should reference *.mmd",
                    field="design.md",
                )
            )

    if design.table_schemas and (
        "| 可空 |" not in md_text and "| 注释 |" not in md_text
    ):
        violations.append(
            warn(
                "DES-218",
                "design.md §4.6 tables should include 可空/注释 columns",
                field="design.md",
            )
        )

    if design.test_cases and "| 类型 |" not in md_text:
        violations.append(
            warn(
                "DES-219",
                "design.md §6 should include 类型 column",
                field="design.md",
            )
        )

    needs_context = len(design.modules) >= 2 or _has_real_external_deps(design)
    if needs_context:
        has_context = any(
            diagram.kind.value == "context" for diagram in design.diagrams
        )
        if not has_context and "### 4.2 系统架构图" not in md_text:
            violations.append(
                warn(
                    "DES-223",
                    "multi-module design should include ### 4.2 系统架构图",
                    field="design.md",
                )
            )

    needs_nfr = bool(design.non_functional) or (
        spec is not None and spec_requires_non_functional(spec)
    )
    if needs_nfr and design.non_functional and "## 5. 非功能性目标" not in md_text:
        violations.append(
            warn(
                "DES-224",
                "design.md missing ## 5. 非功能性目标",
                field="design.md",
            )
        )

    return violations


def validate_design_md_file(
    design: DesignArtifact,
    run_dir: Path | None,
    spec: SpecArtifact | None = None,
) -> list[Violation]:
    """读取 run 目录 design.md 并执行格式校验。"""
    if run_dir is None:
        return []
    design_path = run_dir / "design.md"
    if not design_path.is_file():
        return [
            warn(
                "DES-201",
                "design.md not found in run directory",
                field="design.md",
            )
        ]
    return validate_design_md_rules(
        design, design_path.read_text(encoding="utf-8"), spec=spec
    )
