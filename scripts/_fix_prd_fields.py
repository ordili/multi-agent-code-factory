from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPLS = [
    ("spec: PrdArtifact", "prd: PrdArtifact"),
    ("spec_validation:", "prd_validation:"),
    ("spec_revision_count", "prd_revision_count"),
    ("state.spec", "state.prd"),
    ("self.spec", "self.prd"),
    ("N.SPEC_VALIDATE", "N.PRD_VALIDATE"),
    ("N.SPEC_HITL", "N.PRD_HITL"),
    ("N.ROUTE_AFTER_SPEC_VALIDATE", "N.ROUTE_AFTER_PRD_VALIDATE"),
    ('"prd.json": "spec"', '"prd.json": "prd"'),
    ('"spec": PrdArtifact', '"prd": PrdArtifact'),
    ('fields.get("spec")', 'fields.get("prd")'),
    ("spec_model = spec", "prd_model = prd"),
    ("spec_model", "prd_model"),
    ("using spec fallback", "using prd fallback"),
    (
        "def _resolve_user_request(meta: RunMeta, spec:",
        "def _resolve_user_request(meta: RunMeta, prd:",
    ),
    ("if spec is not None:", "if prd is not None:"),
    ("parts = [spec.title", "parts = [prd.title"),
    ("HitlStage.SPEC", "HitlStage.PRD"),
    ('SPEC = "spec"', 'PRD = "prd"'),
    ("spec_revisions=%s", "prd_revisions=%s"),
    ("spec_validation.passed", "prd_validation.passed"),
    ("spec_validation = ", "prd_validation = "),
]

for path in ROOT.rglob("*.py"):
    rel = path.as_posix()
    if ".venv" in rel or "_fix_prd_fields" in rel or "_apply_prd_r6" in rel:
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    orig = text
    for old, new in REPLS:
        text = text.replace(old, new)
    if text != orig:
        path.write_text(text, encoding="utf-8")
        print("fixed", rel)
