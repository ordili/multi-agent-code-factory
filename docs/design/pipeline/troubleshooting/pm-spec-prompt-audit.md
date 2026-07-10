# PM SpecArtifact — Prompt ↔ Schema 审计表（草稿）

> **状态：** 草稿 · 2026-07-10  
> **目的：** 识别与 `success_metrics` 同类的「机器契约严、prompt 松」风险，指导后续 prompt / Example 补强。  
> **范围：** PM 角色 · `SpecArtifact` · `prompted_json` 路径  
> **不修改代码：** 本文仅审计与排期，实现状态以仓库当时为准。

**相关文档：**

- JSON 契约：[artifact-schemas/prd-spec.md](../artifact-schemas/prd-spec.md)
- 人读模板：[artifact-templates/prd-spec.md](../artifact-templates/prd-spec.md)
- 已观测偏差：[architect-llm-schema-alignment.md](./architect-llm-schema-alignment.md) §1 PM
- 调试脚本：`scripts/debug_pm_spec_llm.py`

---

## 1. 同类问题定义

满足以下 **≥2 条** 时，视为与 `success_metrics` **同类型**风险：

| # | 特征 |
|---|------|
| A | Pydantic 对形状 / 枚举有硬要求 |
| B | `pm.txt` 仅点名或缺少 `NOT plain strings` / 枚举全集 / 可选 `[]` |
| C | `__llm_example__` 缺失、与场景不符，或与文字规则矛盾 |
| D | 与邻近字段语义易混（内容放错桶） |
| E | 无 `coerce_spec_payload` 兜底 → 直接 `LlmParseError` |

**根因（摘要）：** 校验守契约；模型按自然语言填空。prompt + Example 未完整传达 schema 与 prd-spec 分工时，结构/语义/枚举三类错误都会出现。

---

## 2. 审计方法（可重复执行）

1. **四问对照**（每个字段）：形状？枚举？可选/空？分工？
2. **Example 覆盖率**：`SpecArtifact.__llm_example__` 是否展示该字段合法形态？
3. **Coerce 盲区**：有 coerce 的字段问题可能被静默吸收，需单独加压测。
4. **实测台账**：`debug_pm_spec_llm.py` + `captures/pm-spec-artifact/`，记录「要求 vs 模型输出」。
5. **多任务压测**：小 CLI、Todo+存储、多 US/FEAT 各跑 3～5 次看稳定性。

---

## 3. 字段审计总表

图例：**形状** / **枚举** / **可选** / **分工** = prompt 四问；**Coerce** = `coerce_spec_payload`；**风险** = 高/中/低；**状态** = 待观察 / 已加强 / 已观测问题。

| 字段 / 组 | Pydantic 要求 | prd-spec 分工 | pm.txt（2026-07 修后） | `__llm_example__` | Coerce | 已知模型错法 | 风险 | 状态 |
|-----------|---------------|---------------|------------------------|-------------------|--------|--------------|------|------|
| `success_metrics` | `SuccessMetric[]`；可 `[]` | §4 业务 KPI；勿写 pytest | 对象结构 + `NOT strings` + `[]` + KPI/AC 分工 | Todo 示例含 KPI 对象（非空） | 无 | 字符串数组 `["pytest…"]` | 低 | **已加强**；计算器实测 `[]` OK |
| `acceptance_criteria` | `{id, description, verifiable_by}[]` | §10 工程门禁 | 对象结构 + trace + `automated_test` | 有 AC-1 + `automated_test` | 无 | 字符串数组；缺 `verifiable_by` | **中** | 已加强；待多任务压测 |
| `user_stories` | `{id, as_a, want, so_that}[]` | §6 用户行为 | `NOT plain strings` | 有 | **有**（字符串→Connextra 解析） | 纯字符串；缺字段 | 低 | 已加强；coerce 掩盖部分问题 |
| `requirement_pool` | `{id, description, priority}[]` | §7 可排期细项 | `NOT nested dict` | 有 | **有**（嵌套 dict→列表） | 嵌套 dict；复制 US 原文 | 低 | 已加强 |
| `features` | `FeatureItem[]`；非空（SPEC-009） | §5 能力级 | 仅「P0 + user_story_ids」 | 有 | 无 | 字符串数组；写成 US 句式 | **中** | **缺口**：无 `NOT plain strings` |
| `operational_profile.user_scale` | `personal` \| `team` \| `multi_tenant` \| `internet` | §9 运行态 | **MUST 枚举** 已写 | `personal` | 默认 `personal`；**非法枚举不过** | `single_user`（与 `context.audience` 混淆） | 中 | **已加强**；live 曾观测 |
| `operational_profile.performance.tier` | `PerformanceTier` 枚举 | §9 | 仅提 `performance.tier` | `best_effort` | 默认 `best_effort` | 自造 tier 名 | 中 | 枚举全集未写 |
| `operational_profile` 整体 | 对象必填 | §9 | 对象字段概括 | 有 | **部分** default | `performance` 写成字符串 | 低 | coerce 可救 tier 字符串 |
| `consistency_profile` | 多字段 + 多枚举 | §9 一致性 | prefer 档位；无全集 | 有（Todo 档） | **有**（字符串→对象；缺省填充） | 自造 enum；缺必填键 | 中 | 枚举全集未写 |
| `context.storage` | 非空（SPEC-017） | §3 / 持久化 | 枚举列表已写 | **缺**（Todo 无 storage） | glossary 部分 | 省略或空字符串 | 中 | Example 缺口 |
| `context.glossary` | `GlossaryEntry[]` | §2 术语 | 对象 `{term, definition}` | **常缺** | term/definition 校验 | 字符串数组 | 中 | 无 `NOT plain strings` |
| `context.audience` 等 | 产品形态键（非 Pydantic 硬枚举） | §3 | 未单独写 | 不定 | 无 | 与 `user_scale` 混用 | 中 | **分工**：`audience=single_user` ≠ `user_scale=personal` |
| `scope_in` / `scope_out` | `string[]` | §8 边界 | 仅点名 | 有 | 无 | 写成单个字符串 | 低 | — |
| `constraints` | `string[]` | §11 | 举例 | 有 | 无 | 写成对象 | 低 | — |
| `title` / `summary` | 非空 string | §1 | 点名 | 有 | 无 | 空 | 低 | — |
| `version` / `profile` / `revision` | 固定/Profile 一致 | 元数据 | `version "1"` | 有 | **有** default | `revision` 缺 | 低 | coerce 兜底 |

---

## 4. 优先级队列（建议下一批）

按 **风险 × prompt 缺口 × 无 coerce** 排序，**暂不实现**，仅作排期：

| 优先级 | 字段 | 理由 | 建议动作（未来） |
|--------|------|------|------------------|
| P1 | `features` | 无 `NOT plain strings`；与 US/REQ 易混 | pm.txt 补对象结构 + 能力级 vs US 分工 |
| P1 | `context.storage` + Example | SPEC-017 硬门禁；`__llm_example__` 常缺 | Example 补 `storage`；小 CLI 示范 `none` |
| P2 | `context.audience` vs `user_scale` | 文档允许 `audience: single_user`，模型误写入 `user_scale` | pm.txt 显式写「勿把 audience 值用于 user_scale」 |
| P2 | `operational_profile.performance.tier` 等枚举 | 仅点名无全集 | pm.txt 或 Example 列枚举字面量 |
| P2 | `consistency_profile` 枚举 | 同上 | 列 `consistency_model` / `delivery` / `conflict_strategy` 合法值 |
| P3 | `acceptance_criteria` | 已写结构；需压测字符串数组是否仍出现 | 多任务 captures；必要时加 `NOT plain strings` |
| P3 | `context.glossary` | 有对象说明无 NOT strings | 补一行 + Example 带 glossary |
| P3 | `__llm_example__` vs 小 CLI | Pipeline Example 非空 KPI，与「宜 `[]`」并存 | 二选一：注释说明 / 第二示例 / 按 profile 切换 |

---

## 5. 两层校验别混

| 层 | 时机 | `success_metrics: []` |
|----|------|-------------------------|
| **Pydantic**（LLM 解析） | `model_validate` | 合法 |
| **spec_validate**（SPEC-*） | PM 产出后 | 合法；SPEC-012 不触发 |

SPEC-102 / SPEC-106 等 **warn** 规则关心追溯，不要求 KPI 非空。

---

## 6. 实测记录（留白）

| 日期 | 任务 | 模型 | 字段 | 模型输出摘要 | Pydantic | 备注 |
|------|------|------|------|--------------|----------|------|
| 2026-07-10 | 计算器 CLI | DeepSeek | `success_metrics` | `[]` | OK | prompt 修后 |
| 2026-07-10 | 计算器 CLI | DeepSeek | `user_scale` | （见 captures） | 曾失败 `single_user` | 修 pm.txt 前 |
| | | | | | | |

**Captures 路径：** `captures/pm-spec-artifact/`

---

## 7. 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-10 | 初稿：基于 success_metrics 修复后的讨论与仓库现状 |
