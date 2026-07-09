"""LangSmith / LangChain 追踪配置，将 ``task_id`` 关联到 Trace。"""

from __future__ import annotations

import os
from typing import Any


def _truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def is_tracing_enabled() -> bool:
    """是否已通过环境变量启用 LangSmith / LangChain 追踪。"""
    return _truthy(os.environ.get("LANGSMITH_TRACING")) or _truthy(
        os.environ.get("LANGCHAIN_TRACING_V2")
    )


def configure_tracing_env() -> bool:
    """将 LangSmith 标准变量同步到 LangChain 运行时变量；返回是否启用追踪。"""
    if not is_tracing_enabled():
        return False

    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")

    smith_key = os.environ.get("LANGSMITH_API_KEY")
    if smith_key:
        os.environ.setdefault("LANGCHAIN_API_KEY", smith_key)

    project = os.environ.get("LANGSMITH_PROJECT")
    if project:
        os.environ.setdefault("LANGCHAIN_PROJECT", project)

    endpoint = os.environ.get("LANGSMITH_ENDPOINT")
    if endpoint:
        os.environ.setdefault("LANGCHAIN_ENDPOINT", endpoint)

    return True


def build_run_config(*, task_id: str, profile_id: str) -> dict[str, Any]:
    """构建 LangGraph ``invoke`` 用的 RunnableConfig，携带 ``task_id`` 元数据。"""
    configure_tracing_env()
    return {
        "run_name": task_id,
        "metadata": {
            "task_id": task_id,
            "profile_id": profile_id,
        },
        "tags": [f"task_id:{task_id}", f"profile:{profile_id}"],
    }
