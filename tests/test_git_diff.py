from __future__ import annotations

import subprocess
from pathlib import Path

from multi_agent_code_factory.tools.git_diff import git_diff


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "init"], cwd=cwd, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=cwd, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=cwd, check=True)


def test_git_diff_returns_empty_for_non_repo(tmp_path: Path) -> None:
    assert git_diff(tmp_path) == ""


def test_git_diff_shows_uncommitted_changes(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo)
    (repo / "main.py").write_text("print('hi')\n", encoding="utf-8")
    subprocess.run(["git", "add", "main.py"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True)
    (repo / "main.py").write_text("print('bye')\n", encoding="utf-8")

    diff = git_diff(repo)
    assert "main.py" in diff
    assert "bye" in diff


def test_git_diff_filters_paths(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo)
    (repo / "a.py").write_text("a\n", encoding="utf-8")
    (repo / "b.py").write_text("b\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True)
    (repo / "a.py").write_text("a2\n", encoding="utf-8")
    (repo / "b.py").write_text("b2\n", encoding="utf-8")

    diff = git_diff(repo, paths=["a.py"])
    assert "a.py" in diff
    assert "b2" not in diff
