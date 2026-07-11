"""执行 Profile 工具链中的 test_command 并生成 TestReport。"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.schemas.dev_manifest import DevManifest
from multi_agent_code_factory.schemas.prd import PrdArtifact
from multi_agent_code_factory.schemas.test_report import (
    AcceptanceTraceItem,
    CoverageReport,
    TestReport,
)
from multi_agent_code_factory.tools.ac_traceability import (
    compute_acceptance_traceability,
    traceability_blocks_pass,
)
from multi_agent_code_factory.tools.run_coverage import run_coverage
from multi_agent_code_factory.tools.test_parsers._types import CommandResult
from multi_agent_code_factory.tools.test_parsers.registry import get_parser
from multi_agent_code_factory.tools.tests_missing import detect_tests_missing


def _run_shell(command: str, cwd: Path) -> CommandResult:
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=cwd,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    duration = time.perf_counter() - started
    return CommandResult(
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        duration_sec=duration,
        command=command,
    )


def _toolchain_ok(report: TestReport) -> bool:
    return report.exit_code == 0 and report.summary.failed == 0


def _finalize_test_report(
    report: TestReport,
    *,
    tests_missing: list[str],
    profile: ProfileConfig,
    coverage: CoverageReport | None = None,
    acceptance_traceability: list[AcceptanceTraceItem] | None = None,
) -> TestReport:
    """合并工具链、tests_missing、coverage 与 AC 追溯策略，写入 passed。"""
    tests_cfg = profile.tests_missing
    coverage_cfg = profile.coverage
    trace_cfg = profile.acceptance_traceability

    passed = _toolchain_ok(report)
    if passed and tests_missing and tests_cfg.enabled and tests_cfg.block_on:
        passed = False
    if (
        passed
        and coverage is not None
        and coverage_cfg.enabled
        and coverage_cfg.block_on
        and not coverage.passed
    ):
        passed = False
    if (
        passed
        and acceptance_traceability
        and trace_cfg.enabled
        and traceability_blocks_pass(
            acceptance_traceability,
            block_on=trace_cfg.block_on,
        )
    ):
        passed = False

    update: dict[str, object] = {"passed": passed}
    if tests_missing:
        update["tests_missing"] = tests_missing
    if coverage is not None:
        update["coverage"] = coverage
    if acceptance_traceability:
        update["acceptance_traceability"] = acceptance_traceability
    return report.model_copy(update=update)


def run_tests(
    profile: ProfileConfig,
    *,
    code_root: Path | None = None,
    dev_manifest: DevManifest | None = None,
    design: DesignArtifact | None = None,
    prd: PrdArtifact | None = None,
) -> TestReport:
    """在 code_root 下依次执行 setup/build/test/coverage 并解析输出为 TestReport。"""
    cwd = (code_root or profile.code_root).resolve()
    cwd.mkdir(parents=True, exist_ok=True)

    tests_missing = detect_tests_missing(
        profile,
        cwd,
        dev_manifest=dev_manifest,
        design=design,
    )

    toolchain = profile.toolchain
    if toolchain.setup:
        setup = _run_shell(toolchain.setup, cwd)
        if setup.exit_code != 0:
            parser = get_parser("exit_code_only")
            return _finalize_test_report(
                parser(setup, profile, cwd),
                tests_missing=tests_missing,
                profile=profile,
            )

    if toolchain.build:
        build = _run_shell(toolchain.build, cwd)
        if build.exit_code != 0:
            parser = get_parser("exit_code_only")
            return _finalize_test_report(
                parser(build, profile, cwd),
                tests_missing=tests_missing,
                profile=profile,
            )

    test_result = _run_shell(toolchain.test_command, cwd)
    parser = get_parser(toolchain.test_parser)
    report = parser(test_result, profile, cwd)

    coverage = run_coverage(profile, code_root=cwd)

    acceptance_traceability: list[AcceptanceTraceItem] | None = None
    trace_cfg = profile.acceptance_traceability
    if trace_cfg.enabled and prd is not None and design is not None:
        acceptance_traceability = compute_acceptance_traceability(
            prd,
            design,
            toolchain_ok=_toolchain_ok(report),
        )

    return _finalize_test_report(
        report,
        tests_missing=tests_missing,
        profile=profile,
        coverage=coverage,
        acceptance_traceability=acceptance_traceability,
    )
