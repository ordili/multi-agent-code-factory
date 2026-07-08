"""流水线日志辅助（基于标准库 ``logging``）。"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.schemas.validation_report import (
    ValidationReport,
    Violation,
)

_LOGGER_NAMESPACE = "multi_agent_code_factory"
_CONFIGURED = False


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


def configure_logging(*, level: str | int | None = None, force: bool = False) -> None:
    """Configure root logging once per process (idempotent unless ``force``)."""
    global _CONFIGURED
    if _CONFIGURED and not force:
        return

    resolved = _resolve_level(level)
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    root = logging.getLogger()
    if force:
        root.handlers.clear()
    if not root.handlers:
        root.addHandler(handler)
    root.setLevel(resolved)

    # Keep library loggers visible while avoiding duplicate handlers on re-entry.
    logging.getLogger(_LOGGER_NAMESPACE).setLevel(resolved)
    _CONFIGURED = True


def reset_logging_for_tests() -> None:
    """Allow tests to reconfigure logging."""
    global _CONFIGURED
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
        parts.append(f"{item.rule_id}{field}: {item.message}")
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
