from __future__ import annotations

from pathlib import Path

from multi_agent_code_factory.renderers.prd_md import render_prd_md
from multi_agent_code_factory.schemas.prd import PrdArtifact

from tests.conftest import load_snippet_json


def test_render_prd_md_semantic_constraints_section() -> None:
    spec = PrdArtifact.model_validate(
        {
            "version": "1",
            "profile": "python",
            "revision": 1,
            "title": "Calc",
            "summary": "Calc",
            "context": {"language": "python", "interface": "cli", "storage": "none"},
            "success_metrics": [],
            "features": [
                {
                    "id": "FEAT-1",
                    "name": "Calc",
                    "description": "parse",
                    "priority": "P0",
                }
            ],
            "scope_in": ["CLI"],
            "operational_profile": {
                "user_scale": "personal",
                "high_concurrency": False,
                "performance": {"tier": "best_effort"},
            },
            "consistency_profile": {
                "consistency_model": "local_only",
                "delivery": "best_effort",
                "multi_writer": False,
                "idempotency_required": False,
            },
            "acceptance_criteria": [
                {
                    "id": "AC-1",
                    "description": "SEM-IN-1 passes",
                    "verifiable_by": "automated_test",
                }
            ],
            "semantic_constraints": [
                {
                    "id": "SEM-IN-1",
                    "source_ref": "US-1",
                    "source_kind": "US",
                    "kind": "input_shape",
                    "summary": "binary input",
                    "dimensions": {"operand_count": "exactly:2"},
                }
            ],
        }
    )
    md = render_prd_md(spec)
    assert "## 语义约束" in md
    assert "SEM-IN-1" in md
    assert "operand_count=exactly:2" in md


def test_render_prd_md_contains_sections(snippets_dir: Path) -> None:
    data = load_snippet_json(snippets_dir, "prd-default.json")
    spec = PrdArtifact.model_validate(data)
    md = render_prd_md(spec)
    assert "# CLI Todo App" in md
    assert "## 术语与领域概念" in md
    assert "## 背景与上下文" in md
    assert "本地管理待办" in md
    assert "### 产品形态" in md
    assert "**interface：**" in md
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


def test_render_prd_md_background_fallback_to_context_keys() -> None:
    spec = PrdArtifact.model_validate(
        {
            "version": "1",
            "profile": "python",
            "revision": 1,
            "title": "Legacy",
            "summary": "Legacy spec without background narrative",
            "context": {"language": "python", "interface": "cli", "storage": "none"},
            "success_metrics": [],
            "features": [
                {
                    "id": "FEAT-1",
                    "name": "Core",
                    "description": "core",
                    "priority": "P0",
                }
            ],
            "scope_in": ["CLI"],
            "operational_profile": {
                "user_scale": "personal",
                "high_concurrency": False,
                "performance": {"tier": "best_effort"},
            },
            "consistency_profile": {
                "consistency_model": "local_only",
                "delivery": "best_effort",
                "multi_writer": False,
                "idempotency_required": False,
            },
            "acceptance_criteria": [
                {
                    "id": "AC-1",
                    "description": "passes",
                    "verifiable_by": "automated_test",
                }
            ],
        }
    )
    md = render_prd_md(spec)
    assert "## 背景与上下文" in md
    assert "**interface：** `cli`" in md
    assert "### 产品形态" not in md
