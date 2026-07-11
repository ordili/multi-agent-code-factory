"""设计产物（Architect 输出）的 Pydantic 模型。"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, ClassVar

from pydantic import BaseModel, Field, model_validator

from multi_agent_code_factory.schemas._base import ARTIFACT_VERSION
from multi_agent_code_factory.schemas.llm_prompt_shape import LlmPromptShape


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


class ExternalSystemRef(BaseModel):
    name: str
    description: str | None = None
    kind: str | None = None


class ContextView(BaseModel):
    actors: list[str] = Field(default_factory=list)
    external_systems: list[ExternalSystemRef | str] = Field(default_factory=list)
    boundaries: list[str] = Field(default_factory=list)
    notes: str | None = None


class FieldDef(BaseModel):
    name: str
    type: str
    required: bool | None = None
    description: str | None = None
    notes: str | None = None
    nullable: bool | None = None
    pk: bool | None = None
    unique: bool | None = None


class DataEntity(BaseModel):
    name: str
    description: str | None = None
    storage: str | None = None
    fields: list[FieldDef] = Field(default_factory=list)
    notes: str | None = None


class ParamSpec(BaseModel):
    name: str
    type: str
    required: bool
    description: str = ""
    default: Any | None = None
    schema_ref: str | None = None


class OperationSpec(BaseModel):
    name: str
    summary: str
    description: str | None = None
    inputs: list[ParamSpec] = Field(default_factory=list)
    outputs: list[ParamSpec] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    http: Any | None = None
    idempotent: bool | None = None
    notes: str | None = None


class InterfaceSpec(BaseModel):
    name: str
    module_ref: str
    file: str = ""
    protocol: str = "internal"
    description: str | None = None
    operations: list[OperationSpec] = Field(default_factory=list)
    code_domain: str | None = None


class ColumnDef(BaseModel):
    name: str
    type: str
    nullable: bool
    description: str
    pk: bool | None = None
    unique: bool | None = None


class IndexDef(BaseModel):
    name: str
    columns: list[str] = Field(default_factory=list)
    unique: bool | None = None
    type: str | None = None
    purpose: str


class AuditPolicy(BaseModel):
    require_created_at: bool | None = None
    require_updated_at: bool | None = None
    require_version: bool | None = None
    notes: str | None = None


class TableSchema(BaseModel):
    name: str
    storage: str
    columns: list[ColumnDef] = Field(default_factory=list)
    indexes: list[IndexDef] = Field(default_factory=list)
    audit_policy: AuditPolicy | None = None
    notes: str | None = None


class TransactionConstraint(BaseModel):
    id: str
    scope: str
    boundary: str
    isolation: str | None = None
    idempotency: str | None = None
    consistency_ref: str | None = None
    notes: str | None = None


class AdrDecision(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DEFERRED = "deferred"


class AdrItem(BaseModel):
    option: str
    decision: AdrDecision | str
    id: str | None = None
    rationale: str | None = None


class CodeDelta(BaseModel):
    summary: str
    baseline_ref: str | None = None
    notes: str | None = None


class ArchitectureOverview(BaseModel):
    solution_strategy: str
    style: str | None = None
    decisions: list[AdrItem] = Field(default_factory=list)
    code_delta: CodeDelta | None = None


class FilePlanAction(StrEnum):
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"


class FilePlanItem(BaseModel):
    path: str
    action: FilePlanAction | str
    reason: str | None = None


class TestCaseKind(StrEnum):
    HAPPY = "happy"
    NEGATIVE = "negative"
    BOUNDARY = "boundary"


class SemanticEvidence(BaseModel):
    constraint_ref: str
    equivalence_class: str | None = None
    proves_dimensions: list[str] = Field(default_factory=list)


class TestCase(BaseModel):
    id: str
    kind: TestCaseKind | str
    title: str | None = None
    steps: str | None = None
    expected: str | None = None
    covers: list[str] = Field(default_factory=list)
    error_code: str | None = None
    description: str | None = None
    semantic_evidence: SemanticEvidence | None = None


class TraceRow(BaseModel):
    spec_ref_id: str | None = None
    spec_ref_kind: str | None = None
    design_ref: str | None = None
    feature_id: str | None = None


class NfrSpec(BaseModel):
    metric: str
    target: str
    id: str | None = None
    verification: str | None = None
    notes: str | None = None


class TestStrategy(BaseModel):
    approach: str
    paths: list[str] = Field(default_factory=list)
    notes: str | None = None


def model_field(obj: Any, key: str, default: Any = None) -> Any:
    """Read a field from a Pydantic model or legacy dict payload."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


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


def _coerce_data_model(value: Any) -> list[Any]:
    normalized: list[Any] = []
    for item in _coerce_list(value):
        if isinstance(item, dict):
            patched = dict(item)
            if not patched.get("fields"):
                if patched.get("attributes"):
                    patched["fields"] = patched["attributes"]
                elif patched.get("columns"):
                    patched["fields"] = patched["columns"]
            normalized.append(patched)
        else:
            normalized.append(item)
    return normalized


def _coerce_traceability(value: Any) -> list[Any]:
    normalized: list[Any] = []
    for item in _coerce_list(value):
        if isinstance(item, dict):
            patched = dict(item)
            if not patched.get("spec_ref_id") and patched.get("feature_id"):
                patched["spec_ref_id"] = patched["feature_id"]
            if not patched.get("design_ref"):
                for legacy in ("design_element", "design_ref_id"):
                    if patched.get(legacy):
                        patched["design_ref"] = patched[legacy]
                        break
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

    if isinstance(payload.get("architecture"), dict):
        arch = dict(payload["architecture"])
        if not str(arch.get("solution_strategy", "")).strip():
            arch.setdefault("solution_strategy", "Layered implementation per modules[]")
            payload["architecture"] = arch

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
            elif key == "data_model":
                payload[key] = _coerce_data_model(payload[key])
            elif key == "traceability":
                payload[key] = _coerce_traceability(payload[key])
            else:
                payload[key] = _coerce_list(payload[key])
    if "non_functional" in payload and isinstance(payload["non_functional"], dict):
        payload["non_functional"] = [payload["non_functional"]]
    return payload


class DesignArtifact(BaseModel):
    LLM_PROMPT_SHAPE: ClassVar[LlmPromptShape] = LlmPromptShape(
        json_shape={
            "version": "1",
            "spec_ref": "<from spec.title>",
            "revision": 1,
            "summary": "无状态命令行工具示例（按实际 spec 替换）",
            "background": "面向终端用户的本地 CLI；无持久化、无联网，单次求值交付。",
            "non_goals": ["Web UI", "持久化"],
            "design_goals": [
                "CLI 解析表达式并输出求值结果（FEAT-1）",
                "非法输入与除零有明确错误提示（US-4）",
            ],
            "context_view": {"actors": ["User", "CliEntry"]},
            "architecture": {
                "solution_strategy": "CLI 解析参数并调用核心模块",
                "code_delta": {"summary": "greenfield"},
            },
            "cross_cutting": {},
            "modules": [
                {
                    "name": "CliEntry",
                    "path": "src/cli.py",
                    "responsibility": "命令行入口与参数解析",
                    "code_domain": "CLI",
                },
                {
                    "name": "CalcCore",
                    "path": "src/calc_core.py",
                    "responsibility": "领域计算逻辑",
                    "code_domain": "CALC",
                },
            ],
            "interfaces": [
                {
                    "name": "CliEntry API",
                    "module_ref": "CliEntry",
                    "operations": [
                        {
                            "name": "run",
                            "summary": "Parse argv and dispatch",
                            "inputs": [
                                {
                                    "name": "argv",
                                    "type": "list[str]",
                                    "required": True,
                                    "description": "CLI arguments",
                                }
                            ],
                            "outputs": [
                                {
                                    "name": "exit_code",
                                    "type": "int",
                                    "required": True,
                                }
                            ],
                            "errors": ["ERR-CALC-001"],
                        }
                    ],
                },
                {
                    "name": "CalcCore API",
                    "module_ref": "CalcCore",
                    "operations": [
                        {
                            "name": "evaluate",
                            "summary": "Core operation",
                            "inputs": [
                                {
                                    "name": "operands",
                                    "type": "list[float]",
                                    "required": True,
                                }
                            ],
                            "outputs": [
                                {
                                    "name": "result",
                                    "type": "float",
                                    "required": True,
                                }
                            ],
                            "errors": ["ERR-CALC-001"],
                        }
                    ],
                },
            ],
            "diagrams": [],
            "dev_tasks": [
                {
                    "id": "T1",
                    "path": "src/calc_core.py",
                    "description": "Core logic",
                    "depends_on": [],
                    "covers": ["AC-1", "AC-2", "FEAT-1"],
                },
                {
                    "id": "T2",
                    "path": "src/cli.py",
                    "description": "CLI entry",
                    "depends_on": ["T1"],
                    "covers": ["AC-1"],
                },
            ],
            "external_dependencies": [
                {
                    "name": "none",
                    "kind": "none",
                    "purpose": "无外部持久化或第三方服务",
                }
            ],
            "non_functional": [],
            "transaction_constraints": [],
            "data_model": [],
            "table_schemas": [],
            "file_plan": [],
            "error_catalog": [
                {
                    "code": "ERR-CALC-001",
                    "when": "invalid input",
                    "message": "无效输入",
                    "retryable": False,
                }
            ],
            "test_cases": [
                {
                    "id": "TC-HAP-CALC-001",
                    "kind": "happy",
                    "title": "乘法紧凑写法",
                    "description": 'input: "7*8"',
                    "expected": "56",
                    "covers": ["AC-1", "SEM-IN-1"],
                    "semantic_evidence": {
                        "constraint_ref": "SEM-IN-1",
                        "equivalence_class": "multiply-compact",
                        "proves_dimensions": [
                            "operand_count",
                            "operator_count",
                            "operator_set",
                        ],
                    },
                },
                {
                    "id": "TC-HAP-CALC-002",
                    "kind": "happy",
                    "title": "乘法空格写法",
                    "description": 'input: "7 * 8"',
                    "expected": "56",
                    "covers": ["AC-1", "SEM-IN-1"],
                    "semantic_evidence": {
                        "constraint_ref": "SEM-IN-1",
                        "equivalence_class": "multiply-spaced",
                        "proves_dimensions": [
                            "operand_count",
                            "operator_count",
                            "operator_set",
                        ],
                    },
                },
                {
                    "id": "TC-NEG-CALC-001",
                    "kind": "negative",
                    "title": "非法输入",
                    "description": 'input: "1+2+3"',
                    "error_code": "ERR-CALC-001",
                    "covers": ["AC-2", "SEM-IN-1"],
                },
                {
                    "id": "TC-BND-CALC-001",
                    "kind": "boundary",
                    "title": "边界值",
                    "covers": ["AC-2"],
                },
            ],
            "traceability": [
                {
                    "spec_ref_id": "FEAT-1",
                    "spec_ref_kind": "FEAT",
                    "design_ref": "CalcCore",
                },
                {
                    "spec_ref_id": "AC-1",
                    "spec_ref_kind": "AC",
                    "design_ref": "CliEntry",
                },
                {
                    "spec_ref_id": "AC-2",
                    "spec_ref_kind": "AC",
                    "design_ref": "CalcCore",
                },
            ],
        },
    )

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
    context_view: ContextView | None = None
    architecture: ArchitectureOverview | None = None
    interfaces: list[InterfaceSpec] = Field(default_factory=list)
    data_model: list[DataEntity] = Field(default_factory=list)
    table_schemas: list[TableSchema] = Field(default_factory=list)
    traceability: list[TraceRow] = Field(default_factory=list)
    file_plan: list[FilePlanItem] = Field(default_factory=list)
    test_cases: list[TestCase] = Field(default_factory=list)
    cross_cutting: dict[str, Any] | None = None
    non_functional: list[NfrSpec] | None = None
    transaction_constraints: list[TransactionConstraint] = Field(default_factory=list)
    notes: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _coerce_llm_payload(cls, data: Any) -> Any:
        return coerce_design_payload(data)
