# arb-core — 套利运行时设计

> **依据：** [00-master-overview.md](./00-master-overview.md) — 多 Agent 生成可 PROD 上线的 DEX-DEX 套利代码  
> **代码位置：** Profile `arb` 的 `code_root`（默认 `../arb-robot/`，**不在 `multi-agent-code-factory` 仓库内**）。下文路径均相对该根目录。

---

## 1. 范围

| 包含 | 不包含 |
|------|--------|
| Connector、Strategy、Engine、Risk、Executor、Monitor | LangGraph、多 Agent 编排 |
| 链 / DEX / 池、报价与价差 | Agent Tool、HITL 节点实现 |
| Linux systemd 部署、`.env` | 私钥暴露给研发流水线 |
| 熔断与运行时配置 | |

业务代码由 [arb-factory](./arb-factory-design.md) 生成；合并部署后由本运行时加载执行。

---

## 2. 模块

| 模块 | 文件（规划） | 职责 |
|------|--------------|------|
| **Engine** | `core/engine.py` | 事件循环：拉报价 → 策略 → 风控 → 执行 |
| **Connector** | `connectors/*.py` | DEX / RPC 插件，实现 `IConnector` |
| **Strategy** | `strategies/*.py` | `SpreadMonitor`（P1）、`Arbitrage`（P2+） |
| **Risk** | `core/risk.py` | 滑点、仓位、最大亏损、熔断 |
| **Executor** | `core/executor.py` | 下单、nonce、重试（P2+） |
| **Monitor** | `core/monitor.py` 或策略内嵌 | 日志、指标、告警 |
| **Config** | `core/config.py` | 加载 `.env`、`config.yaml` |

**要求：** 确定性、可单测、不 import LLM SDK。

### 2.1 接口（P0 优先）

`core/interfaces.py` 定义：

- `IConnector` — `get_quote(pair, amount_in) -> Quote`
- `IStrategy` — `on_tick(quotes) -> Signal`
- `IRisk` — `approve(signal) -> bool`
- `IExecutor` — `execute(signal) -> Result`

---

## 3. 链、DEX、交易对

| 项 | 决定 |
|----|------|
| 类型 | DEX ↔ DEX，同链 |
| 链 | Arbitrum One（`chain_id=42161`） |
| DEX-A | Uniswap V3 → `connectors/uniswap_v3_arbitrum.py` |
| DEX-B | Camelot → `connectors/camelot_arbitrum.py` |
| MVP 交易对 | `WETH/USDC`（P0 确认 0.05% 或 0.3% 池地址） |

**SpreadMonitor 逻辑：** 两 DEX 同交易对报价 → 算价差（bps）→ 超 `ARB_SPREAD_THRESHOLD_BPS` 则告警（P1 不下单）。

**待定（实现前写入本节）：** Quoter 调用方式、`amount_in`、毛价差 vs 扣 Gas/手续费净价差。

---

## 4. 目录结构

```text
arb/
├── core/
│   ├── interfaces.py
│   ├── engine.py
│   ├── risk.py
│   ├── executor.py      # P2+
│   └── config.py
├── connectors/
│   ├── base.py
│   ├── uniswap_v3_arbitrum.py
│   └── camelot_arbitrum.py
├── strategies/
│   ├── base.py
│   ├── spread_monitor.py
│   └── arbitrage.py     # P2+
└── tests/
    ├── test_connectors.py
    └── test_spread_monitor.py

deploy/
├── arb-core.service      # systemd unit
└── install.sh
```

### 4.1 扩展约定

| 变更 | 操作 |
|------|------|
| 新 DEX | 新增 `connectors/<name>.py`，实现 `IConnector` |
| 新策略 | 新增 `strategies/<name>.py`，注册到策略表 |
| 新链 | 新 Connector + 配置，Executor 核心不改 |
| 改 `risk.py` / `executor.py` | 须 [HITL](./arb-factory-design.md#42-配置草案autonomy_policymulti_agent_code_factory) 后部署 |

---

## 5. 运行时策略与风控

### 5.1 PROD 行为

| 项 | 规则 |
|----|------|
| LLM | **不加载** |
| Agent 进程 | **不常驻** |
| 私钥 | 仅 `arb-core` 进程可读；环境变量 `PRIVATE_KEY`（P2+） |
| 下单 | P1 仅监控；P2 测试网；P3 主网小资金 |

### 5.2 熔断（硬规则）

```text
连续失败 N 次 / 亏损超阈值 / Gas 异常 / RPC 超时
  → 自动暂停策略
  → 告警
  → 仅人工可恢复
```

### 5.3 配置草案（`autonomy_policy.prod_execution`）

```yaml
prod_execution:
  llm_in_prod_runtime: false
  auto_trade: rule_only

emergency:
  auto_pause_on_risk: true
  human_required_to_resume: true
```

---

## 6. 部署

| 项 | 决定 |
|----|------|
| PROD | Linux 裸机，**不用 Docker** |
| 进程管理 | `systemd` 托管 `arb-core` |
| 开发 | Windows 本机开发；push 后 Linux `venv` + systemd |

```text
Windows → pytest / 本地联调 → git push
Linux PROD → venv → systemd start arb-core
```

```text
Linux PROD
├── Python 3.11+ venv
├── arb-core（SpreadMonitor / Arbitrage）
├── 日志文件 + 可选 Webhook 告警
└── .env + config.yaml（无私钥模板可被工厂读作参考）
```

---

## 7. 环境变量

```env
ARB_RPC_URL=https://arb-mainnet.g.alchemy.com/v2/...
ARB_CHAIN_ID=42161
ARB_PAIR=WETH/USDC
ARB_SPREAD_THRESHOLD_BPS=30

# P2+ 仅运行时，勿加入工厂环境
# PRIVATE_KEY=...
```

LangSmith / LLM 密钥 **不属于** arb-core（见 [arb-factory-design.md §6](./arb-factory-design.md#6-环境变量仅工厂)）。

---

## 8. 交付与验收

### 8.1 P0 + P1（监控上线）

**输入示例：** 「监控 Arbitrum 上 WETH/USDC 在 Uniswap V3 与 Camelot 的价差，超阈值告警」

**产出：**

- `connectors/`：Uniswap V3 + Camelot
- `strategies/spread_monitor.py`
- `arb-core` systemd 7×24 运行

**验收：**

- [ ] SpreadMonitor 在 Linux PROD 稳定运行
- [ ] 契约测试 + mock 报价测试通过
- [ ] 工厂流水线曾成功修改上述代码并通过 pytest（见 factory §7）

### 8.2 P2 + P3（交易能力）

| 阶段 | 输入要点 | 增量 |
|------|----------|------|
| **P2** | Arbitrum Sepolia PaperTrade / 小额套利 | `executor.py`、`arbitrage.py` |
| **P3** | 主网小资金 DEX↔DEX，含风控 | 主网 deploy **须 HITL** |

**目标 3 完整验收：**

- [ ] 监控与交易可并存或切换
- [ ] P2 测试网 Executor 跑通
- [ ] P3 主网小资金运行（deploy 经 HITL）

### 8.3 范围边界

| 包含 | 后续 |
|------|------|
| 拉价、价差、日志、告警、测试网/主网下单 | 跨链 |
| Linux systemd | MEV / Flashbots |

---

## 附录：术语

| 术语 | 含义 |
|------|------|
| **arb-core** | PROD 运行时进程与 `code_root` 下 `core/` 代码 |
| **Connector** | 对接 DEX / RPC 的插件 |
| **SpreadMonitor** | P1 只读策略：监控价差并告警 |
| **Executor** | 链上下单执行器（P2+） |
| **bps** | 价差基点，1 bps = 0.01% |
