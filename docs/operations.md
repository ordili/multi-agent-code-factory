# 运行与排错

面向已在 README 完成 Stub Quick Start、需要 **Live LLM** 或 **VM 部署** 的开发者。

## 云 API（DeepSeek / OpenAI / Anthropic）

在 `.env` 中设置厂商与 Key，例如 DeepSeek：

```env
FACTORY_LLM_PROVIDER=deepseek
FACTORY_LLM_MODEL=deepseek-chat
DEEPSEEK_API_KEY=sk-...
```

其它厂商见 [`.env.example`](../.env.example)。

## 本地 Ollama

```env
FACTORY_LLM_PROVIDER=ollama
FACTORY_LLM_MODEL=qwen3.5:9b
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_NUM_CTX=8192
OLLAMA_NUM_PREDICT=4096
OLLAMA_REASONING=false
```

1. 先 `ollama pull qwen3.5:9b`（或与 `FACTORY_LLM_MODEL` 一致的模型）。
2. **`OLLAMA_BASE_URL` 请用 `127.0.0.1`**，不要用 `localhost`——Windows 上 `localhost` 可能解析为 IPv6 `::1`，导致 HTTP 502。
3. CPU 推理较慢：单 Agent 常需数分钟，整轮 pipeline 可能 **30–90 分钟**。
4. `--live` 启动时会做 Ollama **preflight**（探测模型是否可响应），失败时提前报错。

## GCP / Linux VM

在已安装 Ollama 的 VM 上：

```bash
chmod +x scripts/vm-run-pipeline.sh scripts/vm-run-calculator.sh

./scripts/vm-run-pipeline.sh --task-id calculator "实现支持加减乘除的计算器"
./scripts/vm-run-calculator.sh   # 计算器快捷入口（DEBUG 日志）
```

- 脚本默认代码输出到 `/data/generated/<task-id>`。
- 仓库根目录需配置 `.env`（同机 Ollama 时用 `OLLAMA_BASE_URL=http://127.0.0.1:11434`）。
- 参数与环境变量见 `scripts/vm-run-pipeline.sh` 头部注释。

## 集成测试

```bash
pytest tests/integration/test_todo_cli_e2e.py -m integration
```

Ollama e2e 需额外设置 `RUN_OLLAMA_E2E=1`。

## 常见问题

| 现象 | 处理 |
|------|------|
| Ollama HTTP 502 | 将 `OLLAMA_BASE_URL` 改为 `http://127.0.0.1:11434` |
| Live 启动即失败 | 检查 `.env` 中 `FACTORY_LLM_PROVIDER` / Key；Ollama 是否 `ollama list` 可见模型 |
| 产物只有 JSON 无人读 MD | 使用当前 main；旧 run 需重跑 pipeline 或手动调用 renderer |
| 代码不在本仓库 | 设计如此：`code_root` 默认在仓库外，见 Profile |
