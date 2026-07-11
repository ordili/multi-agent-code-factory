"""QA 结果诊断：失败原因分类与结构化日志。"""

from __future__ import annotations

import logging

from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.schemas.test_report import TestFailure, TestReport
from multi_agent_code_factory.tools.ac_traceability import traceability_blocks_pass

_MESSAGE_LIMIT = 200
_OUTPUT_TAIL_LIMIT = 120


def toolchain_ok(report: TestReport) -> bool:
    """工具链测试是否通过（exit_code 与 failed 计数）。"""
    return report.exit_code == 0 and report.summary.failed == 0


def classify_qa_block_reason(
    report: TestReport,
    profile: ProfileConfig | None = None,
) -> str:
    """返回 QA 未通过的主因（passed=true 时返回 ``passed``）。"""
    if report.passed:
        return "passed"
    if not toolchain_ok(report):
        return "toolchain"
    if profile is not None:
        tests_cfg = profile.tests_missing
        if report.tests_missing and tests_cfg.enabled and tests_cfg.block_on:
            return "tests_missing"
        coverage = report.coverage
        coverage_cfg = profile.coverage
        if (
            coverage is not None
            and coverage_cfg.enabled
            and coverage_cfg.block_on
            and not coverage.passed
        ):
            return "coverage"
        trace_cfg = profile.acceptance_traceability
        if (
            report.acceptance_traceability
            and trace_cfg.enabled
            and traceability_blocks_pass(
                report.acceptance_traceability,
                block_on=trace_cfg.block_on,
            )
        ):
            return "acceptance_traceability"
        return "unknown"
    if report.tests_missing:
        return "tests_missing"
    if report.coverage is not None and not report.coverage.passed:
        return "coverage"
    if report.acceptance_traceability:
        unmet = [
            item.id
            for item in report.acceptance_traceability
            if item.designed and not item.met
        ]
        if unmet:
            return "acceptance_traceability"
    return "unknown"


def qa_failure_snapshot_name(impl_retry_count: int) -> str:
    """失败 QA 快照文件名（保留每次 impl 环的 test_report）。"""
    return f"test_report.impl-{impl_retry_count}.json"


def _truncate(text: str, limit: int) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3] + "..."


def _quote(text: str) -> str:
    escaped = text.replace('"', "'")
    return f'"{escaped}"'


def format_failure_details(report: TestReport) -> str:
    """格式化首条失败、输出尾或非阻塞门禁详情，供日志一行展示。"""
    parts: list[str] = []
    if report.failures:
        parts.append(_format_test_failure(report.failures[0]))
    elif report.raw_output_tail:
        tail = _quote(_truncate(report.raw_output_tail, _OUTPUT_TAIL_LIMIT))
        parts.append(f"output_tail={tail}")
    if report.tests_missing:
        parts.append(f"tests_missing={report.tests_missing}")
    if report.coverage is not None and not report.coverage.passed:
        parts.append(f"coverage_violations={report.coverage.violations}")
    if report.acceptance_traceability:
        unmet = [
            item.id
            for item in report.acceptance_traceability
            if item.designed and not item.met
        ]
        if unmet:
            parts.append(f"acceptance_unmet={unmet}")
    return " ".join(parts)


def _format_test_failure(failure: TestFailure) -> str:
    parts: list[str] = []
    if failure.test_id:
        parts.append(f"first_test={failure.test_id!r}")
    if failure.file:
        loc = failure.file
        if failure.line is not None:
            loc = f"{loc}:{failure.line}"
        parts.append(f"file={loc!r}")
    if failure.message:
        parts.append(f"message={_quote(_truncate(failure.message, _MESSAGE_LIMIT))}")
    return " ".join(parts)


def log_qa_outcome(
    logger: logging.Logger,
    report: TestReport,
    profile: ProfileConfig,
    *,
    impl_retry_count: int,
    snapshot: str | None = None,
) -> None:
    """记录 QA 通过/阻塞结果（warn.log 可定位失败用例与原因）。"""
    if report.passed:
        logger.info("qa tests passed impl_retry=%s", impl_retry_count)
        if report.acceptance_traceability:
            unmet = [
                item.id
                for item in report.acceptance_traceability
                if item.designed and not item.met
            ]
            if unmet:
                logger.warning(
                    "qa acceptance_traceability unmet ids=%s block_on=%s impl_retry=%s",
                    unmet,
                    profile.acceptance_traceability.block_on,
                    impl_retry_count,
                )
        if report.tests_missing:
            logger.warning(
                "qa toolchain green with tests_missing count=%s paths=%s "
                "block_on=%s impl_retry=%s",
                len(report.tests_missing),
                report.tests_missing,
                profile.tests_missing.block_on,
                impl_retry_count,
            )
        if report.coverage is not None and not report.coverage.passed:
            logger.warning(
                "qa toolchain green with coverage violations block_on=%s "
                "violations=%s impl_retry=%s",
                profile.coverage.block_on,
                report.coverage.violations,
                impl_retry_count,
            )
        return

    reason = classify_qa_block_reason(report, profile)
    details = format_failure_details(report)
    logger.warning(
        "qa blocked reason=%s exit_code=%s summary_passed=%s summary_failed=%s "
        "command=%r impl_retry=%s%s%s",
        reason,
        report.exit_code,
        report.summary.passed,
        report.summary.failed,
        report.command,
        impl_retry_count,
        f" {details}" if details else "",
        f" snapshot={snapshot}" if snapshot else "",
    )
