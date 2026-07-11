"""Semantic constraint rule-syntax whitelist (PRD-S02b)."""

from __future__ import annotations

import re

_RULE_PREFIXES = (
    re.compile(r"^exactly:\d+$"),
    re.compile(r"^gte:\d+$"),
    re.compile(r"^lte:\d+$"),
    re.compile(r"^one_of:.+$"),
    re.compile(r"^type:(number|string|boolean)$"),
)


def is_valid_semantic_rule(value: str) -> bool:
    """Return True when value matches V1 semantic rule syntax."""
    text = value.strip()
    if not text:
        return False
    return any(pattern.match(text) for pattern in _RULE_PREFIXES)


def parse_one_of_values(rule: str) -> list[str]:
    """Extract enum tokens from a one_of: rule string."""
    if not rule.strip().startswith("one_of:"):
        return []
    body = rule.split(":", 1)[1]
    return [part.strip() for part in body.split(",") if part.strip()]
