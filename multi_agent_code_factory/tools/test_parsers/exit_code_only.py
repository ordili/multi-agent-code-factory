"""Exit-code-only test parser fallback."""

from __future__ import annotations

from pathlib import Path

from multi_agent_code_factory.profiles import ProfileConfig
from multi_agent_code_factory.schemas.test_report import (
    TestFailure,
    TestReport,
    TestSummary,
)
from multi_agent_code_factory.tools.test_parsers._types import CommandResult

_OUTPUT_TAIL_LIMIT = 4000


def parse_exit_code_only(
    result: CommandResult,
    profile: ProfileConfig,
    code_root: Path,
) -> TestReport:
    del code_root
    passed = result.exit_code == 0
    failures: list[TestFailure] = []
    if not passed:
        tail = (result.stderr or result.stdout or "").strip()
        if len(tail) > _OUTPUT_TAIL_LIMIT:
            tail = tail[-_OUTPUT_TAIL_LIMIT:]
        failures.append(
            TestFailure(
                test_id="exit_code",
                message=f"command exited with code {result.exit_code}",
                output=tail or None,
            )
        )
    return TestReport(
        version="1",
        passed=passed,
        exit_code=result.exit_code,
        summary=TestSummary(
            total=0 if passed else 1,
            passed=1 if passed else 0,
            failed=0 if passed else 1,
            skipped=0,
        ),
        failures=failures,
        duration_sec=result.duration_sec,
        command=result.command,
        parser="exit_code_only",
        language=profile.language,
        raw_output_tail=(result.stderr or result.stdout or "")[-_OUTPUT_TAIL_LIMIT:]
        if not passed
        else None,
    )
