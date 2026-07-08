"""将运行产物持久化到 docs/runs/<task_id>/ 目录。"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from multi_agent_code_factory._paths import run_dir
from multi_agent_code_factory.agents.llm_usage import (
    LlmCallUsage,
    LlmUsageLog,
    LlmUsageTotals,
    merge_usage_totals,
)
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
    """将 Profile 配置序列化为可写入 run_meta 的快照字典。"""
    return {
        "id": profile.id,
        "language": profile.language,
        "code_root": str(profile.code_root),
        "toolchain": profile.toolchain.model_dump(),
    }


def loop_limits_snapshot(limits: LoopLimits) -> dict[str, Any]:
    """将循环限制配置序列化为 JSON 兼容字典。"""
    return limits.model_dump(mode="json")


class RunArtifactWriter:
    """写入 JSON 产物并维护 run_meta.json 的运行记录器。"""

    def __init__(self, task_id: str, *, base_dir: Path | None = None) -> None:
        self.task_id = task_id
        self.directory = (base_dir or run_dir(task_id)).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self._meta_path = self.directory / "run_meta.json"
        self._llm_usage_path = self.directory / "llm_usage.json"

    @property
    def llm_usage_path(self) -> Path:
        """LLM 用量日志文件路径。"""
        return self._llm_usage_path

    def write_model(self, filename: str, artifact: BaseModel) -> Path:
        """将 Pydantic 模型序列化为 JSON 并写入指定文件名。"""
        path = self.directory / filename
        payload = artifact.model_dump(mode="json")
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return path

    def write_text(self, filename: str, content: str) -> Path:
        """将纯文本内容写入指定文件名。"""
        path = self.directory / filename
        path.write_text(content, encoding="utf-8")
        return path

    def read_meta(self) -> RunMeta | None:
        """读取 run_meta.json，不存在时返回 None。"""
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
        """合并更新字段并写回 run_meta.json。"""
        meta = self.read_meta()
        if meta is None:
            msg = f"run_meta.json not initialized for task {self.task_id!r}"
            raise FileNotFoundError(msg)
        payload = meta.model_dump(mode="json")
        payload.update(updates)
        updated = RunMeta.model_validate(payload)
        self.write_model("run_meta.json", updated)
        return updated

    def read_llm_usage(self) -> LlmUsageLog | None:
        """读取 llm_usage.json，不存在时返回 None。"""
        if not self._llm_usage_path.is_file():
            return None
        data = json.loads(self._llm_usage_path.read_text(encoding="utf-8"))
        return LlmUsageLog.model_validate(data)

    def record_llm_usage(
        self,
        call: LlmCallUsage,
        *,
        provider: str,
        model: str,
    ) -> LlmUsageLog:
        """追加一次 LLM 调用记录并更新累计用量。"""
        existing = self.read_llm_usage()
        if existing is None:
            log = LlmUsageLog(
                version="1",
                provider=provider,
                model=model,
                calls=[call],
                totals=merge_usage_totals(LlmUsageTotals(), call),
            )
        else:
            log = existing.model_copy(
                update={
                    "provider": provider,
                    "model": model,
                    "calls": [*existing.calls, call],
                    "totals": merge_usage_totals(existing.totals, call),
                }
            )
        self.write_model("llm_usage.json", log)
        return log

    def mark_stale(self, filenames: list[str]) -> None:
        """将指定产物文件名标记为 stale_artifacts（去重追加）。"""
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
