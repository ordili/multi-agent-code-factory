"""LangSmith / LangChain 追踪配置，将 ``task_id`` 关联到 Trace。"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any, TypeVar

from multi_agent_code_factory.schemas.run_meta import RunStatus
from multi_agent_code_factory.state import PipelineState, normalize_pipeline_state

T = TypeVar("T")

_TRACE_INPUT_MAX = 300
_TRACE_ERROR_MAX = 500


def _truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _truncate_text(text: str, max_len: int) -> str:
    stripped = text.strip()
    if len(stripped) <= max_len:
        return stripped
    return stripped[: max_len - 1] + "…"


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


def build_trace_inputs(
    *,
    task_id: str,
    profile_id: str,
    pipeline_mode: str,
    agent_mode: str,
    user_request: str | None = None,
    reentry: str | None = None,
) -> dict[str, Any]:
    """构建 LangSmith 顶层 trace 的可读 input 摘要（不含完整 PRD/Design）。"""
    payload: dict[str, Any] = {
        "task_id": task_id,
        "profile_id": profile_id,
        "pipeline_mode": pipeline_mode,
        "agent_mode": agent_mode,
    }
    if user_request:
        payload["user_request"] = _truncate_text(user_request, _TRACE_INPUT_MAX)
    if reentry:
        payload["reentry"] = reentry
    return payload


def build_trace_output(
    final_raw: PipelineState | dict[str, Any],
    *,
    status: RunStatus,
) -> dict[str, Any]:
    """构建 LangSmith 顶层 trace 的 output 摘要。"""
    state = normalize_pipeline_state(final_raw)
    return {
        "status": status.value,
        "task_id": state.task_id,
        "pipeline_route": state.pipeline_route or None,
        "prd_revision_count": state.prd_revision_count,
        "design_revision_count": state.design_revision_count,
        "impl_retry_count": state.impl_retry_count,
        "has_prd": state.prd is not None,
        "has_design": state.design is not None,
        "has_dev_manifest": state.dev_manifest is not None,
    }


def build_continue_invoke_input(state: PipelineState) -> dict[str, str]:
    """Continue 时传给 LangGraph 的无副作用 state 切片，供 LangSmith 显示 input。"""
    return {
        "task_id": state.task_id,
        "user_request": state.user_request,
    }


def build_run_config(
    *,
    task_id: str,
    profile_id: str,
    pipeline_mode: str | None = None,
    agent_mode: str | None = None,
    user_request: str | None = None,
    reentry: str | None = None,
) -> dict[str, Any]:
    """构建 LangGraph ``invoke`` 用的 RunnableConfig，携带 ``task_id`` 元数据。"""
    configure_tracing_env()
    metadata: dict[str, Any] = {
        "task_id": task_id,
        "profile_id": profile_id,
    }
    if pipeline_mode:
        metadata["pipeline_mode"] = pipeline_mode
    if agent_mode:
        metadata["agent_mode"] = agent_mode
    if reentry:
        metadata["reentry"] = reentry
    if user_request:
        metadata["user_request_preview"] = _truncate_text(
            user_request,
            _TRACE_INPUT_MAX,
        )

    tags = [f"task_id:{task_id}", f"profile:{profile_id}"]
    if pipeline_mode:
        tags.append(f"pipeline_mode:{pipeline_mode}")
    if reentry:
        tags.append(f"reentry:{reentry}")

    return {
        "run_name": task_id,
        "metadata": metadata,
        "tags": tags,
    }


def invoke_graph_with_trace(
    app: Any,
    *,
    invoke_input: Any,
    context: Any,
    config: dict[str, Any],
    trace_inputs: dict[str, Any],
    build_success_output: Callable[[Any], dict[str, Any]],
) -> Any:
    """在启用追踪时为 LangGraph invoke 附加可读的顶层 input/output。"""
    if not is_tracing_enabled():
        return app.invoke(invoke_input, context=context, config=config)

    try:
        from langsmith.run_helpers import trace
    except ImportError:
        return app.invoke(invoke_input, context=context, config=config)

    run_name = str(config.get("run_name") or trace_inputs.get("task_id") or "pipeline")
    with trace(
        name=run_name,
        run_type="chain",
        inputs=trace_inputs,
        metadata=config.get("metadata"),
        tags=config.get("tags"),
    ) as run_tree:
        try:
            result = app.invoke(invoke_input, context=context, config=config)
        except Exception as exc:
            run_tree.end(
                outputs={
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "error": _truncate_text(str(exc), _TRACE_ERROR_MAX),
                }
            )
            raise
        run_tree.end(outputs=build_success_output(result))
        return result
