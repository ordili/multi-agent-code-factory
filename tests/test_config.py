from __future__ import annotations

import pytest
from multi_agent_code_factory._paths import repo_root
from multi_agent_code_factory.config import (
    FactoryConfig,
    OnLimitExceeded,
    load_factory_config,
    policy_path_for_repo,
)


def test_load_factory_config_defaults() -> None:
    config = load_factory_config()
    assert config.loop_limits.max_impl_retries == 3
    assert config.loop_limits.max_design_revisions == 2
    assert config.loop_limits.max_spec_revisions == 1
    assert config.max_hitl_rounds == 5
    assert config.on_limit_exceeded == OnLimitExceeded.FAIL


def test_load_factory_config_cli_override() -> None:
    config = load_factory_config(max_impl_retries=7)
    assert config.loop_limits.max_impl_retries == 7
    assert config.loop_limits.max_design_revisions == 2


def test_load_factory_config_env_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FACTORY_MAX_IMPL_RETRIES", "9")
    monkeypatch.setenv("FACTORY_ON_LIMIT_EXCEEDED", "escalation_hitl")
    config = load_factory_config()
    assert config.loop_limits.max_impl_retries == 9
    assert config.on_limit_exceeded == OnLimitExceeded.ESCALATION_HITL


def test_cli_override_beats_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FACTORY_MAX_IMPL_RETRIES", "9")
    config = load_factory_config(max_impl_retries=2)
    assert config.loop_limits.max_impl_retries == 2


def test_policy_path_for_repo() -> None:
    path = policy_path_for_repo(repo_root())
    assert path.name == "autonomy_policy.yaml"
    assert path.is_file()


def test_factory_config_round_trip() -> None:
    config = FactoryConfig.model_validate(
        {
            "loop_limits": {
                "max_impl_retries": 1,
                "max_design_revisions": 2,
                "max_spec_revisions": 3,
            },
            "budget": {"max_llm_calls": 10},
        }
    )
    assert config.budget is not None
    assert config.budget.max_llm_calls == 10
