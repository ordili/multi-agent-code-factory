"""工厂级配置：循环上限、预算与策略加载。"""

from __future__ import annotations

import os
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

from multi_agent_code_factory._paths import default_policy_path, repo_root
from multi_agent_code_factory.schemas.task_batch import TaskBatchConfig


class OnLimitExceeded(StrEnum):
    """循环次数用尽时的处置方式。"""

    FAIL = "fail"
    ESCALATION_HITL = "escalation_hitl"


class LoopLimits(BaseModel):
    """实现 / 设计 / 规格各阶段的最大重试与升环次数。"""

    max_impl_retries: int = Field(default=3, ge=0)
    max_design_revisions: int = Field(default=2, ge=0)
    max_prd_revisions: int = Field(default=1, ge=0)
    on_limit_exceeded: OnLimitExceeded = OnLimitExceeded.FAIL

    @field_validator("on_limit_exceeded", mode="before")
    @classmethod
    def _coerce_on_limit_exceeded(cls, value: object) -> object:
        if isinstance(value, str):
            return value.lower()
        return value


class BudgetConfig(BaseModel):
    """单次运行的 LLM 调用与 token 预算上限。"""

    max_llm_calls: int | None = Field(default=None, ge=1)
    max_tokens: int | None = Field(default=None, ge=1)


class FactoryConfig(BaseModel):
    """从 autonomy_policy.yaml 解析的工厂运行时配置。"""

    loop_limits: LoopLimits = Field(default_factory=LoopLimits)
    max_hitl_rounds: int = Field(default=5, ge=0)
    budget: BudgetConfig | None = None
    task_batch: TaskBatchConfig = Field(default_factory=TaskBatchConfig)

    @model_validator(mode="before")
    @classmethod
    def _fold_on_limit_exceeded(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        payload = dict(data)
        loop_raw = dict(payload.get("loop_limits") or {})
        if "on_limit_exceeded" in payload:
            loop_raw.setdefault("on_limit_exceeded", payload.pop("on_limit_exceeded"))
        payload["loop_limits"] = loop_raw
        return payload

    @property
    def on_limit_exceeded(self) -> OnLimitExceeded:
        return self.loop_limits.on_limit_exceeded


def _read_policy_file(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    if not isinstance(loaded, dict):
        msg = f"expected mapping in policy file: {path}"
        raise ValueError(msg)
    section = loaded.get("multi_agent_code_factory")
    if not isinstance(section, dict):
        msg = f"missing multi_agent_code_factory section in {path}"
        raise ValueError(msg)
    return section


def _env_int(name: str) -> int | None:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return None
    return int(raw)


def _apply_env_overrides(config: FactoryConfig) -> FactoryConfig:
    updates: dict[str, Any] = {}
    loop_updates: dict[str, int] = {}

    for field_name, env_name in (
        ("max_impl_retries", "FACTORY_MAX_IMPL_RETRIES"),
        ("max_design_revisions", "FACTORY_MAX_DESIGN_REVISIONS"),
        ("max_prd_revisions", "FACTORY_MAX_PRD_REVISIONS"),
    ):
        value = _env_int(env_name)
        if value is not None:
            loop_updates[field_name] = value

    if loop_updates:
        updates["loop_limits"] = config.loop_limits.model_copy(update=loop_updates)

    hitl_rounds = _env_int("FACTORY_MAX_HITL_ROUNDS")
    if hitl_rounds is not None:
        updates["max_hitl_rounds"] = hitl_rounds

    on_limit = os.environ.get("FACTORY_ON_LIMIT_EXCEEDED")
    if on_limit:
        base = updates.get("loop_limits", config.loop_limits)
        if not isinstance(base, LoopLimits):
            base = config.loop_limits
        updates["loop_limits"] = base.model_copy(
            update={"on_limit_exceeded": on_limit.lower()}
        )

    budget_updates: dict[str, int] = {}
    max_llm = _env_int("FACTORY_MAX_LLM_CALLS")
    if max_llm is not None:
        budget_updates["max_llm_calls"] = max_llm
    max_tokens = _env_int("FACTORY_MAX_TOKENS")
    if max_tokens is not None:
        budget_updates["max_tokens"] = max_tokens
    if budget_updates:
        base = config.budget or BudgetConfig()
        updates["budget"] = base.model_copy(update=budget_updates)

    task_batch_updates: dict[str, object] = {}
    if (enabled := os.environ.get("FACTORY_TASK_BATCH_ENABLED")) is not None:
        task_batch_updates["enabled"] = enabled.lower() in {"1", "true", "yes"}
    threshold = _env_int("FACTORY_TASK_BATCH_THRESHOLD")
    if threshold is not None:
        task_batch_updates["threshold"] = threshold
    if task_batch_updates:
        updates["task_batch"] = config.task_batch.model_copy(update=task_batch_updates)

    if not updates:
        return config
    return config.model_copy(update=updates)


def _apply_cli_overrides(
    config: FactoryConfig,
    *,
    max_impl_retries: int | None = None,
    max_design_revisions: int | None = None,
    max_prd_revisions: int | None = None,
    max_hitl_rounds: int | None = None,
    on_limit_exceeded: str | None = None,
) -> FactoryConfig:
    updates: dict[str, Any] = {}
    loop_updates: dict[str, int] = {}
    if max_impl_retries is not None:
        loop_updates["max_impl_retries"] = max_impl_retries
    if max_design_revisions is not None:
        loop_updates["max_design_revisions"] = max_design_revisions
    if max_prd_revisions is not None:
        loop_updates["max_prd_revisions"] = max_prd_revisions
    if loop_updates:
        updates["loop_limits"] = config.loop_limits.model_copy(update=loop_updates)
    if max_hitl_rounds is not None:
        updates["max_hitl_rounds"] = max_hitl_rounds
    if on_limit_exceeded is not None:
        base = updates.get("loop_limits", config.loop_limits)
        if not isinstance(base, LoopLimits):
            base = config.loop_limits
        updates["loop_limits"] = base.model_copy(
            update={"on_limit_exceeded": on_limit_exceeded.lower()}
        )
    if not updates:
        return config
    return config.model_copy(update=updates)


def load_factory_config(
    *,
    policy_path: Path | None = None,
    max_impl_retries: int | None = None,
    max_design_revisions: int | None = None,
    max_prd_revisions: int | None = None,
    max_hitl_rounds: int | None = None,
    on_limit_exceeded: str | None = None,
) -> FactoryConfig:
    """加载工厂配置：YAML 默认 → FACTORY_* 环境变量 → CLI 参数覆盖。"""
    path = policy_path or default_policy_path()
    section = _read_policy_file(path)
    config = FactoryConfig.model_validate(section)
    config = _apply_env_overrides(config)
    return _apply_cli_overrides(
        config,
        max_impl_retries=max_impl_retries,
        max_design_revisions=max_design_revisions,
        max_prd_revisions=max_prd_revisions,
        max_hitl_rounds=max_hitl_rounds,
        on_limit_exceeded=on_limit_exceeded,
    )


def policy_path_for_repo(root: Path | None = None) -> Path:
    return (root or repo_root()) / "config" / "autonomy_policy.yaml"
