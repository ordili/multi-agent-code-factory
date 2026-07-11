"""流水线日志辅助（基于标准库 ``logging``）。"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.schemas.validation_report import (
    ValidationReport,
    Violation,
)

_LOGGER_NAMESPACE = "multi_agent_code_factory"
_CONFIGURED = False
_RUN_FILE_HANDLERS: list[logging.Handler] = []

RUN_LOG_FILENAME = "run.log"
WARNING_LOG_FILENAME = "warn.log"
ERROR_LOG_FILENAME = "error.log"


class _ExactLevelFilter(logging.Filter):
    """仅放行指定级别的日志记录。"""

    def __init__(self, level: int) -> None:
        super().__init__()
        self._level = level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno == self._level


def _resolve_level(level: str | int | None) -> int:
    if level is None:
        level = os.environ.get("FACTORY_LOG_LEVEL", "INFO")
    if isinstance(level, int):
        return level
    normalized = level.strip().upper()
    resolved = logging.getLevelNamesMapping().get(normalized)
    if resolved is None:
        msg = f"unknown log level: {level!r}"
        raise ValueError(msg)
    return resolved


def _log_formatter() -> logging.Formatter:
    return logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def configure_logging(*, level: str | int | None = None, force: bool = False) -> None:
    """Configure root logging once per process (idempotent unless ``force``)."""
    global _CONFIGURED
    if _CONFIGURED and not force:
        return

    resolved = _resolve_level(level)
    handler = logging.StreamHandler()
    handler.setFormatter(_log_formatter())

    root = logging.getLogger()
    if force:
        detach_run_file_logging()
        root.handlers.clear()
    if not any(isinstance(item, logging.StreamHandler) for item in root.handlers):
        root.addHandler(handler)
    root.setLevel(resolved)

    # Keep library loggers visible while avoiding duplicate handlers on re-entry.
    logging.getLogger(_LOGGER_NAMESPACE).setLevel(resolved)
    _CONFIGURED = True


def attach_run_file_logging(
    run_dir: Path, *, append: bool = False
) -> tuple[Path, Path, Path]:
    """将日志写入 run 目录下的 ``run.log``、``warn.log`` 与 ``error.log``。"""
    detach_run_file_logging()

    directory = run_dir.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"

    run_log_path = directory / RUN_LOG_FILENAME
    warning_log_path = directory / WARNING_LOG_FILENAME
    error_log_path = directory / ERROR_LOG_FILENAME

    run_handler = logging.FileHandler(
        run_log_path,
        mode=mode,
        encoding="utf-8",
    )
    run_handler.setFormatter(_log_formatter())

    warning_handler = logging.FileHandler(
        warning_log_path,
        mode=mode,
        encoding="utf-8",
    )
    warning_handler.setLevel(logging.WARNING)
    warning_handler.addFilter(_ExactLevelFilter(logging.WARNING))
    warning_handler.setFormatter(_log_formatter())

    error_handler = logging.FileHandler(
        error_log_path,
        mode=mode,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(_log_formatter())

    root = logging.getLogger()
    root.addHandler(run_handler)
    root.addHandler(warning_handler)
    root.addHandler(error_handler)
    _RUN_FILE_HANDLERS.extend([run_handler, warning_handler, error_handler])
    return run_log_path, warning_log_path, error_log_path


def detach_run_file_logging() -> None:
    """移除并关闭 run 级文件 handler。"""
    global _RUN_FILE_HANDLERS
    root = logging.getLogger()
    for handler in _RUN_FILE_HANDLERS:
        root.removeHandler(handler)
        handler.close()
    _RUN_FILE_HANDLERS = []


def reset_logging_for_tests() -> None:
    """Allow tests to reconfigure logging."""
    global _CONFIGURED
    detach_run_file_logging()
    root = logging.getLogger()
    root.handlers.clear()
    _CONFIGURED = False


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"{_LOGGER_NAMESPACE}.{name}")


def format_violations(violations: list[Violation], *, limit: int = 5) -> str:
    if not violations:
        return "none"
    parts: list[str] = []
    for item in violations[:limit]:
        field = f" field={item.field}" if item.field else ""
        path = f" path={item.path}" if item.path else ""
        parts.append(f"{item.rule_id} ({item.severity}){field}{path}: {item.message}")
    if len(violations) > limit:
        parts.append(f"... +{len(violations) - limit} more")
    return "; ".join(parts)


def log_validation_result(
    logger: logging.Logger,
    *,
    target: str,
    report: ValidationReport,
) -> None:
    if report.passed:
        logger.info(
            "validation passed target=%s errors=%s warnings=%s",
            target,
            report.error_count,
            report.warn_count,
        )
        return
    logger.warning(
        "validation failed target=%s errors=%s warnings=%s violations=%s",
        target,
        report.error_count,
        report.warn_count,
        format_violations(report.violations),
    )


@contextmanager
def agent_run(
    logger: logging.Logger,
    *,
    role_id: AgentRole,
    stub: bool,
    extra: dict[str, Any] | None = None,
) -> Iterator[None]:
    mode = "stub" if stub else "live"
    suffix = ""
    if extra:
        suffix = " " + " ".join(f"{key}={value}" for key, value in extra.items())
    logger.info("agent start role=%s mode=%s%s", role_id, mode, suffix)
    try:
        yield
    except Exception:
        logger.exception("agent failed role=%s mode=%s%s", role_id, mode, suffix)
        raise
    logger.info("agent done role=%s mode=%s%s", role_id, mode, suffix)
