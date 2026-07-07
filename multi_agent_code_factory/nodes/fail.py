"""Terminal fail node when loop limits are exceeded."""

from __future__ import annotations

from datetime import UTC, datetime

from multi_agent_code_factory.log import get_logger
from multi_agent_code_factory.schemas.run_meta import RunStatus
from multi_agent_code_factory.state import PipelineState
from multi_agent_code_factory.tools.write_artifact import RunArtifactWriter

logger = get_logger("nodes.fail")


def run_fail(
    state: PipelineState,
    writer: RunArtifactWriter,
) -> dict[str, object]:
    logger.error(
        "pipeline failed loop_limits spec_revisions=%s design_revisions=%s impl_retries=%s",
        state.spec_revision_count,
        state.design_revision_count,
        state.impl_retry_count,
    )
    writer.update_meta(
        status=RunStatus.FAILED,
        impl_retry_count=state.impl_retry_count,
        design_revision_count=state.design_revision_count,
        spec_revision_count=state.spec_revision_count,
        finished_at=datetime.now(tz=UTC).isoformat(),
    )
    return {}
