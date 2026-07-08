"""DES-001 至 DES-104、DES-011、DES-301 校验规则（MVP 白名单）。"""

from __future__ import annotations

from pathlib import PurePosixPath

from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.schemas.design import DesignArtifact, DevTask
from multi_agent_code_factory.schemas.spec import FeaturePriority, SpecArtifact
from multi_agent_code_factory.schemas.validation_report import Violation
from multi_agent_code_factory.validators._report import error
from multi_agent_code_factory.validators.design_rules_extended import (
    validate_design_extended_rules,
)


def _path_escapes(path: str) -> bool:
    pure = PurePosixPath(path.replace("\\", "/"))
    return path.startswith("/") or ".." in pure.parts


def _dev_task_cycle(tasks: list[DevTask]) -> bool:
    graph: dict[str, list[str]] = {task.id: list(task.depends_on) for task in tasks}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for dep in graph.get(node, []):
            if dep in graph and visit(dep):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(task_id) for task_id in graph)


def _is_spec_non_trivial(spec: SpecArtifact) -> bool:
    op = spec.operational_profile
    if op.user_scale.value != "personal":
        return True
    if op.high_concurrency:
        return True
    if op.performance.tier.value != "best_effort":
        return True
    return spec.consistency_profile.consistency_model.value != "local_only"


def _hitl_required(design: DesignArtifact, profile: ProfileConfig) -> bool:
    if not design.hitl_flags:
        return False
    profile_flags = set(profile.hitl.flags)
    if profile_flags & set(design.hitl_flags):
        return True
    required_flags = set(profile.validation.design.require_hitl_if_flags)
    return bool(required_flags & set(design.hitl_flags))


def validate_design_rules(
    design: DesignArtifact,
    profile: ProfileConfig,
    spec: SpecArtifact | None = None,
) -> tuple[list[Violation], bool]:
    """对 DesignArtifact 执行设计规则校验，返回 (违规列表, 是否需 HITL)。"""
    violations: list[Violation] = []
    require_hitl = False

    # DES-001 至 DES-005：开发任务
    if not design.dev_tasks:
        violations.append(
            error("DES-001", "dev_tasks must not be empty", field="dev_tasks")
        )

    task_ids = [task.id for task in design.dev_tasks]
    for task_id in {item for item in task_ids if task_ids.count(item) > 1}:
        violations.append(
            error("DES-002", f"duplicate dev_task id: {task_id}", field="dev_tasks")
        )

    task_paths = [task.path for task in design.dev_tasks]
    for path in {item for item in task_paths if task_paths.count(item) > 1}:
        violations.append(
            error("DES-003", f"duplicate dev_task path: {path}", field="dev_tasks")
        )

    known_ids = set(task_ids)
    for task in design.dev_tasks:
        if not task.id.strip() or not task.path.strip() or not task.description.strip():
            violations.append(
                error(
                    "DES-003",
                    f"dev_task {task.id!r} requires id, path, and description",
                    field="dev_tasks",
                )
            )
        for dep in task.depends_on:
            if dep not in known_ids:
                violations.append(
                    error(
                        "DES-004",
                        f"dev_task {task.id} depends on unknown task {dep!r}",
                        field="dev_tasks",
                    )
                )

    if design.dev_tasks and _dev_task_cycle(design.dev_tasks):
        violations.append(
            error("DES-005", "dev_tasks dependency cycle detected", field="dev_tasks")
        )

    # DES-006 / DES-007：模块定义
    if not design.modules:
        violations.append(
            error("DES-006", "modules must not be empty", field="modules")
        )

    for module in design.modules:
        if not all(
            [module.name, module.path, module.responsibility, module.code_domain]
        ):
            violations.append(
                error(
                    "DES-007",
                    f"module {module.name!r} missing required fields",
                    field="modules",
                )
            )

    # DES-008：非目标、上下文视图与架构策略
    if not design.non_goals:
        violations.append(
            error("DES-008", "non_goals must not be empty", field="non_goals")
        )
    if not design.context_view:
        violations.append(
            error("DES-008", "context_view must not be empty", field="context_view")
        )
    architecture = design.architecture or {}
    solution_strategy = architecture.get("solution_strategy")
    if not isinstance(solution_strategy, str) or not solution_strategy.strip():
        violations.append(
            error(
                "DES-008",
                "architecture.solution_strategy must not be empty",
                field="architecture.solution_strategy",
            )
        )

    # DES-009：可追溯性（含 P0 功能覆盖）
    if not design.traceability:
        violations.append(
            error("DES-009", "traceability must not be empty", field="traceability")
        )
    elif spec is not None:
        p0_features = [
            feature.id
            for feature in spec.features
            if feature.priority == FeaturePriority.P0
        ]
        traced: set[str] = set()
        for row in design.traceability:
            ref_id = row.get("spec_ref_id")
            if not isinstance(ref_id, str):
                feature_id = row.get("feature_id")
                if isinstance(feature_id, str):
                    ref_id = feature_id
            if isinstance(ref_id, str):
                traced.add(ref_id)
        for task in design.dev_tasks:
            traced.update(task.covers)
        for feature_id in p0_features:
            if feature_id not in traced:
                violations.append(
                    error(
                        "DES-009",
                        f"P0 feature {feature_id} not traced in traceability "
                        f"or dev_tasks.covers",
                        field="traceability",
                    )
                )

    # DES-010 / DES-011：横切关注点与非功能需求
    if design.cross_cutting is None:
        violations.append(
            error("DES-010", "cross_cutting must be present", field="cross_cutting")
        )

    if spec is not None and _is_spec_non_trivial(spec) and not design.non_functional:
        violations.append(
            error(
                "DES-011",
                "non_functional required for non-trivial spec",
                field="non_functional",
            )
        )

    # DES-101 / DES-102：与 Spec 的交叉校验
    if spec is not None:
        covered_ac = set()
        for task in design.dev_tasks:
            covered_ac.update(task.covers)
        for row in design.traceability:
            ref_id = row.get("spec_ref_id")
            ref_kind = row.get("spec_ref_kind")
            if ref_kind == "AC" and isinstance(ref_id, str):
                covered_ac.add(ref_id)
        for ac in spec.acceptance_criteria:
            if ac.id not in covered_ac:
                violations.append(
                    error(
                        "DES-101",
                        f"acceptance criterion {ac.id} not covered by design",
                        field="traceability",
                    )
                )

    if spec is not None and spec.scope_out:
        summary = (design.summary or "").lower()
        for item in spec.scope_out:
            token = item.lower()
            if not token:
                continue
            if token in summary:
                violations.append(
                    error(
                        "DES-102",
                        f"design summary appears to include scoped-out item: {item}",
                        field="scope_out",
                    )
                )
            for module in design.modules:
                haystack = f"{module.name} {module.responsibility}".lower()
                if token in haystack:
                    violations.append(
                        error(
                            "DES-102",
                            f"module {module.name} appears to implement "
                            f"scoped-out item: {item}",
                            field="scope_out",
                        )
                    )

    # DES-103 / DES-104：路径安全与文件计划
    for task in design.dev_tasks:
        if _path_escapes(task.path):
            violations.append(
                error(
                    "DES-103",
                    f"dev_task path escapes code_root: {task.path}",
                    field="dev_tasks",
                )
            )
    for module in design.modules:
        if _path_escapes(module.path):
            violations.append(
                error(
                    "DES-103",
                    f"module path escapes code_root: {module.path}",
                    field="modules",
                )
            )

    if design.file_plan:
        dev_task_paths = {task.path for task in design.dev_tasks}
        for plan_item in design.file_plan:
            plan_path = plan_item.get("path")
            if isinstance(plan_path, str) and plan_path not in dev_task_paths:
                violations.append(
                    error(
                        "DES-104",
                        f"file_plan path {plan_path!r} not present in dev_tasks",
                        field="file_plan",
                    )
                )

    if _hitl_required(design, profile):
        require_hitl = True

    violations.extend(validate_design_extended_rules(design, spec))

    return violations, require_hitl
