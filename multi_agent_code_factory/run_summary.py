"""CLI run 结束摘要：各环节 LLM 调用次数与回路配额。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.llm.usage.models import LlmUsageLog
from multi_agent_code_factory.log import (
    ERROR_LOG_FILENAME,
    RUN_LOG_FILENAME,
    WARNING_LOG_FILENAME,
)
from multi_agent_code_factory.schemas.run_meta import RunMeta


@dataclass(frozen=True)
class StageLlmSummary:
    """单环节 LLM 与回路用量摘要。"""

    stage: str
    label: str
    llm_calls: int
    llm_call_limit: int | None
    loop_used: int | None
    loop_limit: int | None


_STAGE_ORDER: tuple[tuple[str, str, AgentRole], ...] = (
    ("pm", "PM", AgentRole.PM),
    ("architect", "Architect", AgentRole.ARCHITECT),
    ("developer", "Developer", AgentRole.DEVELOPER),
    ("qa", "QA", AgentRole.QA),
    ("reviewer", "Reviewer", AgentRole.REVIEWER),
)

_LOOP_LIMIT_KEYS: dict[str, str] = {
    "pm": "max_prd_revisions",
    "architect": "max_design_revisions",
    "developer": "max_impl_retries",
}

_LOOP_USED_KEYS: dict[str, str] = {
    "pm": "prd_revision_count",
    "architect": "design_revision_count",
    "developer": "impl_retry_count",
}


def _int_or_none(value: object) -> int | None:
    if isinstance(value, int):
        return value
    return None


def count_llm_calls_by_role(usage: LlmUsageLog | None) -> dict[str, int]:
    """按 role_id 统计成功与失败的 LLM 调用次数。"""
    if usage is None:
        return {}
    counts: dict[str, int] = {}
    for call in usage.calls:
        key = str(call.role_id)
        counts[key] = counts.get(key, 0) + 1
    return counts


def build_stage_summaries(
    meta: RunMeta | None,
    usage: LlmUsageLog | None,
) -> list[StageLlmSummary]:
    """从 run_meta 与 llm_usage 构建各环节摘要。"""
    loop_limits = (meta.loop_limits if meta is not None else {}) or {}
    call_counts = count_llm_calls_by_role(usage)
    summaries: list[StageLlmSummary] = []

    for stage, label, role in _STAGE_ORDER:
        llm_calls = call_counts.get(role.value, 0)
        limit_key = _LOOP_LIMIT_KEYS.get(stage)
        used_key = _LOOP_USED_KEYS.get(stage)
        loop_limit = _int_or_none(loop_limits.get(limit_key)) if limit_key else None
        loop_used = (
            getattr(meta, used_key, None) if meta is not None and used_key else None
        )
        if not isinstance(loop_used, int):
            loop_used = None

        llm_call_limit: int | None
        if loop_limit is not None:
            # 首次进入 + 允许的回退次数
            llm_call_limit = 1 + loop_limit
        elif stage == "qa":
            llm_call_limit = 0
        else:
            llm_call_limit = None

        summaries.append(
            StageLlmSummary(
                stage=stage,
                label=label,
                llm_calls=llm_calls,
                llm_call_limit=llm_call_limit,
                loop_used=loop_used,
                loop_limit=loop_limit,
            )
        )
    return summaries


def _format_limit(actual: int, limit: int | None) -> str:
    if limit is None:
        return str(actual)
    return f"{actual}/{limit}"


def format_stage_line(item: StageLlmSummary) -> str:
    """格式化单行环节摘要。"""
    calls = _format_limit(item.llm_calls, item.llm_call_limit)
    if item.loop_limit is None:
        loops = "—"
    else:
        loops = _format_limit(item.loop_used or 0, item.loop_limit)
    return f"  {item.label}: llm_calls={calls} loop_retries={loops}"


def load_run_meta(path: Path) -> RunMeta | None:
    if not path.is_file():
        return None
    return RunMeta.model_validate(json.loads(path.read_text(encoding="utf-8")))


def load_llm_usage(path: Path) -> LlmUsageLog | None:
    if not path.is_file():
        return None
    return LlmUsageLog.model_validate(json.loads(path.read_text(encoding="utf-8")))


def print_run_outcome(run_dir: Path, *, stub: bool) -> None:
    """打印 run 目录中的环节 LLM 用量与全局 budget。"""
    meta = load_run_meta(run_dir / "run_meta.json")
    usage = None if stub else load_llm_usage(run_dir / "llm_usage.json")

    print("stage_llm_summary:")
    for item in build_stage_summaries(meta, usage):
        print(format_stage_line(item))

    if meta is None or meta.budget is None:
        return

    budget = meta.budget
    used_calls = budget.used_llm_calls
    max_calls = budget.max_llm_calls
    used_tokens = budget.used_tokens
    max_tokens = budget.max_tokens

    call_part = _format_limit(used_calls or 0, max_calls)
    token_part = _format_limit(used_tokens or 0, max_tokens)
    print(f"llm_budget: calls={call_part} tokens={token_part}")

    if usage is not None:
        totals = usage.totals
        print(
            "llm_usage_totals: "
            f"prompt_tokens={totals.prompt_tokens} "
            f"completion_tokens={totals.completion_tokens} "
            f"total_tokens={totals.total_tokens}"
        )

    run_log = run_dir / RUN_LOG_FILENAME
    warning_log = run_dir / WARNING_LOG_FILENAME
    error_log = run_dir / ERROR_LOG_FILENAME
    if run_log.is_file():
        print(f"log_files: run={run_log} warn={warning_log} error={error_log}")
