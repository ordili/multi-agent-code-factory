"""DES-105～107 执行计划（dev_tasks）写作 warn 规则。"""

from __future__ import annotations

from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.schemas.design import DesignArtifact, DevTask
from multi_agent_code_factory.schemas.validation_report import Violation
from multi_agent_code_factory.validators._report import warn

_PROFILE_MANIFEST_PATHS: dict[str, frozenset[str]] = {
    "python": frozenset({"pyproject.toml"}),
    "go": frozenset({"go.mod", "go.work"}),
    "java": frozenset({"pom.xml", "build.gradle.kts"}),
    "rust": frozenset({"Cargo.toml"}),
    "solidity": frozenset({"foundry.toml"}),
}


def _root_tasks(tasks: list[DevTask]) -> list[DevTask]:
    return [task for task in tasks if not task.depends_on]


def _depends_on_root(
    task: DevTask, root_ids: set[str], by_id: dict[str, DevTask]
) -> bool:
    if not task.depends_on:
        return task.id in root_ids
    visiting: set[str] = set()

    def visit(task_id: str) -> bool:
        if task_id in root_ids:
            return True
        if task_id in visiting:
            return False
        visiting.add(task_id)
        node = by_id.get(task_id)
        if node is None:
            return False
        return any(visit(dep) for dep in node.depends_on)

    return visit(task.id)


def validate_execution_plan_rules(
    design: DesignArtifact,
    profile: ProfileConfig,
) -> list[Violation]:
    """DES-105～107：附录 C 执行计划写作 warn（默认不阻断）。"""
    violations: list[Violation] = []
    tasks = design.dev_tasks
    if not tasks:
        return violations

    roots = _root_tasks(tasks)
    root_ids = {task.id for task in roots}
    by_id = {task.id: task for task in tasks}

    if len(roots) != 1:
        violations.append(
            warn(
                "DES-105",
                "expected exactly one root dev_task with depends_on=[] "
                "(framework step)",
                field="dev_tasks",
            )
        )
    else:
        root = roots[0]
        for task in tasks:
            if task.id == root.id:
                continue
            if not _depends_on_root(task, root_ids, by_id):
                violations.append(
                    warn(
                        "DES-105",
                        (
                            f"dev_task {task.id!r} should transitively depend "
                            f"on root {root.id!r}"
                        ),
                        field="dev_tasks",
                    )
                )

    if design.modules:
        module_paths = {module.path for module in design.modules}
        language = (profile.language or profile.id or "").lower()
        manifest_paths = _PROFILE_MANIFEST_PATHS.get(language, frozenset())
        for task in tasks:
            if task.path in manifest_paths:
                continue
            if task.path not in module_paths:
                violations.append(
                    warn(
                        "DES-106",
                        f"dev_task path {task.path!r} not listed in modules[].path",
                        field="dev_tasks",
                    )
                )

    language = (profile.language or profile.id or "").lower()
    manifest_paths = _PROFILE_MANIFEST_PATHS.get(language)
    if manifest_paths and roots:
        for root in roots:
            if root.path not in manifest_paths:
                expected = ", ".join(sorted(manifest_paths))
                violations.append(
                    warn(
                        "DES-107",
                        f"root dev_task {root.id!r} path {root.path!r} "
                        f"should be a profile manifest ({expected})",
                        field="dev_tasks",
                    )
                )

    return violations
