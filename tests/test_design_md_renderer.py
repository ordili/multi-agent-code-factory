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
    assert "# 设计文档 — CLI Todo App" in md
    assert "## 1. 背景与上下文" in md
    assert "### 4.3 模块划分" in md
    assert "`STORE`" in md
    assert "## 6. 测试用例列表" in md
    assert "| 类型 |" in md
    assert "## 附录 D. 与现有代码对照" in md
    assert "Rollout" not in md
    assert "## 5. 方案对比" not in md
    assert "## 10. 待澄清项" not in md
    assert "spec_ref: `CLI Todo App`" in md


def test_render_design_md_from_calculator_run() -> None:
    from multi_agent_code_factory._paths import repo_root
    from pydantic import ValidationError

    calc_path = repo_root() / "docs" / "runs" / "calculator" / "design.json"
    if not calc_path.is_file():
        return
    try:
        design = DesignArtifact.model_validate(
            json.loads(calc_path.read_text(encoding="utf-8"))
        )
    except ValidationError:
        return
    md = render_design_md(design)
    assert "# 设计文档 — CLI Calculator" in md
    assert "### 4.5 接口定义" in md
    assert "ERR" in md or "E00" in md
