"""Task-batch 执行计划与 prompt 注入模型。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, computed_field

from multi_agent_code_factory.schemas.design import DevTask, TestCase


class DependencyArtifact(BaseModel):
    path: str
    kind: Literal["signature_stub", "module_header"]
    line_start: int
    line_end: int
    content: str


class TaskBatch(BaseModel):
    index: int
    task_ids: list[str]
    required_paths: list[str]
    dependency_paths: list[str]
    relevant_test_case_ids: list[str]
    estimated_output_lines: int | None = None


class ImplBatch(BaseModel):
    pass_index: int
    pass_total: int
    active_dev_tasks: list[DevTask]
    completed_dev_tasks: list[str]
    required_paths: list[str]
    dependency_artifacts: list[DependencyArtifact]
    relevant_test_cases: list[TestCase]
    omitted_dependencies: list[dict[str, str]]
    closure_note: str = (
        "Implement only impl_batch.required_paths for active_dev_tasks; "
        "do not resend unchanged files from prior batches."
    )


class TaskBatchConfig(BaseModel):
    enabled: bool = False
    threshold: int = Field(default=5, ge=1)
    max_tasks_per_batch: int = Field(default=1, ge=1)
    max_files_per_batch: int = Field(default=8, ge=1)
    max_extra_output_paths: int = Field(default=2, ge=0)
    max_lines_per_file_hint: int = Field(default=400, ge=1)
    max_output_lines_per_batch: int = Field(default=2000, ge=1)
    max_input_lines_per_batch: int = Field(default=2500, ge=1)
    dep_snippet_lines: int = Field(default=60, ge=1)
    require_tests: bool = True

    @computed_field  # type: ignore[prop-decorator]
    @property
    def max_required_paths_per_batch(self) -> int:
        return max(0, self.max_files_per_batch - self.max_extra_output_paths)
