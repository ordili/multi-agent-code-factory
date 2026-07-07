"""Pydantic schemas used for LLM structured output (agent-specific)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from multi_agent_code_factory.schemas.design import DesignArtifact


class ArchitectLLMOutput(BaseModel):
    design: DesignArtifact
    flow_mmd: str = Field(
        description="Mermaid diagram for flow.mmd (sequence or flowchart)"
    )


class SourceFileWrite(BaseModel):
    path: str = Field(description="Relative path under code_root")
    content: str = Field(description="Full file contents")


class DeveloperLLMOutput(BaseModel):
    tasks_completed: list[str] = Field(
        default_factory=list,
        description="dev_task ids completed in this pass",
    )
    source_files: list[SourceFileWrite] = Field(
        default_factory=list,
        description="Files to create or overwrite under code_root",
    )
    notes: str | None = None
