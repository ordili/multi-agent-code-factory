"""spec_validate graph node."""

from __future__ import annotations

from multi_agent_code_factory.profiles import ProfileConfig
from multi_agent_code_factory.schemas.spec import SpecArtifact
from multi_agent_code_factory.schemas.validation_report import (
    ValidationReport,
    ValidationTarget,
)
from multi_agent_code_factory.tools.write_artifact import RunArtifactWriter
from multi_agent_code_factory.validators._report import build_validation_report
from multi_agent_code_factory.validators.spec_rules import validate_spec_rules


def run_spec_validate(
    spec: SpecArtifact,
    profile: ProfileConfig,
    *,
    writer: RunArtifactWriter | None = None,
) -> ValidationReport:
    gate = profile.validation.spec
    if not gate.enabled:
        report = build_validation_report(
            ValidationTarget.SPEC,
            [],
            block_on=gate.block_on,
        )
    else:
        violations = validate_spec_rules(spec, profile)
        report = build_validation_report(
            ValidationTarget.SPEC,
            violations,
            block_on=gate.block_on,
        )
    if writer is not None:
        writer.write_model("spec_validation.json", report)
    return report
