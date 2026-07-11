# PRD 全栈命名统一 — 设计说明

> **日期：** 2026-07-10  
> **状态：** v4 完成 — **R0–R6 + 文案清扫**（2026-07-11）；Semantic validation 独立轨道未开始  
> **关联：** [`pipeline/README.md` §4](../../design/pipeline/README.md#4-命名约定) · [`artifact-schemas/prd-spec.md`](../../design/pipeline/artifact-schemas/prd-spec.md)

## 修订记录

| 版本 | 变更 |
|------|------|
| v1–v2 | Run 产物 `prd.*`；`prd_validation.json` |
| v3 | Run 必改 vs 内部保留（已废止） |
| **v4** | **决策：全栈 PRD 化** — `PrdArtifact`、`PRD-*` rule_id、节点/模块/State 凡需求环 `spec` 均改 `prd` |
| **v4.1** | **实施记录** — R0–R5 落地；§实施进度、§影响面勾选更新；遗留项归入 R6 / 文档清扫 |

## 背景

PM 阶段是 **PRD（需求文档）**，定稿层已是 `prd-spec.md`，但 Run 落盘、Python 类型、校验 rule_id、图节点仍混用 `spec`，与 design 环（`design.json` / `DES-*`）不对称，也易与「技术规格」混淆。

**目标：** 需求环在 **Run 产物、代码、文档、rule_id** 四层统一为 **`prd` / `PRD` / `Prd*`**，与 design 环命名对称。

## 决策摘要（v4）

| 层级 | 原 | 新 |
|------|-----|-----|
| Run JSON / MD | `spec.json`、`spec.md` | **`prd.json`、`prd.md`** |
| 校验报告 | `spec_validation.json` | **`prd_validation.json`** |
| Pydantic 模型 | `SpecArtifact`、`schemas/spec.py` | **`PrdArtifact`、`schemas/prd.py`** |
| State / Meta | `spec`、`spec_validation`、`spec_revision_count` | **`prd`、`prd_validation`、`prd_revision_count`** |
| 图节点 | `spec_validate`、`spec_hitl`、`route_after_spec_validate` | **`prd_validate`、`prd_hitl`、`route_after_prd_validate`** |
| 校验 rule_id | `SPEC-001`…`SPEC-316`、`SPEC-S*` | **`PRD-001`…`PRD-316`、`PRD-S*`** |
| 质量门禁文档 | `quality-gates/spec-validate.md` | **`quality-gates/prd-validate.md`** |
| 校验枚举 | `ValidationTarget.SPEC` | **`ValidationTarget.PRD`** |
| HITL stage | `HitlStage.SPEC` | **`HitlStage.PRD`** |
| Profile / CLI | `validation.spec.*`、`max_spec_revisions` | **`validation.prd.*`、`max_prd_revisions`**（旧键短期别名） |

**保留 `spec` 一词的唯一场景：** 英文普通名词「规格说明」出现在 **注释/外部引用** 中，或 **legacy 回退** 读旧 run 文件名（见 §兼容）。

---

## 命名对照总表

### Run 目录

```text
docs/runs/<task_id>/
  prd.json
  prd.md
  prd_validation.json
  design.json
  design.md
  design_validation.json
  ...
```

### Python 模块（重命名 / 删除旧文件）

| 原路径 | 新路径 |
|--------|--------|
| `schemas/spec.py` | **`schemas/prd.py`** |
| `renderers/spec_md.py` | **`renderers/prd_md.py`** |
| `validators/spec_rules.py` | **`validators/prd_rules.py`** |
| `validators/spec_rules_extended.py` | **`validators/prd_rules_extended.py`** |
| `validators/spec_md_rules.py` | **`validators/prd_md_rules.py`** |
| `validators/spec_semantic_rules.py`（待建） | **`validators/prd_semantic_rules.py`** |
| `nodes/spec_validate.py` | **`nodes/prd_validate.py`** |
| `nodes/spec_hitl.py` | **`nodes/prd_hitl.py`** |
| `agents/normalizers/spec.py` | **`agents/normalizers/prd.py`** |

**类型与符号：**

| 原 | 新 |
|----|-----|
| `SpecArtifact` | `PrdArtifact` |
| `coerce_spec_payload` | `coerce_prd_payload` |
| `render_spec_md` | `render_prd_md` |
| `validate_spec_rules` | `validate_prd_rules` |
| `validate_spec_md_file` | `validate_prd_md_file` |
| `run_spec_validate` | `run_prd_validate` |
| `trim_spec` | `trim_prd` |
| `format_spec_validation_feedback` | `format_prd_validation_feedback` |
| `PipelineNode.SPEC_VALIDATE` | `PipelineNode.PRD_VALIDATE` |
| `PipelineNode.SPEC_HITL` | **`PipelineNode.PRD_HITL`** |
| `PipelineNode.ROUTE_AFTER_SPEC_VALIDATE` | **`ROUTE_AFTER_PRD_VALIDATE`** |

### rule_id 映射

**一次性整体替换**（实现用脚本或 rg，并更新 golden 测试）：

| 原前缀 | 新前缀 | 范围 |
|--------|--------|------|
| `SPEC-0` | `PRD-0` | 结构与必填 PRD-001～017 |
| `SPEC-1` | `PRD-1` | 可测性 PRD-101～118 |
| `SPEC-2` | `PRD-2` | PRD-201～202 等 |
| `SPEC-3` | `PRD-3` | `prd.md` 格式 PRD-301～316 |
| `SPEC-S` | `PRD-S` | 语义层（见 semantic-validation 设计） |

示例：`SPEC-017` → `PRD-017`；`SPEC-301` → `PRD-301`；`SPEC-S01` → `PRD-S01`。

**传导引用：** `design-validate.md` 中「spec→design」改为 **「prd→design」**；`DES-*` 中引用 `PRD-016` 等同步改号。

### 定稿文档

| 原 | 新 |
|----|-----|
| `quality-gates/spec-validate.md` | **`prd-validate.md`** |
| 各文档「spec 环」「spec_validate」 | **PRD 环 / prd_validate** |
| `validation.spec.*`（profiles） | **`validation.prd.*`** |

`artifact-schemas/prd-spec.md`、`artifact-templates/prd-spec.md` **文件名不变**（已是 PRD）。

---

## 常量与回退（`run_artifact_names.py`）

已实现：`multi_agent_code_factory/run_artifact_names.py`
```python
PRD_JSON = "prd.json"
PRD_MD = "prd.md"
PRD_VALIDATION_JSON = "prd_validation.json"

LEGACY_SPEC_JSON = "spec.json"
LEGACY_SPEC_MD = "spec.md"
LEGACY_SPEC_VALIDATION_JSON = "spec_validation.json"
```

加载顺序：新名优先 → legacy 只读；**写入仅用新名**。

---

## 向后兼容

| 项 | 策略 |
|----|------|
| 旧 run 文件 `spec.*` | 双读回退，**不**自动重命名磁盘 |
| `ValidationReport.target == "spec"` | 读 JSON 时 coerce 为 `prd`；写出仅用 `prd` |
| `validation.spec` profile 键 | 读 YAML 时接受 `spec`，归一化为 `prd`；文档只写 `prd` |
| `rule_id` 旧 `SPEC-*` | **不**在 validator 接受；旧 `*_validation.json` 中 violation 仅归档 |

兼容窗口：1 个 minor 版本后移除文件回退与 profile 别名。

---

## 实施分期

| 阶段 | 范围 | 验收 | 状态 |
|------|------|------|------|
| **R0** | 本文 + 定稿层文档（`prd-validate.md`、README、传导表） | 评审通过 | ✅ **部分完成** — 核心 README + `prd-validate.md`；大文档全文清扫见 §待续 |
| **R1** | Run 文件名 + `run_artifact_names` 常量 + 双读 + `pm.py` / `artifact_loader` / `checkpoint` | 新 run 落盘 `prd.*`；continue 可读旧 run | ✅ **完成** |
| **R2** | `schemas/prd.py`、`PrdArtifact`、全库 import；`state` / `run_meta` 字段 | `pytest` 绿 | ✅ **完成**（`schemas/spec.py` 暂留 shim） |
| **R3** | 节点/路由 `prd_validate`；`graph_builder`、`pipeline_nodes` | 图集成测试绿 | ✅ **完成**（节点名 + legacy `_missing_` 回退） |
| **R4** | `prd_rules*`、`prd_md_rules*`；**rule_id `PRD-*`** | validator 测试更新 | ✅ **完成**（旧 `spec_*.py` 暂留 shim） |
| **R5** | `render_prd_md`、prompt、`trim_prd`、CLI `max_prd_revisions` | e2e 绿 | ✅ **完成**（单元测试绿；live e2e 未跑） |
| **R6** | 删除 shim / legacy 别名；示例片段改名；文档全文清扫 | 无 `spec` 模块残留 | ⏳ **待续** |

**验收命令（当前）：** `pytest -q --ignore=tests/integration` → 全绿（2026-07-11）。

**建议单 PR 上限：** R1+R2 或 R3+R4 分批，避免一次 diff 过大。（R0–R5 已按 R1+R2、R3+R4+R5 分批落地。）

---

## 实施进度（2026-07-11）

### 已完成摘要

| 层级 | 落地要点 |
|------|----------|
| **Run 产物** | 新 run 写入 `prd.json` / `prd.md` / `prd_validation.json`；`artifact_loader` / `checkpoint` 双读 legacy `spec.*` |
| **Schema / State** | `schemas/prd.py` + `PrdArtifact`；`state.prd` / `prd_validation` / `prd_revision_count`；checkpoint 反序列化兼容旧键 |
| **图节点** | `PipelineNode.PRD_VALIDATE` / `PRD_HITL` / `ROUTE_AFTER_PRD_VALIDATE`；`nodes/prd_validate.py`、`nodes/prd_hitl.py` |
| **Validators** | `validators/prd_rules*.py`；rule_id **`PRD-*`**（原 `SPEC-*`） |
| **Profile / CLI** | `ValidationConfig.prd`（YAML `validation.prd`，读 `validation.spec` 归一化）；`--max-prd-revisions`（`--max-spec-revisions` 别名） |
| **Prompt / 渲染** | `render_prd_md`、`trim_prd`、`format_prd_validation_feedback`；`pm.txt` → `PrdArtifact` |
| **枚举** | `ValidationTarget.PRD`、`HitlStage.PRD`（JSON `"spec"` coerce） |
| **测试** | `test_prd_rules_extended.py`、`test_prd_md_renderer.py`；`test_graph*` / `test_continue_*` 已适配 |

### 暂留兼容层（R6 删除）

| 类型 | 路径 / 符号 |
|------|-------------|
| Schema shim | `schemas/spec.py` → re-export `prd` |
| 节点 shim | `nodes/spec_validate.py`、`nodes/spec_hitl.py` |
| Validator shim | `validators/spec_rules.py`、`spec_rules_extended.py`、`spec_md_rules.py` |
| 渲染 shim | `renderers/spec_md.py` |
| Normalizer shim | `agents/normalizers/spec.py` |
| 路由别名 | `decide_after_spec_validate`、`route_after_spec_validate` |
| 节点字符串回退 | `PipelineNode._missing_`：`spec_validate` → `prd_validate` 等 |
| Profile 属性 | `ValidationConfig.spec` → 返回 `.prd` |
| Loop 字段 | `max_spec_revisions` 与 `max_prd_revisions` 双写/双读 |

### 明确未改（按 §明确不改）

- `design.spec_ref*`、`validators/design_*` 传导参数名 `spec`
- `design_triggers.spec_*` / `task_tier.is_spec_*` 函数名（表意「来自 PRD 环信号」，非 Run 文件名）
- 旧 run 磁盘：`docs/runs/calculator-10-01/spec.*` 未迁移
- `prd_semantic_rules.py`（语义校验，见 semantic-validation 设计，**未建**）

### 待续（R6 + 文档清扫）

- [ ] 删除上表 **shim / 别名** 模块与符号
- [ ] `examples/snippets/spec-default.json` → `prd-default.json`（及 stub / README 路径）
- [ ] `scripts/debug_pm_spec_llm.py` 标题与 `SpecArtifact` 引用
- [ ] 定稿大文档：`multi-agent-pipeline-design.md`、`artifact-continue-design.md`、`design-validate.md`、`P1-backlog.md`、`profiles.md`、`hitl.md`、`pipeline-overview.mmd` 等
- [ ] `domains/arb/` 术语同步（开放问题 #1）
- [ ] `checkpoint.db` 内嵌旧节点名策略（开放问题 #2）
- [ ] Semantic validation：`prd_semantic_rules.py` + `PRD-S*`（独立轨道，见 semantic-validation 设计）

---

## 影响面清单（实现勾选）

> 勾选状态截至 **2026-07-11**（R0–R5 实施后）。`[~]` = 新模块已建，旧路径 shim 暂留。

### 代码 `multi_agent_code_factory/`

- [x] `schemas/prd.py`（自 `spec.py`）
- [~] `schemas/spec.py` — shim，R6 删除
- [x] `schemas/__init__.py`、`validation_report.py`（`ValidationTarget.PRD`）
- [x] `schemas/hitl.py`（`HitlStage.PRD`）
- [x] `state.py`、`schemas/run_meta.py`
- [x] `artifact_loader.py`、`checkpoint.py`、`graph/runner.py`
- [x] `agents/pm.py`、`agents/normalizers/prd.py`
- [x] `nodes/prd_validate.py`、`nodes/prd_hitl.py`
- [~] `nodes/spec_validate.py`、`nodes/spec_hitl.py` — shim
- [x] `graph/graph_builder.py`、`graph/nodes/*`、`graph_routing.py`
- [x] `pipeline_nodes.py`
- [x] `validators/prd_*.py`、`validators/__init__.py`
- [~] `validators/spec_*.py` — shim
- [x] `renderers/prd_md.py`
- [~] `renderers/spec_md.py` — shim
- [x] `prompt_context.py`、`prompt_context_trim.py`
- [x] `agents/llm/prompt/validation_feedback.py`
- [x] `profile_config/models.py`、`config.py`（`validation.prd`、`max_prd_revisions`）
- [x] `profiles/_base/common.yaml`（`validation.prd`）
- [x] `run_artifact_names.py`
- [x] `tools/run_artifacts/meta.py`
- [x] `__main__.py` CLI（`--max-prd-revisions`）
- [x] `agents/stub/fixtures.py`（`PRD_VALIDATE_RETRY` + legacy coerce）
- [ ] `schemas/README.md`
- [ ] `agents/llm/prompt/schema_hints.py`、`agents/llm/schemas.py`（叙述性「spec」）
- [ ] `scripts/debug_pm_spec_llm.py`

### 测试 `tests/`

- [x] `test_validators.py`
- [x] `test_prd_rules_extended.py`（原 `test_spec_rules_extended.py`）
- [x] `test_prd_md_renderer.py`（原 `test_spec_md_renderer.py`）
- [x] `test_graph*.py`、`test_continue_*.py`
- [x] `agents/llm/test_*` 中 `PrdArtifact`
- [ ] `tests/integration/test_todo_cli_e2e.py`（live，未在本轮验收）

### 文档 `docs/design/pipeline/`

- [x] `quality-gates/spec-validate.md` → **`prd-validate.md`**（全文 `PRD-*`）
- [x] `quality-gates/README.md`、`README.md`、`artifact-schemas/README.md`、`artifact-templates/README.md`（核心路径）
- [ ] `quality-gates/design-validate.md` 传导（`prd→design`、`PRD-016`）
- [ ] `multi-agent-pipeline-design.md`、`artifact-continue-design.md`
- [ ] `profiles.md`、`P1-backlog.md`
- [ ] `quality-gates/hitl.md`、`artifact-schemas/hitl-spec.md`
- [ ] `examples/README.md`、`examples/snippets/pipeline-overview.mmd`
- [ ] [`2026-07-10-semantic-validation-design.md`](./2026-07-10-semantic-validation-design.md)（`PRD-S*` 规则实现未开始）

### 明确不改

- **`DES-*`** design 环 rule_id（已正确）
- **`design.json` / `design.md`**（已正确）
- **定稿文件名 `prd-spec.md`**（已正确；`-spec` = 格式规范，非需求环产物名）
- **`design.spec_ref` / `spec_ref_id` / `spec_ref_kind` / `traceability.spec_ref_*`** — 指向 PRD **内容 ID**（标题、FEAT/AC），非 Run 文件名；**不**改为 `prd_ref`
- **`provider_spec` / `PROVIDER_SPECS`**（LLM provider 配置）— 与 PRD 环无关
- **旧 run 磁盘文件**（如 `calculator-10-01/spec.*`）— 不迁移，靠双读

---

## 遗漏清单（审计 2026-07-10，进度更新 2026-07-11）

> 初版审计相对 v4 §影响面清单的缺口。**2026-07-11 更新：** 下列「代码遗漏」主体已在 R1–R5 完成；未勾项并入 §实施进度「待续」。

### 结论（更新后）

| 维度 | 评估（2026-07-11） |
|------|---------------------|
| **主干覆盖** | Run 产物、schema、state、节点、validators、Profile — **已落地** |
| **兼容层** | shim + 别名 **故意保留**，待 R6 删除 |
| **R0 文档清扫** | **部分完成** — 核心 README + `prd-validate.md`；大文档 / 示例 / hitl 等待续 |
| **实现** | **R1–R5 完成**；`pytest --ignore=tests/integration` 全绿 |
| **语义层** | `prd_semantic_rules.py` / `PRD-S*` — **未开始**（见 semantic-validation 设计） |

### 代码遗漏 — 已完成项（原 §遗漏清单）

以下已在 R1–R5 实现，**不再阻塞**主线 PRD 命名：

- [x] 图中间层：`graph/nodes/validate_nodes.py`、`route_nodes.py`、`terminal_nodes.py`、`runner.py`
- [x] 节点包：`nodes/__init__.py`、`fail.py`、`deploy.py`、`design_validate.py`（`PrdArtifact` / `state.prd`）
- [x] agents：`normalizers/*`、`architect.py`、`reviewer.py`、`stub/fixtures.py`（`PRD_VALIDATE_RETRY`）
- [x] PRD→Design 传导：`validators/design_*`（参数名 `spec` 保留）、`mermaid.py`
- [x] 校验：`validators/prd_*`、`target="prd"`、`validate_prd_extended_rules`
- [x] 配置：`profile_config/models.py`、`common.yaml`、`autonomy_policy.yaml`
- [x] 加载：`artifact_loader.py`、`run_meta.py`、`schemas/__init__.py`
- [x] 符号：`normalize_prd`、`decide_after_prd_validate`、`node_prd_*`、`trim_prd`、`format_prd_validation_feedback`

### 仍待办（自原遗漏清单 + R6）

- [ ] `schemas/README.md`
- [ ] `agents/llm/prompt/schema_hints.py`、`schemas.py`、`prompted_json.py` 注释
- [ ] `validators/design_triggers.py` / `task_tier.py` 函数名 `spec_*`（可选重命名为 `prd_*`，非必须）
- [ ] `scripts/debug_pm_spec_llm.py`、`run_debug_pm_spec_llm.bat`
- [ ] `examples/snippets/spec-default.json` → `prd-default.json`
- [ ] 定稿文档全文（见 §实施进度「待续」）

<details>
<summary>初版审计原文（归档，供对照）</summary>

### 代码遗漏（§影响面未单列）— 初版

| 区域 | 文件 | 待改要点 |
|------|------|----------|
| **图中间层** | `graph/nodes/validate_nodes.py` | `node_spec_validate`、`run_spec_validate`、`spec_validation` 键 |
| | `graph/nodes/route_nodes.py` | `node_route_after_spec_validate`、`decide_after_spec_validate` |
| | `graph/nodes/terminal_nodes.py` | `node_spec_hitl`、`run_spec_hitl` |
| | `graph/nodes/__init__.py` | 导出符号 |
| | `graph/nodes/agent_nodes.py` | 注释 `spec.json` / `spec.md` |
| | `graph/runner.py` | continue 路径 `run_spec_validate`、`spec_validation` |
| **节点包** | `nodes/__init__.py` | `run_spec_*` 导出 |
| | `nodes/fail.py` | `spec_revisions` 日志、`spec_revision_count` |
| | `nodes/deploy.py` | `spec_revision_count` 透传 |
| | `nodes/design_validate.py` | `SpecArtifact` 参数（→ `PrdArtifact` / `prd`） |
| **agents** | `agents/normalizers/__init__.py` | `normalize_spec` 导出 |
| | `agents/normalizers/design.py` | `state.spec` |
| | `agents/normalizers/design_enrichment.py` | `SpecArtifact` 类型与 `spec` 参数 |
| | `agents/architect.py` | `state.spec`、错误文案 |
| | `agents/reviewer.py` | `spec_revision_count` |
| | `agents/stub/fixtures.py` | `SPEC_VALIDATE_RETRY`、`spec` 路径、`spec-default.json` |
| **LLM 辅助** | `agents/llm/prompt/schema_hints.py` | 「from spec」文案 |
| | `agents/llm/schemas.py` | PM schema hint 中 `spec` |
| | `agents/llm/strategies/prompted_json.py` | 注释「spec、design」 |
| **PRD→Design 传导** | `validators/design_rules.py` | `SpecArtifact` / `spec` 参数 |
| | `validators/design_rules_extended.py` | 同上 |
| | `validators/design_md_rules.py` | 同上 |
| | `validators/design_triggers.py` | `spec_*` 函数名（如 `spec_implies_persistence`） |
| | `validators/task_tier.py` | `is_spec_non_trivial`、`spec_implies_persistence` 等 |
| | `validators/mermaid.py` | `spec` 参数 |
| **校验辅助** | `validators/__init__.py` | `validate_spec_*` 导出 |
| | `validators/_report.py` | `log_validation_result(target="spec")` 调用方 |
| | `validators/spec_rules_extended.py` | `validate_spec_extended_rules` → `validate_prd_extended_rules` |
| **配置** | `profile_config/models.py` | `ValidationConfig.spec` 字段 → `prd`（+ legacy alias） |
| | `profiles/_base/common.yaml` 及 extends 链 | `validation.spec` |
| | `config/autonomy_policy.yaml` | `max_spec_revisions` |
| **加载/元数据** | `artifact_loader.py` | `ARTIFACT_MAP` 键、`spec.json` 路径、`_resolve_user_request(spec)` |
| | `schemas/run_meta.py` | `spec_revision_count` |
| | `schemas/__init__.py` | `SpecArtifact` 导出 |
| | `schemas/README.md` | `spec.py` 引用 |
| **脚本** | `scripts/debug_pm_spec_llm.py` | 文件名/标题 `SpecArtifact`；同步 `run_debug_pm_spec_llm.bat` |

**符号表补充（§命名对照）：**

| 原 | 新 |
|----|-----|
| `normalize_spec` | `normalize_prd` |
| `validate_spec_extended_rules` | `validate_prd_extended_rules` |
| `validate_spec_md_rules` | `validate_prd_md_rules` |
| `decide_after_spec_validate` | `decide_after_prd_validate` |
| `node_spec_validate` / `node_spec_hitl` / `node_route_after_spec_validate` | `node_prd_*` |
| `is_spec_non_trivial` | `is_prd_non_trivial`（或保留语义名，参数改 `prd`） |
| `spec_implies_persistence` 等 `spec_*` 触发器 | `prd_*` 前缀 |
| `SPEC_VALIDATE_RETRY`（stub） | `PRD_VALIDATE_RETRY` |
| `log_validation_result(target="spec")` | `target="prd"` |

### 测试遗漏

§影响面已列部分文件，**另需**：

- [ ] `tests/test_profiles.py` — `profile.validation.spec`
- [ ] `tests/test_config.py` — `max_spec_revisions`
- [ ] `tests/test_task_tier.py`、`tests/test_design_triggers.py`
- [ ] `tests/test_design_delivery_rules.py`、`tests/test_design_md_renderer.py`
- [ ] `tests/test_continue_infer.py`、`tests/test_continue_loader.py`、`tests/test_continue_pipeline.py`
- [ ] `tests/integration/test_todo_cli_e2e.py`
- [ ] `tests/agents/llm/test_prompt_shape.py`、`test_validation_feedback.py`
- [ ] 示例片段：`docs/design/pipeline/examples/snippets/spec-default.json` → **`prd-default.json`**（及 README、stub 路径）

### 文档遗漏（R0 未完成项）

| 状态 | 文件 | 残留示例 |
|------|------|----------|
| **未改名** | `quality-gates/spec-validate.md` | 全文 `SPEC-*` |
| **部分更新** | `quality-gates/spec-validate.md` 以外已改 run 路径的文档 | 正文仍 `spec_validate`、`SpecArtifact` |
| **未清扫** | `quality-gates/README.md` | `SPEC-*` 49 条、`spec_validate.py` |
| | `artifact-schemas/README.md` | `SpecArtifact`、`spec.json`、`spec.md` |
| | `artifact-templates/README.md` | `spec_validate` |
| | `artifact-continue-design.md` | `run_spec_validate`、`spec_validate` 正文 |
| | `multi-agent-pipeline-design.md` | 大量旧名 |
| | `implementation-plan.md`、`P1-backlog.md`、`profiles.md` |
| | `quality-gates/design-validate.md` | 「spec→design」传导表述 |
| | `quality-gates/hitl.md`、`artifact-schemas/hitl-spec.md` | `HitlStage=spec`、`loop_limit:spec_revision`、`validation.spec` |
| | `examples/README.md`、`examples/snippets/pipeline-overview.mmd` | `SpecArtifact`、`spec_validate` 节点 |
| | `references/glossary.md`、`python-style.md` |
| | `docs/README.md` |
| | `multi_agent_code_factory/profiles/README.md` |
| | `domains/arb/design/arb-factory-design.md` |
| **Prompt 模板** | `profiles/_shared/prompts/pm.txt` | 「spec」产物表述 |
| | `profiles/_shared/prompts/artifact-language-snippet.txt` | spec 环 |
| | `profiles/_shared/prompts/architect.txt` | 保留 `spec_ref` 字段说明（**字段名不改**），「spec」叙述改 PRD |
| | `profiles/_shared/prompts/dev-principles-snippet.txt`、`python/prompts/python-style-snippet.txt` | 按需改叙述 |

**Hitl / loop 命名（文档 + 实现一致）：**

| 原 | 新 |
|----|-----|
| `HitlStage.SPEC` / `stage: "spec"` | `HitlStage.PRD` / `"prd"` |
| `loop_limit:spec_revision` | `loop_limit:prd_revision` |
| `validation.spec.require_hitl`（reason 字符串） | `validation.prd.require_hitl` |

### 变量 / 环境变量遗漏

| 原 | 新 |
|----|-----|
| `FACTORY_MAX_SPEC_REVISIONS` | `FACTORY_MAX_PRD_REVISIONS`（短期双读） |
| CLI `--max-spec-revisions` | `--max-prd-revisions` |
| `LoopLimits.max_spec_revisions` | `max_prd_revisions` |
| State 返回键 `{"spec": ...}`（`pm.py`） | `{"prd": ...}` |
| `prompt_context` 键 `spec`、`spec_validation` | `prd`、`prd_validation` |
| `trim_spec` / `result["spec"]` | `trim_prd` / `result["prd"]` |

### 建议修订 v4 正文

1. §影响面 **拆分子清单**：`graph/nodes/*`、`validators/design_*` + `task_tier` + `design_triggers`、`agents/normalizers/*`、`profile YAML`、`scripts/`。
2. §明确不改 **显式列出 `spec_ref*`**，避免误改 design schema。
3. §实施分期 **R0 验收** 增加：`rg 'SPEC-|spec_validate|SpecArtifact' docs/design/pipeline` 仅允许例外清单命中。
4. **开放问题 #1** 建议默认：**`domains/arb/` 与主线同步**，避免双套术语。

</details>

---

## 与 Semantic Validation 的关系

语义规则并入 PRD 环编号：**`PRD-S01`～`PRD-S06`**（原 `SPEC-S*`）；DES-S* 不变。详见 [`2026-07-10-semantic-validation-design.md`](./2026-07-10-semantic-validation-design.md) v4。

---

## 开放问题

1. **`domains/arb/`** 等域外文档中的 `SpecArtifact` 是否同步？
2. **checkpoint.db** 内嵌节点名 `spec_validate`：迁移还是新 run 新库？
3. **R6 删除 legacy** 是否与 `calculator-10-01` 演示 run 保留冲突？（建议 run 不迁移，仅代码双读）

---

## 参考

- 废止策略：v3「保留 `spec.py`」— 已由 v4 全栈 PRD 化取代
