"""Cargo test JSON stream parser (``cargo test --message-format=json``)."""

from __future__ import annotations

import json
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


def _parse_cargo_test_events(
    records: list[dict],
) -> tuple[TestSummary, list[TestFailure]]:
    passed = failed = skipped = 0
    failures: list[TestFailure] = []

    for record in records:
        if record.get("reason") != "test" or record.get("type") != "test":
            continue
        event = record.get("event")
        name = str(record.get("name") or "unknown")
        if event == "ok":
            passed += 1
            continue
        if event in {"ignored", "skipped"}:
            skipped += 1
            continue
        if event == "failed":
            failed += 1
            stdout = record.get("stdout")
            message = "test failed"
            if isinstance(stdout, str) and stdout.strip():
                message = stdout.strip().splitlines()[0][:500]
            failures.append(
                TestFailure(
                    test_id=name,
                    name=name,
                    message=message,
                    output=stdout if isinstance(stdout, str) else None,
                )
            )

    total = passed + failed + skipped
    return TestSummary(
        total=total, passed=passed, failed=failed, skipped=skipped
    ), failures


def parse_cargo_json(
    result: CommandResult,
    profile: ProfileConfig,
    code_root: Path,
) -> TestReport:
    """Parse Cargo test NDJSON output into a TestReport."""
    del code_root
    combined = "\n".join(part for part in (result.stdout, result.stderr) if part)
    records = _iter_json_lines(combined)
    summary, failures = _parse_cargo_test_events(records)

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
                    test_id="cargo_json_empty",
                    message="no cargo test JSON events found in command output",
                )
            ]

    return build_test_report(
        result,
        profile,
        parser="cargo_json",
        summary=summary,
        failures=failures,
    )
