"""设计产物（Architect 输出）的 Pydantic 模型。"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, ClassVar

from pydantic import BaseModel, Field, model_validator

from multi_agent_code_factory.schemas._base import ARTIFACT_VERSION


class DesignStatus(StrEnum):
    DRAFT = "draft"
    IN_REVIEW = "in-review"
    APPROVED = "approved"


class DiagramKind(StrEnum):
    SEQUENCE = "sequence"
    FLOWCHART = "flowchart"
    CLASS = "class"
    CONTEXT = "context"
    DEPLOYMENT = "deployment"


class ModuleSpec(BaseModel):
    name: str
    path: str
    responsibility: str
    code_domain: str
    depends_on: list[str] = Field(default_factory=list)


class ExternalDependency(BaseModel):
    name: str
    kind: str
    purpose: str
    code_domain: str | None = None
    technology: str | None = None
    endpoint: str | None = None
    criticality: str | None = None
    failure_behavior: str | None = None


class ErrorCatalogItem(BaseModel):
    code: str
    when: str | None = None
    message: str | None = None
    retryable: bool | None = None
    recovery: str | None = None


class DevTask(BaseModel):
    id: str
    path: str
    description: str
    depends_on: list[str] = Field(default_factory=list)
    covers: list[str] = Field(default_factory=list)


class DiagramRef(BaseModel):
    path: str
    kind: DiagramKind
    title: str | None = None


def _normalize_diagram_kind(kind: Any) -> Any:
    if not isinstance(kind, str):
        return kind
    normalized = kind.strip().lower().replace("_", " ")
    aliases = {
        "sequencediagram": "sequence",
        "sequence diagram": "sequence",
        "flowchart lr": "flowchart",
        "flowchart td": "flowchart",
        "flowchart": "flowchart",
        "classdiagram": "class",
        "class diagram": "class",
        "deploymentdiagram": "deployment",
        "deployment diagram": "deployment",
    }
    if normalized in aliases:
        return aliases[normalized]
    if normalized.startswith("sequence"):
        return "sequence"
    if normalized.startswith("flowchart") or normalized.startswith("flow chart"):
        return "flowchart"
    if normalized.startswith("class"):
        return "class"
    if normalized.startswith("deployment"):
        return "deployment"
    if normalized.startswith("context"):
        return "context"
    return kind


def _coerce_error_catalog(value: Any) -> list[Any]:
    normalized: list[Any] = []
    for item in _coerce_list(value):
        if isinstance(item, dict):
            patched = dict(item)
            if "code" not in patched and isinstance(patched.get("error_code"), str):
                patched["code"] = patched["error_code"]
            normalized.append(patched)
        else:
            normalized.append(item)
    return normalized


def _coerce_diagrams(value: Any) -> list[Any]:
    normalized: list[Any] = []
    for item in _coerce_list(value):
        if isinstance(item, dict):
            patched = dict(item)
            if "kind" in patched:
                patched["kind"] = _normalize_diagram_kind(patched["kind"])
            normalized.append(patched)
        else:
            normalized.append(item)
    return normalized


def _coerce_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, (dict, str)):
        return [value]
    return [value]


def _coerce_str_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [value]
    return [value]


_DESIGN_OBJECT_LIST_FIELDS = (
    "modules",
    "external_dependencies",
    "error_catalog",
    "dev_tasks",
    "diagrams",
    "interfaces",
    "data_model",
    "table_schemas",
    "traceability",
    "file_plan",
    "test_cases",
    "transaction_constraints",
)


def _merge_top_level_aliases(payload: dict[str, Any]) -> None:
    """Merge LLM top-level aliases into canonical nested paths (in-place)."""
    architecture = dict(payload.get("architecture") or {})
    architecture_updated = False

    if "decisions" in payload:
        decisions = payload.pop("decisions")
        if decisions and not architecture.get("decisions"):
            architecture["decisions"] = decisions
            architecture_updated = True

    if "code_delta" in payload:
        code_delta = payload.pop("code_delta")
        if code_delta and not architecture.get("code_delta"):
            architecture["code_delta"] = code_delta
            architecture_updated = True

    if architecture_updated or payload.get("architecture") is not None:
        payload["architecture"] = architecture

    if "test_strategy" in payload:
        test_strategy = payload.pop("test_strategy")
        if test_strategy:
            cross_cutting = dict(payload.get("cross_cutting") or {})
            cross_cutting.setdefault("test_strategy", test_strategy)
            payload["cross_cutting"] = cross_cutting


def coerce_design_payload(data: Any) -> Any:
    """Normalize common LLM JSON shapes before DesignArtifact validation."""
    if not isinstance(data, dict):
        return data
    payload = dict(data)
    payload.setdefault("version", "1")
    payload.setdefault("revision", 1)
    _merge_top_level_aliases(payload)
    for key in ("design_goals", "non_goals", "hitl_flags"):
        if key in payload:
            payload[key] = _coerce_str_list(payload[key])
    for key in _DESIGN_OBJECT_LIST_FIELDS:
        if key in payload:
            if key == "diagrams":
                payload[key] = _coerce_diagrams(payload[key])
            elif key == "error_catalog":
                payload[key] = _coerce_error_catalog(payload[key])
            else:
                payload[key] = _coerce_list(payload[key])
    if "non_functional" in payload and isinstance(payload["non_functional"], dict):
        payload["non_functional"] = [payload["non_functional"]]
    return payload


class DesignArtifact(BaseModel):
    __llm_example__: ClassVar[dict[str, Any]] = {
        "version": "1",
        "spec_ref": "CLI Todo App",
        "revision": 1,
        "summary": "CLI + JSON store",
        "modules": [
            {
                "name": "TodoCLI",
                "path": "src/cli.py",
                "responsibility": "CLI commands",
                "code_domain": "CLI",
            }
        ],
        "dev_tasks": [
            {
                "id": "T1",
                "path": "src/todo_store.py",
                "description": "JSON load/save",
                "depends_on": [],
                "covers": ["AC-1"],
            }
        ],
        "external_dependencies": [
            {
                "name": "todos.json",
                "kind": "filesystem",
                "purpose": "persistence",
                "code_domain": "STORE",
            }
        ],
    }

    version: ARTIFACT_VERSION
    spec_ref: str
    revision: int = Field(ge=1)
    supersedes_revision: int | None = None
    status: DesignStatus | None = None
    summary: str | None = None
    background: str | None = None
    design_goals: list[str] = Field(default_factory=list)
    non_goals: list[str] = Field(default_factory=list)
    modules: list[ModuleSpec] = Field(default_factory=list)
    external_dependencies: list[ExternalDependency] = Field(default_factory=list)
    error_catalog: list[ErrorCatalogItem] = Field(default_factory=list)
    dev_tasks: list[DevTask] = Field(default_factory=list)
    diagrams: list[DiagramRef] = Field(default_factory=list)
    hitl_flags: list[str] = Field(default_factory=list)
    context_view: dict[str, Any] | None = None
    architecture: dict[str, Any] | None = None
    interfaces: list[dict[str, Any]] = Field(default_factory=list)
    data_model: list[dict[str, Any]] = Field(default_factory=list)
    table_schemas: list[dict[str, Any]] = Field(default_factory=list)
    traceability: list[dict[str, Any]] = Field(default_factory=list)
    file_plan: list[dict[str, Any]] = Field(default_factory=list)
    test_cases: list[dict[str, Any]] = Field(default_factory=list)
    cross_cutting: dict[str, Any] | None = None
    non_functional: list[dict[str, Any]] | None = None
    transaction_constraints: list[dict[str, Any]] = Field(default_factory=list)
    notes: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _coerce_llm_payload(cls, data: Any) -> Any:
        return coerce_design_payload(data)
