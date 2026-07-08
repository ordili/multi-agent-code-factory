from __future__ import annotations

import json
from pathlib import Path

from multi_agent_code_factory.renderers.review_md import render_review_md
from multi_agent_code_factory.schemas.review import ReviewReport


def test_render_review_md_happy_path() -> None:
    path = Path(__file__).parent / "fixtures" / "review-deploy.json"
    review = ReviewReport.model_validate(json.loads(path.read_text(encoding="utf-8")))
    md = render_review_md(review)
    assert "# 审查结论" in md
    assert "**通过：** 是" in md
    assert "## 路由" in md
    assert "下一节点：`deploy`" in md
    assert "## 验收覆盖" in md
    assert "| AC-1 | ✓ |" in md
    assert "## 发现项" in md
    assert "无" in md
