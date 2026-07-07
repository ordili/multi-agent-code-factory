"""Deploy graph node — terminal step; updates run_meta.deploy_status."""

from __future__ import annotations

from datetime import UTC, datetime

from multi_agent_code_factory.context import build_node_context
from multi_agent_code_factory.profiles import ProfileConfig
from multi_agent_code_factory.schemas.run_meta import DeployStatus, RunStatus
from multi_agent_code_factory.state import PipelineState
from multi_agent_code_factory.tools.write_artifact import RunArtifactWriter


def run_deploy(
    state: PipelineState,
    profile: ProfileConfig,
    writer: RunArtifactWriter,
) -> dict[str, object]:
    _ = build_node_context("deploy", state, profile)
    hitl = state.hitl
    deploy_status = DeployStatus.SKIPPED
    if hitl is not None and hitl.stage.value == "deploy" and hitl.approved:
        deploy_status = DeployStatus.SUCCESS

    writer.update_meta(
        deploy_status=deploy_status,
        status=RunStatus.COMPLETED,
        impl_retry_count=state.impl_retry_count,
        design_revision_count=state.design_revision_count,
        spec_revision_count=state.spec_revision_count,
        finished_at=datetime.now(tz=UTC).isoformat(),
    )
    return {}
