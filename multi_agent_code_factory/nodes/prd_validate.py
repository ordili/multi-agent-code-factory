"""prd_validate ????? prd ?????????"""

from __future__ import annotations

from pathlib import Path

from multi_agent_code_factory.log import get_logger, log_validation_result
from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.schemas.prd import PrdArtifact
from multi_agent_code_factory.schemas.validation_report import (
    ValidationReport,
    ValidationTarget,
)
from multi_agent_code_factory.tools.run_artifacts import RunArtifactWriter
from multi_agent_code_factory.validators._report import build_validation_report
from multi_agent_code_factory.validators.prd_md_rules import validate_prd_md_file
from multi_agent_code_factory.validators.prd_rules import validate_prd_rules

logger = get_logger("nodes.prd_validate")


def run_prd_validate(
    prd: PrdArtifact,
    profile: ProfileConfig,
    *,
    writer: RunArtifactWriter | None = None,
    run_dir: Path | None = None,
) -> ValidationReport:
    """?? spec ????? ``prd_validation.json``?"""
    gate = profile.validation.prd
    if not gate.enabled:
        report = build_validation_report(
            ValidationTarget.PRD,
            [],
            block_on=gate.block_on,
        )
    else:
        violations = validate_prd_rules(prd, profile)
        md_dir = run_dir or (writer.directory if writer else None)
        violations.extend(validate_prd_md_file(prd, md_dir))
        report = build_validation_report(
            ValidationTarget.PRD,
            violations,
            block_on=gate.block_on,
        )
    if writer is not None:
        writer.write_model("prd_validation.json", report)
    log_validation_result(logger, target="prd", report=report)
    return report
