"""design.json → design.md 渲染器（定稿 §1–§6 + 附录 A–D）。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from multi_agent_code_factory.schemas.design import (
    DesignArtifact,
    DiagramKind,
    ModuleSpec,
)


def _as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, BaseModel):
        return value.model_dump()
    if isinstance(value, dict):
        return value
    return {}


def _yes_no(value: bool | None) -> str:
    if value is None:
        return "—"
    return "是" if value else "否"


def _join_list(items: list[str]) -> str:
    return "、".join(items) if items else "—"


def _format_param(param: Any) -> str:
    param = _as_mapping(param)
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


def _format_operations_table(operations: list[Any]) -> list[str]:
    lines = [
        "| 操作 | 功能说明 | 入参 | 出参 | 错误码 |",
        "|------|----------|------|------|--------|",
    ]
    if not operations:
        lines.append("| — | — | — | — | — |")
        return lines
    for op in operations:
        op = _as_mapping(op)
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


def _has_real_external_deps(design: DesignArtifact) -> bool:
    return any(dep.kind != "none" for dep in design.external_dependencies)


def _context_diagrams(design: DesignArtifact) -> list:
    return [
        d
        for d in design.diagrams
        if (d.kind.value if hasattr(d.kind, "value") else d.kind)
        == DiagramKind.CONTEXT.value
    ]


def _flow_diagrams(design: DesignArtifact) -> list:
    flow_kinds = {DiagramKind.SEQUENCE.value, DiagramKind.FLOWCHART.value}
    return [
        d
        for d in design.diagrams
        if (d.kind.value if hasattr(d.kind, "value") else d.kind) in flow_kinds
    ]


def _should_render_section_42(design: DesignArtifact) -> bool:
    return (
        len(design.modules) >= 2
        or _has_real_external_deps(design)
        or bool(_context_diagrams(design))
    )


def _should_render_section_44(design: DesignArtifact) -> bool:
    return _has_real_external_deps(design)


def _should_render_section_46(design: DesignArtifact) -> bool:
    return bool(
        design.data_model or design.table_schemas or design.transaction_constraints
    )


def render_design_md(design: DesignArtifact) -> str:
    """将 DesignArtifact 渲染为人类可读的 Markdown 设计文档。"""
    title = design.spec_ref
    lines: list[str] = [
        f"# 设计文档 — {title}",
        "",
        f"- **版本：** r{design.revision}",
        f"- **对应需求：** {design.spec_ref}",
    ]
    if design.status is not None:
        lines.append(f"- **状态：** {design.status.value}")
    if design.supersedes_revision is not None:
        lines.append(f"- **取代版本：** r{design.supersedes_revision}")

    lines.extend(["", "## 1. 背景与上下文", ""])
    if design.summary:
        lines.append(design.summary)
        lines.append("")
    if design.background:
        lines.append(design.background)
        lines.append("")
    if design.context_view:
        actors = design.context_view.actors
        external = design.context_view.external_systems
        if actors:
            lines.append("**参与者：**")
            for actor in actors:
                lines.append(f"- {actor}")
            lines.append("")
        if external:
            lines.append("**外部系统：**")
            for item in external:
                if isinstance(item, str):
                    lines.append(f"- {item}")
                else:
                    item_map = _as_mapping(item)
                    name = item_map.get("name", "?")
                    desc = item_map.get("description", "")
                    lines.append(f"- {name}: {desc}")
            lines.append("")

    lines.extend(["## 2. 设计目标", ""])
    if design.design_goals:
        for goal in design.design_goals:
            lines.append(f"- {goal}")
    else:
        lines.append("—")

    lines.extend(["", "## 3. 非目标", ""])
    if design.non_goals:
        for item in design.non_goals:
            lines.append(f"- {item}")
    else:
        lines.append("—")

    lines.extend(["", "## 4. 方案设计", ""])

    if design.architecture:
        lines.extend(["### 4.1 概述", ""])
        strategy = design.architecture.solution_strategy
        style = design.architecture.style
        if strategy:
            lines.append(str(strategy))
            lines.append("")
        if style:
            lines.append(f"**架构风格：** `{style}`")
            lines.append("")

    if _should_render_section_42(design):
        lines.extend(["### 4.2 系统架构图", ""])
        context_diagrams = _context_diagrams(design)
        if context_diagrams:
            for diagram in context_diagrams:
                kind = (
                    diagram.kind.value
                    if hasattr(diagram.kind, "value")
                    else diagram.kind
                )
                title_d = diagram.title or kind
                lines.append(f"- **{title_d}** (`{kind}`): `{diagram.path}`")
        else:
            lines.append("- 见 Run 目录 `architecture-*.mmd`")
        lines.append("")

    if design.modules:
        lines.extend(["### 4.3 模块划分", ""])
        lines.extend(
            [
                "| 模块 | 路径 | 职责 | code_domain | 依赖模块 |",
                "|------|------|------|-------------|----------|",
            ]
        )
        for module in design.modules:
            lines.append(_render_module_row(module))
        lines.append("")

    if _should_render_section_44(design):
        lines.extend(["### 4.4 外部依赖", ""])
        lines.extend(
            [
                "| 名称 | 类型 | 技术 | 用途 | code_domain | 关键性 |",
                "|------|------|------|------|-------------|--------|",
            ]
        )
        for dep in design.external_dependencies:
            if dep.kind == "none":
                continue
            domain = f"`{dep.code_domain}`" if dep.code_domain else "—"
            tech = dep.technology or "—"
            crit = dep.criticality or "—"
            lines.append(
                f"| {dep.name} | `{dep.kind}` | {tech} | {dep.purpose} | "
                f"{domain} | {crit} |"
            )
            if dep.failure_behavior:
                lines.append(f"  - 故障行为：{dep.failure_behavior}")
        lines.append("")

    if design.interfaces or design.error_catalog:
        lines.extend(["### 4.5 接口定义", ""])
        if design.interfaces:
            for iface in design.interfaces:
                name = iface.name
                file_path = iface.file
                protocol = iface.protocol
                domain = iface.code_domain or "—"
                desc = iface.description
                lines.append(
                    f"#### {name}（`{file_path}` · `{protocol}` · `{domain}`）"
                )
                if desc:
                    lines.append("")
                    lines.append(desc)
                    lines.append("")
                lines.extend(_format_operations_table(iface.operations))
                lines.append("")
        if design.error_catalog:
            lines.extend(
                [
                    "#### 错误码目录",
                    "",
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
            lines.append("")

    if _should_render_section_46(design):
        lines.extend(["### 4.6 存储结构", ""])
        if design.data_model:
            lines.append("#### 逻辑模型")
            lines.append("")
            for entity in design.data_model:
                ename = entity.name
                lines.append(f"- **{ename}**")
                fields = entity.fields
                if fields:
                    lines.extend(
                        [
                            "",
                            "| 字段 | 类型 | 可空 | 键 | 注释 |",
                            "|------|------|------|-----|------|",
                        ]
                    )
                    for field in fields:
                        field_map = _as_mapping(field)
                        nullable = _yes_no(field_map.get("nullable"))
                        pk = (
                            "PK"
                            if field_map.get("pk")
                            else ("UK" if field_map.get("unique") else "—")
                        )
                        fname = field_map.get("name", "?")
                        ftype = field_map.get("type", "?")
                        fdesc = field_map.get("description", "—")
                        lines.append(
                            f"| {fname} | {ftype} | {nullable} | {pk} | {fdesc} |"
                        )
                lines.append("")
        if design.table_schemas:
            for table in design.table_schemas:
                tname = table.name
                storage = table.storage
                lines.append(f"#### 表 `{tname}`（`{storage}`）")
                lines.append("")
                columns = table.columns
                if columns:
                    lines.extend(
                        [
                            "| 字段 | 类型 | 可空 | 键 | 注释 |",
                            "|------|------|------|-----|------|",
                        ]
                    )
                    for col in columns:
                        col_map = _as_mapping(col)
                        nullable = _yes_no(col_map.get("nullable"))
                        pk = (
                            "PK"
                            if col_map.get("pk")
                            else ("UK" if col_map.get("unique") else "—")
                        )
                        cname = col_map.get("name", "?")
                        ctype = col_map.get("type", "?")
                        cdesc = col_map.get("description", "—")
                        lines.append(
                            f"| {cname} | {ctype} | {nullable} | {pk} | {cdesc} |"
                        )
                    lines.append("")
                indexes = table.indexes
                if indexes:
                    lines.append("**索引：**")
                    for idx in indexes:
                        idx_map = _as_mapping(idx)
                        cols = ", ".join(idx_map.get("columns") or [])
                        purpose = idx_map.get("purpose") or ""
                        lines.append(
                            f"- `{idx_map.get('name', '?')}` ({cols}) — {purpose}"
                        )
                    lines.append("")
        if design.transaction_constraints:
            lines.extend(["#### 一致性与事务", ""])
            lines.extend(
                [
                    "| ID | 范围 | 边界 | 说明 |",
                    "|----|------|------|------|",
                ]
            )
            for tx in design.transaction_constraints:
                lines.append(
                    f"| {tx.id} | {tx.scope} | {tx.boundary} | {tx.notes or '—'} |"
                )
            lines.append("")

    flow_diagrams = _flow_diagrams(design)
    if flow_diagrams:
        lines.extend(["### 4.7 流程与时序", ""])
        for diagram in flow_diagrams:
            kind = (
                diagram.kind.value if hasattr(diagram.kind, "value") else diagram.kind
            )
            title_d = diagram.title or kind
            lines.append(f"- **{title_d}** (`{kind}`): `{diagram.path}`")
        lines.append("")

    if design.non_functional:
        lines.extend(["", "## 5. 非功能性目标", ""])
        lines.extend(
            [
                "| ID | 指标 | 目标 | 验证 |",
                "|----|------|------|------|",
            ]
        )
        for nfr in design.non_functional:
            lines.append(
                f"| {nfr.id or '—'} | {nfr.metric} | "
                f"{nfr.target} | {nfr.verification or '—'} |"
            )
        lines.append("")

    lines.extend(["", "## 6. 测试用例列表", ""])
    if design.test_cases:
        lines.extend(
            [
                "| ID | 类型 | 标题 | 期望 | 覆盖 | 错误码 |",
                "|----|------|------|------|------|--------|",
            ]
        )
        for tc in design.test_cases:
            kind = tc.kind
            if hasattr(kind, "value"):
                kind = kind.value
            title_tc = tc.title or tc.description or "—"
            expected = tc.expected or "—"
            cover_text = _join_list(tc.covers) if tc.covers else "—"
            error_code = tc.error_code or "—"
            lines.append(
                f"| {tc.id} | {kind or '—'} | {title_tc} | {expected} | "
                f"{cover_text} | {error_code} |"
            )
    else:
        lines.append("—")
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
            spec_id = row.spec_ref_id or "—"
            ref = row.design_ref or "—"
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
            action = item.action
            if hasattr(action, "value"):
                action = action.value
            path = item.path
            purpose = item.reason or str(action)
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

    lines.extend(["", "## 附录 D. 与现有代码对照", ""])
    code_delta = design.architecture.code_delta if design.architecture else None
    if code_delta:
        lines.append(code_delta.summary)
        if code_delta.notes:
            lines.append("")
            lines.append(code_delta.notes)
    else:
        lines.append("`code_root` 空仓库或增量任务；详见附录 B 文件变更计划。")

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
