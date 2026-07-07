"""Test output parser registry."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from multi_agent_code_factory.profiles import ProfileConfig
from multi_agent_code_factory.schemas.test_report import TestReport
from multi_agent_code_factory.tools.test_parsers._types import CommandResult
from multi_agent_code_factory.tools.test_parsers.exit_code_only import (
    parse_exit_code_only,
)
from multi_agent_code_factory.tools.test_parsers.junit_xml import parse_junit_xml

ParserFn = Callable[[CommandResult, ProfileConfig, Path], TestReport]


_PARSERS: dict[str, ParserFn] = {
    "junit_xml": parse_junit_xml,
    "exit_code_only": parse_exit_code_only,
}


def get_parser(parser_id: str) -> ParserFn:
    try:
        return _PARSERS[parser_id]
    except KeyError as exc:
        msg = f"unknown test parser: {parser_id!r}"
        raise ValueError(msg) from exc


def registered_parsers() -> tuple[str, ...]:
    return tuple(sorted(_PARSERS))
