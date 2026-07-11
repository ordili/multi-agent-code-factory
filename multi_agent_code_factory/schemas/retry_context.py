"""Developer 重试上下文 Schema（RetryBundle / FailureContext）。"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field

from multi_agent_code_factory.schemas.dev_manifest import DevManifest
from multi_agent_code_factory.schemas.review import Finding
from multi_agent_code_factory.schemas.test_report import TestReport


class StackFrameRole(StrEnum):
    ROOT_CAUSE = "root_cause"
    CALLER = "caller"
    TEST = "test"


class StackFrame(BaseModel):
    order: int = Field(ge=0)
    role: StackFrameRole
    file: str
    line: int = Field(ge=1)
    function: str | None = None


class FunctionSnippet(BaseModel):
    path: str
    function: str | None = None
    frame_order: int = Field(ge=0)
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)
    total_file_lines: int | None = Field(default=None, ge=0)
    truncated: bool = False
    content: str


class OmittedFrameReason(StrEnum):
    BUDGET_EXHAUSTED = "budget_exhausted"
    FRAMEWORK_FILTERED = "framework_filtered"
    READ_FAILED = "read_failed"
    NO_FUNCTION_BOUND = "no_function_bound"


class OmittedFrame(BaseModel):
    file: str
    function: str | None = None
    line: int | None = Field(default=None, ge=1)
    reason: OmittedFrameReason


class FailureContext(BaseModel):
    test_id: str
    message: str
    traceback_parse_ok: bool = False
    call_path: list[StackFrame] = Field(default_factory=list)
    snippets: list[FunctionSnippet] = Field(default_factory=list)
    omitted_frames: list[OmittedFrame] = Field(default_factory=list)


class ReviewFeedback(BaseModel):
    approved: bool
    summary: str
    findings: list[Finding] = Field(default_factory=list)


RetryCause = Literal["qa_failure", "review_rejection", "both"]


class RetryBundle(BaseModel):
    retry_cause: RetryCause
    test_report: TestReport | None = None
    review_feedback: ReviewFeedback | None = None
    dev_manifest: DevManifest
    reflection: dict[str, Any] | None = None
    failure_contexts: list[FailureContext] = Field(default_factory=list)
    code_snippets_omitted_paths: list[str] = Field(default_factory=list)
