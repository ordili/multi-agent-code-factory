"""Agent 专用 LLM 结构化输出 Pydantic schema。"""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import BaseModel, Field

from multi_agent_code_factory.schemas.design import DesignArtifact


class MermaidFileWrite(BaseModel):
    """Run 目录下的单个 Mermaid 文件。"""

    path: str = Field(description="Relative path under run directory, e.g. flow.mmd")
    content: str = Field(description="Mermaid diagram source")


class ArchitectLLMOutput(BaseModel):
    """Architect LLM 返回：设计产物 + Mermaid 流程图。"""

    __llm_example__: ClassVar[dict[str, Any]] = {
        "design": DesignArtifact.__llm_example__,
        "mmd_files": [],
    }

    # 仅当 spec 有持久化或主动需要图时追加；无状态 CLI 保持 mmd_files=[]、diagrams=[]
    __llm_example_supplement__: ClassVar[str] = (
        "When spec implies persistence OR you add design.diagrams[], also set:\n"
        '  design.diagrams: [{"path":"flow.mmd","kind":"sequence"},'
        '{"path":"flow.mmd","kind":"flowchart"}]\n'
        '  mmd_files: [{"path":"flow.mmd","content":"sequenceDiagram\\n'
        "  participant User\\n  participant CliEntry\\n  participant CalcCore\\n"
        "  User->>CliEntry: request\\n  CliEntry->>CalcCore: evaluate\\n"
        'flowchart LR\\n  CliEntry --> CalcCore"}]\n'
        "Use modules[].name as Mermaid participants. Omit entirely for stateless CLI."
    )

    design: DesignArtifact
    flow_mmd: str | None = Field(
        default=None,
        description="Legacy single-file Mermaid content for flow.mmd",
    )
    mmd_files: list[MermaidFileWrite] = Field(
        default_factory=list,
        description="One or more *.mmd files (preferred over flow_mmd)",
    )


class SourceFileWrite(BaseModel):
    """Developer 待写入的单个源文件。"""

    path: str = Field(description="Relative path under code_root")
    content: str = Field(description="Full file contents")


class DeveloperLLMOutput(BaseModel):
    """Developer LLM 返回：已完成任务与待写入源文件。"""

    __llm_example__: ClassVar[dict[str, Any]] = {
        "tasks_completed": ["T1"],
        "source_files": [
            {
                "path": "src/todo_store.py",
                "content": "def load(): ...\n",
            }
        ],
        "notes": "Initial store module",
    }

    tasks_completed: list[str] = Field(
        default_factory=list,
        description="dev_task ids completed in this pass",
    )
    source_files: list[SourceFileWrite] = Field(
        default_factory=list,
        description="Files to create or overwrite under code_root",
    )
    notes: str | None = None
