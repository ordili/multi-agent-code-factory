"""Schema hint tests."""

from __future__ import annotations

from multi_agent_code_factory.agents.llm.prompt.schema_hints import (
    json_output_instructions,
)
from multi_agent_code_factory.agents.llm.schemas import (
    ArchitectLLMOutput,
    DeveloperLLMOutput,
)
from multi_agent_code_factory.schemas.review import ReviewReport
from multi_agent_code_factory.schemas.spec import SpecArtifact


def test_json_output_instructions_prefers_registered_example() -> None:
    instructions = json_output_instructions(SpecArtifact)
    assert "Example JSON shape" in instructions
    assert '"title": "CLI Todo App"' in instructions
    assert "JSON schema (follow types strictly)" not in instructions


def test_json_output_instructions_cover_agent_schemas() -> None:
    from multi_agent_code_factory.schemas.design import DesignArtifact

    for schema in (
        SpecArtifact,
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


def test_llm_example_defined_on_domain_schemas() -> None:
    from multi_agent_code_factory.schemas.design import DesignArtifact

    assert isinstance(SpecArtifact.__llm_example__, dict)
    assert isinstance(DesignArtifact.__llm_example__, dict)
    assert isinstance(ReviewReport.__llm_example__, dict)


def test_llm_examples_validate_against_pydantic_models() -> None:
    from multi_agent_code_factory.schemas.design import DesignArtifact

    SpecArtifact.model_validate(SpecArtifact.__llm_example__)
    DesignArtifact.model_validate(DesignArtifact.__llm_example__)
    ArchitectLLMOutput.model_validate(ArchitectLLMOutput.__llm_example__)
    ReviewReport.model_validate(ReviewReport.__llm_example__)
