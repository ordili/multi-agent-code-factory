from __future__ import annotations

from pathlib import Path

from multi_agent_code_factory.profile_config.models import (
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
from multi_agent_code_factory.tools.tests_missing import detect_tests_missing


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


def _profile(
    code_root: Path,
    *,
    language: str = "python",
    tests_missing: TestsMissingPolicy | None = None,
    test_dir_glob: str = "tests/**",
) -> ProfileConfig:
    return ProfileConfig(
        id=language,
        language=language,
        code_root=code_root,
        code_root_raw=str(code_root),
        prompts_dir=code_root,
        tools=[],
        toolchain=ToolchainConfig(
            test_command="true",
            test_dir_glob=test_dir_glob,
        ),
        tests_missing=tests_missing or TestsMissingPolicy(),
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
    design = _design("src/todo_store.py")

    missing = detect_tests_missing(
        _profile(code_root),
        code_root,
        dev_manifest=manifest,
        design=design,
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
    design = _design("src/todo_store.py")

    missing = detect_tests_missing(
        _profile(code_root),
        code_root,
        dev_manifest=manifest,
        design=design,
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
    design = _design("src/cli.py")

    missing = detect_tests_missing(
        _profile(code_root),
        code_root,
        dev_manifest=manifest,
        design=design,
    )
    assert missing == ["src/cli.py"]


def test_detect_tests_missing_disabled(tmp_path: Path) -> None:
    code_root = tmp_path / "project"
    src = code_root / "src"
    src.mkdir(parents=True)
    (src / "app.py").write_text("pass\n", encoding="utf-8")
    manifest = DevManifest(
        version="1",
        changed_files=[ChangedFile(path="src/app.py", change_type=ChangeType.CREATE)],
    )
    profile = _profile(
        code_root,
        tests_missing=TestsMissingPolicy(enabled=False),
    )
    missing = detect_tests_missing(profile, code_root, dev_manifest=manifest)
    assert missing == []


def test_rust_inline_tests_clear_tests_missing(tmp_path: Path) -> None:
    code_root = tmp_path / "project"
    src = code_root / "src"
    tests = code_root / "tests"
    src.mkdir(parents=True)
    tests.mkdir(parents=True)
    (src / "calc.rs").write_text(
        "#[cfg(test)]\nmod tests {\n    #[test]\n    fn adds() {}\n}\n",
        encoding="utf-8",
    )
    (tests / "integration_test.rs").write_text("fn main() {}\n", encoding="utf-8")

    manifest = DevManifest(
        version="1",
        changed_files=[
            ChangedFile(path="src/calc.rs", change_type=ChangeType.CREATE),
            ChangedFile(
                path="tests/integration_test.rs", change_type=ChangeType.CREATE
            ),
        ],
    )
    design = _design("src/calc.rs")
    profile = _profile(
        code_root,
        language="rust",
        test_dir_glob="{src/**,tests/**}/*.rs",
        tests_missing=TestsMissingPolicy(
            block_on=False,
            detector="rust",
            inline_tests=True,
            scope="dev_tasks",
        ),
    )

    missing = detect_tests_missing(
        profile,
        code_root,
        dev_manifest=manifest,
        design=design,
    )
    assert missing == []


def test_dev_tasks_scope_ignores_unlisted_manifest_files(tmp_path: Path) -> None:
    code_root = tmp_path / "project"
    src = code_root / "src"
    src.mkdir(parents=True)
    (src / "listed.py").write_text("pass\n", encoding="utf-8")
    (src / "extra.py").write_text("pass\n", encoding="utf-8")

    manifest = DevManifest(
        version="1",
        changed_files=[
            ChangedFile(path="src/listed.py", change_type=ChangeType.CREATE),
            ChangedFile(path="src/extra.py", change_type=ChangeType.CREATE),
        ],
    )
    design = _design("src/listed.py")

    missing = detect_tests_missing(
        _profile(code_root, tests_missing=TestsMissingPolicy(scope="dev_tasks")),
        code_root,
        dev_manifest=manifest,
        design=design,
    )
    assert missing == ["src/listed.py"]


def test_run_tests_marks_failed_when_tests_missing_block_on(tmp_path: Path) -> None:
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
        tests_missing=TestsMissingPolicy(block_on=True),
    )
    manifest = DevManifest(
        version="1",
        changed_files=[
            ChangedFile(path="src/app.py", change_type=ChangeType.CREATE),
            ChangedFile(path="tests/test_ok.py", change_type=ChangeType.CREATE),
        ],
    )
    design = _design("src/app.py")

    report = run_tests(profile, dev_manifest=manifest, design=design)
    assert report.tests_missing == ["src/app.py"]
    assert report.passed is False


def test_run_tests_passes_when_block_on_false(tmp_path: Path) -> None:
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
        tests_missing=TestsMissingPolicy(block_on=False),
    )
    manifest = DevManifest(
        version="1",
        changed_files=[
            ChangedFile(path="src/app.py", change_type=ChangeType.CREATE),
            ChangedFile(path="tests/test_ok.py", change_type=ChangeType.CREATE),
        ],
    )
    design = _design("src/app.py")

    report = run_tests(profile, dev_manifest=manifest, design=design)
    assert report.tests_missing == ["src/app.py"]
    assert report.passed is True
