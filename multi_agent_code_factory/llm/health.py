"""Live 模式启动前 LLM 后端健康检查。"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from multi_agent_code_factory.llm.config import require_llm_api_key, resolve_llm_runtime_config
from multi_agent_code_factory.llm.providers import DEFAULT_OLLAMA_BASE_URL
from multi_agent_code_factory.llm.types import LlmConfigError, LlmRuntimeConfig


def preflight_live_llm(*, timeout_sec: float = 90.0) -> None:
    """流水线启动前探测 live 后端是否可响应，失败则快速报错。"""
    runtime = resolve_llm_runtime_config()
    if runtime.factory_provider != "ollama":
        require_llm_api_key(provider=runtime.factory_provider)
        return

    base = (runtime.base_url or DEFAULT_OLLAMA_BASE_URL).rstrip("/")
    payload = json.dumps(
        {
            "model": runtime.model,
            "prompt": "Reply with OK only.",
            "stream": False,
            "options": {"num_predict": 8},
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{base}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_sec) as response:
            body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        msg = _ollama_failure_message(runtime, exc, detail)
        raise LlmConfigError(msg) from exc
    except Exception as exc:
        msg = _ollama_failure_message(runtime, exc, "")
        raise LlmConfigError(msg) from exc

    if '"error"' in body.lower():
        msg = _ollama_failure_message(runtime, RuntimeError("ollama returned error payload"), body)
        raise LlmConfigError(msg)


def _ollama_failure_message(
    runtime: LlmRuntimeConfig,
    exc: BaseException,
    detail: str,
) -> str:
    hint = (
        f"Ollama live preflight failed for model {runtime.model!r} at {runtime.base_url}.\n"
        f"Cause: {exc}\n"
        "Fixes to try:\n"
        "  1. Set OLLAMA_BASE_URL=http://127.0.0.1:11434 (not localhost; Windows IPv6 → 502)\n"
        "  2. Restart Ollama (quit tray app, run `ollama serve`)\n"
        "  3. `ollama pull qwen3.5:9b` and match FACTORY_LLM_MODEL\n"
        "  4. Lower OLLAMA_NUM_CTX / set OLLAMA_REASONING=false in .env\n"
        "  5. Or use cloud: FACTORY_LLM_PROVIDER=deepseek + DEEPSEEK_API_KEY\n"
    )
    if detail.strip():
        hint += f"Ollama response: {detail.strip()[:500]}\n"
    return hint
