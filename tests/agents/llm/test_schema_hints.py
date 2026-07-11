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
