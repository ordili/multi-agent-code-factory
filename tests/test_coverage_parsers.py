"""Coverage parser unit tests."""

from __future__ import annotations

import json
from pathlib import Path

from multi_agent_code_factory.profile_config.models import (
    CoverageConfig,
    CoverageThresholds,
    ProfileConfig,
    ToolchainConfig,
)
from multi_agent_code_factory.tools.coverage_parsers._types import CoverageCommandResult
from multi_agent_code_factory.tools.coverage_parsers.go_cover import parse_go_cover
from multi_agent_code_factory.tools.coverage_parsers.llvm_cov_json import (
    parse_llvm_cov_json,
)
from multi_agent_code_factory.tools.coverage_parsers.pytest_cov_json import (
    parse_pytest_cov_json,
)
from multi_agent_code_factory.tools.coverage_parsers.registry import get_coverage_parser


def _profile(
    code_root: Path,
    *,
    coverage: CoverageConfig,
) -> ProfileConfig:
    return ProfileConfig(
        id="python",
        language="python",
        code_root=code_root,
        code_root_raw=str(code_root),
        prompts_dir=code_root,
        tools=[],
        toolchain=ToolchainConfig(test_command="true"),
        coverage=coverage,
    )


def _result(exit_code: int = 0, *, stdout: str = "") -> CoverageCommandResult:
    return CoverageCommandResult(
        exit_code=exit_code,
        stdout=stdout,
        stderr="",
        command="cov",
    )


def test_pytest_cov_json_parser_reads_totals(tmp_path: Path) -> None:
    payload = {
        "totals": {
            "covered_lines": 42,
            "num_statements": 50,
            "percent_covered": 84.0,
        }
    }
    (tmp_path / "coverage.json").write_text(json.dumps(payload), encoding="utf-8")
    profile = _profile(
        tmp_path,
        coverage=CoverageConfig(
            enabled=True,
            command="pytest --cov",
            parser="pytest_cov_json",
            artifacts=["coverage.json"],
            thresholds=CoverageThresholds(line_percent=70),
        ),
    )
    report = parse_pytest_cov_json(_result(), profile, tmp_path)
    assert report.line_percent == 84.0
    assert report.lines_covered == 42
    assert report.lines_total == 50
    assert report.passed is True
    assert report.tool == "pytest-cov"


def test_pytest_cov_json_fails_threshold(tmp_path: Path) -> None:
    payload = {
        "totals": {"percent_covered": 62.0, "covered_lines": 62, "num_statements": 100}
    }
    (tmp_path / "coverage.json").write_text(json.dumps(payload), encoding="utf-8")
    profile = _profile(
        tmp_path,
        coverage=CoverageConfig(
            enabled=True,
            command="pytest --cov",
            parser="pytest_cov_json",
            artifacts=["coverage.json"],
            thresholds=CoverageThresholds(line_percent=70),
        ),
    )
    report = parse_pytest_cov_json(_result(), profile, tmp_path)
    assert report.passed is False
    assert any("62.0%" in item for item in report.violations)


def test_llvm_cov_json_parser_reads_summary() -> None:
    stdout = json.dumps(
        {
            "data": [
                {
                    "summary": {
                        "lines": {"count": 100, "covered": 85, "percent": 85.0},
                        "branches": {"count": 20, "covered": 10, "percent": 50.0},
                    }
                }
            ]
        }
    )
    profile = ProfileConfig(
        id="rust",
        language="rust",
        code_root=Path("."),
        code_root_raw=".",
        prompts_dir=Path("."),
        tools=[],
        toolchain=ToolchainConfig(test_command="true"),
        coverage=CoverageConfig(
            enabled=True,
            command="cargo llvm-cov report --summary-only --json",
            parser="llvm_cov_json",
            thresholds=CoverageThresholds(line_percent=80, branch_percent=60),
        ),
    )
    report = parse_llvm_cov_json(_result(stdout=stdout), profile, Path("."))
    assert report.line_percent == 85.0
    assert report.branch_percent == 50.0
    assert report.passed is False
    assert any("branch" in item for item in report.violations)


def test_go_cover_parser_parses_total_line(tmp_path: Path) -> None:
    cover_file = tmp_path / "coverage.out"
    cover_file.write_text("mode: set\n", encoding="utf-8")
    profile = _profile(
        tmp_path,
        coverage=CoverageConfig(
            enabled=True,
            command="go test -coverprofile=coverage.out ./...",
            parser="go_cover",
            artifacts=["coverage.out"],
            thresholds=CoverageThresholds(line_percent=70),
        ),
    )

    def fake_run(command: str, cwd: Path, **kwargs: object) -> object:
        del command, cwd, kwargs

        class Completed:
            returncode = 0
            stdout = "total:\t(statements)\t88.5%\n"
            stderr = ""

        return Completed()

    import multi_agent_code_factory.tools.coverage_parsers.go_cover as go_cover_mod

    original = go_cover_mod.subprocess.run
    go_cover_mod.subprocess.run = fake_run  # type: ignore[assignment]
    try:
        report = parse_go_cover(_result(), profile, tmp_path)
    finally:
        go_cover_mod.subprocess.run = original

    assert report.line_percent == 88.5
    assert report.passed is True


def test_coverage_parser_registry() -> None:
    assert get_coverage_parser("pytest_cov_json") is parse_pytest_cov_json
    assert get_coverage_parser("go_cover") is parse_go_cover
    assert get_coverage_parser("llvm_cov_json") is parse_llvm_cov_json
