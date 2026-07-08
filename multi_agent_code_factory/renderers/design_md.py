"""design.json → design.md 渲染器（P1）。"""

from __future__ import annotations

from typing import Any

from multi_agent_code_factory.schemas.design import DesignArtifact, ModuleSpec


def _yes_no(value: bool | None) -> str:
    if value is None:
        return "—"
    return "是" if value else "否"


def _join_list(items: list[str]) -> str:
    return "、".join(items) if items else "—"


def _format_param(param: dict[str, Any]) -> str:
    name = param.get("name", "?")
    ptype = param.get("type", "?")
    required = param.get("required")
    req = "必填" if required else "可选" if required is False else ""
    desc = param.get("description", "")
    parts = [f"`{name}`: {ptype}"]
    if req:
        parts.append(req)
    if desc:
        parts.append(desc)
    return "，".join(parts)


def _format_operations_table(operations: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| 操作 | 功能说明 | 入参 | 出参 | 错误码 |",
        "|------|----------|------|------|--------|",
    ]
    if not operations:
        lines.append("| — | — | — | — | — |")
        return lines
    for op in operations:
        name = op.get("name", "—")
        summary = op.get("summary") or op.get("description") or "—"
        inputs = op.get("inputs") or []
        outputs = op.get("outputs") or []
        errors = op.get("errors") or []
        in_text = "; ".join(_format_param(p) for p in inputs) if inputs else "—"
        out_text = "; ".join(_format_param(p) for p in outputs) if outputs else "—"
        err_text = ", ".join(errors) if errors else "—"
        lines.append(f"| `{name}` | {summary} | {in_text} | {out_text} | {err_text} |")
    return lines


def _render_module_row(module: ModuleSpec) -> str:
    deps = ", ".join(module.depends_on) if module.depends_on else "—"
    return (
        f"| {module.name} | `{module.path}` | {module.responsibility} | "
        f"`{module.code_domain}` | {deps} |"
    )


def render_design_md(design: DesignArtifact, *, flow_filename: str = "flow.mmd") -> str:
    """将 DesignArtifact 渲染为人类可读的 Markdown 设计文档。"""
    title = design.spec_ref
    lines: list[str] = [
        f"# Design Doc — {title}",
        "",
        f"- **Revision：** {design.revision}",
        f"- **Spec：** {design.spec_ref}",
    ]
    if design.status is not None:
        lines.append(f"- **Status：** {design.status.value}")
    if design.supersedes_revision is not None:
        lines.append(f"- **Supersedes：** r{design.supersedes_revision}")
    lines.extend(["", "## 1. Context & Background", ""])
    if design.summary:
        lines.append(design.summary)
        lines.append("")
    if design.background:
        lines.append(design.background)
        lines.append("")
    if design.context_view:
        actors = design.context_view.get("actors") or []
        external = design.context_view.get("external_systems") or []
        if actors:
            lines.append("**参与者：**")
            for actor in actors:
                lines.append(f"- {actor}")
            lines.append("")
        if external:
            lines.append("**外部系统：**")
            for item in external:
                if isinstance(item, dict):
                    lines.append(
                        f"- {item.get('name', '?')}: {item.get('description', '')}"
                    )
                else:
                    lines.append(f"- {item}")
            lines.append("")

    lines.extend(["## 2. Goals", ""])
    if design.design_goals:
        for goal in design.design_goals:
            lines.append(f"- {goal}")
    else:
        lines.append("—")
    lines.extend(["", "## 3. Non-Goals", ""])
    if design.non_goals:
        for item in design.non_goals:
            lines.append(f"- {item}")
    else:
        lines.append("—")

    lines.extend(["", "## 4. Design", "", "### 4.1 Overview", ""])
    if design.architecture:
        strategy = design.architecture.get("solution_strategy")
        style = design.architecture.get("style")
        if strategy:
            lines.append(str(strategy))
            lines.append("")
        if style:
            lines.append(f"**Style：** `{style}`")
            lines.append("")
    if not design.architecture:
        lines.append("—")
        lines.append("")

    lines.extend(["### 4.2 Components", ""])
    if design.modules:
        lines.extend(
            [
                "| 模块 | 路径 | 职责 | code_domain | 依赖模块 |",
                "|------|------|------|-------------|----------|",
            ]
        )
        for module in design.modules:
            lines.append(_render_module_row(module))
    else:
        lines.append("—")
    lines.append("")

    lines.extend(["### 4.3 External Dependencies", ""])
    if design.external_dependencies:
        lines.extend(
            [
                "| 名称 | 类型 | 技术 | 用途 | code_domain | 关键性 |",
                "|------|------|------|------|-------------|--------|",
            ]
        )
        for dep in design.external_dependencies:
            domain = f"`{dep.code_domain}`" if dep.code_domain else "—"
            tech = dep.technology or "—"
            crit = dep.criticality or "—"
            lines.append(
                f"| {dep.name} | `{dep.kind}` | {tech} | {dep.purpose} | "
                f"{domain} | {crit} |"
            )
            if dep.failure_behavior:
                lines.append(f"  - 故障行为：{dep.failure_behavior}")
    else:
        lines.append("无外部中间件。")
    lines.append("")

    lines.extend(["### 4.4 APIs", ""])
    if design.interfaces:
        for iface in design.interfaces:
            name = iface.get("name", "Interface")
            file_path = iface.get("file", "—")
            protocol = iface.get("protocol", "—")
            domain = iface.get("code_domain") or "—"
            desc = iface.get("description")
            lines.append(f"#### {name}（`{file_path}` · `{protocol}` · `{domain}`）")
            if desc:
                lines.append("")
                lines.append(desc)
                lines.append("")
            lines.extend(_format_operations_table(iface.get("operations") or []))
            lines.append("")
    else:
        lines.append("—")
        lines.append("")

    lines.extend(["### 4.5 Data Model & Table Schema", ""])
    if design.data_model:
        lines.append("**逻辑模型：**")
        lines.append("")
        for entity in design.data_model:
            ename = entity.get("name", "?")
            lines.append(f"- **{ename}**")
            fields = entity.get("fields") or entity.get("attributes") or []
            if fields:
                lines.extend(
                    [
                        "",
                        "| 字段 | 类型 | 可空 | 键 | 注释 |",
                        "|------|------|------|-----|------|",
                    ]
                )
                for field in fields:
                    if not isinstance(field, dict):
                        continue
                    nullable = _yes_no(field.get("nullable"))
                    pk = (
                        "PK"
                        if field.get("pk")
                        else ("UK" if field.get("unique") else "—")
                    )
                    lines.append(
                        f"| {field.get('name', '?')} | {field.get('type', '?')} | "
                        f"{nullable} | {pk} | {field.get('description', '—')} |"
                    )
            lines.append("")
    if design.table_schemas:
        for table in design.table_schemas:
            tname = table.get("name", "?")
            storage = table.get("storage", "—")
            lines.append(f"**表 `{tname}`**（`{storage}`）")
            lines.append("")
            columns = table.get("columns") or []
            if columns:
                lines.extend(
                    [
                        "| 字段 | 类型 | 可空 | 键 | 注释 |",
                        "|------|------|------|-----|------|",
                    ]
                )
                for col in columns:
                    nullable = _yes_no(col.get("nullable"))
                    pk = "PK" if col.get("pk") else ("UK" if col.get("unique") else "—")
                    lines.append(
                        f"| {col.get('name', '?')} | {col.get('type', '?')} | "
                        f"{nullable} | {pk} | {col.get('description', '—')} |"
                    )
                lines.append("")
            indexes = table.get("indexes") or []
            if indexes:
                lines.append("**索引：**")
                for idx in indexes:
                    cols = ", ".join(idx.get("columns") or [])
                    purpose = idx.get("purpose") or ""
                    lines.append(f"- `{idx.get('name', '?')}` ({cols}) — {purpose}")
                lines.append("")
    if not design.data_model and not design.table_schemas:
        lines.append("—")
        lines.append("")

    lines.extend(["### 4.6 Flow", ""])
    if design.diagrams:
        for diagram in design.diagrams:
            path = diagram.path
            if path.endswith(".mmd") and path != flow_filename:
                path = flow_filename
            kind = (
                diagram.kind.value if hasattr(diagram.kind, "value") else diagram.kind
            )
            title = diagram.title or kind
            lines.append(f"- **{title}** (`{kind}`): `{path}`")
    else:
        lines.append(f"- 见 `{flow_filename}`")
    lines.append("")

    lines.extend(["## 5. Alternatives Considered", ""])
    decisions = (
        (design.architecture or {}).get("decisions") if design.architecture else None
    )
    if decisions:
        lines.extend(
            [
                "| Option | Decision | 理由 |",
                "|--------|----------|------|",
            ]
        )
        for decision in decisions:
            if isinstance(decision, dict):
                lines.append(
                    f"| {decision.get('option', '—')} | "
                    f"{decision.get('decision', '—')} | "
                    f"{decision.get('rationale', '—')} |"
                )
    else:
        lines.append("—")
    lines.extend(["", "## 6. Cross-cutting Concerns", ""])

    lines.extend(["### 6.1 Data Consistency & Transactions", ""])
    if design.transaction_constraints:
        lines.extend(
            [
                "| ID | 范围 | 边界 | 说明 |",
                "|----|------|------|------|",
            ]
        )
        for tx in design.transaction_constraints:
            lines.append(
                f"| {tx.get('id', '—')} | {tx.get('scope', '—')} | "
                f"{tx.get('boundary', '—')} | {tx.get('notes', '—')} |"
            )
    else:
        lines.append("—")
    lines.append("")

    lines.extend(["### 6.2 Errors & Error Codes", ""])
    if design.error_catalog:
        lines.extend(
            [
                "| 码 | 场景 | 可重试 | 说明 |",
                "|----|------|--------|------|",
            ]
        )
        for err in design.error_catalog:
            when = err.when or "—"
            message = err.message or "—"
            lines.append(
                f"| `{err.code}` | {when} | {_yes_no(err.retryable)} | {message} |"
            )
    else:
        lines.append("—")
    lines.append("")

    if design.cross_cutting:
        for key, value in design.cross_cutting.items():
            if value:
                lines.append(f"**{key}：** {value}")
                lines.append("")

    lines.extend(["## 7. Performance & Reliability", ""])
    if design.non_functional:
        lines.extend(
            [
                "| ID | 指标 | 目标 | 验证 |",
                "|----|------|------|------|",
            ]
        )
        for nfr in design.non_functional:
            lines.append(
                f"| {nfr.get('id', '—')} | {nfr.get('metric', '—')} | "
                f"{nfr.get('target', '—')} | {nfr.get('verification', '—')} |"
            )
    else:
        lines.append("N/A")
    lines.extend(["", "## 8. Testing Plan", ""])
    test_strategy = (design.cross_cutting or {}).get("test_strategy")
    if test_strategy:
        lines.append(str(test_strategy))
    elif design.test_cases:
        lines.append(f"见附录 D（{len(design.test_cases)} 条用例）。")
    else:
        lines.append("—")
    lines.extend(["", "## 9. Rollout & Deployment", "", "N/A", ""])
    lines.extend(["## 10. Monitoring & Alerting", "", "N/A", ""])
    lines.extend(["## 11. Open Questions", ""])
    if design.notes:
        lines.append(design.notes)
    else:
        lines.append("None")
    lines.append("")

    lines.extend(["## 附录 A. 需求追溯", ""])
    if design.traceability:
        lines.extend(
            [
                "| spec id | 设计落点 |",
                "|---------|----------|",
            ]
        )
        for row in design.traceability:
            spec_id = row.get("spec_ref_id") or row.get("id") or "—"
            ref = (
                row.get("design_ref")
                or row.get("design_element")
                or row.get("design_ref_id")
                or "—"
            )
            lines.append(f"| {spec_id} | {ref} |")
    else:
        lines.append("—")
    lines.extend(["", "## 附录 B. 文件变更计划", ""])
    if design.file_plan:
        lines.extend(
            [
                "| 路径 | 操作/用途 |",
                "|------|-----------|",
            ]
        )
        for item in design.file_plan:
            path = item.get("path", "—")
            purpose = (
                item.get("purpose")
                or item.get("operation")
                or item.get("reason")
                or "—"
            )
            lines.append(f"| `{path}` | {purpose} |")
    else:
        lines.append("—")
    lines.extend(["", "## 附录 C. 开发任务分解", ""])
    if design.dev_tasks:
        lines.extend(
            [
                "| ID | 路径 | 描述 | 依赖 | 覆盖 |",
                "|----|------|------|------|------|",
            ]
        )
        for task in design.dev_tasks:
            deps = _join_list(task.depends_on)
            covers = _join_list(task.covers)
            lines.append(
                f"| {task.id} | `{task.path}` | {task.description} | "
                f"{deps} | {covers} |"
            )
    else:
        lines.append("—")
    lines.extend(["", "## 附录 D. 测试用例设计", ""])
    if design.test_cases:
        lines.extend(
            [
                "| ID | 类型 | 标题 | 期望 | 覆盖 | 错误码 |",
                "|----|------|------|------|------|--------|",
            ]
        )
        for tc in design.test_cases:
            kind = tc.get("kind") or "—"
            title = tc.get("title") or tc.get("description") or "—"
            expected = tc.get("expected") or "—"
            covers = tc.get("covers")
            if isinstance(covers, list):
                cover_text = _join_list(covers)
            else:
                cover_text = str(covers) if covers else "—"
            error_code = tc.get("error_code") or "—"
            lines.append(
                f"| {tc.get('id', '—')} | {kind} | {title} | {expected} | "
                f"{cover_text} | {error_code} |"
            )
    else:
        lines.append("—")
    lines.extend(["", "## 附录 E. 与现有代码对照", ""])
    code_delta = (
        (design.architecture or {}).get("code_delta") if design.architecture else None
    )
    if code_delta:
        lines.append(str(code_delta))
    else:
        lines.append("`code_root` 空仓库或增量任务；详见 `file_plan`。")
    lines.extend(
        [
            "",
            "---",
            "",
            f"spec_ref: `{design.spec_ref}` · revision: `{design.revision}`",
            "",
        ]
    )
    return "\n".join(lines)
