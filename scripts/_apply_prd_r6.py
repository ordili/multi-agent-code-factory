"""Apply PRD full-stack rename (R1-R6) from spec baseline. No legacy shims."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "multi_agent_code_factory"

FILE_RENAMES = [
    ("schemas/spec.py", "schemas/prd.py"),
    ("nodes/spec_validate.py", "nodes/prd_validate.py"),
    ("nodes/spec_hitl.py", "nodes/prd_hitl.py"),
    ("validators/spec_rules.py", "validators/prd_rules.py"),
    ("validators/spec_rules_extended.py", "validators/prd_rules_extended.py"),
    ("validators/spec_md_rules.py", "validators/prd_md_rules.py"),
    ("renderers/spec_md.py", "renderers/prd_md.py"),
    ("agents/normalizers/spec.py", "agents/normalizers/prd.py"),
]

TEST_RENAMES = [
    ("tests/test_spec_rules_extended.py", "tests/test_prd_rules_extended.py"),
    ("tests/test_spec_md_renderer.py", "tests/test_prd_md_renderer.py"),
]

SNIPPET_RENAMES = [
    (
        "docs/design/pipeline/examples/snippets/spec-default.json",
        "docs/design/pipeline/examples/snippets/prd-default.json",
    ),
]

TEXT_REPLACEMENTS = [
    ("SpecArtifact", "PrdArtifact"),
    ("coerce_spec_payload", "coerce_prd_payload"),
    ("render_spec_md", "render_prd_md"),
    ("validate_spec_rules", "validate_prd_rules"),
    ("validate_spec_extended_rules", "validate_prd_extended_rules"),
    ("validate_spec_md_rules", "validate_prd_md_rules"),
    ("validate_spec_md_file", "validate_prd_md_file"),
    ("run_spec_validate", "run_prd_validate"),
    ("run_spec_hitl", "run_prd_hitl"),
    ("normalize_spec", "normalize_prd"),
    ("trim_spec", "trim_prd"),
    ("format_spec_validation_feedback", "format_prd_validation_feedback"),
    ("decide_after_spec_validate", "decide_after_prd_validate"),
    ("route_after_spec_validate", "route_after_prd_validate"),
    ("node_spec_validate", "node_prd_validate"),
    ("node_spec_hitl", "node_prd_hitl"),
    ("node_route_after_spec_validate", "node_route_after_prd_validate"),
    ("PipelineNode.SPEC_VALIDATE", "PipelineNode.PRD_VALIDATE"),
    ("PipelineNode.SPEC_HITL", "PipelineNode.PRD_HITL"),
    ("PipelineNode.ROUTE_AFTER_SPEC_VALIDATE", "PipelineNode.ROUTE_AFTER_PRD_VALIDATE"),
    ('"spec_validate"', '"prd_validate"'),
    ("'spec_validate'", "'prd_validate'"),
    ('"spec_hitl"', '"prd_hitl"'),
    ("'spec_hitl'", "'prd_hitl'"),
    ('"route_after_spec_validate"', '"route_after_prd_validate"'),
    ("state.spec", "state.prd"),
    ("state.spec_validation", "state.prd_validation"),
    ("state.spec_revision_count", "state.prd_revision_count"),
    ('"spec_validation"', '"prd_validation"'),
    ('"spec_revision_count"', '"prd_revision_count"'),
    ('"spec.json"', '"prd.json"'),
    ('"spec.md"', '"prd.md"'),
    ("spec_validation.json", "prd_validation.json"),
    ("spec-default.json", "prd-default.json"),
    ("ValidationTarget.SPEC", "ValidationTarget.PRD"),
    ('ValidationTarget("spec")', 'ValidationTarget("prd")'),
    ("HitlStage.SPEC", "HitlStage.PRD"),
    ("validation.spec", "validation.prd"),
    ("max_spec_revisions", "max_prd_revisions"),
    ("FACTORY_MAX_SPEC_REVISIONS", "FACTORY_MAX_PRD_REVISIONS"),
    ("--max-spec-revisions", "--max-prd-revisions"),
    ("SPEC_VALIDATE_RETRY", "PRD_VALIDATE_RETRY"),
    ("spec_validate_retry", "prd_validate_retry"),
    ("schemas.spec", "schemas.prd"),
    ("nodes.spec_validate", "nodes.prd_validate"),
    ("nodes.spec_hitl", "nodes.prd_hitl"),
    ("validators.spec_rules", "validators.prd_rules"),
    ("validators.spec_rules_extended", "validators.prd_rules_extended"),
    ("validators.spec_md_rules", "validators.prd_md_rules"),
    ("renderers.spec_md", "renderers.prd_md"),
    ("agents.normalizers.spec", "agents.normalizers.prd"),
    ("SPEC-", "PRD-"),
    ('target="spec"', 'target="prd"'),
    ('stage="spec"', 'stage="prd"'),
    ("test_spec_", "test_prd_"),
    ("test_normalize_spec", "test_normalize_prd"),
    ("fixtures.spec", "fixtures.prd"),
    ("StubFixturePaths(\n    spec=", "StubFixturePaths(\n    prd="),
]

SKIP_IF_CONTAINS = (
    "spec_ref",
    "provider_spec",
    "spec_implies",
    "is_spec_",
    "spec_requires",
    "spec_has_",
    "spec_context",
    "spec-default",  # handled by rename
    "_apply_prd_r6",
    "prd-spec.md",
)


def _apply_line(line: str) -> str:
    if any(s in line for s in SKIP_IF_CONTAINS):
        return line
    out = line
    for old, new in TEXT_REPLACEMENTS:
        out = out.replace(old, new)
    return out


def transform_text(text: str) -> str:
    return "".join(_apply_line(line) for line in text.splitlines(keepends=True))


def process_tree(root: Path, patterns: tuple[str, ...]) -> None:
    for pattern in patterns:
        for path in root.rglob(pattern):
            if any(part.startswith(".") for part in path.parts):
                continue
            rel = path.relative_to(ROOT).as_posix()
            if "_apply_prd_r6" in rel:
                continue
            text = path.read_text(encoding="utf-8")
            new_text = transform_text(text)
            if new_text != text:
                path.write_text(new_text, encoding="utf-8")


def main() -> None:
    for old_rel, new_rel in FILE_RENAMES:
        src = PKG / old_rel
        dst = PKG / new_rel
        if not src.is_file():
            continue
        text = transform_text(src.read_text(encoding="utf-8"))
        dst.write_text(text, encoding="utf-8")
        src.unlink()

    for old_rel, new_rel in TEST_RENAMES:
        src = ROOT / old_rel
        dst = ROOT / new_rel
        if not src.is_file():
            continue
        dst.write_text(
            transform_text(src.read_text(encoding="utf-8")), encoding="utf-8"
        )
        src.unlink()

    for old_rel, new_rel in SNIPPET_RENAMES:
        src = ROOT / old_rel
        dst = ROOT / new_rel
        if src.is_file() and not dst.is_file():
            shutil.copy2(src, dst)
            src.unlink()
        elif src.is_file() and dst.is_file():
            src.unlink()

    # run_artifact_names.py
    names = PKG / "run_artifact_names.py"
    names.write_text(
        '''"""Run directory artifact filenames (PRD ring)."""

from __future__ import annotations

PRD_JSON = "prd.json"
PRD_MD = "prd.md"
PRD_VALIDATION_JSON = "prd_validation.json"

PRD_ARTIFACT_FILENAMES = (PRD_JSON,)
PRD_MD_FILENAMES = (PRD_MD,)
PRD_VALIDATION_FILENAMES = (PRD_VALIDATION_JSON,)


def resolve_existing(run_dir, filenames: tuple[str, ...]):
    """Return first existing filename under run_dir, else None."""
    from pathlib import Path

    base = Path(run_dir)
    for name in filenames:
        if (base / name).is_file():
            return name
    return None
''',
        encoding="utf-8",
    )

    process_tree(ROOT / "multi_agent_code_factory", ("*.py", "*.yaml", "*.txt"))
    process_tree(ROOT / "tests", ("*.py",))
    process_tree(ROOT / "config", ("*.yaml",))
    process_tree(ROOT / "domains", ("*.yaml",))
    process_tree(ROOT / "scripts", ("*.py",))

    debug_old = ROOT / "scripts" / "debug_pm_spec_llm.py"
    debug_new = ROOT / "scripts" / "debug_pm_prd_llm.py"
    if debug_old.is_file():
        text = transform_text(debug_old.read_text(encoding="utf-8"))
        text = text.replace("debug_pm_spec_llm.py", "debug_pm_prd_llm.py")
        text = re.sub(r"spec\.md", "prd.md", text)
        text = re.sub(r"spec_validation", "prd_validation", text)
        text = re.sub(r"spec\.context", "prd.context", text)
        debug_new.write_text(text, encoding="utf-8")
        debug_old.unlink()

    # schemas/prd.py from recovered copy if checkout left spec only
    prd_schema = PKG / "schemas" / "prd.py"
    if not prd_schema.is_file() and (PKG / "schemas" / "spec.py").is_file():
        prd_schema.write_text(
            transform_text((PKG / "schemas" / "spec.py").read_text(encoding="utf-8")),
            encoding="utf-8",
        )
        (PKG / "schemas" / "spec.py").unlink()

    print("PRD R1-R6 migration applied")


if __name__ == "__main__":
    main()
