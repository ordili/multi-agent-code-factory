# review.md — Reviewer 人读摘要格式

> **机器真源：** [`../artifact-schemas/review.md`](../artifact-schemas/review.md)（`ReviewReport` / `review.json`）  
> **Run 路径：** `docs/runs/<task_id>/review.md`

---

## 固定章节

| § | 标题 | 对应 JSON |
|---|------|-----------|
| — | `# 审查结论` | `summary`、`approved` |
| 1 | `## 路由` | `next_stage` |
| 2 | `## 验收覆盖` | `acceptance_coverage[]` |
| 3 | `## 发现项` | `findings[]` |

---

## 示例（节选）

```markdown
# 审查结论

**通过：** 是  
**摘要：** AC 全部满足，无 blocking 发现。

## 路由

下一节点：`deploy`

## 验收覆盖

| AC | 满足 | 说明 |
|----|------|------|
| AC-1 | ✓ | test_report.passed |

## 发现项

无
```

路由与 `findings[].blocking` 以 **`review.json` 为准**；MD 仅供 HITL / 人工速读。
