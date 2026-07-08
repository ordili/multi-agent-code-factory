"""review.json → review.md 渲染器（P1）。"""

from __future__ import annotations

from multi_agent_code_factory.schemas.review import ReviewReport


def render_review_md(review: ReviewReport) -> str:
    """将 ReviewReport 渲染为人类可读的 Markdown 审查报告。"""
    approved = "是" if review.approved else "否"
    lines = [
        "# 审查结论",
        "",
        f"**通过：** {approved}",
        f"**摘要：** {review.summary}",
        "",
        "## 路由",
        "",
        f"下一节点：`{review.next_stage.value}`",
        "",
        "## 验收覆盖",
        "",
    ]
    if review.acceptance_coverage:
        lines.extend(
            [
                "| AC | 满足 | 说明 |",
                "|----|------|------|",
            ]
        )
        for item in review.acceptance_coverage:
            met = "✓" if item.met else "✗"
            note = item.note or "—"
            lines.append(f"| {item.id} | {met} | {note} |")
    else:
        lines.append("—")
    lines.extend(["", "## 发现项", ""])
    if review.findings:
        for finding in review.findings:
            blocking = "blocking" if finding.blocking else "non-blocking"
            location = f" (`{finding.file}`)" if finding.file else ""
            routing = (
                f" → `{finding.routing.value}`" if finding.routing is not None else ""
            )
            lines.append(
                f"- **{finding.id}** [{finding.severity.value}/"
                f"{finding.category.value}] ({blocking}){location}: "
                f"{finding.message}{routing}"
            )
    else:
        lines.append("无")
    lines.extend(
        [
            "",
            "---",
            "",
            f"approved: `{review.approved}` · next_stage: `{review.next_stage.value}`",
            "",
        ]
    )
    return "\n".join(lines)
