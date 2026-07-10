from __future__ import annotations

from pathlib import Path

from multi_agent_code_factory.__main__ import main


def test_run_rejects_existing_task_without_force_new(
    tmp_path: Path, monkeypatch
) -> None:
    run_dir = tmp_path / "runs" / "dup-task"
    run_dir.mkdir(parents=True)
    (run_dir / "run_meta.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(
        "multi_agent_code_factory.__main__.run_dir",
        lambda task_id: tmp_path / "runs" / task_id,
    )
    code = main(
        [
            "run",
            "--profile",
            "python",
            "--task-id",
            "dup-task",
            "hello",
        ]
    )
    assert code == 2


def test_run_force_new_allowed(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "multi_agent_code_factory.__main__.run_dir",
        lambda task_id: tmp_path / "runs" / task_id,
    )
    code = main(
        [
            "run",
            "--profile",
            "python",
            "--task-id",
            "fresh-task",
            "--force-new",
            "hello",
        ]
    )
    assert code in (0, 1)
