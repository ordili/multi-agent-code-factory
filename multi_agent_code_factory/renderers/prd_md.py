"""prd.json → prd.md 渲染器（中文固定章节，对齐 prd-spec 模板）。"""

from __future__ import annotations

from typing import Any

from multi_agent_code_factory.schemas.prd import (
    ConsistencyModel,
    PerformanceTier,
    PrdArtifact,
    UserScale,
    VerifiableBy,
)

_NON_PERSISTENT_STORAGE = frozenset(
    {"", "none", "memory", "in_memory", "in-memory", "stateless"}
)

_USER_SCALE_LABELS = {
    UserScale.PERSONAL: "个人使用",
    UserScale.TEAM: "团队使用",
    UserScale.MULTI_TENANT: "多租户",
    UserScale.INTERNET: "互联网规模",
}

_PERFORMANCE_TIER_LABELS = {
    PerformanceTier.BEST_EFFORT: "尽力而为",
    PerformanceTier.INTERACTIVE: "交互可感知",
    PerformanceTier.LOW_LATENCY: "低延迟",
    PerformanceTier.CUSTOM: "自定义",
}

_CONSISTENCY_MODEL_LABELS = {
    ConsistencyModel.LOCAL_ONLY: "本地单写",
    ConsistencyModel.STRONG: "强一致",
    ConsistencyModel.EVENTUAL: "最终一致",
    ConsistencyModel.SESSION: "会话级",
    ConsistencyModel.CUSTOM: "自定义",
}

_VERIFIABLE_BY_LABELS = {
    VerifiableBy.AUTOMATED_TEST: "automated_test",
    VerifiableBy.MANUAL: "manual",
    VerifiableBy.DEPLOY_CHECK: "deploy_check",
    VerifiableBy.LINT: "lint",
}


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


def _storage_kind(spec: PrdArtifact) -> str | None:
    storage = spec.context.get("storage")
    if isinstance(storage, str) and storage.strip():
        return storage.strip().lower()
    return None


def _consistency_nfr_trivial(spec: PrdArtifact) -> bool:
    storage = _storage_kind(spec)
    if storage and storage not in _NON_PERSISTENT_STORAGE:
        return False
    cp = spec.consistency_profile
    return (
        cp.consistency_model == ConsistencyModel.LOCAL_ONLY
        and not cp.multi_writer
        and not cp.idempotency_required
    )


def render_prd_md(spec: PrdArtifact) -> str:
    """将 PrdArtifact 渲染为人类可读的 Markdown 文档。"""
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
        lines.append("无")
    lines.append("")

    lines.extend(["## 背景与上下文", ""])
    context_lines = _context_lines(spec.context)
    if context_lines:
        lines.extend(context_lines)
    else:
        lines.append("—")
    lines.append("")

    lines.extend(["## 业务指标", ""])
    if spec.success_metrics:
        lines.extend(
            [
                "| ID | 名称 | 目标 | 验证方式 |",
                "|----|------|------|----------|",
            ]
        )
        for metric in spec.success_metrics:
            verifiable = _VERIFIABLE_BY_LABELS.get(
                metric.verifiable_by, metric.verifiable_by.value
            )
            lines.append(
                f"| {metric.id} | {metric.name} | {metric.target} | {verifiable} |"
            )
    else:
        lines.append("无")
    lines.append("")

    lines.extend(["## 功能", ""])
    for feature in spec.features:
        story_refs = ""
        if feature.user_story_ids:
            story_refs = f" — {', '.join(feature.user_story_ids)}"
        lines.append(
            f"- **{feature.id}** ({feature.priority.value}) {feature.name}: "
            f"{feature.description}{story_refs}"
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

    if spec.semantic_constraints:
        lines.extend(["## 语义约束", ""])
        lines.extend(["| ID | 来源 | 类型 | 摘要 |", "|----|------|------|------|"])
        for constraint in spec.semantic_constraints:
            lines.append(
                f"| {constraint.id} | {constraint.source_ref} | "
                f"{constraint.kind.value} | {constraint.summary} |"
            )
        lines.append("")
        for constraint in spec.semantic_constraints:
            dim_text = "；".join(
                f"{key}={value}" for key, value in constraint.dimensions.items()
            )
            lines.append(f"**{constraint.id} 维度：** {dim_text}")
            if constraint.excludes:
                exclude_text = "；".join(item.summary for item in constraint.excludes)
                lines.append(f"**{constraint.id} 明确排除：** {exclude_text}")
            lines.append("")

    lines.extend(["## 范围", ""])
    lines.append("**本次包含**")
    lines.append("")
    for item in spec.scope_in:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("**明确不做**")
    lines.append("")
    if spec.scope_out:
        for item in spec.scope_out:
            lines.append(f"- {item}")
    else:
        lines.append("无")
    lines.append("")

    op = spec.operational_profile
    cp = spec.consistency_profile
    lines.extend(["## 非功能性需求", ""])

    lines.extend(["### 稳定性与性能", ""])
    scale_label = _USER_SCALE_LABELS.get(op.user_scale, op.user_scale.value)
    tier_label = _PERFORMANCE_TIER_LABELS.get(
        op.performance.tier, op.performance.tier.value
    )
    perf_desc = tier_label
    if op.performance.notes:
        perf_desc = f"{tier_label} — {op.performance.notes}"
    lines.extend(
        [
            "| 项 | 说明 |",
            "|----|------|",
            f"| 用户体量 | {scale_label} |",
            f"| 高并发 | {'是' if op.high_concurrency else '否'} |",
            f"| 性能预期 | {perf_desc} |",
            "",
        ]
    )

    lines.extend(["### 数据一致性", ""])
    if _consistency_nfr_trivial(spec):
        lines.append("无")
    else:
        model_label = _CONSISTENCY_MODEL_LABELS.get(
            cp.consistency_model, cp.consistency_model.value
        )
        lines.extend(
            [
                "| 项 | 说明 |",
                "|----|------|",
                f"| 一致性模型 | {model_label} |",
                f"| 投递语义 | {cp.delivery.value} |",
                f"| 多写者 | {'是' if cp.multi_writer else '否'} |",
                f"| 须幂等 | {'是' if cp.idempotency_required else '否'} |",
            ]
        )
        if cp.conflict_strategy is not None:
            lines.append(f"| 冲突策略 | {cp.conflict_strategy.value} |")
        if cp.notes:
            lines.append(f"| 说明 | {cp.notes} |")
    lines.append("")

    lines.extend(["## 验收标准", ""])
    lines.extend(
        [
            "| ID | 描述 | 验证方式 |",
            "|----|------|----------|",
        ]
    )
    for ac in spec.acceptance_criteria:
        verifiable = _VERIFIABLE_BY_LABELS.get(ac.verifiable_by, ac.verifiable_by.value)
        lines.append(f"| {ac.id} | {ac.description} | {verifiable} |")
    lines.append("")

    lines.extend(["## 约束", ""])
    if spec.constraints:
        for item in spec.constraints:
            lines.append(f"- {item}")
    else:
        lines.append("无额外约束。")
    lines.extend(["", "---", ""])
    lines.append(f"task_profile: {spec.profile}")
    lines.append(f"revision: {spec.revision}")
    if spec.parent_task_id:
        lines.append(f"parent_task_id: {spec.parent_task_id}")
    else:
        lines.append("parent_task_id: —")
    lines.append("")
    return "\n".join(lines)
