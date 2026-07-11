"""PRD semantic narrow-trigger heuristics (PRD-S01)."""

from __future__ import annotations

import re

from multi_agent_code_factory.schemas.prd import PrdArtifact

_INPUT_SIGNAL_RE = re.compile(
    r"输入|解析|parse|expression|submit|upload|请求体|输入格式",
    re.IGNORECASE,
)
_PARSEABLE_OBJECT_RE = re.compile(
    r"数字|表达式|请求|文件|number|expression|request|body|input",
    re.IGNORECASE,
)
_GLOSSARY_INPUT_RE = re.compile(r"表达式|请求体|输入格式|input", re.IGNORECASE)
_SUBCOMMAND_CLI_RE = re.compile(
    r"\b(add|list|done|create|delete|update)\b|子命令|subcommand",
    re.IGNORECASE,
)
_STRUCTURED_INTERFACES = frozenset({"api", "web", "form"})


def _text_has_freeform_input_signal(text: str) -> bool:
    return bool(_INPUT_SIGNAL_RE.search(text) and _PARSEABLE_OBJECT_RE.search(text))


def prd_requires_semantic_constraints(prd: PrdArtifact) -> bool:
    """True when narrow trigger requires non-empty semantic_constraints."""
    interface = str(prd.context.get("interface", "")).strip().lower()
    if interface in _STRUCTURED_INTERFACES:
        return True

    for story in prd.user_stories:
        blob = f"{story.want} {story.so_that}"
        if _text_has_freeform_input_signal(blob):
            return True
    for feature in prd.features:
        if _text_has_freeform_input_signal(feature.description):
            return True

    glossary = prd.context.get("glossary")
    if isinstance(glossary, list):
        for item in glossary:
            if not isinstance(item, dict):
                continue
            term = str(item.get("term", ""))
            definition = str(item.get("definition", ""))
            if _GLOSSARY_INPUT_RE.search(f"{term} {definition}"):
                return True

    if interface == "cli":
        combined = " ".join(
            [story.want for story in prd.user_stories]
            + [feature.description for feature in prd.features]
        )
        if _SUBCOMMAND_CLI_RE.search(combined) and not any(
            _text_has_freeform_input_signal(story.want) for story in prd.user_stories
        ):
            return False

    return False
