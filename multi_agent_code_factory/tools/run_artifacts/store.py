"""Run 目录 JSON / 文本产物写入。"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from multi_agent_code_factory._paths import run_dir


class ArtifactFileStore:
    """写入 ``docs/runs/<task_id>/`` 下的 JSON 与文本产物。"""

    def __init__(self, task_id: str, *, base_dir: Path | None = None) -> None:
        self.task_id = task_id
        self.directory = (base_dir or run_dir(task_id)).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)

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
