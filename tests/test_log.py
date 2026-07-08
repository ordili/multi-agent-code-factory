"""Tests for pipeline logging helpers."""

from __future__ import annotations

import logging

import pytest

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.log import (
    agent_run,
    configure_logging,
    get_logger,
    reset_logging_for_tests,
)


@pytest.fixture(autouse=True)
def _reset_logging() -> None:
    reset_logging_for_tests()
    yield
    reset_logging_for_tests()


def test_configure_logging_is_idempotent(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(level="INFO", force=True)
    logger = get_logger("test")
    configure_logging(level="DEBUG", force=False)
    logger.info("once")
    captured = capsys.readouterr().err
    assert captured.count("once") == 1


def test_agent_run_logs_success(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(level="INFO", force=True)
    logger = get_logger("test.agent")
    with agent_run(logger, role_id=AgentRole.PM, stub=True):
        pass
    captured = capsys.readouterr().err
    assert "agent start role=pm mode=stub" in captured
    assert "agent done role=pm mode=stub" in captured


def test_agent_run_logs_exception(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(level="INFO", force=True)
    logger = get_logger("test.agent")
    with pytest.raises(RuntimeError, match="boom"):
        with agent_run(logger, role_id=AgentRole.ARCHITECT, stub=False):
            raise RuntimeError("boom")
    captured = capsys.readouterr().err
    assert "agent failed role=architect mode=live" in captured
