from __future__ import annotations

import json
from pathlib import Path

from multi_agent_code_factory.profile_config.models import (
    CoverageConfig,
    CoverageThresholds,
    ProfileConfig,
    ToolchainConfig,
)
from multi_agent_code_factory.profile_config.models import (
    TestsMissingConfig as TestsMissingPolicy,
)
from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.schemas.dev_manifest import (
    ChangedFile,
    ChangeType,
    DevManifest,
)
from multi_agent_code_factory.tools.run_tests import run_tests


def _design(*paths: str) -> DesignArtifact:
    return DesignArtifact.model_validate(
        {
            "version": "1",
            "title": "t",
            "spec_ref": "t",
            "dev_tasks": [
                {"id": f"T{i + 1}", "path": path, "description": "task"}
                for i, path in enumerate(paths)
            ],
        }
    )


def _mini_profile(
    code_root: Path,
    *,
    coverage: CoverageConfig,
    tests_missing_block_on: bool = False,
) -> ProfileConfig:
    return ProfileConfig(
        id="pytest-mini",
        language="python",
        code_root=code_root,
        code_root_raw=str(code_root),
        prompts_dir=code_root,
        tools=["run_tests"],
        toolchain=ToolchainConfig(
            test_command="python -m pytest -q --junitxml=reports/junit.xml",
            test_parser="junit_xml",
            test_artifacts=["reports/junit.xml"],
            test_dir_glob="tests/**",
        ),
        tests_missing=TestsMissingPolicy(block_on=tests_missing_block_on),
        coverage=coverage,
    )


def _write_passing_pytest_project(code_root: Path) -> None:
    src = code_root / "src"
    tests = code_root / "tests"
    reports = code_root / "reports"
    src.mkdir(parents=True)
    tests.mkdir(parents=True)
    reports.mkdir(parents=True)
    (src / "app.py").write_text("def add(a, b): return a + b\n", encoding="utf-8")
    (tests / "test_app.py").write_text(
        "def test_add():\n    assert True\n", encoding="utf-8"
    )


def test_run_tests_includes_coverage_when_enabled(tmp_path: Path) -> None:
    code_root = tmp_path / "project"
    _write_passing_pytest_project(code_root)
    (code_root / "coverage.json").write_text(
        json.dumps(
            {
                "totals": {
                    "covered_lines": 1,
                    "num_statements": 1,
                    "percent_covered": 100.0,
                }
            }
        ),
        encoding="utf-8",
    )

    profile = _mini_profile(
        code_root,
        coverage=CoverageConfig(
            enabled=True,
            block_on=False,
            command="python -c \"print('cov')\"",
            parser="pytest_cov_json",
            artifacts=["coverage.json"],
            thresholds=CoverageThresholds(line_percent=70),
        ),
        tests_missing_block_on=False,
    )
    manifest = DevManifest(
        version="1",
        changed_files=[
            ChangedFile(path="src/app.py", change_type=ChangeType.CREATE),
            ChangedFile(path="tests/test_app.py", change_type=ChangeType.CREATE),
        ],
    )

    report = run_tests(profile, dev_manifest=manifest, design=_design("src/app.py"))
    assert report.passed is True
    assert report.coverage is not None
    assert report.coverage.line_percent == 100.0
    assert report.coverage.passed is True


def test_run_tests_coverage_block_on_fails_passed(tmp_path: Path) -> None:
    code_root = tmp_path / "project"
    _write_passing_pytest_project(code_root)
    (code_root / "coverage.json").write_text(
        json.dumps(
            {
                "totals": {
                    "covered_lines": 1,
                    "num_statements": 2,
                    "percent_covered": 50.0,
                }
            }
        ),
        encoding="utf-8",
    )

    profile = _mini_profile(
        code_root,
        coverage=CoverageConfig(
            enabled=True,
            block_on=True,
            command="python -c \"print('cov')\"",
            parser="pytest_cov_json",
            artifacts=["coverage.json"],
            thresholds=CoverageThresholds(line_percent=70),
        ),
    )
    manifest = DevManifest(
        version="1",
        changed_files=[
            ChangedFile(path="src/app.py", change_type=ChangeType.CREATE),
            ChangedFile(path="tests/test_app.py", change_type=ChangeType.CREATE),
        ],
    )

    report = run_tests(profile, dev_manifest=manifest, design=_design("src/app.py"))
    assert report.summary.failed == 0
    assert report.coverage is not None
    assert report.coverage.passed is False
    assert report.passed is False
