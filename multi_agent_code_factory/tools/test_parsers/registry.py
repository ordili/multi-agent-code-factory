"""测试输出解析器注册表。"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from multi_agent_code_factory.profile_config import ProfileConfig
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
    """按 ID 获取测试输出解析函数。"""
    try:
        return _PARSERS[parser_id]
    except KeyError as exc:
        msg = f"unknown test parser: {parser_id!r}"
        raise ValueError(msg) from exc


def registered_parsers() -> tuple[str, ...]:
    """返回所有已注册的解析器 ID（排序后）。"""
    return tuple(sorted(_PARSERS))
