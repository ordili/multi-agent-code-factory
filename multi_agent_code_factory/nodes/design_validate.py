"""design_validate graph node."""

from __future__ import annotations

from pathlib import Path

from multi_agent_code_factory.log import get_logger, log_validation_result
from multi_agent_code_factory.profiles import ProfileConfig
from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.schemas.spec import SpecArtifact
from multi_agent_code_factory.schemas.validation_report import (
    ValidationReport,
    ValidationTarget,
    Violation,
)
from multi_agent_code_factory.tools.write_artifact import RunArtifactWriter
from multi_agent_code_factory.validators._report import build_validation_report, warn
from multi_agent_code_factory.validators.design_rules import validate_design_rules

logger = get_logger("nodes.design_validate")


def _check_flow_mmd(run_dir: Path | None) -> list[Violation]:
    if run_dir is None:
        return []
    flow_path = run_dir / "flow.mmd"
    if not flow_path.is_file() or not flow_path.read_text(encoding="utf-8").strip():
        return [
            warn(
                "DES-017",
                "flow.mmd should exist and be non-empty in run directory (MVP check)",
                field="flow.mmd",
            )
        ]
    return []


def run_design_validate(
    design: DesignArtifact,
    profile: ProfileConfig,
    *,
    spec: SpecArtifact | None = None,
    writer: RunArtifactWriter | None = None,
    run_dir: Path | None = None,
) -> ValidationReport:
    gate = profile.validation.design
    if not gate.enabled:
        report = build_validation_report(
            ValidationTarget.DESIGN,
            [],
            block_on=gate.block_on,
        )
    else:
        violations, require_hitl = validate_design_rules(design, profile, spec)
        if not gate.validate_mermaid:
            flow_dir = run_dir or (writer.directory if writer else None)
            violations.extend(_check_flow_mmd(flow_dir))
        report = build_validation_report(
            ValidationTarget.DESIGN,
            violations,
            require_hitl=require_hitl,
            block_on=gate.block_on,
        )
    if writer is not None:
        writer.write_model("design_validation.json", report)
    log_validation_result(logger, target="design", report=report)
    return report
