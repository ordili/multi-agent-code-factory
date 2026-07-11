"""Mermaid *.mmd 解析与 DES-203/214 校验。"""

from __future__ import annotations

import re
from pathlib import Path

from multi_agent_code_factory.schemas.design import DesignArtifact, DiagramKind
from multi_agent_code_factory.schemas.prd import PrdArtifact
from multi_agent_code_factory.schemas.validation_report import Violation
from multi_agent_code_factory.validators._report import error, warn
from multi_agent_code_factory.validators.design_triggers import requires_diagram_pair

_SEQUENCE_RE = re.compile(r"^\s*sequenceDiagram\b", re.MULTILINE | re.IGNORECASE)
_FLOWCHART_RE = re.compile(
    r"^\s*(flowchart|graph)\s+(TD|TB|BT|RL|LR|DR|DU)?\b",
    re.MULTILINE | re.IGNORECASE,
)
_PARTICIPANT_RE = re.compile(
    r"^\s*participant\s+\w+\s+as\s+(\w+)",
    re.MULTILINE | re.IGNORECASE,
)


def detect_mermaid_kinds(text: str) -> set[str]:
    """识别 Mermaid 文本中包含的 diagram 类型。"""
    kinds: set[str] = set()
    if _SEQUENCE_RE.search(text):
        kinds.add(DiagramKind.SEQUENCE.value)
    if _FLOWCHART_RE.search(text):
        kinds.add(DiagramKind.FLOWCHART.value)
    if re.search(r"^\s*classDiagram\b", text, re.MULTILINE | re.IGNORECASE):
        kinds.add(DiagramKind.CLASS.value)
    if re.search(r"C4Context|contextDiagram", text, re.IGNORECASE):
        kinds.add(DiagramKind.CONTEXT.value)
    return kinds


def _collect_mmd_files(run_dir: Path) -> list[Path]:
    return sorted(run_dir.glob("*.mmd"))


def validate_mermaid_files(
    design: DesignArtifact,
    run_dir: Path | None,
    *,
    strict: bool = True,
    spec: PrdArtifact | None = None,
) -> list[Violation]:
    """校验 Run 目录 *.mmd 可解析且含 sequence + flowchart。"""
    violations: list[Violation] = []
    if not requires_diagram_pair(design, spec):
        return violations

    severity = error if strict else warn

    if run_dir is None:
        return violations

    mmd_files = _collect_mmd_files(run_dir)
    if not mmd_files:
        violations.append(
            severity(
                "DES-203",
                "no *.mmd files found in run directory",
                field="*.mmd",
            )
        )
        return violations

    combined_kinds: set[str] = set()
    file_kinds: dict[str, set[str]] = {}
    for path in mmd_files:
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            violations.append(
                severity(
                    "DES-203",
                    f"{path.name} is empty",
                    field=path.name,
                )
            )
            continue
        kinds = detect_mermaid_kinds(text)
        file_kinds[path.name] = kinds
        combined_kinds.update(kinds)

    if DiagramKind.SEQUENCE.value not in combined_kinds:
        violations.append(
            severity(
                "DES-203",
                "run *.mmd must include a sequenceDiagram",
                field="*.mmd",
            )
        )
    if DiagramKind.FLOWCHART.value not in combined_kinds:
        violations.append(
            severity(
                "DES-203",
                "run *.mmd must include a flowchart/graph diagram",
                field="*.mmd",
            )
        )

    registered_diagram_kinds = {
        diagram.kind.value if hasattr(diagram.kind, "value") else str(diagram.kind)
        for diagram in design.diagrams
    }
    if DiagramKind.SEQUENCE.value not in registered_diagram_kinds:
        violations.append(
            severity(
                "DES-214",
                "design.diagrams must register kind=sequence",
                field="diagrams",
            )
        )
    if DiagramKind.FLOWCHART.value not in registered_diagram_kinds:
        violations.append(
            severity(
                "DES-214",
                "design.diagrams must register kind=flowchart",
                field="diagrams",
            )
        )

    for diagram in design.diagrams:
        if not diagram.path.endswith(".mmd"):
            continue
        path = run_dir / diagram.path
        if not path.is_file():
            violations.append(
                warn(
                    "DES-214",
                    f"diagram path {diagram.path!r} not found on disk",
                    field="diagrams",
                )
            )
            continue
        kind = (
            diagram.kind.value if hasattr(diagram.kind, "value") else str(diagram.kind)
        )
        present = file_kinds.get(path.name, set())
        if kind not in present:
            violations.append(
                severity(
                    "DES-214",
                    f"{path.name} missing registered diagram kind={kind}",
                    field=path.name,
                )
            )

    module_names = {module.name for module in design.modules}
    for path in mmd_files:
        text = path.read_text(encoding="utf-8")
        participants = set(_PARTICIPANT_RE.findall(text))
        unknown = participants - module_names - {"User", "U"}
        if unknown and module_names:
            violations.append(
                warn(
                    "DES-204",
                    f"{path.name} participants {sorted(unknown)} not in modules",
                    field=path.name,
                )
            )

    return violations
