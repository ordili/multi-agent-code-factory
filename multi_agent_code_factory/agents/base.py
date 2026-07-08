"""Agent 共享辅助：提示词片段、上下文构建、stub fixture 加载。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from multi_agent_code_factory._paths import repo_root
from multi_agent_code_factory.prompt_context import build_prompt_context
from multi_agent_code_factory.profiles import ProfileConfig
from multi_agent_code_factory.state import PipelineState


class StubScenario(StrEnum):
    """Stub 模式下可注入的流水线分支场景。"""

    HAPPY = "happy"
    QA_FAIL_THEN_PASS = "qa_fail_then_pass"
    QA_ALWAYS_FAIL = "qa_always_fail"
    REVIEWER_ESCALATE_ARCHITECT = "reviewer_escalate_architect"
    REVIEWER_ESCALATE_PM = "reviewer_escalate_pm"
    SPEC_VALIDATE_RETRY = "spec_validate_retry"
    DESIGN_VALIDATE_RETRY = "design_validate_retry"


@dataclass(frozen=True)
class StubFixturePaths:
    """各 Agent stub 产物对应的 fixture 文件路径。"""

    spec: Path
    design: Path
    design_invalid: Path
    dev_manifest: Path
    test_report: Path
    test_report_fail: Path
    review: Path
    review_architect: Path
    review_pm: Path
    flow_mmd: Path


def default_stub_fixtures() -> StubFixturePaths:
    """返回仓库内默认 stub fixture 路径集合。"""
    root = repo_root()
    snippets = root / "docs" / "design" / "pipeline" / "examples" / "snippets"
    fixtures = root / "tests" / "fixtures"
    return StubFixturePaths(
        spec=snippets / "spec-default.json",
        design=fixtures / "design-todo-valid.json",
        design_invalid=snippets / "design-todo-excerpt.json",
        dev_manifest=fixtures / "dev-manifest-todo.json",
        test_report=fixtures / "test-report-pass.json",
        test_report_fail=fixtures / "test-report-fail.json",
        review=fixtures / "review-deploy.json",
        review_architect=fixtures / "review-architect.json",
        review_pm=fixtures / "review-pm.json",
        flow_mmd=snippets / "flow-todo.mmd",
    )


def load_json_fixture(path: Path) -> dict[str, Any]:
    """从 JSON fixture 文件加载并校验为 dict。"""
    with path.open(encoding="utf-8") as handle:
        loaded = json.load(handle)
    if not isinstance(loaded, dict):
        msg = f"expected object in fixture {path}"
        raise TypeError(msg)
    return loaded


def load_prompt_snippet(profile: ProfileConfig, filename: str) -> str | None:
    """读取 Profile 提示词目录下的片段文件；不存在则返回 None。"""
    path = profile.prompts_dir / filename
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def agent_context(
    role_id: str,
    state: PipelineState,
    profile: ProfileConfig,
) -> dict[str, Any]:
    """为指定 Agent 角色构建 LLM 调用上下文。"""
    return build_prompt_context(role_id, state, profile)


def write_artifact_model(
    writer: Any,
    filename: str,
    artifact: BaseModel,
) -> None:
    """将 Pydantic 模型写入 run 目录产物文件。"""
    writer.write_model(filename, artifact)
