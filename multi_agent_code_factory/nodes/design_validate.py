"""design_validate 图节点：对 design 产物执行规则校验。"""

from __future__ import annotations

from pathlib import Path

from multi_agent_code_factory.log import get_logger, log_validation_result
from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.schemas.prd import PrdArtifact
from multi_agent_code_factory.schemas.validation_report import (
    ValidationReport,
    ValidationTarget,
)
from multi_agent_code_factory.tools.run_artifacts import RunArtifactWriter
from multi_agent_code_factory.validators._semantic_report import (
    build_gate_validation_report,
)
from multi_agent_code_factory.validators.design_md_rules import validate_design_md_file
from multi_agent_code_factory.validators.design_rules import validate_design_rules
from multi_agent_code_factory.validators.design_semantic_rules import (
    validate_design_semantic_rules,
)
from multi_agent_code_factory.validators.mermaid import validate_mermaid_files

logger = get_logger("nodes.design_validate")


def run_design_validate(
    design: DesignArtifact,
    profile: ProfileConfig,
    *,
    spec: PrdArtifact | None = None,
    writer: RunArtifactWriter | None = None,
    run_dir: Path | None = None,
) -> ValidationReport:
    """校验 design 并可选写入 ``design_validation.json``。"""
    gate = profile.validation.design
    flow_dir = run_dir or (writer.directory if writer else None)
    if not gate.enabled:
        report = build_gate_validation_report(
            ValidationTarget.DESIGN,
            [],
            block_on=gate.block_on,
            semantic_block_on=gate.semantic_block_on,
        )
    else:
        violations, require_hitl = validate_design_rules(design, profile, spec)
        violations.extend(validate_design_md_file(design, flow_dir, spec=spec))
        violations.extend(
            validate_mermaid_files(
                design,
                flow_dir,
                strict=gate.validate_mermaid,
                spec=spec,
            )
        )
        violations.extend(validate_design_semantic_rules(design, spec))
        report = build_gate_validation_report(
            ValidationTarget.DESIGN,
            violations,
            require_hitl=require_hitl,
            block_on=gate.block_on,
            semantic_block_on=gate.semantic_block_on,
        )
    if writer is not None:
        writer.write_model("design_validation.json", report)
    log_validation_result(logger, target="design", report=report)
    return report
