"""Go test JSON stream parser (``go test -json``)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.schemas.test_report import (
    TestFailure,
    TestReport,
    TestSummary,
)
from multi_agent_code_factory.tools.test_parsers._report_builder import (
    build_test_report,
)
from multi_agent_code_factory.tools.test_parsers._types import CommandResult

_GO_FILE_LINE_RE = re.compile(
    r"(?P<file>[\w./\\-]+\.go):(?P<line>\d+)",
)


def _iter_json_lines(text: str) -> list[dict]:
    records: list[dict] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("{"):
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            records.append(payload)
    return records


def _first_file_line(output: str) -> tuple[str | None, int | None]:
    for match in _GO_FILE_LINE_RE.finditer(output):
        return match.group("file"), int(match.group("line"))
    return None, None


def _parse_go_test_events(
    records: list[dict],
) -> tuple[TestSummary, list[TestFailure]]:
    passed = failed = skipped = 0
    failures: list[TestFailure] = []
    outputs: dict[str, list[str]] = {}

    for record in records:
        action = record.get("Action") or record.get("action")
        if not isinstance(action, str):
            continue
        test_name = record.get("Test") or record.get("test")
        pkg = record.get("Package") or record.get("package") or ""
        test_id = f"{pkg}::{test_name}" if test_name else str(pkg or "unknown")

        if action == "output" and isinstance(test_name, str):
            output = record.get("Output")
            if isinstance(output, str):
                outputs.setdefault(test_name, []).append(output)
            continue

        if action == "pass":
            passed += 1
            continue
        if action == "skip":
            skipped += 1
            continue
        if action != "fail":
            continue

        failed += 1
        combined_output = "".join(outputs.get(str(test_name), []))
        message = "test failed"
        if combined_output.strip():
            message = combined_output.strip().splitlines()[-1][:500]
        file_path, line = _first_file_line(combined_output)
        failures.append(
            TestFailure(
                test_id=test_id,
                name=str(test_name) if test_name else None,
                message=message,
                file=file_path,
                line=line,
                output=combined_output or None,
            )
        )

    total = passed + failed + skipped
    return TestSummary(
        total=total, passed=passed, failed=failed, skipped=skipped
    ), failures


def parse_go_json(
    result: CommandResult,
    profile: ProfileConfig,
    code_root: Path,
) -> TestReport:
    """Parse ``go test -json`` NDJSON output into a TestReport."""
    del code_root
    combined = "\n".join(part for part in (result.stdout, result.stderr) if part)
    records = _iter_json_lines(combined)
    summary, failures = _parse_go_test_events(records)

    if summary.total == 0:
        passed = result.exit_code == 0
        summary = TestSummary(
            total=0 if passed else 1,
            passed=1 if passed else 0,
            failed=0 if passed else 1,
            skipped=0,
        )
        if not passed:
            failures = [
                TestFailure(
                    test_id="go_json_empty",
                    message="no go test JSON events found in command output",
                )
            ]

    return build_test_report(
        result,
        profile,
        parser="go_json",
        summary=summary,
        failures=failures,
    )
