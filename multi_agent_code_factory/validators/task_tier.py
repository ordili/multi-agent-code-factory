"""任务 tier 推断：决定部分 DES 规则是否要求非空字段。"""

from __future__ import annotations

from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.schemas.spec import SpecArtifact

_MIDDLEWARE_KINDS = frozenset({"db", "cache", "mq", "rpc", "api", "blockchain"})
_NON_PERSISTENT_STORAGE = frozenset(
    {"", "none", "memory", "in_memory", "in-memory", "stateless"}
)


def is_spec_non_trivial(spec: SpecArtifact) -> bool:
    """spec 是否超出 personal / best_effort / local_only 小任务档位（DES-011）。"""
    op = spec.operational_profile
    if op.user_scale.value != "personal":
        return True
    if op.high_concurrency:
        return True
    if op.performance.tier.value != "best_effort":
        return True
    return spec.consistency_profile.consistency_model.value != "local_only"


def _spec_context_storage(spec: SpecArtifact) -> str | None:
    storage = spec.context.get("storage")
    return (
        storage.strip().lower()
        if isinstance(storage, str) and storage.strip()
        else None
    )


def spec_implies_persistence(spec: SpecArtifact | None) -> bool:
    """spec 是否暗示需要持久化或表结构（DES-013）。"""
    if spec is None:
        return False
    storage = _spec_context_storage(spec)
    if storage and storage not in _NON_PERSISTENT_STORAGE:
        return True
    cp = spec.consistency_profile
    if cp.multi_writer:
        return True
    return cp.consistency_model.value != "local_only"


def design_has_middleware_deps(design: DesignArtifact) -> bool:
    return any(dep.kind in _MIDDLEWARE_KINDS for dep in design.external_dependencies)


def design_has_filesystem_deps(design: DesignArtifact) -> bool:
    return any(dep.kind == "filesystem" for dep in design.external_dependencies)


def design_has_table_columns(design: DesignArtifact) -> bool:
    for table in design.table_schemas:
        columns = table.get("columns") or []
        if columns:
            return True
    return False


def requires_table_schemas(
    design: DesignArtifact,
    spec: SpecArtifact | None = None,
) -> bool:
    """是否要求 ``table_schemas`` 非空（DES-013）。"""
    if design_has_table_columns(design):
        return True
    if design_has_middleware_deps(design):
        return True
    if design_has_filesystem_deps(design):
        return True
    return spec_implies_persistence(spec)


def requires_transaction_constraints(
    design: DesignArtifact,
    spec: SpecArtifact | None = None,
) -> bool:
    """是否要求 ``transaction_constraints`` 非空（DES-014）。"""
    if requires_table_schemas(design, spec):
        return True
    if design_has_filesystem_deps(design):
        return True
    return spec is not None and spec.consistency_profile.multi_writer


def is_stateless_design(
    design: DesignArtifact,
    spec: SpecArtifact | None = None,
) -> bool:
    """无持久化、无中间件、无表结构的小任务（如纯内存 CLI）。"""
    if design_has_table_columns(design):
        return False
    if design_has_middleware_deps(design) or design_has_filesystem_deps(design):
        return False
    return not spec_implies_persistence(spec)
