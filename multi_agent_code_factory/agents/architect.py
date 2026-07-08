"""Architect Agent 图节点：根据 spec 生成设计与流程图。"""

from __future__ import annotations

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.base import agent_context
from multi_agent_code_factory.agents.live import require_llm_runner
from multi_agent_code_factory.agents.llm import LlmRunner
from multi_agent_code_factory.agents.llm.prompt.validation_feedback import (
    format_design_validation_feedback,
)
from multi_agent_code_factory.agents.llm.schemas import ArchitectLLMOutput
from multi_agent_code_factory.agents.normalizers.design import normalize_design
from multi_agent_code_factory.agents.stub.fixtures import (
    StubScenario,
    default_stub_fixtures,
    load_json_fixture,
)
from multi_agent_code_factory.log import agent_run, get_logger
from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.renderers.design_md import render_design_md
from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.state import PipelineState
from multi_agent_code_factory.tools.run_artifacts import RunArtifactWriter

logger = get_logger("agents.architect")


def _write_mermaid_artifacts(
    writer: RunArtifactWriter,
    *,
    mmd_files: list[object] | None = None,
    flow_mmd: str | None = None,
    fallback_text: str | None = None,
) -> None:
    """将 Architect 产出的 Mermaid 写入 Run 目录（支持多文件）。"""
    if mmd_files:
        for item in mmd_files:
            path = getattr(item, "path", None) or (
                item.get("path") if isinstance(item, dict) else None
            )
            content = getattr(item, "content", None) or (
                item.get("content") if isinstance(item, dict) else None
            )
            if isinstance(path, str) and isinstance(content, str):
                writer.write_text(path, content)
        return
    text = flow_mmd or fallback_text or ""
    writer.write_text("flow.mmd", text)


def run_architect(
    state: PipelineState,
    profile: ProfileConfig,
    writer: RunArtifactWriter,
    *,
    stub: bool = True,
    stub_scenario: StubScenario = StubScenario.HAPPY,
    llm_runner: LlmRunner | None = None,
) -> dict[str, object]:
    """运行 Architect 节点，产出 ``design.json`` / ``flow.mmd`` / ``design.md``。"""
    extra = {"revision": state.design_revision_count}
    with agent_run(logger, role_id=AgentRole.ARCHITECT, stub=stub, extra=extra):
        if stub:
            fixtures = default_stub_fixtures()
            if (
                stub_scenario == StubScenario.DESIGN_VALIDATE_RETRY
                and state.design_revision_count == 0
            ):
                data = load_json_fixture(fixtures.design_invalid)
            else:
                data = load_json_fixture(fixtures.design)
            design = DesignArtifact.model_validate(data)
            flow_text = fixtures.flow_mmd.read_text(encoding="utf-8")
        else:
            runner = require_llm_runner(llm_runner)
            if state.spec is None:
                msg = "architect requires spec in live mode"
                raise ValueError(msg)
            output = runner.invoke_structured(
                role_id=AgentRole.ARCHITECT,
                output_schema=ArchitectLLMOutput,
                context=agent_context(AgentRole.ARCHITECT, state, profile),
                extra_system=format_design_validation_feedback(state),
            )
            design = normalize_design(output.design, state)
            flow_text = None
            _write_mermaid_artifacts(
                writer,
                mmd_files=output.mmd_files,
                flow_mmd=output.flow_mmd,
            )

        writer.write_model("design.json", design)
        if stub:
            _write_mermaid_artifacts(writer, fallback_text=flow_text)
        writer.write_text("design.md", render_design_md(design))
    return {"design": design}
