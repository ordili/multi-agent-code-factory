"""Minimal spec.json → spec.md renderer (P0)."""

from __future__ import annotations

from multi_agent_code_factory.schemas.spec import SpecArtifact


def render_spec_md(spec: SpecArtifact) -> str:
    lines = [
        f"# {spec.title}",
        "",
        "## 概述",
        "",
        spec.summary,
        "",
        "## 成功指标",
        "",
    ]
    for metric in spec.success_metrics:
        lines.append(f"- **{metric.id}** {metric.name}: {metric.target}")
    lines.extend(["", "## 功能", ""])
    for feature in spec.features:
        lines.append(
            f"- **{feature.id}** ({feature.priority}) {feature.name}: "
            f"{feature.description}"
        )
    lines.extend(["", "## 验收标准", ""])
    for ac in spec.acceptance_criteria:
        lines.append(f"- **{ac.id}** {ac.description} (`{ac.verifiable_by}`)")
    lines.extend(["", "## 范围", ""])
    lines.append("**纳入:**")
    for item in spec.scope_in:
        lines.append(f"- {item}")
    if spec.scope_out:
        lines.append("")
        lines.append("**排除:**")
        for item in spec.scope_out:
            lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## 稳定性、性能与数据一致性",
            "",
            f"- 用户体量: `{spec.operational_profile.user_scale}`",
            f"- 高并发: `{spec.operational_profile.high_concurrency}`",
            f"- 性能档位: `{spec.operational_profile.performance.tier}`",
            f"- 一致性模型: `{spec.consistency_profile.consistency_model}`",
            "",
            "---",
            "",
            f"task_profile: `{spec.profile}` · revision: `{spec.revision}`",
            "",
        ]
    )
    return "\n".join(lines)
