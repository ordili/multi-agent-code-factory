"""Agent 产物 Live 模式后处理。"""

from multi_agent_code_factory.agents.normalizers.design import normalize_design
from multi_agent_code_factory.agents.normalizers.design_enrichment import (
    enrich_design_for_validation,
)
from multi_agent_code_factory.agents.normalizers.prd import normalize_prd

__all__ = [
    "enrich_design_for_validation",
    "normalize_design",
    "normalize_prd",
]
