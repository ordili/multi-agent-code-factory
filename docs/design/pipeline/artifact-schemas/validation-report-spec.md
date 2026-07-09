# validation-report-spec.md — ValidationReport（校验 JSON 契约）

> **实现：** `multi_agent_code_factory/schemas/validation_report.py`  
> **产生方式：** **程序规则**（`spec_validate` / `design_validate`），非 LLM  
> **Run 路径：** `spec_validation.json` | `design_validation.json`

## 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `version` | `"1"` | |
| `target` | enum | `spec` \| `design` — 校验对象 |
| `passed` | boolean | 无阻断级 violation |
| `error_count` | integer | |
| `warn_count` | integer | |
| `violations` | Violation[] | 规则命中列表 |
| `require_hitl` | boolean | 规则推导出须 `design_hitl` 等 |
| `validated_at` | string? | ISO8601 |

### Violation

| 字段 | 类型 | 说明 |
|------|------|------|
| `rule_id` | string | 如 `SPEC-001`、`DES-101` |
| `severity` | enum | `error` \| `warn` \| `info` |
| `message` | string | 人类可读 |
| `path` | string? | JSON 指针 |
| `field` | string? | 相关字段名 |

## 示例（design_validate 失败）

```json
{
  "version": "1",
  "target": "design",
  "passed": false,
  "error_count": 1,
  "warn_count": 0,
  "require_hitl": false,
  "violations": [
    {
      "rule_id": "DES-005",
      "severity": "error",
      "message": "dev_tasks 依赖环: T1 → T2 → T1",
      "path": "/dev_tasks"
    }
  ]
}
```

`rule_id` 格式为 `SPEC-*` 或 `DES-*`；各规则语义与触发条件在校验规则文档中定义，**不在此重复**。
