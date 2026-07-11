from __future__ import annotations

from pathlib import Path

from multi_agent_code_factory.renderers.prd_md import render_prd_md
from multi_agent_code_factory.schemas.prd import PrdArtifact

from tests.conftest import load_snippet_json


def test_render_prd_md_contains_sections(snippets_dir: Path) -> None:
    data = load_snippet_json(snippets_dir, "prd-default.json")
    spec = PrdArtifact.model_validate(data)
    md = render_prd_md(spec)
    assert "# CLI Todo App" in md
    assert "## 术语与领域概念" in md
    assert "## 背景与上下文" in md
    assert "## 业务指标" in md
    assert "### 稳定性与性能" in md
    assert "### 数据一致性" in md
    assert "**本次包含**" in md
    assert "**明确不做**" in md
    assert "## 用户故事" in md
    assert "## 需求池" in md
    assert "## 验收标准" in md
    assert "| AC-1 |" in md
    assert "## 约束" in md
    assert "task_profile: python" in md
    assert "revision: 1" in md
    assert "## 待澄清项" not in md
