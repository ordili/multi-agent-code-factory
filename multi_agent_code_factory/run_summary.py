"""CLI / run.log 结束摘要：环节 LLM 用量、耗时与 budget。"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.llm.usage.models import LlmUsageLog
from multi_agent_code_factory.log import (
    ERROR_LOG_FILENAME,
    RUN_LOG_FILENAME,
    WARNING_LOG_FILENAME,
    run_log_dir,
)
from multi_agent_code_factory.schemas.run_meta import RunMeta
from multi_agent_code_factory.schemas.test_report import TestReport


@dataclass(frozen=True)
class StageLlmSummary:
    """单环节 LLM 与回路用量摘要。"""

    stage: str
    label: str
    llm_calls: int
    llm_call_limit: int | None
    loop_used: int | None
    loop_limit: int | None
    duration_ms: int | None = None


@dataclass(frozen=True)
class RunTimingSummary:
    """从已有产物聚合的任务耗时（不埋点采集）。"""

    wall_clock_sec: float | None
    started_at: str | None
    finished_at: str | None
    llm_duration_total_ms: int
    qa_duration_sec: float | None


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


def _parse_iso_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
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


def sum_duration_ms_by_role(usage: LlmUsageLog | None) -> dict[str, int]:
    """按 role_id 累计 llm_usage 中的 duration_ms。"""
    if usage is None:
        return {}
    totals: dict[str, int] = {}
    for call in usage.calls:
        if call.duration_ms is None:
            continue
        key = str(call.role_id)
        totals[key] = totals.get(key, 0) + call.duration_ms
    return totals


def sum_llm_duration_ms(usage: LlmUsageLog | None) -> int:
    """累计全部 LLM 调用的 duration_ms。"""
    return sum(sum_duration_ms_by_role(usage).values())


def build_run_timing(
    meta: RunMeta | None, usage: LlmUsageLog | None
) -> RunTimingSummary:
    """从 run_meta 与 llm_usage 聚合墙钟与 LLM 耗时。"""
    wall_clock_sec: float | None = None
    started_at = meta.started_at if meta is not None else None
    finished_at = meta.finished_at if meta is not None else None
    if meta is not None:
        start = _parse_iso_timestamp(meta.started_at)
        end = _parse_iso_timestamp(meta.finished_at)
        if start is not None and end is not None:
            wall_clock_sec = max(0.0, (end - start).total_seconds())
    return RunTimingSummary(
        wall_clock_sec=wall_clock_sec,
        started_at=started_at,
        finished_at=finished_at,
        llm_duration_total_ms=sum_llm_duration_ms(usage),
        qa_duration_sec=None,
    )


def load_qa_duration_sec(run_dir: Path) -> float | None:
    """读取最近一次 test_report 的工具链耗时。"""
    path = run_dir / "test_report.json"
    if not path.is_file():
        return None
    report = TestReport.model_validate(json.loads(path.read_text(encoding="utf-8")))
    return report.duration_sec


def build_stage_summaries(
    meta: RunMeta | None,
    usage: LlmUsageLog | None,
) -> list[StageLlmSummary]:
    """从 run_meta 与 llm_usage 构建各环节摘要。"""
    loop_limits = (meta.loop_limits if meta is not None else {}) or {}
    call_counts = count_llm_calls_by_role(usage)
    duration_by_role = sum_duration_ms_by_role(usage)
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
            llm_call_limit = 1 + loop_limit
        elif stage == "qa":
            llm_call_limit = 0
        else:
            llm_call_limit = None

        duration_ms = duration_by_role.get(role.value)
        summaries.append(
            StageLlmSummary(
                stage=stage,
                label=label,
                llm_calls=llm_calls,
                llm_call_limit=llm_call_limit,
                loop_used=loop_used,
                loop_limit=loop_limit,
                duration_ms=duration_ms if duration_ms else None,
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
    duration = "—" if item.duration_ms is None else str(item.duration_ms)
    return (
        f"  {item.label}: llm_calls={calls} loop_retries={loops} duration_ms={duration}"
    )


def format_timing_line(timing: RunTimingSummary) -> str:
    """格式化墙钟与 LLM/QA 耗时一行摘要。"""
    wall = "—" if timing.wall_clock_sec is None else f"{timing.wall_clock_sec:.1f}"
    qa = "—" if timing.qa_duration_sec is None else f"{timing.qa_duration_sec:.3f}"
    return (
        "pipeline timing "
        f"wall_clock_sec={wall} "
        f"started_at={timing.started_at or '—'} "
        f"finished_at={timing.finished_at or '—'} "
        f"llm_duration_total_ms={timing.llm_duration_total_ms} "
        f"qa_duration_sec={qa}"
    )


def load_run_meta(path: Path) -> RunMeta | None:
    if not path.is_file():
        return None
    return RunMeta.model_validate(json.loads(path.read_text(encoding="utf-8")))


def load_llm_usage(path: Path) -> LlmUsageLog | None:
    if not path.is_file():
        return None
    return LlmUsageLog.model_validate(json.loads(path.read_text(encoding="utf-8")))


def build_run_outcome_lines(run_dir: Path, *, stub: bool) -> list[str]:
    """构建 run 结束摘要行（CLI 与 run.log 共用）。"""
    meta = load_run_meta(run_dir / "run_meta.json")
    usage = None if stub else load_llm_usage(run_dir / "llm_usage.json")
    timing = build_run_timing(meta, usage)
    qa_sec = load_qa_duration_sec(run_dir)
    if qa_sec is not None:
        timing = RunTimingSummary(
            wall_clock_sec=timing.wall_clock_sec,
            started_at=timing.started_at,
            finished_at=timing.finished_at,
            llm_duration_total_ms=timing.llm_duration_total_ms,
            qa_duration_sec=qa_sec,
        )

    lines = [format_timing_line(timing), "stage_llm_summary:"]
    for item in build_stage_summaries(meta, usage):
        lines.append(format_stage_line(item))

    if meta is not None and meta.budget is not None:
        budget = meta.budget
        call_part = _format_limit(budget.used_llm_calls or 0, budget.max_llm_calls)
        token_part = _format_limit(budget.used_tokens or 0, budget.max_tokens)
        lines.append(f"llm_budget: calls={call_part} tokens={token_part}")

    if usage is not None:
        totals = usage.totals
        lines.append(
            "llm_usage_totals: "
            f"calls={totals.llm_calls} "
            f"prompt_tokens={totals.prompt_tokens} "
            f"completion_tokens={totals.completion_tokens} "
            f"total_tokens={totals.total_tokens}"
        )

    log_dir = run_log_dir(run_dir)
    run_log = log_dir / RUN_LOG_FILENAME
    warning_log = log_dir / WARNING_LOG_FILENAME
    error_log = log_dir / ERROR_LOG_FILENAME
    if run_log.is_file():
        lines.append(f"log_files: run={run_log} warn={warning_log} error={error_log}")

    return lines


def log_run_outcome(
    logger: logging.Logger,
    run_dir: Path,
    *,
    stub: bool = False,
) -> None:
    """将 run 结束摘要写入 run.log。"""
    for line in build_run_outcome_lines(run_dir, stub=stub):
        logger.info("%s", line)


def print_run_outcome(run_dir: Path, *, stub: bool) -> None:
    """打印 run 目录中的环节 LLM 用量、耗时与全局 budget。"""
    for line in build_run_outcome_lines(run_dir, stub=stub):
        print(line)
