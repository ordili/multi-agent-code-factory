"""Schema hint tests."""

from __future__ import annotations

from multi_agent_code_factory.agents.llm.prompt.schema_hints import (
    json_output_instructions,
)
from multi_agent_code_factory.agents.llm.schemas import (
    ArchitectLLMOutput,
    DeveloperLLMOutput,
)
from multi_agent_code_factory.schemas.llm_prompt_shape import (
    LlmPromptShape,
    prompt_shape_for_schema,
)
from multi_agent_code_factory.schemas.prd import PrdArtifact
from multi_agent_code_factory.schemas.review import ReviewReport


def test_json_output_instructions_prefers_registered_example() -> None:
    instructions = json_output_instructions(PrdArtifact)
    assert "Example JSON shape" in instructions
    assert '"title": "CLI Todo App"' in instructions
    assert "JSON schema (follow types strictly)" not in instructions


def test_json_output_instructions_cover_agent_schemas() -> None:
    from multi_agent_code_factory.schemas.design import DesignArtifact

    for schema in (
        PrdArtifact,
        DesignArtifact,
        ArchitectLLMOutput,
        DeveloperLLMOutput,
        ReviewReport,
    ):
        instructions = json_output_instructions(schema)
        assert "Example JSON shape" in instructions


def test_architect_instructions_include_diagram_supplement() -> None:
    instructions = json_output_instructions(ArchitectLLMOutput)
    assert "Optional supplement" in instructions
    assert "stateless CLI" in instructions
    assert '"mmd_files": []' in instructions


def test_architect_instructions_include_nfr_and_transaction_shape() -> None:
    instructions = json_output_instructions(ArchitectLLMOutput)
    assert '"non_functional": []' in instructions
    assert '"transaction_constraints": []' in instructions
    assert '"data_model": []' in instructions
    assert '"table_schemas": []' in instructions
    assert '"file_plan": []' in instructions
    assert "Optional supplement" in instructions
    assert '"metric"' in instructions
    assert '"target"' in instructions
    assert '"scope"' in instructions
    assert '"boundary"' in instructions
    assert '"nullable"' in instructions
    assert "success_metrics/KPI" in instructions
    assert "NOT {name}" in instructions
    assert "data_model" in instructions
    assert "table_schemas.columns" in instructions or '"columns":' in instructions


def test_architect_instructions_include_persistence_supplement() -> None:
    instructions = json_output_instructions(ArchitectLLMOutput)
    assert "cross_cutting.test_strategy" in instructions
    assert "file_plan" in instructions
    assert "design_ref" in instructions
    assert "design.background" in instructions
    assert "design.design_goals" in instructions
    assert '"background":' in instructions


def test_architect_design_prompt_shape_includes_readable_design_goals() -> None:
    from multi_agent_code_factory.schemas.design import DesignArtifact

    shape = DesignArtifact.LLM_PROMPT_SHAPE.json_shape
    goals = shape.get("design_goals")
    assert isinstance(goals, list)
    assert goals
    assert all(isinstance(goal, str) and goal.strip() for goal in goals)
    assert not any(
        goal.strip().upper().startswith("FEAT-") and "(" not in goal for goal in goals
    )


def test_architect_design_prompt_shape_includes_background() -> None:
    from multi_agent_code_factory.schemas.design import DesignArtifact

    shape = DesignArtifact.LLM_PROMPT_SHAPE.json_shape
    assert isinstance(shape.get("background"), str)
    assert shape["background"].strip()


def test_llm_prompt_shape_defined_on_domain_schemas() -> None:
    from multi_agent_code_factory.schemas.design import DesignArtifact

    for schema in (PrdArtifact, DesignArtifact, ReviewReport):
        shape = prompt_shape_for_schema(schema)
        assert isinstance(shape, LlmPromptShape)
        assert isinstance(shape.json_shape, dict)


def test_llm_prompt_shapes_validate_against_pydantic_models() -> None:
    from multi_agent_code_factory.schemas.design import DesignArtifact

    PrdArtifact.model_validate(PrdArtifact.LLM_PROMPT_SHAPE.json_shape)
    DesignArtifact.model_validate(DesignArtifact.LLM_PROMPT_SHAPE.json_shape)
    ArchitectLLMOutput.model_validate(ArchitectLLMOutput.LLM_PROMPT_SHAPE.json_shape)
    ReviewReport.model_validate(ReviewReport.LLM_PROMPT_SHAPE.json_shape)
