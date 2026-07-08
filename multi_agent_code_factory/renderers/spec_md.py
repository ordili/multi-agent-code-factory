"""spec.json → spec.md 渲染器（中文固定章节）。"""

from __future__ import annotations

from typing import Any

from multi_agent_code_factory.schemas.spec import SpecArtifact


def _glossary_entries(context: dict[str, Any]) -> list[dict[str, str]]:
    raw = context.get("glossary")
    if not isinstance(raw, list):
        return []
    entries: list[dict[str, str]] = []
    for item in raw:
        if isinstance(item, dict):
            term = item.get("term")
            definition = item.get("definition")
            if isinstance(term, str) and isinstance(definition, str):
                entries.append({"term": term, "definition": definition})
    return entries


def _context_lines(context: dict[str, Any]) -> list[str]:
    skip = {"language", "glossary"}
    lines: list[str] = []
    for key, value in context.items():
        if key in skip:
            continue
        if value is None or value == "":
            continue
        if isinstance(value, (dict, list)):
            continue
        lines.append(f"- **{key}：** `{value}`")
    return lines


def render_spec_md(spec: SpecArtifact) -> str:
    """将 SpecArtifact 渲染为人类可读的 Markdown 文档。"""
    lines: list[str] = [
        f"# {spec.title}",
        "",
        "## 概述",
        "",
        spec.summary,
        "",
        f"- **Profile：** `{spec.profile}`",
        f"- **Revision：** {spec.revision}",
    ]
    if spec.parent_task_id:
        lines.append(f"- **Parent task：** `{spec.parent_task_id}`")
    lines.append("")

    lines.extend(["## 术语与领域概念", ""])
    glossary = _glossary_entries(spec.context)
    if glossary:
        lines.extend(["| 名词 | 解释 |", "|------|------|"])
        for entry in glossary:
            lines.append(f"| {entry['term']} | {entry['definition']} |")
    else:
        lines.append("—")
    lines.append("")

    lines.extend(["## 背景与上下文", ""])
    context_lines = _context_lines(spec.context)
    if context_lines:
        lines.extend(context_lines)
    else:
        lines.append("—")
    lines.append("")

    if spec.success_metrics:
        lines.extend(["## 业务指标", ""])
        for metric in spec.success_metrics:
            lines.append(
                f"- **{metric.id}** {metric.name}: {metric.target} "
                f"(`{metric.verifiable_by.value}`)"
            )
        lines.append("")

    lines.extend(["## 功能", ""])
    for feature in spec.features:
        lines.append(
            f"- **{feature.id}** ({feature.priority.value}) {feature.name}: "
            f"{feature.description}"
        )
    lines.append("")

    lines.extend(["## 用户故事", ""])
    if spec.user_stories:
        lines.extend(["| ID | 作为 | 我想要 | 以便 |", "|----|------|--------|------|"])
        for story in spec.user_stories:
            lines.append(
                f"| {story.id} | {story.as_a} | {story.want} | {story.so_that} |"
            )
    else:
        lines.append("—")
    lines.append("")

    lines.extend(["## 需求池", ""])
    if spec.requirement_pool:
        lines.extend(["| ID | 描述 | 优先级 | 依赖 |", "|----|------|--------|------|"])
        for req in spec.requirement_pool:
            priority = (
                req.priority.value
                if hasattr(req.priority, "value")
                else str(req.priority)
            )
            deps = "、".join(req.depends_on) if req.depends_on else "—"
            feature = f" → `{req.feature_id}`" if req.feature_id else ""
            lines.append(
                f"| {req.id} | {req.description}{feature} | {priority} | {deps} |"
            )
    else:
        lines.append("—")
    lines.append("")

    lines.extend(["## 范围", ""])
    lines.append("**纳入：**")
    for item in spec.scope_in:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("**排除：**")
    if spec.scope_out:
        for item in spec.scope_out:
            lines.append(f"- {item}")
    else:
        lines.append("- —")
    lines.append("")

    op = spec.operational_profile
    cp = spec.consistency_profile
    lines.extend(
        [
            "## 稳定性、性能与数据一致性",
            "",
            f"- **用户体量：** `{op.user_scale.value}`",
            f"- **高并发：** `{op.high_concurrency}`",
            f"- **性能档位：** `{op.performance.tier.value}`",
        ]
    )
    if op.performance.notes:
        lines.append(f"- **性能说明：** {op.performance.notes}")
    lines.extend(
        [
            f"- **一致性模型：** `{cp.consistency_model.value}`",
            f"- **投递语义：** `{cp.delivery.value}`",
            f"- **多写者：** `{cp.multi_writer}`",
            f"- **幂等要求：** `{cp.idempotency_required}`",
        ]
    )
    if cp.conflict_strategy is not None:
        lines.append(f"- **冲突策略：** `{cp.conflict_strategy.value}`")
    if cp.notes:
        lines.append(f"- **一致性说明：** {cp.notes}")
    lines.append("")

    lines.extend(["## 验收标准", ""])
    for ac in spec.acceptance_criteria:
        lines.append(f"- **{ac.id}** {ac.description} (`{ac.verifiable_by.value}`)")
    lines.append("")

    lines.extend(["## 约束", ""])
    if spec.constraints:
        for item in spec.constraints:
            lines.append(f"- {item}")
    else:
        lines.append("无额外约束。")
    lines.extend(
        [
            "",
            "## 待澄清项",
            "",
            "None",
            "",
            "---",
            "",
            f"task_profile: `{spec.profile}` · revision: `{spec.revision}`",
        ]
    )
    if spec.parent_task_id:
        lines.append(f"parent_task_id: `{spec.parent_task_id}`")
    else:
        lines.append("parent_task_id: —")
    lines.append("")
    return "\n".join(lines)
