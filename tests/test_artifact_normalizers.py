from __future__ import annotations

from pathlib import Path

from multi_agent_code_factory.agents.llm.prompt.validation_feedback import (
    format_design_validation_feedback,
    format_prd_validation_feedback,
)
from multi_agent_code_factory.agents.normalizers.design_enrichment import (
    enrich_design_for_validation,
)
from multi_agent_code_factory.schemas.design import (
    ContextView,
    DesignArtifact,
    DevTask,
    ModuleSpec,
)
from multi_agent_code_factory.schemas.prd import PrdArtifact
from multi_agent_code_factory.schemas.validation_report import (
    ValidationReport,
    ValidationTarget,
    Violation,
)
from multi_agent_code_factory.state import PipelineState

from tests.conftest import load_snippet_json


def _minimal_design(**updates: object) -> DesignArtifact:
    base = DesignArtifact(
        version="1",
        spec_ref="calc",
        revision=1,
        modules=[
            ModuleSpec(
                name="Core",
                path="src/core.py",
                responsibility="logic",
                code_domain="core",
            )
        ],
        dev_tasks=[
            DevTask(
                id="t1",
                path="src/core.py",
                description="implement",
                covers=["feat-01"],
            )
        ],
        traceability=[{"feature_id": "feat-01", "dev_task_ids": ["t1"]}],
    )
    return base.model_copy(update=updates)


def test_enrich_design_fills_required_mvp_fields(snippets_dir: Path) -> None:
    design = _minimal_design(
        non_goals=[],
        context_view=None,
        architecture=None,
        cross_cutting=None,
    )
    raw = load_snippet_json(snippets_dir, "prd-default.json")
    raw["scope_out"] = ["web ui"]
    spec = PrdArtifact.model_validate(raw)

    enriched = enrich_design_for_validation(design, spec=spec)

    assert enriched.non_goals == ["web ui"]
    assert enriched.context_view == ContextView(actors=["Core"])
    assert enriched.architecture is not None
    assert enriched.architecture.solution_strategy.strip()
    assert enriched.cross_cutting == {}
    assert enriched.traceability[0].spec_ref_id == "feat-01"


def test_enrich_design_expands_bare_design_goal_ids(snippets_dir: Path) -> None:
    design = _minimal_design(
        design_goals=["FEAT-1", "US-1"],
    )
    spec = PrdArtifact.model_validate(
        load_snippet_json(snippets_dir, "prd-default.json")
    )

    enriched = enrich_design_for_validation(design, spec=spec)

    assert enriched.design_goals[0].startswith("FEAT-1:")
    assert "add/list" in enriched.design_goals[0]
    assert enriched.design_goals[1].startswith("US-1:")
    assert "（" in enriched.design_goals[1]
    assert enriched.design_goals != ["FEAT-1", "US-1"]


def test_enrich_design_preserves_readable_design_goals(snippets_dir: Path) -> None:
    readable = ["CLI 解析表达式并输出求值结果（FEAT-1）", "异常输入有明确错误提示"]
    design = _minimal_design(design_goals=readable)
    spec = PrdArtifact.model_validate(
        load_snippet_json(snippets_dir, "prd-default.json")
    )

    enriched = enrich_design_for_validation(design, spec=spec)

    assert enriched.design_goals == readable


def test_enrich_design_merges_duplicate_dev_task_paths() -> None:
    design = _minimal_design(
        dev_tasks=[
            DevTask(
                id="t1",
                path="src/core.py",
                description="part one",
                covers=["feat-01"],
            ),
            DevTask(
                id="t2",
                path="src/core.py",
                description="part two with more detail",
                covers=["ac-01"],
            ),
        ]
    )

    enriched = enrich_design_for_validation(design, spec=None)

    assert len(enriched.dev_tasks) == 1
    assert enriched.dev_tasks[0].covers == ["feat-01", "ac-01"]


def test_format_design_validation_feedback_lists_violations() -> None:
    report = ValidationReport(
        version="1",
        target=ValidationTarget.DESIGN,
        passed=False,
        error_count=1,
        warn_count=0,
        violations=[
            Violation(
                rule_id="DES-008",
                severity="error",
                message="non_goals must not be empty",
                field="non_goals",
            )
        ],
    )
    state = PipelineState(
        user_request="calc",
        design_validation=report,
    )

    feedback = format_design_validation_feedback(state)

    assert feedback is not None
    assert "DES-008" in feedback
    assert "(error)" in feedback
    assert "field=non_goals" in feedback
    assert "non_goals must not be empty" in feedback


def test_format_prd_validation_feedback_lists_violations_with_path() -> None:
    report = ValidationReport(
        version="1",
        target=ValidationTarget.PRD,
        passed=False,
        error_count=1,
        warn_count=1,
        violations=[
            Violation(
                rule_id="PRD-017",
                severity="error",
                message="context.storage is required",
                field="storage",
                path="/context/storage",
            ),
            Violation(
                rule_id="PRD-102",
                severity="warn",
                message="P0 user story US-1 not traced",
                field="user_stories",
            ),
        ],
    )
    state = PipelineState(
        user_request="calc",
        prd_validation=report,
    )

    feedback = format_prd_validation_feedback(state)

    assert feedback is not None
    assert "Previous spec failed validation" in feedback
    assert "PRD-017" in feedback
    assert "(error)" in feedback
    assert "path=/context/storage" in feedback
    assert "PRD-102" in feedback
    assert "(warn)" in feedback
    assert feedback.index("PRD-017") < feedback.index("PRD-102")
