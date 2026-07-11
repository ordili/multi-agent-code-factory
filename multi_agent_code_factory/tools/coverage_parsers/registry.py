"""Coverage 输出解析器注册表。"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.schemas.test_report import CoverageReport
from multi_agent_code_factory.tools.coverage_parsers._types import CoverageCommandResult
from multi_agent_code_factory.tools.coverage_parsers.forge_coverage import (
    parse_forge_coverage,
)
from multi_agent_code_factory.tools.coverage_parsers.go_cover import parse_go_cover
from multi_agent_code_factory.tools.coverage_parsers.jacoco_xml import parse_jacoco_xml
from multi_agent_code_factory.tools.coverage_parsers.llvm_cov_json import (
    parse_llvm_cov_json,
)
from multi_agent_code_factory.tools.coverage_parsers.pytest_cov_json import (
    parse_pytest_cov_json,
)

CoverageParserFn = Callable[
    [CoverageCommandResult, ProfileConfig, Path],
    CoverageReport,
]

_PARSERS: dict[str, CoverageParserFn] = {
    "pytest_cov_json": parse_pytest_cov_json,
    "go_cover": parse_go_cover,
    "llvm_cov_json": parse_llvm_cov_json,
    "jacoco_xml": parse_jacoco_xml,
    "forge_coverage": parse_forge_coverage,
}


def get_coverage_parser(parser_id: str) -> CoverageParserFn:
    try:
        return _PARSERS[parser_id]
    except KeyError as exc:
        msg = f"unknown coverage parser: {parser_id!r}"
        raise ValueError(msg) from exc


def registered_coverage_parsers() -> tuple[str, ...]:
    return tuple(sorted(_PARSERS))
