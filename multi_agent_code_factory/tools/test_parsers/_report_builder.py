"""Shared helpers for building TestReport from command output."""

from __future__ import annotations

from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.schemas.test_report import (
    TestFailure,
    TestReport,
    TestSummary,
)
from multi_agent_code_factory.tools.test_parsers._types import CommandResult

_OUTPUT_TAIL_LIMIT = 4000


def raw_output_tail(result: CommandResult, *, passed: bool) -> str | None:
    if passed:
        return None
    combined = "\n".join(part for part in (result.stdout, result.stderr) if part)
    tail = combined.strip()
    if len(tail) > _OUTPUT_TAIL_LIMIT:
        tail = tail[-_OUTPUT_TAIL_LIMIT:]
    return tail or None


def build_test_report(
    result: CommandResult,
    profile: ProfileConfig,
    *,
    parser: str,
    summary: TestSummary,
    failures: list[TestFailure],
) -> TestReport:
    passed = result.exit_code == 0 and summary.failed == 0 and not failures
    return TestReport(
        version="1",
        passed=passed,
        exit_code=result.exit_code,
        summary=summary,
        failures=failures,
        duration_sec=result.duration_sec,
        command=result.command,
        parser=parser,
        language=profile.language,
        raw_output_tail=raw_output_tail(result, passed=passed),
    )
