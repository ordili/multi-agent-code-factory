from __future__ import annotations

from pathlib import Path

from multi_agent_code_factory.config import LoopLimits
from multi_agent_code_factory.profiles import ProfileConfig, ToolchainConfig
from multi_agent_code_factory.tools.run_tests import run_tests
from multi_agent_code_factory.tools.write_artifact import RunArtifactWriter


def test_run_tests_with_pytest_junit(tmp_path: Path) -> None:
    code_root = tmp_path / "project"
    tests_dir = code_root / "tests"
    reports_dir = code_root / "reports"
    tests_dir.mkdir(parents=True)
    reports_dir.mkdir()

    (tests_dir / "test_ok.py").write_text(
        "def test_passes():\n    assert True\n",
        encoding="utf-8",
    )

    profile = ProfileConfig(
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
        ),
    )

    report = run_tests(profile)
    assert report.parser == "junit_xml"
    assert report.passed is True
    assert report.summary.failed == 0
    assert (code_root / "reports" / "junit.xml").is_file()


def test_run_artifact_writer(tmp_path: Path) -> None:
    writer = RunArtifactWriter("demo-task", base_dir=tmp_path / "runs" / "demo-task")
    profile = ProfileConfig(
        id="python",
        language="python",
        code_root=tmp_path / "generated",
        code_root_raw=str(tmp_path / "generated"),
        prompts_dir=tmp_path / "prompts",
        tools=[],
        toolchain=ToolchainConfig(test_command="true"),
    )
    limits = LoopLimits()
    meta = writer.init_run_meta(profile, limits)
    assert meta.task_id == "demo-task"
    assert meta.profile["id"] == "python"
    assert (writer.directory / "run_meta.json").is_file()

    updated = writer.update_meta(impl_retry_count=1)
    assert updated.impl_retry_count == 1
