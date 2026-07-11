"""Task-batch 双阶段门禁（§8.1 闭包 / §8.2 输出）。"""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Any

from multi_agent_code_factory.context_lines import count_context_lines
from multi_agent_code_factory.log import get_logger
from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.schemas.dev_manifest import DevManifest
from multi_agent_code_factory.schemas.task_batch import TaskBatch, TaskBatchConfig


class BatchClosureError(ValueError):
    """validate_batch_closure 失败。"""


class BatchOutputError(ValueError):
    """validate_batch_output 失败。"""


logger = get_logger("batch_closure")


def _dirname(path: str) -> str:
    parent = PurePosixPath(_posix(path)).parent
    return "" if str(parent) == "." else str(parent)


def _warn_paths_extra(required: set[str], extra: set[str]) -> None:
    """§8.2：额外路径非同目录时 warn-only。"""
    required_dirs = {_dirname(path) for path in required}
    for path in sorted(extra):
        if _dirname(path) not in required_dirs and path not in required_dirs:
            logger.warning(
                "paths_extra: %s not under required_paths directory (warn-only)",
                path,
            )


def _posix(path: str) -> str:
    return path.replace("\\", "/")


def _path_escapes(path: str) -> bool:
    pure = PurePosixPath(path.replace("\\", "/"))
    return path.startswith("/") or ".." in pure.parts


def validate_batch_closure(
    batch: TaskBatch,
    manifest: DevManifest,
    design: DesignArtifact,
    profile: ProfileConfig,
    config: TaskBatchConfig,
    context: dict | None = None,
    *,
    code_root: Path | None = None,
    omitted_dependencies: list[dict[str, str]] | None = None,
) -> None:
    """调用 LLM 前门禁；失败抛 BatchClosureError。"""
    root = code_root or profile.code_root
    completed = set(manifest.tasks_completed)
    by_id = {task.id: task for task in design.dev_tasks}

    for task_id in batch.task_ids:
        task = by_id.get(task_id)
        if task is None:
            msg = f"deps_satisfied: unknown task {task_id!r}"
            raise BatchClosureError(msg)
        for dep in task.depends_on:
            if dep not in completed:
                msg = f"deps_satisfied: task {task_id} requires completed {dep!r}"
                raise BatchClosureError(msg)

    required_set = set(batch.required_paths)
    for path in batch.dependency_paths:
        full = root / path
        if not full.is_file() and path not in required_set:
            msg = f"deps_readable: dependency {path!r} not on disk"
            raise BatchClosureError(msg)

    if config.require_tests:
        for task_id in batch.task_ids:
            task = by_id[task_id]
            if not task.covers:
                continue
            if profile.tests_missing.inline_tests and profile.language == "rust":
                continue
            has_test = any(
                _posix(p) in required_set
                for p in batch.required_paths
                if _is_test_path(p)
            )
            if not has_test:
                msg = (
                    f"tests_mapped: task {task_id} covers non-empty "
                    "but no test path in batch"
                )
                raise BatchClosureError(msg)

    if len(batch.required_paths) > config.max_required_paths_per_batch:
        msg = (
            f"files_budget: {len(batch.required_paths)} required paths "
            f"(max {config.max_required_paths_per_batch})"
        )
        raise BatchClosureError(msg)

    if (
        batch.estimated_output_lines is not None
        and batch.estimated_output_lines > config.max_output_lines_per_batch
    ):
        msg = (
            f"lines_budget: estimated {batch.estimated_output_lines} lines "
            f"(max {config.max_output_lines_per_batch})"
        )
        raise BatchClosureError(msg)

    if context is not None:
        lines = count_context_lines(context)
        if lines > config.max_input_lines_per_batch:
            msg = (
                f"input_budget: {lines} context lines "
                f"(max {config.max_input_lines_per_batch})"
            )
            raise BatchClosureError(msg)

    if omitted_dependencies:
        omitted_paths = {item.get("path", "") for item in omitted_dependencies}
        for path in batch.dependency_paths:
            if path in omitted_paths:
                msg = f"deps_readable: failed to read dependency {path!r}"
                raise BatchClosureError(msg)


def _is_test_path(path: str) -> bool:
    normalized = _posix(path).lower()
    if normalized.startswith("tests/") or normalized.startswith("test/"):
        return True
    stem = PurePosixPath(normalized).stem
    return stem.startswith("test_") or stem.endswith("_test")


def validate_batch_output(
    output: Any,
    batch: TaskBatch,
    config: TaskBatchConfig,
    *,
    code_root: Path | None = None,
) -> None:
    """invoke 之后、apply 之前门禁；失败抛 BatchOutputError。"""
    _ = code_root
    output_paths = {_posix(item.path) for item in output.source_files}
    required = {_posix(path) for path in batch.required_paths}

    for task_id in batch.task_ids:
        if task_id not in output.tasks_completed:
            msg = f"tasks_done: missing task {task_id!r} in tasks_completed"
            raise BatchOutputError(msg)

    missing = required - output_paths
    if missing:
        msg = f"paths_complete: missing paths {sorted(missing)!r}"
        raise BatchOutputError(msg)

    extra = output_paths - required
    if extra:
        _warn_paths_extra(required, extra)
    if len(extra) > config.max_extra_output_paths:
        msg = (
            f"paths_extra: {len(extra)} extra paths "
            f"(max {config.max_extra_output_paths})"
        )
        raise BatchOutputError(msg)

    if len(output.source_files) > config.max_files_per_batch:
        msg = (
            f"files_budget: {len(output.source_files)} source files "
            f"(max {config.max_files_per_batch})"
        )
        raise BatchOutputError(msg)

    total_lines = 0
    per_file_max = config.max_lines_per_file_hint * 2
    for item in output.source_files:
        line_count = len(item.content.splitlines())
        total_lines += line_count
        if line_count > per_file_max:
            msg = (
                f"per_file_lines: {item.path} has {line_count} lines "
                f"(max {per_file_max})"
            )
            raise BatchOutputError(msg)

    if total_lines > config.max_output_lines_per_batch:
        msg = (
            f"output_lines: {total_lines} total lines "
            f"(max {config.max_output_lines_per_batch})"
        )
        raise BatchOutputError(msg)

    for item in output.source_files:
        if _path_escapes(item.path):
            msg = f"paths_safe: path escapes code_root: {item.path!r}"
            raise BatchOutputError(msg)


def format_batch_output_retry_feedback(error: BatchOutputError) -> str:
    """本批输出校验失败时的 extra_system 反馈。"""
    return (
        "Previous Developer output failed batch validation. "
        f"Fix and return ONLY this batch's required paths.\n"
        f"Validation error: {error}"
    )
