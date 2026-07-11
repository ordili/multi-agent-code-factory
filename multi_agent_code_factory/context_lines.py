"""Prompt 上下文行数估算（避免 batch_closure ↔ prompt 循环导入）。"""

from __future__ import annotations

import json
from typing import Any


def count_context_lines(context: dict[str, Any]) -> int:
    """估算 prompt 上下文行数（JSON 序列化）。"""
    payload = json.dumps(context, ensure_ascii=False, indent=2)
    return len(payload.splitlines())
