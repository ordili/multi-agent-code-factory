"""Developer Agent 图节点：实现代码并写入 dev_manifest。"""

from __future__ import annotations

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.base import agent_context
from multi_agent_code_factory.agents.developer_output import apply_developer_output
from multi_agent_code_factory.agents.live import require_llm_runner
from multi_agent_code_factory.agents.llm import LlmRunner
from multi_agent_code_factory.agents.llm.prompt.validation_feedback import (
    format_developer_retry_extra_system,
)
from multi_agent_code_factory.agents.llm.schemas import DeveloperLLMOutput
from multi_agent_code_factory.agents.stub.fixtures import (
    default_stub_fixtures,
    load_json_fixture,
)
from multi_agent_code_factory.log import agent_run, get_logger
from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.schemas.dev_manifest import DevManifest
from multi_agent_code_factory.state import PipelineState
from multi_agent_code_factory.tools.run_artifacts import RunArtifactWriter

logger = get_logger("agents.developer")


def run_developer(
    state: PipelineState,
    profile: ProfileConfig,
    writer: RunArtifactWriter,
    *,
    stub: bool = True,
    llm_runner: LlmRunner | None = None,
) -> dict[str, object]:
    """运行 Developer 节点，写入源码并产出 ``dev_manifest.json``。"""
    extra = {"impl_retry": state.impl_retry_count}
    with agent_run(logger, role_id=AgentRole.DEVELOPER, stub=stub, extra=extra):
        if stub:
            manifest = DevManifest.model_validate(
                load_json_fixture(default_stub_fixtures().dev_manifest)
            )
        else:
            runner = require_llm_runner(llm_runner)
            if state.prd is None or state.design is None:
                msg = "developer requires prd and design in live mode"
                raise ValueError(msg)
            output = runner.invoke_structured(
                role_id=AgentRole.DEVELOPER,
                output_schema=DeveloperLLMOutput,
                context=agent_context(AgentRole.DEVELOPER, state, profile),
                extra_system=format_developer_retry_extra_system(state, profile),
            )
            patch_only = state.impl_retry_count > 0
            manifest = apply_developer_output(profile, output, patch_only=patch_only)

        writer.write_model("dev_manifest.json", manifest)
    return {"dev_manifest": manifest}
