from __future__ import annotations

import json
from pathlib import Path

from multi_agent_code_factory.renderers.design_md import render_design_md
from multi_agent_code_factory.schemas.design import DesignArtifact


def test_render_design_md_contains_sections() -> None:
    fixture = Path(__file__).parent / "fixtures" / "design-todo-valid.json"
    design = DesignArtifact.model_validate(
        json.loads(fixture.read_text(encoding="utf-8"))
    )
    md = render_design_md(design)
    assert "# Design Doc — CLI Todo App" in md
    assert "## 1. Context & Background" in md
    assert "### 4.2 Components" in md
    assert "`STORE`" in md
    assert "## 附录 D. 测试用例设计" in md
    assert "spec_ref: `CLI Todo App`" in md


def test_render_design_md_from_calculator_run() -> None:
    from multi_agent_code_factory._paths import repo_root

    calc_path = repo_root() / "docs" / "runs" / "calculator" / "design.json"
    if not calc_path.is_file():
        return
    design = DesignArtifact.model_validate(
        json.loads(calc_path.read_text(encoding="utf-8"))
    )
    md = render_design_md(design)
    assert "# Design Doc — CLI Calculator" in md
    assert "### 4.4 APIs" in md
    assert "ERR" in md or "E00" in md
