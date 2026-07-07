from __future__ import annotations

import os
from pathlib import Path

from multi_agent_code_factory.env import (
    load_env_file,
    reset_env_loaded_for_tests,
)


def test_load_env_file_sets_variables(tmp_path: Path, monkeypatch) -> None:
    reset_env_loaded_for_tests()
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    env_path = tmp_path / ".env"
    env_path.write_text("DEEPSEEK_API_KEY=sk-from-dotenv\n", encoding="utf-8")

    loaded = load_env_file(root=tmp_path)

    assert loaded is True
    assert os.environ.get("DEEPSEEK_API_KEY") == "sk-from-dotenv"


def test_load_env_file_does_not_override_existing_env(
    tmp_path: Path,
    monkeypatch,
) -> None:
    reset_env_loaded_for_tests()
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-shell")
    env_path = tmp_path / ".env"
    env_path.write_text("DEEPSEEK_API_KEY=sk-from-dotenv\n", encoding="utf-8")

    load_env_file(root=tmp_path)

    assert os.environ.get("DEEPSEEK_API_KEY") == "sk-shell"


def test_load_env_file_missing_is_noop(tmp_path: Path, monkeypatch) -> None:
    reset_env_loaded_for_tests()
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    loaded = load_env_file(root=tmp_path)

    assert loaded is False
    assert "DEEPSEEK_API_KEY" not in os.environ
