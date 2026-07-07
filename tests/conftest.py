from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from multi_agent_code_factory._paths import repo_root
from multi_agent_code_factory.env import load_env_file

load_env_file()


@pytest.fixture
def snippets_dir() -> Path:
    return repo_root() / "docs" / "design" / "pipeline" / "examples" / "snippets"


def load_snippet_json(snippets_dir: Path, name: str) -> dict[str, Any]:
    path = snippets_dir / name
    with path.open(encoding="utf-8") as handle:
        loaded = json.load(handle)
    if not isinstance(loaded, dict):
        msg = f"expected object in snippet {name}"
        raise TypeError(msg)
    return loaded
