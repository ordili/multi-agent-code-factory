"""Run directory artifact filenames (PRD ring)."""

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
