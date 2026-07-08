"""DES-201 至 DES-223 design.md 格式规则。"""

from __future__ import annotations

import re
from pathlib import Path

from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.schemas.validation_report import Violation
from multi_agent_code_factory.validators._report import warn

_REQUIRED_SECTIONS = (
    ("DES-201", "## 1. 背景与上下文"),
    ("DES-201", "## 2. 设计目标"),
    ("DES-201", "## 3. 非目标"),
    ("DES-201", "## 4. 方案设计"),
    ("DES-201", "## 5. 方案对比"),
    ("DES-201", "## 6. 横切关注点"),
    ("DES-201", "## 7. 性能与可靠性"),
    ("DES-201", "## 8. 测试计划"),
    ("DES-201", "## 9. 监控与告警"),
    ("DES-210", "## 10. 待澄清项"),
)

_APPENDIX_SECTIONS = (
    ("DES-202", "## 附录 A. 需求追溯"),
    ("DES-202", "## 附录 B. 文件变更计划"),
    ("DES-202", "## 附录 C. 开发任务分解"),
    ("DES-215", "## 附录 D. 测试用例设计"),
    ("DES-207", "## 附录 E. 与现有代码对照"),
)

_ROLLOUT_RE = re.compile(r"##\s*9\.\s*Rollout|Rollout\s*&\s*Deployment", re.I)


def validate_design_md_rules(
    design: DesignArtifact,
    md_text: str,
) -> list[Violation]:
    """对照 design.json 校验 design.md 中文固定章节。"""
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

    if _ROLLOUT_RE.search(md_text):
        violations.append(
            warn(
                "DES-208",
                "design.md must not contain Rollout & Deployment section",
                field="design.md",
            )
        )

    if "### 4.3 外部依赖" not in md_text:
        violations.append(
            warn(
                "DES-212",
                "design.md missing ### 4.3 外部依赖",
                field="design.md",
            )
        )
    if "### 4.5 数据模型与表结构" not in md_text:
        violations.append(
            warn(
                "DES-213",
                "design.md missing ### 4.5 数据模型与表结构",
                field="design.md",
            )
        )
    if "### 4.6 流程与时序" not in md_text:
        violations.append(
            warn(
                "DES-206",
                "design.md missing ### 4.6 流程与时序",
                field="design.md",
            )
        )
    elif ".mmd" not in md_text and not design.diagrams:
        violations.append(
            warn(
                "DES-217",
                "design.md §4.6 should reference *.mmd",
                field="design.md",
            )
        )

    if "### 4.2 模块划分" not in md_text or "code_domain" not in md_text:
        violations.append(
            warn(
                "DES-220",
                "design.md missing ### 4.2 模块划分 with code_domain column",
                field="design.md",
            )
        )
    if "### 4.4 接口定义" not in md_text:
        violations.append(
            warn(
                "DES-221",
                "design.md missing ### 4.4 接口定义",
                field="design.md",
            )
        )
    if "### 6.1 数据一致性与事务" not in md_text:
        violations.append(
            warn(
                "DES-216",
                "design.md missing ### 6.1 数据一致性与事务",
                field="design.md",
            )
        )
    if "### 6.2 异常与错误码" not in md_text:
        violations.append(
            warn(
                "DES-216",
                "design.md missing ### 6.2 异常与错误码",
                field="design.md",
            )
        )

    if "| 可空 |" not in md_text and "| 注释 |" not in md_text:
        violations.append(
            warn(
                "DES-218",
                "design.md §4.5 tables should include 可空/注释 columns",
                field="design.md",
            )
        )

    if design.test_cases and "| 类型 |" not in md_text:
        violations.append(
            warn(
                "DES-219",
                "design.md appendix D should include 类型 column",
                field="design.md",
            )
        )
    elif not design.test_cases and "## 8. 测试计划" in md_text:
        violations.append(
            warn(
                "DES-205",
                "design.md should describe test_strategy or test_cases",
                field="design.md",
            )
        )

    if len(design.modules) >= 2 or design.external_dependencies:
        has_context = any(
            diagram.kind.value == "context" for diagram in design.diagrams
        )
        if not has_context and "architecture-" not in md_text:
            violations.append(
                warn(
                    "DES-223",
                    "multi-module design should include context architecture diagram",
                    field="diagrams",
                )
            )

    return violations


def validate_design_md_file(
    design: DesignArtifact,
    run_dir: Path | None,
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
    return validate_design_md_rules(design, design_path.read_text(encoding="utf-8"))
