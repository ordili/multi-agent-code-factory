"""从 run 目录水合 PipelineState（支持 stale 过滤）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from multi_agent_code_factory.log import get_logger
from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.schemas.dev_manifest import DevManifest
from multi_agent_code_factory.schemas.hitl import HitlDecision
from multi_agent_code_factory.schemas.review import ReviewReport
from multi_agent_code_factory.schemas.run_meta import RunMeta
from multi_agent_code_factory.schemas.spec import SpecArtifact
from multi_agent_code_factory.schemas.test_report import TestReport
from multi_agent_code_factory.schemas.validation_report import ValidationReport
from multi_agent_code_factory.state import PipelineState

logger = get_logger("artifact_loader")

_ARTIFACT_FILES: dict[str, str] = {
    "spec.json": "spec",
    "spec_validation.json": "spec_validation",
    "design.json": "design",
    "design_validation.json": "design_validation",
    "dev_manifest.json": "dev_manifest",
    "test_report.json": "test_report",
    "review.json": "review",
    "hitl.json": "hitl",
}

ARTIFACT_MODEL_BY_FIELD: dict[str, type[BaseModel]] = {
    "spec": SpecArtifact,
    "spec_validation": ValidationReport,
    "design": DesignArtifact,
    "design_validation": ValidationReport,
    "dev_manifest": DevManifest,
    "test_report": TestReport,
    "review": ReviewReport,
    "hitl": HitlDecision,
}

TModel = TypeVar("TModel", bound=BaseModel)


def is_stale(filename: str, meta: RunMeta) -> bool:
    """判断产物是否已标记为 stale。"""
    return filename in (meta.stale_artifacts or [])


def artifact_available(run_dir: Path, filename: str, meta: RunMeta) -> bool:
    """磁盘存在且未标记 stale。"""
    return (run_dir / filename).is_file() and not is_stale(filename, meta)


def load_artifact_json(
    run_dir: Path,
    filename: str,
    model: type[TModel],
) -> TModel | None:
    """读取单个 JSON 产物；不存在时返回 None。"""
    path = run_dir / filename
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return model.model_validate(data)


def _resolve_user_request(meta: RunMeta, spec: SpecArtifact | None) -> str:
    if meta.user_request:
        return meta.user_request
    if spec is not None:
        parts = [spec.title, spec.summary]
        fallback = " ".join(part for part in parts if part).strip()
        if fallback:
            logger.warning(
                "run_meta.user_request missing for task %s; using spec fallback",
                meta.task_id,
            )
            return fallback
    return ""


def hydrate_state(run_dir: Path, meta: RunMeta) -> PipelineState:
    """从 run 目录与 run_meta 组装 PipelineState（跳过 stale 产物）。"""
    fields: dict[str, Any] = {
        "task_id": meta.task_id,
        "impl_retry_count": meta.impl_retry_count,
        "design_revision_count": meta.design_revision_count,
        "spec_revision_count": meta.spec_revision_count,
    }

    for filename, field_name in _ARTIFACT_FILES.items():
        if is_stale(filename, meta):
            continue
        model_cls = ARTIFACT_MODEL_BY_FIELD[field_name]
        loaded = load_artifact_json(run_dir, filename, model_cls)
        if loaded is not None:
            fields[field_name] = loaded

    spec = fields.get("spec")
    spec_model = spec if isinstance(spec, SpecArtifact) else None
    fields["user_request"] = _resolve_user_request(meta, spec_model)

    return PipelineState(**fields)
