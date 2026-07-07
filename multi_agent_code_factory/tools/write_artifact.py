"""Persist run artifacts under docs/runs/<task_id>/."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from multi_agent_code_factory._paths import run_dir
from multi_agent_code_factory.config import FactoryConfig, LoopLimits
from multi_agent_code_factory.profiles import ProfileConfig
from multi_agent_code_factory.schemas.run_meta import (
    BudgetUsage,
    DeployStatus,
    RunMeta,
    RunStatus,
)


def _iso_now() -> str:
    return datetime.now(tz=UTC).isoformat()


def profile_snapshot(profile: ProfileConfig) -> dict[str, Any]:
    return {
        "id": profile.id,
        "language": profile.language,
        "code_root": str(profile.code_root),
        "toolchain": profile.toolchain.model_dump(),
    }


def loop_limits_snapshot(limits: LoopLimits) -> dict[str, Any]:
    return limits.model_dump(mode="json")


class RunArtifactWriter:
    """Write JSON artifacts and maintain run_meta.json."""

    def __init__(self, task_id: str, *, base_dir: Path | None = None) -> None:
        self.task_id = task_id
        self.directory = (base_dir or run_dir(task_id)).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self._meta_path = self.directory / "run_meta.json"

    def write_model(self, filename: str, artifact: BaseModel) -> Path:
        path = self.directory / filename
        payload = artifact.model_dump(mode="json")
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return path

    def write_text(self, filename: str, content: str) -> Path:
        path = self.directory / filename
        path.write_text(content, encoding="utf-8")
        return path

    def read_meta(self) -> RunMeta | None:
        if not self._meta_path.is_file():
            return None
        data = json.loads(self._meta_path.read_text(encoding="utf-8"))
        return RunMeta.model_validate(data)

    def init_run_meta(
        self,
        profile: ProfileConfig,
        limits: LoopLimits,
        *,
        factory_config: FactoryConfig | None = None,
    ) -> RunMeta:
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
            task_id=self.task_id,
            profile=profile_snapshot(profile),
            loop_limits=loop_limits_snapshot(limits),
            deploy_status=DeployStatus.SKIPPED,
            status=RunStatus.RUNNING,
            budget=budget_usage,
            started_at=_iso_now(),
        )
        self.write_model("run_meta.json", meta)
        return meta

    def update_meta(self, **updates: Any) -> RunMeta:
        meta = self.read_meta()
        if meta is None:
            msg = f"run_meta.json not initialized for task {self.task_id!r}"
            raise FileNotFoundError(msg)
        payload = meta.model_dump(mode="json")
        payload.update(updates)
        updated = RunMeta.model_validate(payload)
        self.write_model("run_meta.json", updated)
        return updated

    def mark_stale(self, filenames: list[str]) -> None:
        if not filenames:
            return
        meta = self.read_meta()
        if meta is None:
            return
        current = list(meta.stale_artifacts or [])
        for name in filenames:
            if name not in current:
                current.append(name)
        self.update_meta(stale_artifacts=current)
