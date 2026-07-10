# Python 代码规范

## 依赖上游文档（只读）

审查 / 修订本文时 **以本表及正文为准**；语言无关原则见 [dev-principles-spec.md](./artifact-templates/dev-principles-spec.md)（下游）。


| 分类       | 上游文档                                                                          | 定位                |
| -------- | ----------------------------------------------------------------------------- | ----------------- |
| **总设计** | [multi-agent-pipeline-design.md](../multi-agent-pipeline-design.md) | 系统的总体设计书 |
| **工具配置** | [pyproject.toml](../../../pyproject.toml)                                     | Ruff / mypy / pytest 权威配置 |


---

> **适用范围：** `language: python` 的 Profile（V1 主要为 `python`）  
> **通用工程原则：** [artifact-templates/dev-principles-spec.md](./artifact-templates/dev-principles-spec.md)（README、SRP 等；Developer 必遵）  
> **工具配置以：** 仓库根 [`pyproject.toml`](../../../pyproject.toml) 中 `[tool.ruff]`、`[tool.mypy]`、`[tool.pytest]` **为准**

---

## 1. 参考标准

本规范 **不另起标准**，在下列公开标准上取交集，冲突时以 **`pyproject.toml` 工具配置** 为准。

| 标准 | 内容 | 本项目用法 |
|------|------|------------|
| **[PEP 8](https://peps.python.org/pep-0008/)** | 代码风格 | **基线**；由 Ruff lint 执行 |
| **[PEP 257](https://peps.python.org/pep-0257/)** | docstring | 公开 API 必填 |
| **[PEP 484 / 526](https://peps.python.org/pep-0484/)** | 类型注解 | 公开 API 必填；引擎 **mypy strict** |
| **[PEP 621](https://peps.python.org/pep-0621/)** | 项目元数据 | 根目录 `pyproject.toml` |
| **[PEP 440](https://peps.python.org/pep-0440/)** | 版本号 | 发包时遵循 |
| **Ruff format** | 格式化 | [Black](https://black.readthedocs.io/) 兼容风格 |
| **pytest 惯例** | 测试布局 | `tests/`、`test_*.py` |
| **Google Python Style Guide**（子集） | docstring、命名补充 | §4 docstring 采用 **Google 风格** |

**偏离 PEP 8 之处：** 行宽 88、双引号、import 排序等以 `[tool.ruff]` 为准（与 Black 默认一致）。

---

## 2. 两层代码与严格程度

| 代码 | 路径 | 严格程度 |
|------|------|----------|
| **引擎** | 本仓库 `multi_agent_code_factory/` | Ruff + **mypy strict** + pytest；CI 硬门禁 |
| **生成业务代码** | Profile.`code_root`（仓库外） | 同套 Ruff/pytest 命令；mypy **推荐**、MVP 可不阻断 |

Developer / QA 节点通过 Profile.`toolchain.lint_command` 与 `test_command` 校验生成代码，**命令必须与本文一致**。

---

## 3. 语言与工具版本

| 项 | 约定 |
|----|------|
| **Python** | `>=3.11`（`pyproject.toml` `requires-python`） |
| **Lint** | `python -m ruff check .` |
| **Format** | `python -m ruff format --check .` |
| **类型** | `python -m mypy multi_agent_code_factory`（引擎） |
| **测试** | `python -m pytest -q --junitxml=reports/junit.xml` |

**Profile 默认 lint（以 Profile.`toolchain.lint_command` 为准）：**

```bash
python -m ruff check . && python -m ruff format --check .
```

---

## 4. 风格规则

### 4.1 布局与命名

| 项 | 规则 |
|----|------|
| 缩进 | 4 空格，不用 Tab |
| 行宽 | 88 字符（Ruff/Black 默认） |
| 模块 | 小写 + 下划线：`graph_routing.py` |
| 包 | 小写 + 下划线：`multi_agent_code_factory` |
| 函数 / 变量 | `snake_case` |
| 类 | `PascalCase` |
| 常量 | `UPPER_SNAKE_CASE` |
| 私有 | 单下划线 `_helper`；双下划线仅用于 name mangling |
| import | 标准库 → 第三方 → 本地；每组之间空一行（Ruff isort 自动） |

**单一职责、安全、资源管理：** 见 [dev-principles-spec.md](./artifact-templates/dev-principles-spec.md) §2–§4。

### 4.2 类型注解

- 公开函数、方法、类属性：**必须有**参数与返回值注解（含 `-> None`）。
- 优先 `list[str]`、`dict[str, Any]`、`X | None`（3.10+），避免裸 `Optional` 除非已有代码一致。
- 引擎 Schema：**Pydantic v2** `BaseModel`（见 [artifact-schemas/](./artifact-schemas/README.md)）。
- 禁止无理由的 `Any`；协议类用 `typing.Protocol`。

### 4.3 Docstring（Google 风格）

公开模块、类、函数须有 docstring。示例：

```python
def route_after_test(state: PipelineState, limits: LoopLimits) -> str:
    """Route the graph after QA produces a test report.

    Args:
        state: Current LangGraph state with ``test_report`` populated.
        limits: Loop counters and ``on_limit_exceeded`` policy.

    Returns:
        Next node id: ``reviewer``, ``developer``, ``fail``, or ``escalation_hitl``.
    """
```

- 模块：一句话说明职责即可。
- 不写与签名重复的废话（避免 「Returns: None」 除非有副作用说明）。

### 4.4 错误处理与日志（Python）

| 允许 | 禁止 |
|------|------|
| `logging.getLogger(__name__)` | 裸 `print`（CLI 用户输出除外） |
| 项目异常层次（如 `FactoryError`） | 裸 `except:` / `except Exception:` 吞掉错误 |
| `raise X from e` 链式异常 | 静默 `pass` 忽略失败 |
| `with` / context manager 管理文件、锁、连接 | 手动 open/close 且缺少 finally |

通用原则见 [dev-principles-spec.md](./artifact-templates/dev-principles-spec.md) §3–§4。

### 4.5 依赖

- 优先标准库；仅在 Spec / 验收标准明确要求时添加第三方包。
- 新增依赖须写入 `pyproject.toml` 的 `[project]` / `[project.optional-dependencies]`。

---

## 5. 项目结构

### 5.1 引擎（本仓库）

```text
multi-agent-code-factory/
├── pyproject.toml
├── multi_agent_code_factory/
│   ├── __init__.py
│   ├── graph_routing.py
│   └── ...
└── tests/
    └── test_*.py
```

### 5.2 生成项目（`code_root`）

**必备文件与 README 章节：** [dev-principles-spec.md](./artifact-templates/dev-principles-spec.md) §1、§6。

```text
<code_root>/
├── pyproject.toml          # 推荐；含 [tool.ruff] 与本文对齐
├── README.md
├── src/<package>/          # 推荐 src layout；简单 CLI 可 flat
│   └── __init__.py
└── tests/
    └── test_*.py
```

Architect 在 `file_plan` 中体现上述布局；Developer 新建项目时 **复制 Ruff/pytest 段** 或引用与 `default` Profile 相同的命令。

---

## 6. 测试

| 项 | 规则 |
|----|------|
| 框架 | pytest |
| 目录 | `tests/` |
| 文件 | `test_<module>.py` |
| 函数 | `test_<行为>_<条件>` |
| 隔离 | 默认无网络；外部 API 用 mock/fixture |
| 覆盖率 | 引擎核心模块 **≥ 80%**（`pytest --cov`）；生成项目按 Spec AC |

---

## 7. 流水线集成

### 7.1 Profile toolchain（Python）

与 [`default.yaml`](../../../multi_agent_code_factory/profiles/default.yaml) 对齐：

```yaml
toolchain:
  setup: pip install -e ".[dev]"
  test_command: python -m pytest -q --junitxml=reports/junit.xml
  lint_command: python -m ruff check . && python -m ruff format --check .
  test_dir_glob: "tests/**"
```

QA 节点跑 `test_command`；Developer / `linter` Tool 跑 `lint_command`。**合并代码前两者均须通过。**

### 7.2 Developer prompt 注入摘要

引擎在 **Developer** 节点组装 system prompt 时依次注入：

1. ``profiles/_shared/prompts/dev-principles-snippet.txt``（跨语言，见 [dev-principles-spec.md](./artifact-templates/dev-principles-spec.md)）
2. ``profiles/<language>/prompts/{language}-style-snippet.txt``（本文 Python 细则）

PM / Architect 等产出 JSON 或设计文档的角色 **不注入** 上述摘要。

---

## 8. 本地与 CI 命令

```bash
# 安装
pip install -e ".[dev]"

# 与 QA / linter Tool 一致（Windows 可用 python -m）
python -m ruff check .
python -m ruff format --check .
python -m pytest -q --junitxml=reports/junit.xml
python -m mypy multi_agent_code_factory

# 自动格式化
ruff format .
```

---

## 9. 变更流程

1. 改规则 → 先改 **`pyproject.toml`** `[tool.ruff]` / `[tool.mypy]`。
2. 同步 **`profiles/*.yaml`** 的 `lint_command`（若命令变化）。
3. 更新本文 §3、§7 与 `python-style-snippet.txt`。
4. 其他语言规范另文（Go/Rust/Java 不在本文范围）。

---

## 10. 附录：Ruff 规则集说明

`pyproject.toml` 默认启用：

| 前缀 | 来源 | 说明 |
|------|------|------|
| `E`, `W` | pycodestyle | PEP 8 |
| `F` | Pyflakes | 未使用变量、未定义名等 |
| `I` | isort | import 排序 |
| `UP` | pyupgrade | 现代 Python 语法 |
| `B` | flake8-bugbear | 常见逻辑错误 |
| `SIM` | flake8-simplify | 可简化写法 |
| `RUF` | Ruff 自有 | Ruff 特定规则 |

完整列表：[Ruff rules](https://docs.astral.sh/ruff/rules/)。
