"""Foundry ``forge test --json`` output parser."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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

_FAILURE_STATUSES = frozenset({"failure", "fail", "revert", "panic"})


def _extract_json_object(text: str) -> dict[str, Any] | None:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        payload = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _test_passed(result: dict[str, Any]) -> bool | None:
    if "success" in result:
        return bool(result.get("success"))
    status = result.get("status")
    if isinstance(status, str):
        normalized = status.strip().lower()
        if normalized in {"success", "pass", "passed"}:
            return True
        if normalized in _FAILURE_STATUSES:
            return False
        if normalized == "skip":
            return None
    return None


def _parse_forge_payload(
    payload: dict[str, Any],
) -> tuple[TestSummary, list[TestFailure]]:
    passed = failed = skipped = 0
    failures: list[TestFailure] = []

    for suite_path, suite in payload.items():
        if not isinstance(suite, dict):
            continue
        test_results = suite.get("test_results")
        if not isinstance(test_results, dict):
            continue
        for test_name, test_result in test_results.items():
            if not isinstance(test_result, dict):
                continue
            test_id = f"{suite_path}::{test_name}"
            outcome = _test_passed(test_result)
            if outcome is None:
                skipped += 1
                continue
            if outcome:
                passed += 1
                continue
            failed += 1
            reason = test_result.get("reason")
            message = (
                reason if isinstance(reason, str) and reason.strip() else "test failed"
            )
            failures.append(
                TestFailure(
                    test_id=test_id,
                    suite=str(suite_path),
                    name=str(test_name),
                    message=message,
                )
            )

    total = passed + failed + skipped
    return TestSummary(
        total=total, passed=passed, failed=failed, skipped=skipped
    ), failures


def parse_forge_json(
    result: CommandResult,
    profile: ProfileConfig,
    code_root: Path,
) -> TestReport:
    """Parse Foundry JSON test output into a TestReport."""
    del code_root
    combined = "\n".join(part for part in (result.stdout, result.stderr) if part)
    payload = _extract_json_object(combined)
    if payload is None:
        passed = result.exit_code == 0
        summary = TestSummary(
            total=0 if passed else 1,
            passed=1 if passed else 0,
            failed=0 if passed else 1,
            skipped=0,
        )
        failures: list[TestFailure] = []
        if not passed:
            failures.append(
                TestFailure(
                    test_id="forge_json_invalid",
                    message="could not parse forge test --json output",
                )
            )
        return build_test_report(
            result,
            profile,
            parser="forge_json",
            summary=summary,
            failures=failures,
        )

    summary, failures = _parse_forge_payload(payload)
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
                    test_id="forge_json_empty",
                    message="forge JSON contained no test_results entries",
                )
            ]

    return build_test_report(
        result,
        profile,
        parser="forge_json",
        summary=summary,
        failures=failures,
    )
