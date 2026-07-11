"""Tests for pipeline logging helpers."""

from __future__ import annotations

from pathlib import Path

import pytest
from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.log import (
    ERROR_LOG_FILENAME,
    RUN_LOG_FILENAME,
    WARNING_LOG_FILENAME,
    agent_run,
    attach_run_file_logging,
    configure_logging,
    detach_run_file_logging,
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
    with (
        pytest.raises(RuntimeError, match="boom"),
        agent_run(logger, role_id=AgentRole.ARCHITECT, stub=False),
    ):
        raise RuntimeError("boom")
    captured = capsys.readouterr().err
    assert "agent failed role=architect mode=live" in captured


def test_attach_run_file_logging_writes_run_and_error_logs(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_logging(level="INFO", force=True)
    logger = get_logger("test.files")
    run_log, warning_log, error_log = attach_run_file_logging(tmp_path, append=False)
    assert run_log.name == RUN_LOG_FILENAME
    assert warning_log.name == WARNING_LOG_FILENAME
    assert error_log.name == ERROR_LOG_FILENAME

    logger.info("info message")
    logger.warning("warn message")
    logger.error("error message")
    detach_run_file_logging()

    run_text = run_log.read_text(encoding="utf-8")
    warning_text = warning_log.read_text(encoding="utf-8")
    error_text = error_log.read_text(encoding="utf-8")
    assert "info message" in run_text
    assert "warn message" in run_text
    assert "error message" in run_text
    assert "info message" not in warning_text
    assert "warn message" in warning_text
    assert "error message" not in warning_text
    assert "info message" not in error_text
    assert "warn message" not in error_text
    assert "error message" in error_text

    captured = capsys.readouterr().err
    assert "info message" in captured
    assert "error message" in captured


def test_attach_run_file_logging_append_mode(tmp_path: Path) -> None:
    configure_logging(level="INFO", force=True)
    logger = get_logger("test.append")
    attach_run_file_logging(tmp_path, append=False)
    logger.info("first")
    detach_run_file_logging()

    attach_run_file_logging(tmp_path, append=True)
    logger.info("second")
    detach_run_file_logging()

    run_text = (tmp_path / RUN_LOG_FILENAME).read_text(encoding="utf-8")
    assert "first" in run_text
    assert "second" in run_text
