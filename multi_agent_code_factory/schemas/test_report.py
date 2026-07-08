"""测试报告（QA 输出）的 Pydantic 模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field

from multi_agent_code_factory.schemas._base import ARTIFACT_VERSION


class TestSummary(BaseModel):
    __test__ = False

    total: int = Field(ge=0)
    passed: int = Field(ge=0)
    failed: int = Field(ge=0)
    skipped: int = Field(ge=0)


class TestFailure(BaseModel):
    test_id: str
    message: str
    suite: str | None = None
    name: str | None = None
    file: str | None = None
    line: int | None = Field(default=None, ge=1)
    output: str | None = None


class TestReport(BaseModel):
    __test__ = False

    version: ARTIFACT_VERSION
    passed: bool
    exit_code: int
    summary: TestSummary
    failures: list[TestFailure] = Field(default_factory=list)
    duration_sec: float = Field(ge=0)
    command: str
    parser: str
    language: str | None = None
    tests_missing: list[str] | None = None
    raw_output_tail: str | None = None
