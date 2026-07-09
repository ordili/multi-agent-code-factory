# design_validate — 规则清单

> **索引：** [quality-gates/README.md](./README.md)  
> **实现：** `multi_agent_code_factory/validators/design_rules.py` · `design_rules_extended.py` · `mermaid.py`  
> **JSON 契约：** [artifact-schemas/design-spec.md](../artifact-schemas/design-spec.md)  
> **人读模板：** [artifact-templates/design-spec.md](../artifact-templates/design-spec.md) · [flow-spec.md](../artifact-templates/flow-spec.md)

**rule_id 合计：** **62** 条（§4.1 JSON **38** · §4.2 `design.md` / `*.mmd` **23** · §4.4 HITL **1**）。

**小任务 / CLI / 无持久化：** 模板 [极简指引](../artifact-templates/design-spec.md#小任务--无持久化极简指引) 与部分 `DES-*` error 规则（如 `DES-012`–`014`）存在张力；Live trivial 项目可能触顶 `max_design_revisions` — 见 calculator 类 run 的 `design_validation.json`。

---

## 4.1 JSON 结构（error / warn）

| rule_id | 严重度 | 必检 | 触发条件 | 字段 | 判定 |
|---------|--------|------|----------|------|------|
| `DES-001` | error | 是 | — | `dev_tasks` | 非空 |
| `DES-002` | error | 是 | — | `dev_tasks[].id` | 唯一 |
| `DES-003` | error | 是 | — | `dev_tasks[].path`、`id`、`description` | 唯一 path；必填 |
| `DES-004` | error | 是 | — | `dev_tasks[].depends_on` | 引用已知 task id |
| `DES-005` | error | 是 | — | `dev_tasks` | 依赖无环 |
| `DES-006` | error | 是 | — | `modules` | 非空 |
| `DES-007` | error | 是 | — | `modules[]` | `name`、`path`、`responsibility`、`code_domain` 必填 |
| `DES-008` | error | 是 | — | `non_goals`、`context_view`、`architecture.solution_strategy` | 非空 |
| `DES-009` | error | 是 | — | `traceability`、`dev_tasks[].covers` | 非空；P0 `FEAT` 可追溯 |
| `DES-010` | error | 是 | — | `cross_cutting` | 须存在（可为 `{}`） |
| `DES-011` | error | 条件 | spec `operational_profile` 非 trivial | `non_functional` | 非空 |
| `DES-012` | error | 是 | — | `external_dependencies` | 非空（无中间件时显式 `filesystem`/`none`） |
| `DES-013` | error | 是 | — | `table_schemas`、`data_model` | 非空或字段级 `columns` 齐全 |
| `DES-014` | error | 是 | — | `transaction_constraints` | 非空（落实 spec `consistency_profile`） |
| `DES-015` | error | 是 | — | `error_catalog` | 非空；≥1 条可映射 Flow 异常分支 |
| `DES-016` | error | 是 | — | `test_cases` | 非空；每个 P0 AC 有 `covers` 或用例 |
| `DES-017` | error | 是 | — | `diagrams[]` | 同时含 `kind=sequence` 与 `kind=flowchart` |
| `DES-018` | error | 是 | — | `table_schemas[].columns[]` | 显式 `nullable`；`description` 非空 |
| `DES-019` | error | 条件 | `storage` 为关系型 DB | `table_schemas[]` | 含 `created_at`、`updated_at`；索引或 `notes`；`version`（若 `require_version`） |
| `DES-020` | warn | 是 | — | `indexes[]` | 每条含 `purpose` |
| `DES-021` | error | 是 | — | `error_catalog[].code`、`test_cases[]` | 每 code ≥1 条 `kind=negative` 且 `error_code` 匹配 |
| `DES-022` | warn | 是 | — | `test_cases[]` | 含 `happy`、`negative`、`boundary`；P0 FEAT/US 有 happy |
| `DES-023` | error | 是 | — | `error_catalog[].code` | 匹配 `^ERR-[A-Z][A-Z0-9_]{1,11}-\d{3}$` |
| `DES-024` | error | 是 | — | `test_cases[].id` | 匹配 `^TC-(HAP/NEG/BND)-[A-Z][A-Z0-9_]{1,11}-\d{3}$` |
| `DES-025` | error | 是 | — | `test_cases[].error_code` | 须存在于 `error_catalog[].code` |
| `DES-026` | warn | 是 | — | `test_cases[].kind`、`test_cases[].id` | `kind` 与 id 中段一致 |
| `DES-027` | error | 是 | — | `modules[].code_domain` | 非空、格式合法、模块间不重复 |
| `DES-028` | error | 是 | — | `external_dependencies[]` | `code_domain` 规则（`none`/`filesystem`/中间件） |
| `DES-029` | error | 是 | — | `error_catalog[].code` | `{域}` 段在已注册域集合 |
| `DES-030` | error | 是 | — | `test_cases[].id` | `{域}` 段在已注册域集合 |
| `DES-031` | warn | 条件 | `kind=negative` 且填 `error_code` | `test_cases[]` | `error_code` 与 `id` 域段宜一致 |
| `DES-032` | error | 是 | — | `modules[].interfaces[]` | 存在且 `module_ref` 匹配（`SYS` 豁免） |
| `DES-033` | error | 是 | — | `interfaces[].operations[]` | 非空；`summary`、`inputs`、`outputs` 齐全 |
| `DES-034` | warn | 条件 | `operations[].errors[]` 非空 | `operations[].errors[]` | 须存在于 `error_catalog[].code` |
| `DES-101` | error | 条件 | 提供 spec | `traceability`、`dev_tasks[].covers` | 覆盖全部 `acceptance_criteria[].id` |
| `DES-102` | error | 条件 | spec 有 `scope_out` | `summary`、`modules[]` | 不得实现 scope_out 项 |
| `DES-103` | error | 是 | — | `dev_tasks[].path`、`modules[].path` | 不得路径逃逸（`..` / 绝对路径） |
| `DES-104` | error | 条件 | `file_plan` 非空 | `file_plan[].path` | 须在 `dev_tasks[].path` 中 |

> **字段** 列与 [design-spec.md](../artifact-schemas/design-spec.md) JSON 契约一致（英文键名）。

## 4.2 design.md / `*.mmd` 格式（P1）

Run `design.md` 须 **中文固定章节**（§1–§10 + 附录 A–E）；**不含** Rollout & Deployment。

| rule_id | 严重度 | 必检 | 触发条件 | 检查对象 | 判定 |
|---------|--------|------|----------|----------|------|
| `DES-201` | warn | 是 | — | `design.md` | 须含 §1–§6、§8、§10 中文标题 |
| `DES-202` | warn | 是 | — | `design.md` | 须含附录 A–E |
| `DES-203` | error* | 是 | — | `*.mmd` | 可解析；至少 1 文件含 sequence + flowchart |
| `DES-204` | warn | 是 | — | `*.mmd` | participant / 节点与 `modules`、`interfaces` 一致 |
| `DES-205` | warn | 是 | — | `design.md` / `test_strategy` | 须含 `## 8. 测试计划` 或 `test_strategy` 非空 |
| `DES-206` | warn | 是 | — | `design.md` §4 | 须含 `### 4.6 流程与时序` 或引用 `*.mmd` |
| `DES-207` | warn | 是 | — | `design.md` | 须含附录 E |
| `DES-209` | warn | 是 | — | `design.md` | 须含 `## 3. 非目标` |
| `DES-210` | warn | 是 | — | `design.md` | 须含 `## 10. 待澄清项` |
| `DES-211` | warn | 条件 | 长运行服务 | `design.md` §9 | `## 9. 监控与告警` 非「不适用」（CLI 可 N/A） |
| `DES-212` | warn | 是 | — | `design.md` | 须含 `### 4.3 外部依赖` |
| `DES-213` | warn | 是 | — | `design.md` | 须含 `### 4.5 数据模型与表结构` |
| `DES-214` | error* | 是 | — | `diagrams[]`、`*.mmd` | 登记 sequence + flowchart；文件内可识别两类图 |
| `DES-215` | warn | 是 | — | `design.md` / `test_cases` | 须含附录 D 或 `test_cases` 非空 |
| `DES-216` | warn | 是 | — | `design.md` §6 | 须含 `### 6.1` 事务/一致性 与 `### 6.2` 异常与错误码 |
| `DES-217` | warn | 是 | — | `design.md` §4.6 | 须引用 `*.mmd`（较 DES-206 更严） |
| `DES-218` | warn | 是 | — | `design.md` §4.5 表格 | 须含「可空」「注释」列 |
| `DES-219` | warn | 是 | — | `design.md` 附录 D | 须含「类型」列（happy / negative / boundary） |
| `DES-220` | warn | 是 | — | `design.md` §4.2 | 模块表含 `code_domain` 列 |
| `DES-221` | warn | 是 | — | `design.md` §4.4 | 须含接口定义；HTTP 宜分入参/出参表 |
| `DES-222` | warn | 是 | — | `design.md` | 须含 `## 5. 方案对比`（宜 2 行） |
| `DES-223` | warn | 条件 | 模块 ≥2 或 §4.3 有外部依赖 | `architecture-*.mmd` | 宜有 `kind=context` 架构图 |

> **`DES-208`（非 rule_id）：** 已废弃（原 §9 Rollout）；Run **不得**含 Rollout 章节。  
> \* `DES-203` / `DES-214` 在 `validation.design.validate_mermaid: false` 时降为 warn 或跳过。

## 4.4 HITL 标志

| rule_id | 严重度 | 必检 | 触发条件 | 字段 | 判定 |
|---------|--------|------|----------|------|------|
| `DES-301` | — | 条件 | `hitl_flags` 命中 Profile.`require_hitl_if_flags` | `hitl_flags` | 标记 `require_hitl` → **design_hitl** |

**失败：** `route_after_design_validate` → **architect**；violations 注入 Architect prompt。
