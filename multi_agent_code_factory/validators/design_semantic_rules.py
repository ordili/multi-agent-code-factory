"""DES-S01 through DES-S05 semantic validation rules."""

from __future__ import annotations

import re

from multi_agent_code_factory.schemas.design import DesignArtifact, TestCaseKind
from multi_agent_code_factory.schemas.prd import PrdArtifact, SemanticConstraintKind
from multi_agent_code_factory.schemas.validation_report import Violation
from multi_agent_code_factory.validators._report import error, warn
from multi_agent_code_factory.validators._semantic_syntax import parse_one_of_values

_INPUT_PREFIX_RE = re.compile(r"^\s*(input|request)\s*:", re.IGNORECASE)
_LITERAL_EXAMPLE_RE = re.compile(r"如.*\d")
_DIMENSION_WORDS_RE = re.compile(
    r"operand|operator|操作数|运算符|dimension",
    re.IGNORECASE,
)
_SEM_ID_RE = re.compile(r"^SEM-[A-Z0-9_-]+$")


def _happy_cases(cases: list) -> list:
    return [tc for tc in cases if str(tc.kind).lower() == TestCaseKind.HAPPY.value]


def _negative_cases(cases: list) -> list:
    return [tc for tc in cases if str(tc.kind).lower() == TestCaseKind.NEGATIVE.value]


def _cases_for_constraint(cases: list, sem_id: str) -> list:
    matched = []
    for tc in cases:
        covers = set(tc.covers or [])
        evidence = tc.semantic_evidence
        if sem_id in covers:
            matched.append(tc)
            continue
        if evidence is not None and evidence.constraint_ref == sem_id:
            matched.append(tc)
    return matched


def _description_input_text(description: str | None) -> str:
    return description or ""


def validate_design_semantic_rules(
    design: DesignArtifact,
    prd: PrdArtifact | None,
) -> list[Violation]:
    """Evaluate DES-S* rules when PRD declares semantic_constraints."""
    if prd is None or not prd.semantic_constraints:
        return []

    violations: list[Violation] = []
    sem_ids = [
        item.id for item in prd.semantic_constraints if _SEM_ID_RE.match(item.id)
    ]
    if not sem_ids:
        return violations

    constraint_by_id = {item.id: item for item in prd.semantic_constraints}

    for sem_id in sem_ids:
        constraint = constraint_by_id[sem_id]
        related = _cases_for_constraint(design.test_cases, sem_id)
        happy = [
            tc for tc in related if str(tc.kind).lower() == TestCaseKind.HAPPY.value
        ]
        negative = [
            tc for tc in related if str(tc.kind).lower() == TestCaseKind.NEGATIVE.value
        ]
        boundary = [
            tc for tc in related if str(tc.kind).lower() == TestCaseKind.BOUNDARY.value
        ]

        if constraint.kind == SemanticConstraintKind.INPUT_SHAPE:
            classes = {
                tc.semantic_evidence.equivalence_class
                for tc in happy
                if tc.semantic_evidence is not None
                and tc.semantic_evidence.equivalence_class
            }
            proved: set[str] = set()
            for tc in happy:
                if tc.semantic_evidence is not None:
                    proved.update(tc.semantic_evidence.proves_dimensions)
            if len(classes) < 2:
                violations.append(
                    error(
                        "DES-S01",
                        f"{sem_id} needs >=2 happy TC with distinct equivalence_class",
                        field="test_cases",
                    )
                )
            missing_dims = set(constraint.dimensions) - proved
            if missing_dims:
                violations.append(
                    error(
                        "DES-S01",
                        (
                            f"{sem_id} missing proves_dimensions for "
                            f"{sorted(missing_dims)!r}"
                        ),
                        field="test_cases",
                    )
                )
            for key, rule in constraint.dimensions.items():
                if not rule.strip().startswith("one_of:"):
                    continue
                values = parse_one_of_values(rule)
                covered: set[str] = set()
                for tc in happy:
                    text = _description_input_text(tc.description)
                    for value in values:
                        if value in text:
                            covered.add(value)
                if covered != set(values):
                    missing = sorted(set(values) - covered)
                    violations.append(
                        error(
                            "DES-S01b",
                            (
                                f"{sem_id} one_of dimension {key!r} "
                                f"missing TC for {missing!r}"
                            ),
                            field="test_cases",
                        )
                    )
            for tc in happy:
                desc = _description_input_text(tc.description)
                if not _INPUT_PREFIX_RE.search(desc):
                    violations.append(
                        error(
                            "DES-S05",
                            (
                                f"happy TC {tc.id} missing input:/request: "
                                "prefix in description"
                            ),
                            path=f"/test_cases/{tc.id}/description",
                            field="description",
                        )
                    )

        elif constraint.kind == SemanticConstraintKind.INVARIANT:
            if not happy and not boundary:
                violations.append(
                    error(
                        "DES-S01",
                        f"{sem_id} invariant requires >=1 happy or boundary TC",
                        field="test_cases",
                    )
                )
            if not negative:
                violations.append(
                    error(
                        "DES-S01",
                        f"{sem_id} invariant requires >=1 negative TC",
                        field="test_cases",
                    )
                )

        elif constraint.kind == SemanticConstraintKind.STATE_TRANSITION:
            if not any((tc.steps or "").strip() for tc in related):
                violations.append(
                    error(
                        "DES-S01",
                        f"{sem_id} state_transition requires TC with non-empty steps",
                        field="test_cases",
                    )
                )

        elif constraint.kind == SemanticConstraintKind.OUTPUT_SHAPE:
            if not related:
                violations.append(
                    warn(
                        "DES-S01",
                        (
                            f"{sem_id} output_shape should have >=1 TC "
                            "with output evidence"
                        ),
                        field="test_cases",
                    )
                )

        if constraint.excludes:
            for exclude in constraint.excludes:
                has_negative = any(
                    tc
                    for tc in negative + _negative_cases(design.test_cases)
                    if sem_id in (tc.covers or [])
                    or (
                        tc.semantic_evidence is not None
                        and tc.semantic_evidence.constraint_ref == sem_id
                    )
                    or exclude.summary.lower() in (tc.description or "").lower()
                )
                if not has_negative:
                    violations.append(
                        error(
                            "DES-S03",
                            f"exclude {exclude.id} for {sem_id} lacks negative TC",
                            field="test_cases",
                        )
                    )

    for sem_id in sem_ids:
        if not any(sem_id in (tc.covers or []) for tc in design.test_cases):
            violations.append(
                error(
                    "DES-S04",
                    f"test_cases.covers missing {sem_id}",
                    field="test_cases",
                )
            )

    for item in design.error_catalog:
        when = item.when or ""
        message = item.message or ""
        blob = f"{when} {message}"
        if not re.search(r"format|input|输入", blob, re.IGNORECASE):
            continue
        if _LITERAL_EXAMPLE_RE.search(blob) and not _DIMENSION_WORDS_RE.search(blob):
            violations.append(
                warn(
                    "DES-S02",
                    f"error {item.code} message anchors a single literal example",
                    path=f"/error_catalog/{item.code}",
                    field="message",
                )
            )

    return violations
