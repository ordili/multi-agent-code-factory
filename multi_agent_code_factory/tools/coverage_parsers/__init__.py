"""Coverage 解析器包。"""

from multi_agent_code_factory.tools.coverage_parsers.registry import (
    get_coverage_parser,
    registered_coverage_parsers,
)

__all__ = ["get_coverage_parser", "registered_coverage_parsers"]
