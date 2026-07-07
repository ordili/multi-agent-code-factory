"""deploy_hitl graph node (MVP: skip when no sensitive paths/flags)."""

from __future__ import annotations

import fnmatch

from multi_agent_code_factory.profiles import ProfileConfig
from multi_agent_code_factory.schemas.hitl import HitlDecision, HitlStage
from multi_agent_code_factory.state import PipelineState
from multi_agent_code_factory.tools.write_artifact import RunArtifactWriter


def deploy_hitl_required(state: PipelineState, profile: ProfileConfig) -> bool:
    design = state.design
    if (
        design is not None
        and design.hitl_flags
        and set(design.hitl_flags) & set(profile.hitl.flags)
    ):
        return True

    manifest = state.dev_manifest
    globs = profile.hitl.sensitive_globs
    if manifest is not None and globs:
        for changed in manifest.changed_files:
            for pattern in globs:
                if fnmatch.fnmatch(changed.path, pattern):
                    return True
    return False


def run_deploy_hitl(
    state: PipelineState,
    profile: ProfileConfig,
    writer: RunArtifactWriter,
) -> dict[str, object]:
    if not deploy_hitl_required(state, profile):
        return {}
    decision = HitlDecision(
        version="1",
        stage=HitlStage.DEPLOY,
        required=True,
        reason=["sensitive deploy path or hitl flag matched"],
        approved=True,
        reviewer="stub",
        comment="MVP auto-approved (no interrupt)",
    )
    writer.write_model("hitl.json", decision)
    return {"hitl": decision}
