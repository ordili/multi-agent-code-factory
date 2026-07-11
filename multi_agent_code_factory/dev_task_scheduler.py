"""dev_tasks 静态调度：Kahn 拓扑序、闭包展开、batch 规划。"""

from __future__ import annotations

import re
from collections import defaultdict, deque
from pathlib import Path, PurePosixPath

from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.schemas.design import (
    DesignArtifact,
    DevTask,
    FilePlanItem,
)
from multi_agent_code_factory.schemas.task_batch import TaskBatch, TaskBatchConfig

_PATH_LIKE = re.compile(
    r"(?:tests?/|src/|test/)[\w./_-]+\.(?:py|go|java|rs|sol|t\.sol)",
    re.IGNORECASE,
)


class DevTaskScheduleError(ValueError):
    """调度或闭包展开失败。"""


def _posix(path: str) -> str:
    return path.replace("\\", "/")


def _dirname(path: str) -> str:
    parent = PurePosixPath(_posix(path)).parent
    return "" if str(parent) == "." else str(parent)


def _stem(path: str) -> str:
    return PurePosixPath(_posix(path)).stem


def _is_test_path(path: str) -> bool:
    normalized = _posix(path).lower()
    if normalized.startswith("tests/") or normalized.startswith("test/"):
        return True
    stem = PurePosixPath(normalized).stem
    return stem.startswith("test_") or stem.endswith("_test")


def kahn_sort_tasks(tasks: list[DevTask]) -> list[DevTask]:
    """Kahn 拓扑排序；有环时抛出 DevTaskScheduleError。"""
    if not tasks:
        return []
    by_id = {task.id: task for task in tasks}
    in_degree = {task.id: len(task.depends_on) for task in tasks}
    dependents: dict[str, list[str]] = defaultdict(list)
    for task in tasks:
        for dep in task.depends_on:
            dependents[dep].append(task.id)

    queue: deque[str] = deque(
        sorted(task.id for task in tasks if in_degree[task.id] == 0)
    )
    ordered: list[DevTask] = []
    while queue:
        node = queue.popleft()
        ordered.append(by_id[node])
        for child in sorted(dependents.get(node, [])):
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    if len(ordered) != len(tasks):
        msg = "dev_tasks dependency cycle detected"
        raise DevTaskScheduleError(msg)
    return ordered


def file_plan_aux_paths(task: DevTask, file_plan: list[FilePlanItem]) -> list[str]:
    """从 file_plan 筛选与本 task 关联路径（DES-104：path 须为 dev_task.path）。"""
    task_dir = _dirname(task.path)
    paths: list[str] = []
    for item in file_plan:
        path = _posix(item.path)
        if path == _posix(task.path):
            paths.append(path)
            continue
        if task_dir and _dirname(path) == task_dir:
            paths.append(path)
            continue
        reason = item.reason or ""
        if task.id in reason:
            paths.append(path)
    return sorted(dict.fromkeys(paths))


def _extract_explicit_test_paths(test_cases: list) -> list[str]:
    explicit: list[str] = []
    for case in test_cases:
        for field in ("steps", "description", "title"):
            text = getattr(case, field, None)
            if not isinstance(text, str):
                continue
            for match in _PATH_LIKE.findall(text):
                explicit.append(_posix(match))
    return sorted(dict.fromkeys(explicit))


def default_test_path(task_path: str, profile: ProfileConfig) -> str | None:
    """按 Profile tests_missing.detector 映射默认测试路径。"""
    if _is_test_path(task_path):
        return None

    stem = _stem(task_path)
    if not stem:
        return None

    detector = profile.tests_missing.detector
    language = profile.language or profile.id

    if language == "java":
        return f"src/test/java/{stem}Test.java"
    if language == "solidity":
        contract = stem[0].upper() + stem[1:] if stem else stem
        return f"test/{contract}.t.sol"
    if detector == "go" or language == "go":
        parent = _dirname(task_path)
        if parent:
            return f"{parent}/{stem}_test.go"
        return f"tests/{stem}_test.go"
    if detector == "rust" or language == "rust":
        return f"tests/{stem}.rs"
    if detector == "file_stem" or language == "python":
        return f"tests/test_{stem}.py"
    return f"tests/test_{stem}.py"


def map_test_paths(
    task: DevTask,
    design: DesignArtifact,
    profile: ProfileConfig,
    config: TaskBatchConfig,
) -> tuple[list[str], list[str]]:
    """返回 (test_paths, relevant_test_case_ids)。"""
    task_covers = set(task.covers)
    relevant = [
        case
        for case in design.test_cases
        if task_covers and set(case.covers) & task_covers
    ]
    case_ids = [case.id for case in relevant]

    if not task_covers or not config.require_tests:
        return [], case_ids

    if profile.tests_missing.inline_tests and (profile.language == "rust"):
        return [], case_ids

    explicit = _extract_explicit_test_paths(relevant)
    if explicit:
        return explicit, case_ids

    mapped = default_test_path(task.path, profile)
    if mapped is None:
        return [], case_ids
    return [mapped], case_ids


def expand_task_closure(
    task: DevTask,
    design: DesignArtifact,
    profile: ProfileConfig,
    config: TaskBatchConfig,
    *,
    code_root: Path | None = None,
) -> tuple[list[str], list[str], list[str], int]:
    """展开单 task 闭包；返回 required/dependency、test_case_ids、行数估算。"""
    aux = file_plan_aux_paths(task, design.file_plan)
    test_paths, case_ids = map_test_paths(task, design, profile, config)
    required = sorted(
        dict.fromkeys([_posix(task.path), *aux, *test_paths]),
    )

    max_required = config.max_required_paths_per_batch
    if len(required) > max_required:
        msg = (
            f"batch_files_budget_exceeded: task {task.id} "
            f"requires {len(required)} paths (max {max_required})"
        )
        raise DevTaskScheduleError(msg)

    estimated = 0
    root = code_root or profile.code_root
    for path in required:
        full = root / path
        if full.is_file():
            estimated += len(
                full.read_text(encoding="utf-8", errors="replace").splitlines()
            )
        else:
            estimated += config.max_lines_per_file_hint

    if estimated > config.max_output_lines_per_batch:
        msg = (
            f"batch_lines_budget_exceeded: task {task.id} "
            f"estimated {estimated} lines (max {config.max_output_lines_per_batch})"
        )
        raise DevTaskScheduleError(msg)

    dependency_paths = _dependency_paths_for_task(
        task,
        design,
        profile,
        config,
        code_root=root,
    )
    return required, dependency_paths, case_ids, estimated


def _dependency_paths_for_task(
    task: DevTask,
    design: DesignArtifact,
    profile: ProfileConfig,
    config: TaskBatchConfig,
    *,
    code_root: Path,
) -> list[str]:
    by_id = {item.id: item for item in design.dev_tasks}
    paths: set[str] = set()
    for dep_id in task.depends_on:
        dep = by_id.get(dep_id)
        if dep is None:
            continue
        dep_required, _, _, _ = expand_task_closure(
            dep,
            design,
            profile,
            config,
            code_root=code_root,
        )
        for path in dep_required:
            if _is_test_path(path):
                continue
            full = code_root / path
            if full.is_file():
                paths.add(path)
    return sorted(paths)


def refresh_batch_runtime(
    batch: TaskBatch,
    design: DesignArtifact,
    profile: ProfileConfig,
    config: TaskBatchConfig,
    *,
    code_root: Path | None = None,
) -> TaskBatch:
    """按当前写盘刷新 dependency_paths 与 estimated_output_lines（§4.3）。"""
    root = code_root or profile.code_root
    by_id = {item.id: item for item in design.dev_tasks}
    dep_union: set[str] = set()
    estimated = 0

    for path in batch.required_paths:
        full = root / path
        if full.is_file():
            estimated += len(
                full.read_text(encoding="utf-8", errors="replace").splitlines()
            )
        else:
            estimated += config.max_lines_per_file_hint

    for task_id in batch.task_ids:
        task = by_id.get(task_id)
        if task is None:
            continue
        dep_union.update(
            _dependency_paths_for_task(
                task,
                design,
                profile,
                config,
                code_root=root,
            )
        )

    return batch.model_copy(
        update={
            "dependency_paths": sorted(dep_union),
            "estimated_output_lines": estimated,
        }
    )


def can_batch_together(
    tasks: list[DevTask],
    design: DesignArtifact,
    profile: ProfileConfig,
    config: TaskBatchConfig,
    *,
    code_root: Path | None = None,
) -> bool:
    """多 task 同批可行性（首期 max_tasks_per_batch=1 时通常不调用）。"""
    if len(tasks) <= 1:
        return True
    task_ids = {task.id for task in tasks}
    for task in tasks:
        for dep in task.depends_on:
            if dep in task_ids:
                return False

    required: set[str] = set()
    for task in tasks:
        paths, _, _, _ = expand_task_closure(
            task,
            design,
            profile,
            config,
            code_root=code_root,
        )
        required.update(paths)
    return len(required) <= config.max_required_paths_per_batch


def schedule(
    design: DesignArtifact,
    profile: ProfileConfig,
    config: TaskBatchConfig,
    *,
    code_root: Path | None = None,
) -> list[TaskBatch]:
    """静态生成有序 batches[]。"""
    root = code_root or profile.code_root
    ordered = kahn_sort_tasks(design.dev_tasks)
    batches: list[TaskBatch] = []
    index = 0

    pending = list(ordered)
    while pending:
        group: list[DevTask] = []
        if config.max_tasks_per_batch <= 1:
            group = [pending.pop(0)]
        else:
            candidate = pending[0]
            group = [candidate]
            for other in pending[1:]:
                if len(group) >= config.max_tasks_per_batch:
                    break
                trial = [*group, other]
                if can_batch_together(trial, design, profile, config, code_root=root):
                    group.append(other)
            for task in group:
                pending.remove(task)

        task_ids = [task.id for task in group]
        required_union: list[str] = []
        dependency_union: set[str] = set()
        case_ids: set[str] = set()
        estimated_total = 0

        for task in group:
            req, deps, cases, est = expand_task_closure(
                task,
                design,
                profile,
                config,
                code_root=root,
            )
            required_union = sorted(dict.fromkeys([*required_union, *req]))
            dependency_union.update(deps)
            case_ids.update(cases)
            estimated_total += est

        if len(required_union) > config.max_required_paths_per_batch:
            msg = (
                f"batch_files_budget_exceeded: tasks {task_ids} "
                f"require {len(required_union)} paths"
            )
            raise DevTaskScheduleError(msg)

        batches.append(
            TaskBatch(
                index=index,
                task_ids=task_ids,
                required_paths=required_union,
                dependency_paths=sorted(dependency_union),
                relevant_test_case_ids=sorted(case_ids),
                estimated_output_lines=estimated_total,
            )
        )
        index += 1

    return batches
