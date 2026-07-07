#!/usr/bin/env python3
"""Validate relative markdown links under docs/design/."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "design"
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def is_external(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https", "mailto") or url.startswith("#")


def resolve_link(source: Path, target: str) -> Path | None:
    target = unquote(target.strip())
    if not target or is_external(target):
        return None
    path_part, *_ = target.split("#", 1)
    if not path_part:
        return source
    resolved = (source.parent / path_part).resolve()
    return resolved


def main() -> int:
    broken: list[tuple[Path, str, Path]] = []
    checked = 0

    for md in sorted(DOCS.rglob("*.md")):
        text = md.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            raw = match.group(1)
            if raw.startswith("<") and raw.endswith(">"):
                raw = raw[1:-1]
            resolved = resolve_link(md, raw)
            if resolved is None:
                continue
            checked += 1
            if not resolved.exists():
                broken.append((md.relative_to(ROOT), raw, resolved.relative_to(ROOT)))

    print(f"Checked {checked} relative links under {DOCS.relative_to(ROOT)}/")
    if not broken:
        print("OK: no broken links")
        return 0

    print(f"BROKEN ({len(broken)}):")
    for src, raw, resolved in broken:
        print(f"  {src}: ({raw}) -> {resolved}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
