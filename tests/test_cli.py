from __future__ import annotations

import subprocess
import sys
import uuid

from multi_agent_code_factory.__main__ import main


def test_cli_run_default_profile(tmp_path, monkeypatch, capsys) -> None:
    task_id = f"cli-stub-smoke-{uuid.uuid4().hex[:8]}"
    monkeypatch.setattr(
        "multi_agent_code_factory.__main__.run_dir",
        lambda tid: tmp_path / "runs" / tid,
    )
    code = main(
        [
            "run",
            "--profile",
            "python",
            "--task-id",
            task_id,
            "实现命令行 Todo",
        ]
    )
    captured = capsys.readouterr()
    assert code == 0, captured.err
    assert "profile=python" in captured.out
    assert f"task_id={task_id}" in captured.out
    assert "mode=stub" in captured.out
    assert "status=completed" in captured.out


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
