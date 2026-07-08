"""Run 产物写入门面：组合文件存储、run_meta 与 LLM 用量审计。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel

from multi_agent_code_factory.agents.llm.usage import LlmCallUsage, LlmUsageLog
from multi_agent_code_factory.config import FactoryConfig, LoopLimits
from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.schemas.run_meta import RunMeta
from multi_agent_code_factory.tools.run_artifacts.meta import RunMetaStore
from multi_agent_code_factory.tools.run_artifacts.store import ArtifactFileStore
from multi_agent_code_factory.tools.run_artifacts.usage_log import LlmUsageStore


class RunArtifactWriter:
    """写入 JSON 产物并维护 run_meta.json 的运行记录器。"""

    def __init__(self, task_id: str, *, base_dir: Path | None = None) -> None:
        self._files = ArtifactFileStore(task_id, base_dir=base_dir)
        self.task_id = self._files.task_id
        self.directory = self._files.directory
        self._meta = RunMetaStore(
            self.directory,
            task_id=self.task_id,
            write_model=self._files.write_model,
        )
        self._usage = LlmUsageStore(
            self.directory,
            write_model=self._files.write_model,
        )

    @property
    def llm_usage_path(self) -> Path:
        """LLM 用量日志文件路径。"""
        return self._usage.path

    def write_model(self, filename: str, artifact: BaseModel) -> Path:
        return self._files.write_model(filename, artifact)

    def write_text(self, filename: str, content: str) -> Path:
        return self._files.write_text(filename, content)

    def read_meta(self) -> RunMeta | None:
        return self._meta.read()

    def init_run_meta(
        self,
        profile: ProfileConfig,
        limits: LoopLimits,
        *,
        factory_config: FactoryConfig | None = None,
    ) -> RunMeta:
        return self._meta.init(profile, limits, factory_config=factory_config)

    def update_meta(self, **updates: Any) -> RunMeta:
        return self._meta.update(**updates)

    def read_llm_usage(self) -> LlmUsageLog | None:
        return self._usage.read()

    def record_llm_usage(
        self,
        call: LlmCallUsage,
        *,
        provider: str,
        model: str,
    ) -> LlmUsageLog:
        return self._usage.record(call, provider=provider, model=model)

    def mark_stale(self, filenames: list[str]) -> None:
        self._meta.mark_stale(filenames)
