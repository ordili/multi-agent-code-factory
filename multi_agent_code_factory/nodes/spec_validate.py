"""spec_validate 图节点：对 spec 产物执行规则校验。"""

from __future__ import annotations

from pathlib import Path

from multi_agent_code_factory.log import get_logger, log_validation_result
from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.schemas.spec import SpecArtifact
from multi_agent_code_factory.schemas.validation_report import (
    ValidationReport,
    ValidationTarget,
)
from multi_agent_code_factory.tools.run_artifacts import RunArtifactWriter
from multi_agent_code_factory.validators._report import build_validation_report
from multi_agent_code_factory.validators.spec_md_rules import validate_spec_md_file
from multi_agent_code_factory.validators.spec_rules import validate_spec_rules

logger = get_logger("nodes.spec_validate")


def run_spec_validate(
    spec: SpecArtifact,
    profile: ProfileConfig,
    *,
    writer: RunArtifactWriter | None = None,
    run_dir: Path | None = None,
) -> ValidationReport:
    """校验 spec 并可选写入 ``spec_validation.json``。"""
    gate = profile.validation.spec
    if not gate.enabled:
        report = build_validation_report(
            ValidationTarget.SPEC,
            [],
            block_on=gate.block_on,
        )
    else:
        violations = validate_spec_rules(spec, profile)
        md_dir = run_dir or (writer.directory if writer else None)
        violations.extend(validate_spec_md_file(spec, md_dir))
        report = build_validation_report(
            ValidationTarget.SPEC,
            violations,
            block_on=gate.block_on,
        )
    if writer is not None:
        writer.write_model("spec_validation.json", report)
    log_validation_result(logger, target="spec", report=report)
    return report
