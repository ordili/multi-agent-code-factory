"""Fix prd rename doc link corruption and remaining spec→prd run-path references."""
# ruff: noqa: E501

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "design" / "pipeline"

# Over-aggressive bulk replace broke *-spec.md links into *-prd.md for non-PRD artifacts.
LINK_FIXES = [
    ("prd-prd.md", "prd-spec.md"),
    ("design-prd.md", "design-spec.md"),
    ("flow-prd.md", "flow-spec.md"),
    ("validation-report-prd.md", "validation-report-spec.md"),
    ("hitl-prd.md", "hitl-spec.md"),
    ("run-meta-prd.md", "run-meta-spec.md"),
    ("dev-principles-prd.md", "dev-principles-spec.md"),
    ("test-report-prd.md", "test-report-spec.md"),
    ("review-prd.md", "review-spec.md"),
    ("dev-manifest-prd.md", "dev-manifest-spec.md"),
]

RUN_PATH_FIXES = [
    ("Run `spec.json`", "Run `prd.json`"),
    ("Run `spec.md`", "Run `prd.md`"),
    ("→ Run `spec.md`", "→ Run `prd.md`"),
    ("Run 含 `spec.json`", "Run 含 `prd.json`"),
    ("同目录 `spec.json`", "同目录 `prd.json`"),
    ("上游 `spec.json`", "上游 `prd.json`"),
    ("`spec.json`", "`prd.json`"),
    ("`spec.md`", "`prd.md`"),
    ("spec-validate.md", "prd-validate.md"),
    ("spec_md.py", "prd_md.py"),
    ("spec_md_rules.py", "prd_md_rules.py"),
    ("spec_rules.py", "prd_rules.py"),
    ("SpecArtifact", "PrdArtifact"),
    ("stage=spec", "stage=prd"),
    ("#spec--design-传导只读", "#prd--design-传导只读"),
    ("spec→design 传导", "prd→design 传导"),
    ("[spec→design 传导]", "[prd→design 传导]"),
    ("spec 基线", "prd 基线"),
    ("spec 侧信号", "prd 侧信号"),
    ("spec / design", "prd / design"),
    ("`spec` / `design`", "`prd` / `design`"),
    ("`spec` \\| `design`", "`prd` \\| `design`"),
    ("validation:\n  spec:", "validation:\n  prd:"),
]

# Revert accidental prd.json replacements inside design-spec context (spec_ref field docs)
REVERT_IN_DESIGN = [
    ("与上游 `prd.json` **的** `title`", "与上游 `prd.json` **的** `title`"),  # keep
]


def fix_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    original = text

    for old, new in LINK_FIXES:
        text = text.replace(old, new)

    # Run-path and naming fixes — skip design-spec files for spec_ref lines
    is_design_schema = path.name == "design-spec.md" and "artifact-schemas" in str(path)
    for old, new in RUN_PATH_FIXES:
        if is_design_schema and old == "`spec.json`":
            continue
        text = text.replace(old, new)

    # design-spec.md: spec_ref still references upstream prd.json (correct after fix)
    if path.name == "design-spec.md":
        text = text.replace(
            "与上游 `prd.json` **的** `title`", "与上游 `prd.json` **的** `title`"
        )

    # H1 title fixes for corrupted headers
    text = re.sub(
        r"^# design-spec\.md —",
        "# design-spec.md —",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if (
        text.startswith("# design-spec.md —") is False
        and "# design-spec.md —" in text[:200]
    ):
        pass  # already fixed via design-prd → design-spec

    path.write_text(text, encoding="utf-8")
    return text != original


def main() -> None:
    changed = 0
    for path in DOCS.rglob("*.md"):
        if fix_file(path):
            changed += 1
            print(path.relative_to(ROOT))
    print(f"updated {changed} files")


if __name__ == "__main__":
    main()
