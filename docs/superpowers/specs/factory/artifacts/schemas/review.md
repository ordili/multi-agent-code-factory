# ReviewReport — Reviewer 输出

> **实现：** `multi_agent_code_factory/schemas/review.py`  
> **Run 路径：** `review.json`（+ `review.md`）  
> **人读格式：** [format-to-human/review.md](../format-to-human/review.md)  
> **产生方式：** LLM Structured Output（`role_id=reviewer`）

## 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `version` | `"1"` | |
| `approved` | boolean | 是否通过审查 |
| `next_stage` | enum | `developer` \| `architect` \| `pm` \| `deploy` — **图路由** |
| `summary` | string | 结论摘要 |
| `findings` | Finding[] | 发现项 |
| `acceptance_coverage` | object[] | `{ "id", "met", "note" }` 对齐 PM 的 AC |

### Finding

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 如 `F-1` |
| `severity` | enum | `critical` \| `major` \| `minor` |
| `category` | enum | `security` \| `performance` \| `correctness` \| `style` |
| `file` | string? | 相关文件 |
| `message` | string | 描述 |
| `blocking` | boolean | 是否阻断 |
| `routing` | enum? | `developer_fix` \| `architect_redesign` \| `pm_scope_change` — **人读/自检**；图路由只看报告级 `next_stage` |

## 通过条件

`approved=true` 且 `next_stage=deploy`，且无 `blocking=true` 的 `critical` 发现项。`Finding.routing` **不参与** `route_after_review`。

## 路由（route_after_review）

`route_after_review` **仅看** `next_stage`；`Finding.routing` 不参与。进入 `deploy` 路径须 **`approved=true`**；若 `next_stage=deploy` 但 `approved=false`（LLM 矛盾输出），按实现问题回 Developer（见主线 §4.3 伪代码）。

| 条件 | `next_stage` |
|------|----------------|
| 通过 | `deploy` |
| 实现/测试可修 | `developer` |
| 设计/接口问题 | `architect` |
| 需求/验收矛盾 | `pm` |

## 示例

```json
{
  "version": "1",
  "approved": true,
  "next_stage": "deploy",
  "summary": "AC 全部满足，无 blocking 发现",
  "findings": [],
  "acceptance_coverage": [
    { "id": "AC-1", "met": true, "note": "test_report.passed" }
  ]
}
```
