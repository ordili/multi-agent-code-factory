from __future__ import annotations

from pathlib import Path

from multi_agent_code_factory.profile_config import ProfileConfig, ToolchainConfig
from multi_agent_code_factory.schemas.dev_manifest import (
    ChangedFile,
    ChangeType,
    DevManifest,
)
from multi_agent_code_factory.tools.tests_missing import detect_tests_missing


def _profile(code_root: Path) -> ProfileConfig:
    return ProfileConfig(
        id="python",
        language="python",
        code_root=code_root,
        code_root_raw=str(code_root),
        prompts_dir=code_root,
        tools=[],
        toolchain=ToolchainConfig(
            test_command="true",
            test_dir_glob="tests/**",
        ),
    )


def test_detect_tests_missing_when_no_test_files(tmp_path: Path) -> None:
    code_root = tmp_path / "project"
    src = code_root / "src"
    src.mkdir(parents=True)
    (src / "todo_store.py").write_text("pass\n", encoding="utf-8")

    manifest = DevManifest(
        version="1",
        changed_files=[
            ChangedFile(path="src/todo_store.py", change_type=ChangeType.CREATE),
        ],
    )

    missing = detect_tests_missing(
        _profile(code_root),
        code_root,
        dev_manifest=manifest,
    )
    assert missing == ["src/todo_store.py"]


def test_detect_tests_missing_resolved_by_test_file(tmp_path: Path) -> None:
    code_root = tmp_path / "project"
    src = code_root / "src"
    tests = code_root / "tests"
    src.mkdir(parents=True)
    tests.mkdir(parents=True)
    (src / "todo_store.py").write_text("pass\n", encoding="utf-8")
    (tests / "test_todo_store.py").write_text("def test_ok(): pass\n", encoding="utf-8")

    manifest = DevManifest(
        version="1",
        changed_files=[
            ChangedFile(path="src/todo_store.py", change_type=ChangeType.CREATE),
            ChangedFile(path="tests/test_todo_store.py", change_type=ChangeType.CREATE),
        ],
    )

    missing = detect_tests_missing(
        _profile(code_root),
        code_root,
        dev_manifest=manifest,
    )
    assert missing == []


def test_detect_tests_missing_ignores_docs_and_config(tmp_path: Path) -> None:
    code_root = tmp_path / "project"
    src = code_root / "src"
    src.mkdir(parents=True)
    (code_root / "README.md").write_text("# app\n", encoding="utf-8")
    (code_root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    (src / "cli.py").write_text("def main(): pass\n", encoding="utf-8")

    manifest = DevManifest(
        version="1",
        changed_files=[
            ChangedFile(path="README.md", change_type=ChangeType.CREATE),
            ChangedFile(path="pyproject.toml", change_type=ChangeType.CREATE),
            ChangedFile(path="src/cli.py", change_type=ChangeType.CREATE),
        ],
    )

    missing = detect_tests_missing(
        _profile(code_root),
        code_root,
        dev_manifest=manifest,
    )
    assert missing == ["src/cli.py"]


def test_run_tests_marks_failed_when_tests_missing(tmp_path: Path) -> None:
    from multi_agent_code_factory.tools.run_tests import run_tests

    code_root = tmp_path / "project"
    src = code_root / "src"
    tests = code_root / "tests"
    reports = code_root / "reports"
    src.mkdir(parents=True)
    tests.mkdir(parents=True)
    reports.mkdir(parents=True)
    (src / "app.py").write_text("def add(a, b): return a + b\n", encoding="utf-8")
    (tests / "test_ok.py").write_text(
        "def test_passes():\n    assert True\n", encoding="utf-8"
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
            test_dir_glob="tests/**",
        ),
    )
    manifest = DevManifest(
        version="1",
        changed_files=[
            ChangedFile(path="src/app.py", change_type=ChangeType.CREATE),
            ChangedFile(path="tests/test_ok.py", change_type=ChangeType.CREATE),
        ],
    )

    report = run_tests(profile, dev_manifest=manifest)
    assert report.tests_missing == ["src/app.py"]
    assert report.passed is False
