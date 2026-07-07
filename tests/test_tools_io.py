from __future__ import annotations

from pathlib import Path

import pytest
from multi_agent_code_factory.tools._paths import PathEscapeError, resolve_in_root
from multi_agent_code_factory.tools.read_file import read_file
from multi_agent_code_factory.tools.write_file import write_file


def test_resolve_in_root_allows_nested_path(tmp_path: Path) -> None:
    root = tmp_path / "code"
    root.mkdir()
    path = resolve_in_root(root, "src/main.py")
    assert path == (root / "src/main.py").resolve()


def test_resolve_in_root_rejects_escape(tmp_path: Path) -> None:
    root = tmp_path / "code"
    root.mkdir()
    with pytest.raises(PathEscapeError):
        resolve_in_root(root, "../outside.txt")


def test_read_and_write_file_round_trip(tmp_path: Path) -> None:
    root = tmp_path / "code"
    root.mkdir()
    write_file(root, "hello.txt", "world")
    assert read_file(root, "hello.txt") == "world"
