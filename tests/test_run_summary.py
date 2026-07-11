from __future__ import annotations

import json
from pathlib import Path

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.llm.usage.models import (
    LlmCallUsage,
    LlmUsageLog,
    LlmUsageTotals,
)
from multi_agent_code_factory.run_summary import (
    build_run_timing,
    build_stage_summaries,
    count_llm_calls_by_role,
    format_stage_line,
    format_timing_line,
    print_run_outcome,
    sum_duration_ms_by_role,
)
from multi_agent_code_factory.schemas.run_meta import BudgetUsage, RunMeta, RunStatus


def _meta(**overrides: object) -> RunMeta:
    payload: dict[str, object] = {
        "version": "1",
        "task_id": "demo",
        "profile": {"id": "python"},
        "loop_limits": {
            "max_impl_retries": 3,
            "max_design_revisions": 2,
            "max_prd_revisions": 1,
            "on_limit_exceeded": "fail",
        },
        "impl_retry_count": 1,
        "design_revision_count": 0,
        "prd_revision_count": 0,
        "budget": {
            "max_llm_calls": 50,
            "max_tokens": 100000,
            "used_llm_calls": 5,
            "used_tokens": 12000,
        },
        "status": RunStatus.COMPLETED,
    }
    payload.update(overrides)
    return RunMeta.model_validate(payload)


def _usage() -> LlmUsageLog:
    return LlmUsageLog(
        version="1",
        provider="deepseek",
        model="deepseek-v4-pro",
        calls=[
            LlmCallUsage(
                role_id=AgentRole.PM,
                schema_name="PrdArtifact",
                duration_ms=1000,
            ),
            LlmCallUsage(
                role_id=AgentRole.ARCHITECT,
                schema_name="ArchitectLLMOutput",
                duration_ms=2000,
            ),
            LlmCallUsage(
                role_id=AgentRole.DEVELOPER,
                schema_name="DeveloperLLMOutput",
                duration_ms=3000,
            ),
            LlmCallUsage(
                role_id=AgentRole.DEVELOPER,
                schema_name="DeveloperLLMOutput",
                duration_ms=4000,
            ),
            LlmCallUsage(
                role_id=AgentRole.REVIEWER,
                schema_name="ReviewReport",
                duration_ms=500,
            ),
        ],
        totals=LlmUsageTotals(
            llm_calls=5,
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300,
        ),
    )


def test_count_llm_calls_by_role() -> None:
    counts = count_llm_calls_by_role(_usage())
    assert counts["pm"] == 1
    assert counts["developer"] == 2
    assert counts.get("qa") is None


def test_build_stage_summaries_limits() -> None:
    summaries = build_stage_summaries(_meta(), _usage())
    by_stage = {item.stage: item for item in summaries}
    assert by_stage["pm"].llm_calls == 1
    assert by_stage["pm"].llm_call_limit == 2
    assert by_stage["developer"].llm_calls == 2
    assert by_stage["developer"].llm_call_limit == 4
    assert by_stage["developer"].loop_used == 1
    assert by_stage["developer"].loop_limit == 3
    assert by_stage["reviewer"].llm_call_limit is None
    assert by_stage["qa"].llm_call_limit == 0


def test_sum_duration_ms_by_role() -> None:
    totals = sum_duration_ms_by_role(_usage())
    assert totals["pm"] == 1000
    assert totals["developer"] == 7000
    assert totals.get("qa") is None


def test_build_run_timing_wall_clock() -> None:
    meta = _meta(
        started_at="2026-07-11T03:44:57+00:00",
        finished_at="2026-07-11T03:54:15+00:00",
    )
    timing = build_run_timing(meta, _usage())
    assert timing.wall_clock_sec == 558.0
    assert timing.llm_duration_total_ms == 10500
    line = format_timing_line(timing)
    assert "wall_clock_sec=558.0" in line
    assert "llm_duration_total_ms=10500" in line


def test_format_stage_line_includes_duration() -> None:
    summaries = build_stage_summaries(_meta(), _usage())
    dev = next(item for item in summaries if item.stage == "developer")
    assert "llm_calls=2/4" in format_stage_line(dev)
    assert "loop_retries=1/3" in format_stage_line(dev)
    assert "duration_ms=7000" in format_stage_line(dev)


def test_print_run_outcome_from_files(tmp_path: Path, capsys) -> None:
    meta = _meta(
        started_at="2026-07-11T03:44:57+00:00",
        finished_at="2026-07-11T03:54:15+00:00",
    )
    (tmp_path / "run_meta.json").write_text(
        json.dumps(meta.model_dump(mode="json")),
        encoding="utf-8",
    )
    (tmp_path / "llm_usage.json").write_text(
        json.dumps(_usage().model_dump(mode="json")),
        encoding="utf-8",
    )

    print_run_outcome(tmp_path, stub=False)
    out = capsys.readouterr().out
    assert "pipeline timing" in out
    assert "wall_clock_sec=558.0" in out
    assert "stage_llm_summary:" in out
    assert "Developer: llm_calls=2/4" in out
    assert "llm_budget: calls=5/50" in out
    assert "llm_usage_totals:" in out


def test_print_run_outcome_stub_skips_usage_file(tmp_path: Path, capsys) -> None:
    meta = _meta(budget=BudgetUsage())
    (tmp_path / "run_meta.json").write_text(
        json.dumps(meta.model_dump(mode="json")),
        encoding="utf-8",
    )

    print_run_outcome(tmp_path, stub=True)
    out = capsys.readouterr().out
    assert "PM: llm_calls=0/2" in out
    assert "llm_usage_totals:" not in out
