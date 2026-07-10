from __future__ import annotations

from pathlib import Path

from multi_agent_code_factory.agents.llm.prompt.validation_feedback import (
    format_design_validation_feedback,
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
from multi_agent_code_factory.schemas.spec import SpecArtifact
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
    raw = load_snippet_json(snippets_dir, "spec-default.json")
    raw["scope_out"] = ["web ui"]
    spec = SpecArtifact.model_validate(raw)

    enriched = enrich_design_for_validation(design, spec=spec)

    assert enriched.non_goals == ["web ui"]
    assert enriched.context_view == ContextView(actors=["Core"])
    assert enriched.architecture is not None
    assert enriched.architecture.solution_strategy.strip()
    assert enriched.cross_cutting == {}
    assert enriched.traceability[0].spec_ref_id == "feat-01"


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
    assert "non_goals must not be empty" in feedback
