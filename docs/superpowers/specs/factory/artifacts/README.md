# Artifacts — 产物规格总索引

> **Run 落盘：** `docs/factory/runs/<task_id>/`  
> **代码实现：** [`multi_agent_code_factory/schemas/`](../../../../../multi_agent_code_factory/schemas/)

## 目录命名说明（schemas / format-to-human 能否看出角色？）

| 子目录 | 命名依据 | 能否直接看出角色？ |
|--------|----------|-------------------|
| **`schemas/`** | 对齐 `multi_agent_code_factory/schemas/*.py` 与 **Run 的 `.json` 文件名** | **部分能**：看 **产物名**（spec、design…），不是 role_id（pm、architect…） |
| **`format-to-human/`** | 与 **Run 人读 basename 同名**（`spec.md`；`flow.mmd` 的规格为 `flow.md`） | **能**：见产物名 → 角色映射表 |

**结论：** 文件夹按 **「规格类型」**（JSON Schema vs 人读模板）分，**不是**按角色分。角色信息在 **产物名 ↔ role_id 映射表**（下表）里查。

### 文件名 → 角色（Run 产物 & 设计 Spec 对照）

| role_id | 文档称呼 | Run 机器文件 | Run 人读文件 | `schemas/` 规格 | `format-to-human/` 模板 |
|---------|----------|--------------|--------------|-----------------|-----------------|
| **`pm`** | PM | `spec.json` | `spec.md` | [schemas/spec.md](./schemas/spec.md) | [format-to-human/spec.md](./format-to-human/spec.md) |
| **`architect`** | Architect | `design.json` | `design.md`、`flow.mmd` | [schemas/design.md](./schemas/design.md) | [format-to-human/design.md](./format-to-human/design.md)、[format-to-human/flow.md](./format-to-human/flow.md) |
| **`developer`** | Developer | `dev_manifest.json` | — | [schemas/dev-manifest.md](./schemas/dev-manifest.md) | — |
| **`qa`** | QA | `test_report.json` | — | [schemas/test-report.md](./schemas/test-report.md) | — |
| **`reviewer`** | Reviewer | `review.json` | `review.md` | [schemas/review.md](./schemas/review.md) | [format-to-human/review.md](./format-to-human/review.md) |
| — | **validate 节点** | `spec_validation.json`、`design_validation.json` | — | [schemas/validation-report.md](./schemas/validation-report.md) | — |
| — | **HITL 节点** | `hitl.json` | — | [schemas/hitl.md](./schemas/hitl.md) | — |
| — | **引擎** | `run_meta.json` | — | [schemas/run-meta.md](./schemas/run-meta.md) | — |

**从文件名猜角色的口诀：**

- `spec*` → **pm**
- `design*` / `flow*` → **architect**（`flow.mmd` 无 `design` 前缀，需记住）
- `dev_manifest` / `dev-manifest` → **developer**
- `test_report` / `test-report` → **qa**
- `review*` → **reviewer**
- `*_validation` / `validation-report` → **程序节点**，非 Agent
- `hitl` → **人工 interrupt 节点**
- `run_meta` → **引擎**

**当前不够直观之处：** `spec` 不等于 `pm`；`dev-manifest` 用缩写 dev 而非 `developer`。`format-to-human/` 与 `schemas/` 下可有同名 `spec.md`，靠 **目录** 区分 JSON 规格 vs 人读模板。

## 三层分工（格式约束放哪？）

| 层级 | 目录 | 回答的问题 |
|------|------|------------|
| **机器可读** | [`schemas/`](./schemas/README.md) | `spec.json` 有哪些字段？与 `multi_agent_code_factory/schemas/*.py` 一一对应 |
| **给人看** | [`format-to-human/`](./format-to-human/README.md) | `spec.md` / `design.md` / `flow.mmd` 有哪些固定章节？ |
| **程序校验** | [../quality-gates.md](../quality-gates.md) | `spec_validate` / `design_validate` 的 rule_id 与 Profile 配置 |

**结论：** `artifacts/` 是 **产物规格** 根目录，但 **JSON 与人读格式分开放**——不要全堆在 `artifacts/*.md` 根下混用 `-artifact` / `-report` 等后缀。

## Run 对照表

| Schema | 机器路径 | 人读 / 图 | 生产者 | 细目 |
|--------|----------|-----------|--------|------|
| `SpecArtifact` | `spec.json` | [spec.md](./format-to-human/spec.md) | `pm` | [schemas/spec.md](./schemas/spec.md) |
| `DesignArtifact` | `design.json` | [design.md](./format-to-human/design.md)、[flow.mmd](./format-to-human/flow.md) | `architect` | [schemas/design.md](./schemas/design.md) |
| `DevManifest` | `dev_manifest.json` | — | `developer` | [schemas/dev-manifest.md](./schemas/dev-manifest.md) |
| `TestReport` | `test_report.json` | — | `qa` | [schemas/test-report.md](./schemas/test-report.md) |
| `ReviewReport` | `review.json` | [review.md](./format-to-human/review.md) | `reviewer` | [schemas/review.md](./schemas/review.md) |
| `ValidationReport` | `spec_validation.json` / `design_validation.json` | — | validate 节点 | [schemas/validation-report.md](./schemas/validation-report.md) |
| `HitlDecision` | `hitl.json` | — | hitl 节点 | [schemas/hitl.md](./schemas/hitl.md) |
| `RunMeta` | `run_meta.json` | — | 引擎 | [schemas/run-meta.md](./schemas/run-meta.md) |

**角色命名：** [§3.1](../../multi-agent-pipeline-design.md#31-角色命名约定)

## 依赖顺序

```text
pm → spec.json (+ spec.md)
architect → design.json (+ design.md, flow.mmd)
developer → dev_manifest.json + code_root
qa → test_report.json
reviewer → review.json (+ review.md)
```

## 可选优化（若要以路径识别角色）

不改 Run 落盘文件名（仍 `spec.json`），仅调整 **设计 Spec 目录**（当前已采用 basename 对齐，一般不必再拆）：

```text
artifacts/format-to-human/
├── pm/spec.md
├── architect/design.md
├── architect/flow.md
└── reviewer/review.md
```

`schemas/` 建议 **保持产物名**（与 `schemas/*.py` 一致），不按角色分子目录。
