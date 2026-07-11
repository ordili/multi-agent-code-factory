"""prd_validate 节点：对 prd 产物执行规则校验。"""

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
from multi_agent_code_factory.validators._semantic_report import (
    build_gate_validation_report,
)
from multi_agent_code_factory.validators.prd_md_rules import validate_prd_md_file
from multi_agent_code_factory.validators.prd_rules import validate_prd_rules
from multi_agent_code_factory.validators.prd_semantic_rules import (
    validate_prd_semantic_rules,
)

logger = get_logger("nodes.prd_validate")


def _load_prd_md_text(run_dir: Path | None) -> str | None:
    if run_dir is None:
        return None
    path = run_dir / "prd.md"
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def run_prd_validate(
    prd: PrdArtifact,
    profile: ProfileConfig,
    *,
    writer: RunArtifactWriter | None = None,
    run_dir: Path | None = None,
) -> ValidationReport:
    """校验 prd 并可选写入 ``prd_validation.json``。"""
    gate = profile.validation.prd
    md_dir = run_dir or (writer.directory if writer else None)
    if not gate.enabled:
        report = build_gate_validation_report(
            ValidationTarget.PRD,
            [],
            block_on=gate.block_on,
            semantic_block_on=gate.semantic_block_on,
        )
    else:
        violations = validate_prd_rules(prd, profile)
        violations.extend(validate_prd_md_file(prd, md_dir))
        violations.extend(
            validate_prd_semantic_rules(
                prd,
                prd_md_text=_load_prd_md_text(md_dir),
            )
        )
        report = build_gate_validation_report(
            ValidationTarget.PRD,
            violations,
            block_on=gate.block_on,
            semantic_block_on=gate.semantic_block_on,
        )
    if writer is not None:
        writer.write_model("prd_validation.json", report)
    log_validation_result(logger, target="prd", report=report)
    return report
