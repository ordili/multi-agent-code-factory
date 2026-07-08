"""Budget guard tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from multi_agent_code_factory.agents.llm.budget.guard import check_llm_budget
from multi_agent_code_factory.config import BudgetConfig, FactoryConfig, LoopLimits
from multi_agent_code_factory.agents.llm.budget.errors import LlmBudgetExceededError
from multi_agent_code_factory.profile_config import load_profile
from multi_agent_code_factory.tools.run_artifacts import RunArtifactWriter


def test_check_llm_budget_raises_when_call_limit_reached(tmp_path: Path) -> None:
    profile = load_profile("python")
    writer = RunArtifactWriter("budget-test", base_dir=tmp_path)
    factory_config = FactoryConfig(
        loop_limits=LoopLimits(),
        budget=BudgetConfig(max_llm_calls=1),
    )
    writer.init_run_meta(profile, LoopLimits(), factory_config=factory_config)
    writer.update_meta(
        budget={
            "max_llm_calls": 1,
            "used_llm_calls": 1,
            "used_tokens": 0,
        }
    )
    with pytest.raises(LlmBudgetExceededError, match="call budget exceeded"):
        check_llm_budget(writer, factory_config)
