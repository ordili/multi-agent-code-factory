"""PRD-S01 through PRD-S06 semantic validation rules."""

from __future__ import annotations

import re

from multi_agent_code_factory.schemas.prd import (
    FeaturePriority,
    PrdArtifact,
)
from multi_agent_code_factory.schemas.validation_report import Violation
from multi_agent_code_factory.validators._report import error, warn
from multi_agent_code_factory.validators._semantic_syntax import is_valid_semantic_rule
from multi_agent_code_factory.validators.prd_semantic_triggers import (
    prd_requires_semantic_constraints,
)

_SCOPE_OUT_KEYWORDS = re.compile(
    r"链式|混合|chained|mixed|gui|持久化|multi.?step",
    re.IGNORECASE,
)
_FEAT_WIDE_RE = re.compile(
    r"解析|表达式引擎|parse expression|expression engine",
    re.IGNORECASE,
)
_US_NARROW_RE = re.compile(
    r"两个|一个|two|one|binary|二元",
    re.IGNORECASE,
)


def _known_ref_ids(prd: PrdArtifact) -> set[str]:
    ids = {story.id for story in prd.user_stories}
    ids.update(feature.id for feature in prd.features)
    ids.update(req.id for req in prd.requirement_pool)
    return ids


def _text_refs_id(text: str, ref_id: str) -> bool:
    return ref_id.lower() in text.lower()


def _prd_md_has_semantic_section(run_dir_text: str, sem_ids: set[str]) -> bool:
    if "## 语义约束" not in run_dir_text and "## Semantic" not in run_dir_text:
        return False
    return all(sem_id in run_dir_text for sem_id in sem_ids)


def validate_prd_semantic_rules(
    prd: PrdArtifact,
    *,
    prd_md_text: str | None = None,
) -> list[Violation]:
    """Evaluate PRD-S* semantic rules."""
    violations: list[Violation] = []

    if prd_requires_semantic_constraints(prd) and not prd.semantic_constraints:
        violations.append(
            error(
                "PRD-S01",
                "semantic_constraints required for this PRD (narrow trigger)",
                field="semantic_constraints",
            )
        )

    if not prd.semantic_constraints:
        return violations

    known = _known_ref_ids(prd)
    for index, constraint in enumerate(prd.semantic_constraints):
        path = f"/semantic_constraints/{index}"
        if constraint.source_ref not in known:
            violations.append(
                error(
                    "PRD-S02",
                    f"source_ref {constraint.source_ref!r} not found in US/FEAT/REQ",
                    path=f"{path}/source_ref",
                    field="source_ref",
                )
            )
        for key, value in constraint.dimensions.items():
            if not is_valid_semantic_rule(value):
                violations.append(
                    warn(
                        "PRD-S02b",
                        f"dimensions[{key!r}] has invalid rule syntax: {value!r}",
                        path=f"{path}/dimensions/{key}",
                        field="dimensions",
                    )
                )
        for ex_index, exclude in enumerate(constraint.excludes):
            if not is_valid_semantic_rule(exclude.rule):
                violations.append(
                    warn(
                        "PRD-S02b",
                        f"excludes[{ex_index}].rule invalid: {exclude.rule!r}",
                        path=f"{path}/excludes/{ex_index}/rule",
                        field="excludes",
                    )
                )

    if prd.scope_out:
        for index, item in enumerate(prd.scope_out):
            if not _SCOPE_OUT_KEYWORDS.search(item):
                continue
            matched = any(
                _SCOPE_OUT_KEYWORDS.search(exclude.summary)
                or _text_refs_id(exclude.summary, item)
                for constraint in prd.semantic_constraints
                for exclude in constraint.excludes
            ) or any(
                _text_refs_id(req.description, item) for req in prd.requirement_pool
            )
            if not matched:
                violations.append(
                    warn(
                        "PRD-S03",
                        f"scope_out[{index!r}] lacks structured exclude or REQ text",
                        path=f"/scope_out/{index}",
                        field="scope_out",
                    )
                )

    for feature in prd.features:
        if feature.priority != FeaturePriority.P0 or not feature.user_story_ids:
            continue
        if not _FEAT_WIDE_RE.search(feature.description):
            continue
        linked = [
            story for story in prd.user_stories if story.id in feature.user_story_ids
        ]
        if linked and all(_US_NARROW_RE.search(story.want) for story in linked):
            violations.append(
                warn(
                    "PRD-S04",
                    f"FEAT {feature.id} description may be wider than linked US intent",
                    path=f"/features/{feature.id}/description",
                    field="description",
                )
            )

    for constraint in prd.semantic_constraints:
        referenced = any(
            _text_refs_id(ac.description, constraint.id)
            for ac in prd.acceptance_criteria
        ) or any(
            _text_refs_id(req.description, constraint.id)
            for req in prd.requirement_pool
        )
        if not referenced:
            violations.append(
                warn(
                    "PRD-S05",
                    f"{constraint.id} not referenced in AC or requirement_pool text",
                    field="semantic_constraints",
                )
            )

    if prd_md_text is not None:
        sem_ids = {item.id for item in prd.semantic_constraints}
        if not _prd_md_has_semantic_section(prd_md_text, sem_ids):
            violations.append(
                warn(
                    "PRD-S06",
                    "prd.md missing ## 语义约束 section or SEM ids",
                    field="prd.md",
                )
            )

    return violations
