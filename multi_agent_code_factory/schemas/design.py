"""DesignArtifact — Architect output."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

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


class DesignArtifact(BaseModel):
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
    transaction_constraints: list[dict[str, Any]] = Field(default_factory=list)
    notes: str | None = None
