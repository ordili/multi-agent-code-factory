# prd-spec.md — PM 需求文档（人读）格式规范

> **状态：** 定稿 · [artifact-templates 索引](./README.md)  
> **配套规范：** [design-spec.md](./design-spec.md) · [flow-spec.md](./flow-spec.md) · [review-spec.md](./review-spec.md)  
> **节点交接以：** [`../artifact-schemas/prd-spec.md`](../artifact-schemas/prd-spec.md)（`SpecArtifact` / `spec.json`）**为准**；本文件定义 Run `spec.md` 的章节与写法。  
> **Run 路径：** `docs/runs/<task_id>/spec.md`  
> **校验：** JSON → [quality-gates.md §3](../quality-gates.md#3-spec_validate--规则清单)；MD 格式 → §3.3（P1）

借鉴主流 PRD（功能清单 + 业务指标 + 用户故事 + 验收标准）与 MetaGPT WritePRD；字段与 `SpecArtifact` **一一对应**；**以 `spec.json` 为准**，本文件为 Run `spec.md` 的渲染目标。

---

## 概念分工

| 概念 | 回答的问题 | JSON 字段 |

|------|------------|-----------|

| **业务指标** | 业务上怎样算「做成了」？（可选） | `success_metrics[]` |

| **功能 / Features** | 交付哪些能力？ | `features[]` |

| **用户故事** | 用户怎么用？ | `user_stories[]` |

| **需求池** | 可排期交付细项、优先级与前置？ | `requirement_pool[]` |

| **验收标准 AC** | 流水线怎样判定可交付？ | `acceptance_criteria[]` |
| **术语 / 领域概念** | 名词在本产品里指什么？ | `context.glossary[]`（约定） |
| **稳定性与性能** | 体量、并发、性能 **档位与文字预期**（非具体数值） | `operational_profile` |
| **数据一致性** | 一致性与投递 **模型与文字预期**（非具体数值） | `consistency_profile` |

业务指标（KPI）偏 **业务结果与目标**；AC 偏 **可执行验收**（含 `automated_test`）。二者可呼应（如 KPI 引用 AC id），但不互相替代。**无明确业务度量时可不写 §4**，以 §10 验收标准为准。

### 功能 vs 用户故事 vs 需求池

**不重复，但层次不同**（细则见 §5–§7；反重复规则见 §6、§7）：

| 字段 | 视角 | 粒度 | 典型 id |
|------|------|------|---------|
| `features[]` | 有什么 **能力** | 模块级 | `FEAT-*` |
| `user_stories[]` | **谁**怎么用、为何 | 场景级 | `US-*` |
| `requirement_pool[]` | 可排期 **交付细项** | 条目级 | `REQ-*` |

```text
FEAT-1 待办 CRUD
  ├── US-1 添加待办
  ├── US-2 重启后仍能看到列表
  └── REQ-2 CLI 子命令（feature_id=FEAT-1, depends_on REQ-1）

FEAT-2 本地持久化
  ├── US-2（共用）
  └── REQ-1 持久化（feature_id=FEAT-2）
```

**最小条数：** `FEAT` ≥1、`US` ≥2、`REQ` ≥1（极简单任务 REQ 可仅 1 条；见 §7）。**异常场景** 在 §6 / §7 **可选**（见各节）；有用户可感知失败路径时建议至少 1 条 US + 对应 REQ / AC。

### 追溯链（FEAT → US → REQ → AC）

```text
FEAT-1 ──user_story_ids──► US-1, US-2
FEAT-2 ──user_story_ids──► US-2
US-*  ◄──行为覆盖── REQ-*（实现层，depends_on 可选）
US-* / KPI-*  ◄──验收── AC-*（§10 门禁）
```

---

## 固定章节（§4 可选；其余 §1–3、§5–11 必填，§12 推荐）


| §   | Markdown 标题       | 对应 JSON 字段                                  | 必填            |
| --- | ----------------- | ------------------------------------------- | ------------- |
| —   | `# {title}`       | `title`                                     | ✓             |
| 1   | `## 概述`           | `summary`、`profile`、`revision`              | ✓             |
| 2   | `## 术语与领域概念`      | `context.glossary[]`（约定，见下文）                | ✓             |
| 3   | `## 背景与上下文`       | `context`（领域键）                              | ✓             |
| 4   | `## 业务指标`         | `success_metrics[]`                         | 可选            |
| 5   | `## 功能`           | `features[]`                                | ✓             |
| 6   | `## 用户故事`         | `user_stories[]`                            | ✓             |
| 7   | `## 需求池`          | `requirement_pool[]`                        | ✓             |
| 8   | `## 范围`           | `scope_in[]`、`scope_out[]`                  | ✓             |
| 9   | `## 稳定性、性能与数据一致性` | `operational_profile`、`consistency_profile` | ✓             |
| 10  | `## 验收标准`         | `acceptance_criteria[]`                     | ✓             |
| 11  | `## 约束`           | `constraints[]`                             | ✓（无则写「无额外约束」） |
| 12  | `## 待澄清项`         | —（仅 MD）                                     | 推荐            |


**页脚元数据（必填，放文末）：**

```markdown

---

task_profile: {profile}

revision: {revision}

parent_task_id: {parent_task_id 或 —}

```

---

## 各节写法

### §1 概述

- **`# {title}`**（文首标题）与 JSON `title` 一致；`summary` 为 1～2 句目标，**不**展开功能列表（功能在 §5）。
- 首段：`summary` 原文或略扩写（不超过 3 句）。
- 列表：`Profile`、`Revision`；增量 run 时注明 `Parent task`。

### §2 术语与领域概念

列出正文中出现的 **领域名词** 及 **一句话定义**，供 HITL、Architect、Developer 统一理解，避免同一词多种含义。

表格推荐列：**名词** | **解释**

#### 写什么

- **领域实体 / 业务概念**（如「表达式」「订单」「仓位」「链上账户」）。
- **在本产品内有特殊含义的简称**（如「完成」「归档」在本系统指什么状态）。
- **后文 US / FEAT / 业务指标 会反复用到的词**，优先收录。

#### 怎么写

- 每条 **一名一词一释**；解释用 **领域语言**，说明「是什么 / 不是什么」，避免循环定义。
- **长度：** 通常 1～3 句；不必写百科全书，但要能消除歧义。
- **数量：** 至少 **1 条**；有领域术语的任务建议 **3～10 条**；通用 CLI 无专用术语时可只写 1 条核心实体（如「表达式」）。

#### JSON 映射（约定，非正式 schema）

§2 表格的 **机器可读形态**：写入 `spec.json` → `context.glossary[]`。字段定义见 [`artifact-schemas/prd-spec.md`](../artifact-schemas/prd-spec.md#context)（Pydantic 未单独建模前经 `context` 透传；渲染器可能未实现）。

```json
"context": {
  "interface": "cli",
  "storage": "none",
  "glossary": [
    {
      "term": "表达式",
      "definition": "用户输入的算式字符串，由数字、运算符、括号组成"
    },
    {
      "term": "CLI 使用者",
      "definition": "在命令行输入表达式并查看结果的人"
    }
  ]
}
```

- Run `spec.md` §2 渲染自该数组（表格列 **名词 | 解释** ↔ `term` | `definition`）。
- 下游 Agent **只读 JSON** 时，Persona / 领域词以 `context.glossary` 为准，与 §6 `as_a` 等保持一致。

**字段命名（约定项）：**

| JSON 路径 / 字段 | 含义 | 命名说明 |
|------------------|------|----------|
| `context.glossary` | 术语条目数组 | 放在 `context` 下，与 interface、storage 等领域元数据同类；未单独设顶层 `glossary`，避免再增顶层字段 |
| `term` | 名词 | 不用 `name`（易与实体名/id 混淆） |
| `definition` | 解释 | 不用 `description`（与 REQ、AC 的 `description` 区分） |

条目内 **仅** `term` + `definition` 两个字段；同义词、缩写另起一条或写在 `definition` 中一句带过。

#### 与 §3 背景、§5 功能的区别


| 章节        | 回答                                    |
| --------- | ------------------------------------- |
| **§2 术语** | 名词 **是什么意思**                          |
| **§3 背景** | 运行 / 交付 **环境形态**（interface、storage 等） |
| **§5 功能** | 交付 **哪些能力**                           |


### §3 背景与上下文

说明产品的 **运行 / 交付环境形态**（对应 `spec.json` → `context` 中的领域键）。**正文形式不限**：短段落、bullet 或「键 | 值」表均可；以读者能扫读为准。

**常见领域键（示例，按任务选用）：**


| 键（示例）        | 含义                                             |
| ------------ | ---------------------------------------------- |
| `interface`  | 交互形态：`cli` / `web` / `api` / `batch` 等         |
| `deployment` | 运行形态：`local` / `single_server` / `saas` 等（可选）  |
| `storage`    | 持久化意图：`local_file` / `database` / `none` 等（可选） |
| `audience`   | 目标用户：`single_user` / `team` 等（可选）              |


- 写入 JSON 时，键名须与 [`artifact-schemas/prd-spec.md`](../artifact-schemas/prd-spec.md) 中 `context` 及 Profile.`context_schema`（若有）一致。
- 仅 **1～2 项** 时不必强行制表；**3 项及以上** 或需与 JSON 逐字段对照时，表格式更清晰。
- **与 §9 分工：** §3 写 **产品形态**（interface、storage、audience 等）；§9 写 **运行态假设**（体量档位、并发、一致性模型）。已写在 §3 的键（如 `audience: single_user`）不要在 §9 再展开成同义段落；§9 填对应枚举（如 `user_scale: personal`）即可。

### §4 业务指标（可选）

对应 JSON `success_metrics[]`（id 仍可用 `KPI-*` 前缀）。**本节约业务结果**，不是工程指标（p99、QPS、可用性百分比等留 design / §9 档位说明）。

#### 何时写

- **写：** 有明确 **业务目标或结果度量**（如「用户能完成核心交易」「重启后业务数据不丢」）。
- **不写：** 小工具、内部 CLI、目标已在 §1 概述 + §10 AC 说清时；Run `spec.md` 可 **省略本章** 或写「无单独业务指标」，`success_metrics` 为 `[]`。

#### 写法

正文形式不限（表或 bullet 均可）。若用表，推荐列：`ID` | 指标名称 | 说明 | 目标值 | 验证方式

- id 形如 `KPI-1`。
- **指标名称 / 说明：** 用 **领域语言** 描述业务结果，避免「测试通过」「lint 无报错」——那是 §10 AC。
- **与 §10 AC 分工：** 业务指标写 **做成什么样**；AC 写 **流水线怎么验**。`target` 可引用 `US-*` 或 `AC-*`，勿与 AC 同义重复。
- `target` 须 **业务上可判断**（如「手动走通 US-1、US-2」）；`verifiable_by` 同 AC 枚举。

### §5 功能

表格推荐列：`ID` | 功能名 | 描述 | 优先级 | 关联用户故事

- id 形如 `FEAT-1`。
- **写什么：** **能力 / 模块级**说明（如「四则运算」「括号求值」「本地持久化」）。
- **不要写：** Connextra 用户句式（As a / I want）；那是 §6 用户故事。
- `priority`：`P0` | `P1` | `P2`（P0 = 本次必须交付）。
- **P0 功能** 推荐在 `user_story_ids` 中至少挂 1 个 `US-*`；id 须与 §6 表中 **完全一致**。
- **与 §7 REQ 优先级：** 通常 REQ 的 `priority` **不高于** 其 `feature_id` 所属 FEAT；跨 FEAT 顺序用 REQ `depends_on`，不靠给 REQ 降 P 级表达顺序。

| | 示例 | 评价 |
|---|------|------|
| ✓ | FEAT-1 待办 CRUD（P0） | 能力级 |
| ✗ | FEAT-1 As a 用户 I want… | 用户故事句式 → §6 |

### §6 用户故事

对应 JSON `user_stories[]`。正文可用 **表格三列** 或 **Connextra 整句**（中/英均可），语义须能落入 `as_a` / `want` / `so_that`。

#### 句式（业界 Connextra）

**英文（常见）：**

```text
As a {角色}, I want {可观察行为}, so that {业务价值}.
```

**中文（等价，推荐国内 PRD）：**

```text
作为{角色}，我希望{可观察行为}，以便{业务价值}。
```

`I need …` 与 `I want …` 等价，统一写入 `want`。LLM 可输出整句 Connextra 字符串或结构化三字段（见 schema 解析）。

#### 字段规则

| 列 / 字段 | 规则 |
|-----------|------|
| **As a / `as_a`** | **具体角色 / Persona**（如「CLI 使用者」「门店店长」）。优先使用 §2 术语表中已定义的角色；避免泛称「用户」——若无专用 Persona，可用「CLI 使用者」等 **场景化称呼**。不要用「系统」当角色。 |
| **Want / `want`** | **用户可观察的行为**（做什么、看到什么）。不写实现细节（如「用 JSON 存储」「调用 REST API」）。 |
| **So that / `so_that`** | **动机 / 业务价值**，一句即可。 |

#### 可选：Job Story（复杂场景）

场景驱动时可写：

```text
When {情境}, I want {动机}, so I can {期望结果}.
```

映射：`When …` 并入 `want` 前半或 `so_that` 语境；核心仍须 **可观察、可验收**，且能被 §10 AC 覆盖。

#### INVEST 自检（写完后快速过一遍）

| 字母 | 含义 | 本规范中的要求 |
|------|------|----------------|
| **I** | Independent | 单条 US 可独立理解，少硬依赖其它 US 的前置说明 |
| **N** | Negotiable | 写行为与价值，不写死实现（实现进 §7 REQ） |
| **V** | Valuable | `so_that` 对角色有明确业务价值 |
| **E** | Estimable | `want` 足够具体，Developer 能估工作量 |
| **S** | Small | 一条 US 一个场景；过大则拆成 US-2、US-3 |
| **T** | Testable | 行为可被 §10 AC 或手动场景验证 |

#### id 与数量

- id 形如 `US-1`，全文 **全局唯一**（不与 `FEAT-*` / `REQ-*` 混号）。
- **小任务至少 2 条 US**：主流程 + 边界/持久化/**异常**等之一。

#### 异常 / 边界场景（可选）

产品有 **用户可感知的失败或边界行为** 时，建议在 §6 增加至少 **1 条** 异常向 US（**非必填**；纯 happy-path 且无显著失败路径时可省略）。

| 写什么 | 怎么写 | 示例 |
|--------|--------|------|
| **用户可见的失败结果** | Want 描述 **看到/得到什么**（明确错误提示、友好失败），不写实现 | 输入 `2/0` 时看到「除数不能为零」类提示 |
| **合并同类异常** | 一条 US 可覆盖多类输入错误，不必每种异常各一条 | 「除零或非法表达式时看到明确错误」 |
| **与 REQ 分工** | US = 用户侧；校验/错误码/保护逻辑 → §7 REQ | US-4 除零提示 ↔ REQ-5 除零处理 |

- **不要** 把异常写成实现任务（「捕获 ZeroDivisionError」→ REQ，不是 US）。
- 写了异常 US 时，§10 AC 应能验收（手动场景或自动化测试覆盖）。

#### 好 / 坏示例（「添加待办」）

| | 写法 | 评价 |
|---|------|------|
| ✓ | 作为 **CLI 使用者**，我希望 **添加一条待办并能在列表中看到**，以便 **记录任务** | 中文 Connextra；角色具体；行为可见 |
| ✓ | As a **CLI user**, I want **to add a todo and see it in the list**, so that **I can capture tasks** | 英文等价 |
| ✗ | As a 用户, I want **实现 add 子命令**, so that … | Want 是实现 → §7 REQ |
| ✗ | As a **系统**, I want 写入 JSON, so that … | 角色错误 + 实现细节 |
| ✓ | 作为 **CLI 使用者**，输入 **`2/0` 时我希望看到明确错误提示**，以便知道算式无效 | 异常场景 US（可选） |
| ✗ | As a 用户, I want **抛出 ZeroDivisionError**, so that … | 异常实现 → §7 REQ |

#### 与 §5 / §7 / §10 的边界

- **US** → 谁、怎么用、为何；**FEAT** → 有什么能力；**REQ** → 可排期实现细项；**AC** → 流水线如何验收。
- 每条 P0 `FEAT-*` 至少对应 1 条 `US-*`（`features[].user_story_ids` 或叙事可追溯）。
- 每条 US 的 `want` 应能被 **§10 验收标准** 或 KPI（若有 §4）覆盖到。

### §7 需求池

可排期交付细项（JSON `requirement_pool[]`）。表格推荐列：

**`ID` | 描述 | 优先级 | 关联功能 | 前置（可选）**

#### 优先级（必填）

每条 REQ **必须** 有 `priority`：`P0` | `P1` | `P2`。

| 级别 | 含义 |
|------|------|
| **P0** | 本次必须交付；缺则 MVP 不成立 |
| **P1** | 重要但可紧随 MVP |
| **P2** | 可延后 |

**优先级 ≠ 开发顺序。** 多个 P0 之间仍可能有「必须先做 A 才能做 B」——用 **前置** 表达，不要靠 P1/P2 硬排同批 P0 的顺序。

#### 前置 / 依赖（可选，有则写）

当 **交付项之间存在先后**（尤其跨 FEAT）时，在 **前置** 列或 JSON `depends_on` 中写明依赖的 `REQ-*` id。

| 层次 | 写什么 | 示例 |
|------|--------|------|
| **§7 REQ** | **交付级** 前置（先有什么能力/存储，再做何功能） | REQ-2 依赖 REQ-1 |
| **design `dev_tasks`** | **实现级** 模块/文件/任务拓扑 | `depends_on: ["T1"]`（见 [design-spec.md](./design-spec.md)） |

- PRD **不写** 完整模块依赖图；Architect 在 design 阶段细化。
- 无明确前置时，前置列留空或 `—`；不要为每条 REQ 编造依赖。

**JSON 映射（约定）：**

```json
{
  "id": "REQ-2",
  "description": "实现 add/list/done 子命令与参数校验",
  "priority": "P0",
  "feature_id": "FEAT-1",
  "depends_on": ["REQ-1"]
}
```

`depends_on` 为 **可选** 约定字段（见 [`artifact-schemas/prd-spec.md`](../artifact-schemas/prd-spec.md#requirementitem)；`RequirementItem` 在 Pydantic 中尚未声明前可只在 MD「前置」列体现）。命名与 design `dev_tasks[].depends_on` 一致，值为 **`REQ-*` id 字符串数组**。

#### 写什么

- **可排期、可优先级的交付细项**，可略 **技术 / 实现向**，例如：
  - CLI 子命令与参数校验
  - 存储格式、文件路径约定
  - 错误码、边界条件、幂等要求
- 推荐 `feature_id` 指向 `FEAT-*`；REQ 的 `priority` 与所属 FEAT 对齐（见 §5）。
- **小任务：** 仅 1 条 REQ 亦可（如单一脚本）；多条 US 共享同一 REQ 时，前置依赖写清即可。

#### 异常 / 边界场景（可选）

§6 有异常向 US 时，§7 宜有 **对应 REQ**（**非必填**；异常仅由 §10 自动化测试覆盖、且无单独交付项时可合并进一条 REQ）。

| 写什么 | 示例 |
|--------|------|
| 输入校验、错误提示、除零保护、幂等/重试 | REQ：除零与非法表达式错误提示 |
| 与异常 US 可追溯 | US-4 除零提示 ↔ REQ-5 除零处理 |
| 合并实现 | 一条 REQ 可覆盖「解析错误 + 除零 + 溢出」等多类异常 |

- **不要** 把异常 US 的 `want` 原样抄进 REQ；REQ 写 **实现层**（校验规则、错误码、返回形态）。
- 无异常 US 时，仍可在 REQ 中写通用「错误处理」（如 CLI 参数校验），不必强行配 US-4。

#### 不要写什么

- **不要** 与 `features[].description` **逐字相同**（`SPEC-107` warn）。
- **不要** 把 `user_stories[].want` **原样复制**；若 US 已写「添加待办」，REQ 应写「实现 `add` 子命令与参数校验」这类 **实现层** 条目。
- **不要** 用 Connextra 句式写 REQ。
- **不要** 把 design 级任务清单（文件路径、类名）塞进 REQ。

#### 与 US 对照（Todo 示例）

| 用户故事（§6） | 需求池（§7） | 前置 |
|----------------|-------------|------|
| US-1：添加待办 | REQ-2：实现 `add` 子命令与参数校验（P0） | REQ-1 |
| US-2：重启后仍能看到列表 | REQ-1：todos 持久化到单 JSON 文件（P0） | — |

持久化（REQ-1）为先，CLI 子命令（REQ-2）依赖存储层就绪。


### §8 范围

- **本次包含（scope_in）**：交付 **边界** 清单（如「本地 CLI」「含自动化测试」）。**不要** 逐条复述 §5 功能表；**不要** 与 §3 `context` 键值重复（如 audience 已写 `single_user`，scope 不必再写「单用户」）。
- **明确不做（scope_out）**：产品边界（如「不做 Web UI」）。无则 Run MD 写「无」或列表为空，JSON `scope_out: []`。
- 与 `constraints[]` 区分：scope = 本次 **不做**；constraints = **不可违反** 的规则。

### §9 稳定性、性能与数据一致性

本节对应 JSON `operational_profile` 与 `consistency_profile`（非功能 / 运行态 **基线假设**）。

> **PM 阶段写法（重要）：** 只写 **档位枚举 + 是/否 + 简短文字说明**（如「本地 CLI、无 SLA」）。**不要**写具体数值（p99、QPS、RPO/RTO 秒数等）；量化归属 [design-spec.md](./design-spec.md)。  
> **小任务可极简：** 一段总述 + 9.1/9.2 各一个小表即可（见完整示例）。**Run MD 表内须能对应 JSON 枚举**（人读可写中文说明，但 `delivery` 等不能写「不适用」字面量进 JSON）。

Architect 据此选型：单线程 vs 异步、缓存、连接池、事务边界、幂等等。

#### 9.1 稳定性与性能（`operational_profile`）

**Run `spec.md` 推荐：** 一段说明 + 简表（无数字列）

| 项 | 说明（文字） |
|----|----------------|
| 用户体量 | 选 `user_scale` 枚举 + 一句场景（勿重复 §3 `audience` 全文） |
| 高并发 | 是 / 否 + 一句原因 |
| 性能预期 | 选 `performance.tier` + 文字说明 |

JSON 映射（PM 阶段）：

| 字段 | PM 填什么 | PM 阶段 **不填** |
|------|-----------|------------------|
| `user_scale` | 枚举 | — |
| `user_scale_notes` | 定性场景描述 | 具体 DAU / 并发数 |
| `high_concurrency` | boolean | — |
| `performance.tier` | 枚举 | — |
| `performance.notes` | **主要** 性能文字说明 | — |
| `performance.latency` / `throughput` / `availability` | — | 留给 design |

**`user_scale` 枚举（含义）：**

| 值 | 含义 | 文字示例 |
|----|------|----------|
| `personal` | 单用户、本地/CLI | Todo CLI、脚本 |
| `team` | 小团队内部 | 内部工具 |
| `multi_tenant` | 多租户或较大规模 | SaaS 单区域 |
| `internet` | 面向公网大规模 | 消费级产品 |

**`performance.tier` 枚举：**

| 值 | 含义 |
|----|------|
| `best_effort` | 功能优先，无 SLA（CLI 默认） |
| `interactive` | 人可感知的交互响应 |
| `low_latency` | 低延迟场景 |
| `custom` | 非标准；须在 `performance.notes` 文字说明，数值进 design |

#### 9.2 数据一致性（`consistency_profile`）

**Run `spec.md` 推荐：** 简表（**JSON 枚举值** + 文字说明列；勿把「不适用」当作 JSON 字段值）

| 项 | 说明（文字） |
|----|----------------|
| 一致性模型 | 选 `consistency_model` + 一句 |
| 投递语义 | 选 `delivery` 枚举 + 一句（无消息/队列时用 `best_effort` 并说明） |
| 多写者 | 是 / 否 → `multi_writer` |
| 须幂等 | 是 / 否 → `idempotency_required`（见下表，勿与「确定性」混淆） |
| 冲突策略 | 选 `conflict_strategy` 枚举（无冲突时用 `not_applicable`） |
| 补充说明 | 一致性 / 状态相关定性预期；**不写** RPO/RTO 秒数；**不写** 功能异常（→ §6/§7） |

**幂等 vs 确定性（勿混用）：**

| 场景 | `idempotency_required` | `notes` 写什么 |
|------|------------------------|----------------|
| API / 写操作 / 可能重试的副作用 | 按产品定 `true`/`false` | 重试安全、重复提交等 |
| 纯函数求值、无状态 CLI | **`false`** | 可选写「确定性：相同输入相同输出」——**不是**分布式幂等 |
| 本地单文件、单写者 | 通常 `false` | 写盘语义见 `delivery` / `consistency_model` |

**无持久化 / 纯 CLI 默认填法（§3 `storage: none` 等）：**

| JSON 字段 | 推荐值 | Run MD 说明示例 |
|-----------|--------|-----------------|
| `consistency_model` | `local_only` | 无跨请求/跨进程共享状态 |
| `delivery` | `best_effort` | 无消息队列；纯本地计算/写盘 |
| `multi_writer` | `false` | 无并发写同一数据源 |
| `idempotency_required` | `false` | 无重试型副作用；确定性见 notes |
| `conflict_strategy` | `not_applicable` | 无多写者冲突 |
| `notes` | 可选 | 仅一致性/状态假设；**不要**写除零、参数校验等功能需求 |

```json
"consistency_profile": {
  "consistency_model": "local_only",
  "delivery": "best_effort",
  "multi_writer": false,
  "idempotency_required": false,
  "conflict_strategy": "not_applicable",
  "notes": "无持久化；单次求值无跨请求状态"
}
```

JSON 映射（PM 阶段）：

| 字段 | PM 填什么 | PM 阶段 **不填** |
|------|-----------|------------------|
| `consistency_model` | 枚举 | — |
| `delivery` | 枚举 | — |
| `multi_writer` / `idempotency_required` | boolean | — |
| `conflict_strategy` | 枚举（多写者时必填） | — |
| `notes` | **主要** 一致性文字说明 | — |
| `staleness_bound` / `recovery` | — | 留给 design |

`consistency_model` / `delivery` / `conflict_strategy` 枚举见 [artifact-schemas/prd-spec.md](../artifact-schemas/prd-spec.md)。

**与其它章节：** §3 写形态、§9 写运行态假设（勿重复叙述）；§4（可选）写业务结果；§6/§7 写功能与异常；§11 写禁止项；具体数值见 Run `design.md`。


### §10 验收标准

表格：`ID` | 描述 | 验证方式（`verifiable_by`）

- id 形如 `AC-1`。
- **写什么：** 流水线 **可判定是否可交付** 的检查项。描述宜 **可执行**；工具链由 Profile 决定（可写「自动化测试套件通过」，不必写 pytest/cargo）。
- **与 §4 分工（若有 §4）：** AC = 门禁；业务指标 = 业务目标。无 §4 时，仅 AC 即可。
- **与 §6 追溯：** 每条 P0 US 的行为应至少被 1 条 AC（或 §4 KPI 的 manual 项）覆盖；**若 §6 含异常 US**，AC 须覆盖对应场景（可并入 manual 项或依赖 `automated_test` 测异常用例）。
- 至少一条 `automated_test`（`SPEC-201`，warn）。建议 P0 FEAT 在 AC 或（若有）§4 中有覆盖（`SPEC-106`，warn）。

**组合示例（Todo）：**

| ID | 描述 | 验证方式 |
|----|------|----------|
| AC-1 | 自动化测试套件全部通过 | `automated_test` |
| AC-2 | 手动走通 US-1、US-2 主流程 | `manual` |

### §11 约束

逐条列出 `constraints[]`（硬规则，非「本次不做」——后者见 §8）。

- 无额外约束时：Run MD 写 **「无额外约束」**，JSON `constraints: []`。
- 常见示例：`no_secrets_in_repo`、`no_pii_in_logs`、领域相关的 `no_mainnet_rpc_in_tests`（链上 Profile）等。

### §12 待澄清项（推荐）

借鉴 MetaGPT `Anything UNCLEAR`；列出 **尚待产品确认** 的问题（范围、角色、边界、合规等）。无则写「无」。

示例：「是否支持待办优先级字段？」「删除待办是物理删除还是标记完成？」

---

## 完整示例

```markdown

# CLI 四则运算计算器



## 概述



命令行输入数学表达式，支持加减乘除、括号与小数，输出求值结果。



- **Profile：** default

- **Revision：** 1



## 术语与领域概念



| 名词 | 解释 |

|------|------|

| 表达式 | 用户输入的算式字符串，由数字、运算符、括号组成 |

| 运算符 | 本产品中指 `+`、`-`、`*`、`/` 四则运算符号 |

| 小数 | 含小数点的数值字面量（如 `3.14`、`.5`） |

| CLI 使用者 | 在命令行输入表达式并查看结果的人（本示例唯一角色） |



## 背景与上下文



| 键 | 值 |

|----|-----|

| interface | cli |

| storage | none |

| audience | single_user |



## 业务指标



| ID | 指标名称 | 说明 | 目标值 | 验证方式 |

|----|----------|------|--------|----------|

| KPI-1 | 典型算式正确 | 四则、括号、小数组合表达式结果正确 | 见 AC-2 | manual |



## 功能



| ID | 功能名 | 描述 | 优先级 | 关联用户故事 |

|----|--------|------|--------|--------------|

| FEAT-1 | 四则运算 | 支持 `+`、`-`、`*`、`/` 及运算符优先级 | P0 | US-1, US-4 |

| FEAT-2 | 括号求值 | 支持 `()` 改变运算顺序，含嵌套括号 | P0 | US-2 |

| FEAT-3 | 小数运算 | 支持小数输入与输出；除法产生小数结果 | P0 | US-3 |



## 用户故事



| ID | As a | Want | So that |

|----|------|------|---------|

| US-1 | CLI 使用者 | 输入 `1+2*3` 等四则表达式并得到正确结果 | 快速完成基础计算 |

| US-2 | CLI 使用者 | 输入 `(1+2)*3` 等含括号的表达式并得到正确结果 | 计算需改变优先级的算式 |

| US-3 | CLI 使用者 | 输入 `3.5/2` 等含小数的表达式并得到正确结果 | 处理非整数计算 |

| US-4 | CLI 使用者 | 输入 `2/0` 或非法表达式时看到明确错误提示 | 知道输入有误而非程序崩溃 |



## 需求池



| ID | 描述 | 优先级 | 关联功能 | 前置 |

|----|------|--------|----------|------|

| REQ-1 | 表达式词法/语法解析（数字、运算符、括号、小数） | P0 | FEAT-1 | — |

| REQ-2 | 求值引擎：四则运算与运算符优先级 | P0 | FEAT-1 | REQ-1 |

| REQ-3 | 括号嵌套求值 | P0 | FEAT-2 | REQ-2 |

| REQ-4 | 小数解析与除法小数结果处理 | P0 | FEAT-3 | REQ-2 |

| REQ-5 | 除零与非法表达式错误提示 | P0 | FEAT-1 | REQ-2 |



## 范围



**本次包含（scope_in）**



- 本地 CLI 表达式求值（单次或 REPL）

- 含自动化测试与基本错误处理



**明确不做（scope_out）**



- Web / GUI

- 科学函数（sin、sqrt 等）、取模、幂运算

- 计算历史持久化



## 稳定性、性能与数据一致性

本地 CLI、无状态求值：无持久化、无高并发。具体数值指标见设计文档。

### 稳定性与性能

| 项 | 说明 |
|----|------|
| 用户体量 | `personal` — 本地 CLI（§3 `audience: single_user`） |
| 高并发 | 否 — 无并行请求场景 |
| 性能预期 | `best_effort` — 交互可感知即可，不设 SLA |

### 数据一致性

| 项 | 说明 |
|----|------|
| 一致性模型 | `local_only` — 无跨请求状态，无持久化 |
| 投递语义 | `best_effort` — 无消息/队列，纯本地求值 |
| 多写者 | 否 |
| 须幂等 | 否 — 无重试型副作用；相同表达式结果确定 |
| 冲突策略 | `not_applicable` |
| 补充说明 | 无持久化；单次求值不共享进程外状态 |



## 验收标准



| ID | 描述 | 验证方式 |

|----|------|----------|

| AC-1 | 自动化测试套件全部通过 | automated_test |

| AC-2 | 手动走通 US-1～US-3 典型表达式，且 US-4（如 `2/0`）有明确错误提示 | manual |



## 约束



- no_secrets_in_repo



## 待澄清项



除法结果默认保留几位小数？（若未指定，实现阶段按 Profile 约定）



---

task_profile: default

revision: 1

parent_task_id: —

```

---

## 与 MetaGPT PRD 对照

| MetaGPT（WritePRD） | 本格式规范（prd-spec） |

|---------------------|--------|

| Product Goals | §1 `summary` + 可选 §4 `success_metrics`（业务指标） |

| User Stories | §6 |

| Requirement Pool | §7 |

| Requirement Analysis | 并入 §5 功能描述或 §7 |

| Competitive Analysis / UI draft | **非 MVP**；可选附录或 §12 待澄清 |

| Anything UNCLEAR | §12 待澄清项 |

| Programming Language | §1 `profile`（运行时绑定；见 artifact-schemas） |

---

## 实现提示

- 渲染器：`multi_agent_code_factory/renderers/spec_md.py`（P0）；当前未必覆盖 §2 `glossary`、§7 `depends_on`、§4 可选等业务约定。
- HITL：`spec_hitl` 审批人阅读 Run `spec.md` + `spec_validation.json`。
- 禁止：下游 Agent 仅读 `spec.md` 而不读 `spec.json`。
- **约定字段：** `context.glossary[]`、`requirement_pool[].depends_on` 见 [`artifact-schemas/prd-spec.md`](../artifact-schemas/prd-spec.md)；Pydantic / 校验器 / 渲染器未完全跟进前，可只在 MD 或 JSON 透传体现。

