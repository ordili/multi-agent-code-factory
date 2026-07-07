from __future__ import annotations

from pathlib import Path

from multi_agent_code_factory.renderers.spec_md import render_spec_md
from multi_agent_code_factory.schemas.spec import SpecArtifact

from tests.conftest import load_snippet_json


def test_render_spec_md_contains_sections(snippets_dir: Path) -> None:
    data = load_snippet_json(snippets_dir, "spec-default.json")
    spec = SpecArtifact.model_validate(data)
    md = render_spec_md(spec)
    assert "# CLI Todo App" in md
    assert "## 验收标准" in md
    assert "**AC-1**" in md
    assert "task_profile: `default`" in md
