"""LLM usage extraction and persistence tests."""

from __future__ import annotations

from types import SimpleNamespace

from pathlib import Path

import pytest

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.llm_usage import (
    LlmCallUsage,
    LlmUsageTotals,
    extract_token_usage,
    merge_usage_totals,
)
from multi_agent_code_factory.tools.write_artifact import RunArtifactWriter


def test_extract_token_usage_from_usage_metadata() -> None:
    response = SimpleNamespace(
        usage_metadata={
            "input_tokens": 120,
            "output_tokens": 80,
            "total_tokens": 200,
        }
    )
    usage = extract_token_usage(response)
    assert usage.prompt_tokens == 120
    assert usage.completion_tokens == 80
    assert usage.total_tokens == 200


def test_extract_token_usage_from_response_metadata() -> None:
    response = SimpleNamespace(
        usage_metadata=None,
        response_metadata={
            "token_usage": {
                "prompt_tokens": 50,
                "completion_tokens": 25,
                "total_tokens": 75,
            }
        },
    )
    usage = extract_token_usage(response)
    assert usage.prompt_tokens == 50
    assert usage.completion_tokens == 25
    assert usage.total_tokens == 75


def test_merge_usage_totals_accumulates_calls() -> None:
    totals = merge_usage_totals(
        LlmUsageTotals(),
        LlmCallUsage(
            role_id=AgentRole.PM,
            schema_name="SpecArtifact",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
        ),
    )
    assert totals.llm_calls == 1
    assert totals.prompt_tokens == 100
    assert totals.completion_tokens == 50
    assert totals.total_tokens == 150


def test_record_llm_usage_writes_artifact(tmp_path: Path) -> None:
    writer = RunArtifactWriter("usage-test", base_dir=tmp_path)
    call = LlmCallUsage(
        role_id=AgentRole.PM,
        schema_name="SpecArtifact",
        duration_ms=1200,
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
    )
    log = writer.record_llm_usage(call, provider="deepseek", model="deepseek-chat")
    assert log.totals.llm_calls == 1
    assert log.totals.total_tokens == 30
    reread = writer.read_llm_usage()
    assert reread is not None
    assert reread.totals.total_tokens == 30

    second = LlmCallUsage(
        role_id=AgentRole.ARCHITECT,
        schema_name="ArchitectLLMOutput",
        prompt_tokens=100,
        completion_tokens=200,
        total_tokens=300,
    )
    writer.record_llm_usage(second, provider="deepseek", model="deepseek-chat")
    reread = writer.read_llm_usage()
    assert reread is not None
    assert reread.totals.llm_calls == 2
    assert reread.totals.total_tokens == 330
