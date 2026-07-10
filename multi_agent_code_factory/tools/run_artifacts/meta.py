"""run_meta.json 读写与 stale 标记。"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from multi_agent_code_factory.config import FactoryConfig, LoopLimits
from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.schemas.run_meta import (
    BudgetUsage,
    DeployStatus,
    RunMeta,
    RunStatus,
)
from multi_agent_code_factory.tools.run_artifacts.snapshots import (
    loop_limits_snapshot,
    profile_snapshot,
)


def _iso_now() -> str:
    return datetime.now(tz=UTC).isoformat()


class RunMetaStore:
    """维护单次 run 的 ``run_meta.json``。"""

    def __init__(
        self,
        directory: Path,
        *,
        task_id: str,
        write_model: Callable[[str, BaseModel], Path],
    ) -> None:
        self._directory = directory
        self._task_id = task_id
        self._write_model = write_model
        self._meta_path = directory / "run_meta.json"

    def read(self) -> RunMeta | None:
        """读取 run_meta.json，不存在时返回 None。"""
        if not self._meta_path.is_file():
            return None
        data = json.loads(self._meta_path.read_text(encoding="utf-8"))
        return RunMeta.model_validate(data)

    def init(
        self,
        profile: ProfileConfig,
        limits: LoopLimits,
        *,
        factory_config: FactoryConfig | None = None,
        user_request: str | None = None,
    ) -> RunMeta:
        """初始化 run_meta.json 并标记运行状态为 RUNNING。"""
        budget_usage = None
        if factory_config and factory_config.budget:
            budget_usage = BudgetUsage(
                max_llm_calls=factory_config.budget.max_llm_calls,
                max_tokens=factory_config.budget.max_tokens,
                used_llm_calls=0,
                used_tokens=0,
            )
        meta = RunMeta(
            version="1",
            task_id=self._task_id,
            user_request=user_request,
            profile=profile_snapshot(profile),
            loop_limits=loop_limits_snapshot(limits),
            deploy_status=DeployStatus.SKIPPED,
            status=RunStatus.RUNNING,
            budget=budget_usage,
            started_at=_iso_now(),
        )
        self._write_model("run_meta.json", meta)
        return meta

    def prepare_continue(
        self,
        *,
        reentry_node: str,
        reset_loops: bool = True,
    ) -> RunMeta:
        """续跑前重置 budget / 触顶回路计数，并记录 continue 审计字段。"""
        meta = self.read()
        if meta is None:
            msg = f"run_meta.json not initialized for task {self._task_id!r}"
            raise FileNotFoundError(msg)

        limits = LoopLimits.model_validate(meta.loop_limits)
        updates: dict[str, Any] = {
            "status": RunStatus.RUNNING,
            "finished_at": None,
            "last_continue_at": _iso_now(),
            "last_reentry_node": reentry_node,
        }

        budget = meta.budget
        if budget is not None:
            updates["budget"] = budget.model_copy(
                update={"used_llm_calls": 0, "used_tokens": 0}
            )

        if reset_loops and meta.status == RunStatus.FAILED:
            impl_retry = meta.impl_retry_count
            if impl_retry >= limits.max_impl_retries:
                updates["impl_retry_count"] = 0
            design_rev = meta.design_revision_count
            if design_rev >= limits.max_design_revisions:
                updates["design_revision_count"] = 0
            spec_rev = meta.spec_revision_count
            if spec_rev >= limits.max_spec_revisions:
                updates["spec_revision_count"] = 0

        return self.update(**updates)

    def update(self, **updates: Any) -> RunMeta:
        """合并更新字段并写回 run_meta.json。"""
        meta = self.read()
        if meta is None:
            msg = f"run_meta.json not initialized for task {self._task_id!r}"
            raise FileNotFoundError(msg)
        payload = meta.model_dump(mode="json")
        payload.update(updates)
        updated = RunMeta.model_validate(payload)
        self._write_model("run_meta.json", updated)
        return updated

    def mark_stale(self, filenames: list[str]) -> None:
        """将指定产物文件名标记为 stale_artifacts（去重追加）。"""
        if not filenames:
            return
        meta = self.read()
        if meta is None:
            return
        current = list(meta.stale_artifacts or [])
        for name in filenames:
            if name not in current:
                current.append(name)
        self.update(stale_artifacts=current)
