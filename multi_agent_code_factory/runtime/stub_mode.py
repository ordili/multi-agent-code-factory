"""CLI / 流水线 stub 与 live 运行模式解析。"""

from __future__ import annotations

from multi_agent_code_factory.llm.config import require_llm_api_key


def resolve_stub_mode(*, stub: bool, live: bool) -> bool:
    """解析 stub / live 互斥标志；live 模式要求 API key 可用。"""
    if stub and live:
        msg = "cannot use both --stub and --live"
        raise ValueError(msg)
    if live:
        require_llm_api_key()
        return False
    if stub:
        return True
    return True
