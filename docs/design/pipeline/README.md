# 工厂设计 — 细目索引

## 依赖上游文档（只读）

阅读 / 修订 pipeline 细目时 **以本表为目录级上游**；各子文档另含专属上游表，细则以子文档正文为准。


| 分类        | 上游文档                                                        | 定位                          |
| --------- | ----------------------------------------------------------- | --------------------------- |
| **总览**    | [00-master-overview.md](../00-master-overview.md)           | V1 边界与 master 设计依据          |
| **总设计**   | [multi-agent-pipeline-design.md](./multi-agent-pipeline-design.md) | 系统的总体设计书 |
| **领域（V2）** | [domains/README.md](../../../domains/README.md)             | 领域 Profile 扩展（非 V1 主线）      |


---

> **主线文档：** [multi-agent-pipeline-design.md](./multi-agent-pipeline-design.md)（流程、路由、目录、验收）  
> **本目录：** Profile、结构化产物规格、校验、示例与参考的 **详细设计 Spec**，避免主线过长。  
> **V1 范围：** 通用流水线；**V2 领域**见 [domains/](../../../domains/README.md)

---

## 目录与职责

本目录按 **文档类型** 分子目录；**运行时落盘**在 `docs/runs/<task_id>/`（单次任务产物，不在此定义）。

| 目录 / 文件 | 存什么 | 作用 | 代码落点（以实现为准） |
|-------------|--------|------|------------------------|
| [multi-agent-pipeline-design.md](./multi-agent-pipeline-design.md) | 流水线 **总设计** | 角色、图路由、Run 目录、验收；其它细目 **索引入口** | `graph.py`、`graph_routing.py`、`state.py` |
| [profiles.md](./profiles.md) | **Profile** 字段说明 | 语言、toolchain、`validation` / `hitl`、prompt 路径；与业务无关的配置注入 | `profiles/*.yaml`、`profiles.py` |
| [artifact-schemas/](./artifact-schemas/README.md) | **JSON 契约** `*-spec.md` | 定义 Run `*.json` 的字段、类型、枚举、示例；机器读 **唯一字段基线** | `schemas/*.py` |
| [artifact-templates/](./artifact-templates/README.md) | **人读格式** `*-spec.md` | 定义 Run `*.md` / `*.mmd` 怎么写、章节结构、写作约束 | `renderers/*.py` |
| [quality-gates/](./quality-gates/README.md) | **校验与 HITL** | `SPEC-*` / `DES-*` 规则、`validation` 配置、人工 interrupt 约定 | `validators/`、`nodes/*_validate.py` |
| [examples/](./examples/README.md) | JSON / Mermaid **片段** | 可拷贝示例；**非规范**，以 schemas 为准 | — |
| [references/](./references/README.md) | 术语、MetaGPT、调研 | **非规范性**参考；不参与校验 | — |
| [implementation-plan.md](./implementation-plan.md) | V1 **编码计划** | 阶段、PR 拆分、与 §10 验收对照 | `multi_agent_code_factory/` |
| [P1-backlog.md](./P1-backlog.md) | P1 待办清单 | 可勾选 backlog，与验收对齐 | — |
| [python-style.md](./python-style.md) | Python 工程规范 | PEP 8 / Ruff / pytest（工厂自身代码） | `pyproject.toml` |

---

## 产物规格：三层分工

流水线每个阶段产出 **JSON（机器）+ 人读视图（可选）**。设计文档也分三层，**职责不重叠**：

```text
artifact-schemas/*-spec.md     JSON 字段、类型、标识符、嵌套结构
        ↓  （templates 引用 schemas）
artifact-templates/*-spec.md   人读章节、表格写法、Profile 选用、样例叙事
        ↓  （quality-gates 引用 schemas + templates）
quality-gates/*.md             校验规则规格（rule_id + 触发条件 + 判定）
        ↓  （validators 实现规则；引用 schemas + templates）
multi_agent_code_factory/      Pydantic、renderers、validators、nodes
```

| 层 | 回答的问题 | 典型读者 |
|----|------------|----------|
| **schemas** | `spec.json` / `design.json` **有哪些键、什么类型** | Agent prompt 作者、Pydantic 维护者 |
| **templates** | Run `spec.md` / `design.md` **长什么样、写哪些 §** | Architect / PM 文档作者、HITL 评审 |
| **quality-gates** | 产物 **怎样算过门禁**（**规则正文**：`rule_id`、严重度、触发条件、判定） | 校验器实现、Profile 配置 |

**成对文档**（同名 `-spec`，不同目录）：

| Schema | JSON 契约（schemas） | 人读格式（templates） | Run JSON | Run 人读 |
|--------|----------------------|----------------------|----------|----------|
| `SpecArtifact` | [prd-spec.md](./artifact-schemas/prd-spec.md) | [prd-spec.md](./artifact-templates/prd-spec.md) | `spec.json` | `spec.md` |
| `DesignArtifact` | [design-spec.md](./artifact-schemas/design-spec.md) | [design-spec.md](./artifact-templates/design-spec.md) + [flow-spec.md](./artifact-templates/flow-spec.md) | `design.json` | `design.md` + `*.mmd` |
| `ReviewReport` | [review-spec.md](./artifact-schemas/review-spec.md) | [review-spec.md](./artifact-templates/review-spec.md) | `review.json` | `review.md` |

仅 JSON、无人读 template 的契约（如 `dev_manifest.json`、`test_report.json`）见 [artifact-schemas/README.md](./artifact-schemas/README.md)。

---

## 流水线阶段的文档依赖

与 Agent 执行顺序一致（**上游 → 下游**）：

```text
multi-agent-pipeline-design.md
profiles.md
    ↓
artifact-schemas/prd-spec.md          → spec.json
artifact-templates/prd-spec.md        → spec.md
quality-gates/spec-validate.md
    ↓
artifact-schemas/design-spec.md       → design.json
artifact-templates/design-spec.md     → design.md
artifact-templates/flow-spec.md       → *.mmd
quality-gates/design-validate.md
    ↓
artifact-templates/dev-principles-spec.md   （约束 code_root，非 JSON）
artifact-schemas/dev-manifest-spec.md     → dev_manifest.json
    ↓
（实现 / QA）
artifact-schemas/test-report-spec.md        → test_report.json
artifact-schemas/review-spec.md             → review.json
artifact-templates/review-spec.md           → review.md
```

**横切：** [artifact-schemas/hitl-spec.md](./artifact-schemas/hitl-spec.md)、[validation-report-spec.md](./artifact-schemas/validation-report-spec.md)、[run-meta-spec.md](./artifact-schemas/run-meta-spec.md) — 校验/HITL/元数据，由各节点引用。

---

## 文档规则

### 1. 单向依赖 {#1-单向依赖}

**每条设计文档只允许引用「上游」文档和本文自身内容，不引用、不描述下游文档的职责。**

| 文档层 | 可引用 | 不可引用 / 不可展开 |
|--------|--------|---------------------|
| **artifact-schemas** | 上游 schema（如 design 引用 prd-spec）、Pydantic 路径、本文字段 | templates 章节写法、quality-gates rule_id、renderers |
| **artifact-templates** | 总设计、**上游模板**（如 design-spec → prd-spec）、姊妹 templates（如 design-spec → flow-spec）、artifact-schemas 字段（正文引用，不进依赖表）、本文 | quality-gates 具体规则、实现类名（除必要一行落点） |
| **quality-gates** | schemas + templates（校验基线） | 实现细节、下游 run 样例目录 |
| **examples** | schemas（字段为准） | 自造与 schema 冲突的字段 |
| **references** | 外部资料 | 不作为它 doc 的上游规范 |

**目的：** 改 JSON 字段只动 schemas；改 MD 章节只动 templates；改门禁只动 quality-gates — **避免 circular doc edits**。

**索引文档例外：** 本 README、各目录 `README.md`、`multi-agent-pipeline-design.md` 的文档地图 **可以列出下游路径**（仅索引，不在正文重复下游规格）。

### 2. 一文一责

| 原则 | 说明 |
|------|------|
| **schemas = 机器契约** | 只写 JSON 字段、类型、标识符、`diagrams[]` 等；**不写** Run Markdown 章节映射（映射在 templates） |
| **templates = 人读格式** | 只写章节、表格、写作约束、Profile 选用；字段定义 **引用 schemas**，不重复造字段 |
| **quality-gates = 校验规则规格** | **规则正文在此定义**：`rule_id`、严重度、触发条件、检查字段/章节、判定；字段/章节含义 **引用 schemas/templates**，不重复造字段 |
| **examples = 片段** | 方便拷贝；与 schema 冲突时 **以 schema 为准** |
| **references = 背景** | 不参与产物校验，不被 schemas 引用 |

### 3. 文首依赖表

每个 `pipeline/**/*.md` 在 **H1 下** 须有 **`## 依赖上游文档（只读）`**（分类 · 上游文档 · 定位）；**只列独立上游文档**，章节不算单独一行；细则约定写在表前引导语并链到 [README.md §单向依赖](#1-单向依赖)。**`artifact-schemas/`** 不得把 `artifact-templates/`、`quality-gates/` 列入上游表；**`artifact-templates/`** 不得把 `artifact-schemas/`、`quality-gates/` 列入上游表。**`artifact-templates/`** 下各 `*-spec.md` **一般**须在表中列出流水线更早阶段的**上游人读模板**（分类 **上游模板**，定位 **上游人读 {name}-spec.md**）；同层配套（如 `flow-spec` 对 `design-spec`）在**下游**模板记 **姊妹模板**，在**本模板**记 **上游模板**。范例：[prd-spec.md（schemas）](./artifact-schemas/prd-spec.md#依赖上游文档只读) · [prd-spec.md（templates）](./artifact-templates/prd-spec.md#依赖上游文档只读) · [design-validate.md](./quality-gates/design-validate.md#依赖上游文档只读)（gates 层）。

### 4. 命名约定

```text
artifact-schemas/{name}-spec.md   →  JSON 契约说明（设计文档，非 run 文件）
artifact-templates/{name}-spec.md →  人读格式规范（设计文档，非 run 文件）
docs/runs/<task_id>/{basename}    →  单次 run 落盘（spec.json、design.md 等）
```

后缀 **`-spec`** 表示 **格式/契约规范**；Run 落盘用 **短 basename**（`spec.json`、`design.md`）。

### 5. 定稿与实现

- **定稿层：** `artifact-schemas/`、`artifact-templates/`、`quality-gates/` 下的 `*-spec.md` 为规格基线。
- **实现层：** `schemas/`、`renderers/`、`validators/` 须与规格一致；滞后项记在 templates 页眉「待同步」或 [P1-backlog.md](./P1-backlog.md)，**不在 schemas 里写实现 TODO**。

---

## 阅读顺序

| 目的 | 路径 |
|------|------|
| 理解整条流水线 | [multi-agent-pipeline-design.md](./multi-agent-pipeline-design.md) §1–§4、§6 |
| 配 Profile / 多语言 | [profiles.md](./profiles.md) |
| 查 JSON 字段 | [artifact-schemas/README.md](./artifact-schemas/README.md) |
| 写 / 审 spec.md、design.md | [artifact-templates/README.md](./artifact-templates/README.md) |
| 查校验规则 | [quality-gates/README.md](./quality-gates/README.md) |
| 抄 JSON / 图片段 | [examples/README.md](./examples/README.md) |
| 开始编码 | [implementation-plan.md](./implementation-plan.md) |
| 查 P1 待办 | [P1-backlog.md](./P1-backlog.md) |

**Agent 角色命名：** [§3.1](./multi-agent-pipeline-design.md#31-角色命名约定)（PM / Architect / Developer / QA / Reviewer ↔ `role_id`）。
