"""Fix param/body mismatches after PRD rename."""
# ruff: noqa: E501

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PRD_BODY_FILES = [
    "multi_agent_code_factory/validators/prd_rules.py",
    "multi_agent_code_factory/validators/prd_rules_extended.py",
    "multi_agent_code_factory/validators/prd_md_rules.py",
    "multi_agent_code_factory/renderers/prd_md.py",
    "multi_agent_code_factory/agents/normalizers/prd.py",
    "multi_agent_code_factory/prompt_context.py",
    "multi_agent_code_factory/prompt_context_trim.py",
]

DESIGN_PARAM_FILES = [
    "multi_agent_code_factory/validators/design_rules.py",
    "multi_agent_code_factory/validators/design_rules_extended.py",
    "multi_agent_code_factory/validators/design_md_rules.py",
    "multi_agent_code_factory/validators/design_triggers.py",
    "multi_agent_code_factory/validators/mermaid.py",
    "multi_agent_code_factory/nodes/design_validate.py",
    "multi_agent_code_factory/agents/normalizers/design_enrichment.py",
]


def fix_prd_bodies(text: str) -> str:
    return re.sub(r"\bspec\.", "prd.", text)


def fix_design_params(text: str) -> str:
    text = re.sub(
        r"(\bdef \w+\([^)]*?\b)prd(\s*:\s*PrdArtifact)",
        r"\1spec\2",
        text,
    )
    text = re.sub(
        r"(\bdef \w+\([^)]*?, )prd(\s*:\s*PrdArtifact)",
        r"\1spec\2",
        text,
    )
    return text


def fix_artifact_loader(text: str) -> str:
    return text.replace(
        '    spec = fields.get("prd")\n'
        "    prd_model = prd if isinstance(spec, PrdArtifact) else None\n",
        '    prd = fields.get("prd")\n'
        "    prd_model = prd if isinstance(prd, PrdArtifact) else None\n",
    )


def fix_validation_config(text: str) -> str:
    if "class ValidationConfig" not in text:
        return text
    text = text.replace(
        "class ValidationConfig(BaseModel):\n"
        "    spec: ValidationGateConfig = Field(default_factory=ValidationGateConfig)",
        "class ValidationConfig(BaseModel):\n"
        "    prd: ValidationGateConfig = Field(default_factory=ValidationGateConfig)",
    )
    if "model_validator" not in text:
        text = text.replace(
            "from pydantic import BaseModel, Field, field_validator",
            "from pydantic import BaseModel, Field, field_validator, model_validator",
        )
        insert = """
    @model_validator(mode="before")
    @classmethod
    def _coerce_legacy_spec_key(cls, data: object) -> object:
        if isinstance(data, dict):
            payload = dict(data)
            if "spec" in payload and "prd" not in payload:
                payload["prd"] = payload.pop("spec")
            else:
                payload.pop("spec", None)
            return payload
        return data

"""
        text = text.replace(
            "class ValidationConfig(BaseModel):\n"
            "    prd: ValidationGateConfig = Field(default_factory=ValidationGateConfig)\n"
            "    design: ValidationGateConfig = Field(default_factory=ValidationGateConfig)",
            "class ValidationConfig(BaseModel):\n"
            "    prd: ValidationGateConfig = Field(default_factory=ValidationGateConfig)\n"
            "    design: ValidationGateConfig = Field(default_factory=ValidationGateConfig)"
            + insert,
        )
    return text


def fix_tests(text: str) -> str:
    text = text.replace("spec_validation=", "prd_validation=")
    text = text.replace("PipelineState(spec=", "PipelineState(prd=")
    text = text.replace(", spec=", ", prd=")
    text = text.replace(
        "enrich_design_for_validation(spec=", "enrich_design_for_validation(prd="
    )
    text = text.replace(
        "validate_design_md_rules(spec=", "validate_design_md_rules(spec="
    )
    text = text.replace("run_design_validate(spec=", "run_design_validate(spec=")
    return text


def main() -> None:
    for rel in PRD_BODY_FILES:
        path = ROOT / rel
        if path.is_file():
            path.write_text(
                fix_prd_bodies(path.read_text(encoding="utf-8")), encoding="utf-8"
            )
            print("prd body", rel)

    for rel in DESIGN_PARAM_FILES:
        path = ROOT / rel
        if path.is_file():
            path.write_text(
                fix_design_params(path.read_text(encoding="utf-8")), encoding="utf-8"
            )
            print("design param", rel)

    loader = ROOT / "multi_agent_code_factory/artifact_loader.py"
    loader.write_text(
        fix_artifact_loader(loader.read_text(encoding="utf-8")), encoding="utf-8"
    )

    models = ROOT / "multi_agent_code_factory/profile_config/models.py"
    models.write_text(
        fix_validation_config(models.read_text(encoding="utf-8")), encoding="utf-8"
    )

    for path in (ROOT / "tests").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        new = fix_tests(text)
        if new != text:
            path.write_text(new, encoding="utf-8")
            print("test", path.relative_to(ROOT))

    fb = ROOT / "tests/agents/llm/test_validation_feedback.py"
    if fb.is_file():
        t = fb.read_text(encoding="utf-8").replace(
            "spec_validation=", "prd_validation="
        )
        fb.write_text(t, encoding="utf-8")


if __name__ == "__main__":
    main()
