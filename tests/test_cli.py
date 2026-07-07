from __future__ import annotations

import subprocess
import sys


def test_cli_run_default_profile() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "multi_agent_code_factory",
            "run",
            "--profile",
            "default",
            "--task-id",
            "todo-cli",
            "实现命令行 Todo",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "profile=default" in result.stdout
    assert "task_id=todo-cli" in result.stdout
    assert "mode=stub" in result.stdout
    assert "status=completed" in result.stdout


def test_cli_run_unknown_profile() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "multi_agent_code_factory",
            "run",
            "--profile",
            "missing-profile",
            "--task-id",
            "x",
            "hello",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "profile not found" in result.stderr
