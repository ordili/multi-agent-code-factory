"""fail 终止节点：环路超限时标记 run 为 FAILED。"""

from __future__ import annotations

from datetime import UTC, datetime

from multi_agent_code_factory.log import get_logger
from multi_agent_code_factory.schemas.run_meta import RunStatus
from multi_agent_code_factory.state import PipelineState
from multi_agent_code_factory.tools.run_artifacts import RunArtifactWriter

logger = get_logger("nodes.fail")


def run_fail(
    state: PipelineState,
    writer: RunArtifactWriter,
) -> dict[str, object]:
    """记录失败日志并将 run_meta.status 设为 FAILED。"""
    logger.error(
        "pipeline failed loop_limits prd_revisions=%s "
        "design_revisions=%s impl_retries=%s",
        state.prd_revision_count,
        state.design_revision_count,
        state.impl_retry_count,
    )
    writer.update_meta(
        status=RunStatus.FAILED,
        impl_retry_count=state.impl_retry_count,
        design_revision_count=state.design_revision_count,
        prd_revision_count=state.prd_revision_count,
        finished_at=datetime.now(tz=UTC).isoformat(),
    )
    return {}
