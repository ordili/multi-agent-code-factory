"""DES 规则触发条件：决定部分校验是否要求非空字段或章节。"""

from __future__ import annotations

import re

from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.schemas.spec import SpecArtifact

_NONLINEAR_US_RE = re.compile(
    r"如果|否则|当.+时|异常|失败|重试|补偿|并发|异步|回调|超时|回滚|"
    r"分支|随后|然后|并且|之后|先.+再|下单|支付|结算|对账|库存|秒杀"
)

_MIDDLEWARE_KINDS = frozenset({"db", "cache", "mq", "rpc", "api", "blockchain"})
_NON_PERSISTENT_STORAGE = frozenset(
    {"", "none", "memory", "in_memory", "in-memory", "stateless"}
)


def spec_requires_non_functional(spec: SpecArtifact) -> bool:
    """spec 是否触发 DES-011（传导表：operational_profile 含非 trivial NFR 信号）。"""
    op = spec.operational_profile
    perf = op.performance
    if any(
        str(value).strip()
        for value in (perf.latency, perf.throughput, perf.availability)
        if value is not None
    ):
        return True
    if op.user_scale.value != "personal":
        return True
    if op.high_concurrency:
        return True
    return perf.tier.value != "best_effort"


def _spec_context_storage(spec: SpecArtifact) -> str | None:
    storage = spec.context.get("storage")
    return (
        storage.strip().lower()
        if isinstance(storage, str) and storage.strip()
        else None
    )


def spec_implies_persistence(spec: SpecArtifact | None) -> bool:
    """spec 是否暗示需要持久化或表结构（DES-013 传导信号）。"""
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
    return any(table.columns for table in design.table_schemas)


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
    _ = design
    return spec is not None and spec.consistency_profile.multi_writer


def requires_diagram_pair(
    design: DesignArtifact,
    spec: SpecArtifact | None = None,
) -> bool:
    """是否要求 diagrams 含 sequence + flowchart（DES-017）。"""
    if design.diagrams:
        return True
    return spec_implies_persistence(spec)


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


def spec_has_nonlinear_us(spec: SpecArtifact) -> bool:
    """spec 是否含非线性 / 多步业务 US 信号（DES-206 传导）。"""
    cp = spec.consistency_profile
    if cp.multi_writer:
        return True
    if cp.idempotency_required and cp.delivery.value == "at_least_once":
        return True
    for story in spec.user_stories:
        blob = f"{story.want} {story.so_that}"
        if _NONLINEAR_US_RE.search(blob):
            return True
    for criterion in spec.acceptance_criteria:
        if _NONLINEAR_US_RE.search(criterion.description):
            return True
    return False


def design_has_cross_module_collaboration(
    design: DesignArtifact,
    spec: SpecArtifact | None = None,
) -> bool:
    """多模块协作（非线性分层 CLI 如计算器不计入）。"""
    if len(design.modules) < 2:
        return False
    if spec is not None and is_stateless_design(design, spec):
        return False
    module_refs = {iface.module_ref for iface in design.interfaces if iface.module_ref}
    return len(module_refs) >= 2


def requires_flow_section(
    design: DesignArtifact,
    spec: SpecArtifact | None = None,
) -> bool:
    """是否宜写 design.md §4.7 流程与时序（DES-206 / DES-217）。"""
    if spec is not None and spec_has_nonlinear_us(spec):
        return True
    return design_has_cross_module_collaboration(design, spec)
