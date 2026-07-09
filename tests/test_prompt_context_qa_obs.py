from __future__ import annotations

from pathlib import Path

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.profile_config import ProfileConfig, ToolchainConfig
from multi_agent_code_factory.prompt_context import build_prompt_context
from multi_agent_code_factory.schemas.dev_manifest import (
    ChangedFile,
    ChangeType,
    DevManifest,
)
from multi_agent_code_factory.schemas.test_report import TestReport, TestSummary
from multi_agent_code_factory.state import PipelineState


def _profile(code_root: Path) -> ProfileConfig:
    return ProfileConfig(
        id="python",
        language="python",
        code_root=code_root,
        code_root_raw=str(code_root),
        prompts_dir=code_root,
        tools=[],
        toolchain=ToolchainConfig(test_command="true"),
        auto_generate_tests=True,
    )


def test_developer_context_includes_tests_missing_on_retry(tmp_path: Path) -> None:
    state = PipelineState(
        task_id="t",
        user_request="todo",
        impl_retry_count=1,
        dev_manifest=DevManifest(
            version="1",
            changed_files=[
                ChangedFile(path="src/app.py", change_type=ChangeType.CREATE),
            ],
        ),
        test_report=TestReport(
            version="1",
            passed=False,
            exit_code=0,
            summary=TestSummary(total=0, passed=0, failed=0, skipped=0),
            duration_sec=0.0,
            command="true",
            parser="exit_code_only",
            tests_missing=["src/app.py"],
        ),
    )
    context = build_prompt_context(AgentRole.DEVELOPER, state, _profile(tmp_path))
    assert context.get("auto_generate_tests") is True
    assert context.get("tests_missing") == ["src/app.py"]


def test_reviewer_context_includes_git_diff(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "main.py").write_text("x = 1\n", encoding="utf-8")

    state = PipelineState(
        task_id="t",
        user_request="todo",
        dev_manifest=DevManifest(
            version="1",
            changed_files=[
                ChangedFile(path="main.py", change_type=ChangeType.CREATE),
            ],
        ),
    )
    context = build_prompt_context(AgentRole.REVIEWER, state, _profile(repo))
    assert "git_diff" not in context or context["git_diff"] == ""

    import subprocess

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=repo, check=True)
    subprocess.run(["git", "add", "main.py"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True)
    (repo / "main.py").write_text("x = 2\n", encoding="utf-8")

    context = build_prompt_context(AgentRole.REVIEWER, state, _profile(repo))
    assert "git_diff" in context
    assert "main.py" in context["git_diff"]
