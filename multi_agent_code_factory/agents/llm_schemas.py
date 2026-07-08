"""Agent 专用 LLM 结构化输出 Pydantic schema。"""

from __future__ import annotations

from pydantic import BaseModel, Field

from multi_agent_code_factory.schemas.design import DesignArtifact


class ArchitectLLMOutput(BaseModel):
    """Architect LLM 返回：设计产物 + Mermaid 流程图。"""

    design: DesignArtifact
    flow_mmd: str = Field(
        description="Mermaid diagram for flow.mmd (sequence or flowchart)"
    )


class SourceFileWrite(BaseModel):
    """Developer 待写入的单个源文件。"""

    path: str = Field(description="Relative path under code_root")
    content: str = Field(description="Full file contents")


class DeveloperLLMOutput(BaseModel):
    """Developer LLM 返回：已完成任务与待写入源文件。"""

    tasks_completed: list[str] = Field(
        default_factory=list,
        description="dev_task ids completed in this pass",
    )
    source_files: list[SourceFileWrite] = Field(
        default_factory=list,
        description="Files to create or overwrite under code_root",
    )
    notes: str | None = None
