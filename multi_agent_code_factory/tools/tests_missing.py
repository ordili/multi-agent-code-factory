"""对照 Profile 检测缺测源码路径（语言感知、可配置 scope）。"""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.schemas.dev_manifest import ChangeType, DevManifest

_TEST_DIR_MARKERS = ("tests/", "test/", "__tests__/")
_TEST_NAME_MARKERS = ("test_", "_test")
_RUST_INLINE_MARKERS = ("#[cfg(test)]", "#[test]")
_RUST_EXEMPT_BASENAMES = frozenset({"main.rs", "lib.rs", "mod.rs"})

_LANGUAGE_SOURCE_SUFFIXES: dict[str, frozenset[str]] = {
    "python": frozenset({".py"}),
    "go": frozenset({".go"}),
    "java": frozenset({".java"}),
    "rust": frozenset({".rs"}),
    "solidity": frozenset({".sol"}),
}


def _posix(path: str) -> str:
    return path.replace("\\", "/")


def _is_test_path(path: str) -> bool:
    normalized = _posix(path).lower()
    if any(marker in normalized for marker in _TEST_DIR_MARKERS):
        return True
    stem = PurePosixPath(normalized).stem
    return stem.startswith("test_") or stem.endswith("_test")


def _glob_test_files(code_root: Path, test_dir_glob: str) -> list[str]:
    return sorted(
        _posix(str(path.relative_to(code_root)))
        for path in code_root.glob(test_dir_glob)
        if path.is_file()
    )


def _test_stems(test_files: list[str]) -> set[str]:
    stems: set[str] = set()
    for path in test_files:
        stem = PurePosixPath(path).stem.lower()
        stems.add(stem)
        if stem.startswith("test_"):
            stems.add(stem.removeprefix("test_"))
        if stem.endswith("_test"):
            stems.add(stem.removesuffix("_test"))
    return stems


def _source_stem(path: str) -> str:
    return PurePosixPath(_posix(path)).stem.lower()


def _requires_matching_test(path: str, *, language: str) -> bool:
    """仅对实现语言源码扩展名要求对应测试；文档/配置/占位文件跳过。"""
    normalized = _posix(path).lower()
    if normalized.endswith(".gitkeep"):
        return False
    suffix = PurePosixPath(normalized).suffix
    allowed = _LANGUAGE_SOURCE_SUFFIXES.get(language, frozenset({".py"}))
    return suffix in allowed


def _is_rust_exempt(path: str) -> bool:
    basename = PurePosixPath(_posix(path)).name.lower()
    return basename in _RUST_EXEMPT_BASENAMES


def _has_rust_inline_tests(code_root: Path, source_path: str) -> bool:
    full = code_root / source_path
    if not full.is_file():
        return False
    text = full.read_text(encoding="utf-8", errors="replace")
    return any(marker in text for marker in _RUST_INLINE_MARKERS)


def _has_matching_test(
    source_path: str,
    test_stems: set[str],
    *,
    language: str,
    code_root: Path,
    inline_tests: bool,
) -> bool:
    stem = _source_stem(source_path)
    if stem in {"__init__", "main", "mod", "lib"}:
        return True
    if language == "rust" and _is_rust_exempt(source_path):
        return True
    if (
        language == "rust"
        and inline_tests
        and _has_rust_inline_tests(code_root, source_path)
    ):
        return True

    candidates = {stem, f"test_{stem}", f"{stem}_test"}
    if language == "go":
        candidates.add(f"{stem}_test")
    if language == "rust":
        candidates.update({stem, f"{stem}_tests"})
    if language == "java":
        candidates.update({f"{stem}test", f"test{stem}"})
    return bool(candidates & test_stems)


def _collect_manifest_paths(dev_manifest: DevManifest | None) -> list[str]:
    if dev_manifest is None:
        return []
    paths: list[str] = []
    for item in dev_manifest.changed_files:
        if item.change_type == ChangeType.DELETE:
            continue
        if not _is_test_path(item.path):
            paths.append(_posix(item.path))
    return sorted(set(paths))


def _collect_file_plan_paths(design: DesignArtifact | None) -> list[str]:
    if design is None:
        return []
    paths: list[str] = []
    for entry in design.file_plan:
        action = entry.get("action")
        path = entry.get("path")
        if not isinstance(path, str) or action == "delete":
            continue
        if not _is_test_path(path):
            paths.append(_posix(path))
    return sorted(set(paths))


def _collect_dev_task_paths(
    design: DesignArtifact | None,
    dev_manifest: DevManifest | None,
) -> list[str]:
    if design is None or not design.dev_tasks:
        return []
    task_paths = [
        _posix(task.path)
        for task in design.dev_tasks
        if isinstance(task.path, str) and task.path.strip()
    ]
    if not task_paths:
        return []
    if dev_manifest is None:
        return sorted(set(task_paths))
    manifest_paths = {
        _posix(item.path)
        for item in dev_manifest.changed_files
        if item.change_type != ChangeType.DELETE
    }
    scoped = sorted(set(task_paths) & manifest_paths)
    return scoped if scoped else sorted(set(task_paths))


def _collect_source_paths(
    *,
    scope: str,
    dev_manifest: DevManifest | None,
    design: DesignArtifact | None,
) -> list[str]:
    if scope == "dev_tasks":
        dev_task_paths = _collect_dev_task_paths(design, dev_manifest)
        if dev_task_paths:
            return dev_task_paths
    manifest_paths = _collect_manifest_paths(dev_manifest)
    if manifest_paths:
        return manifest_paths
    return _collect_file_plan_paths(design)


def detect_tests_missing(
    profile: ProfileConfig,
    code_root: Path,
    *,
    dev_manifest: DevManifest | None = None,
    design: DesignArtifact | None = None,
) -> list[str]:
    """返回缺测源码路径；是否阻断见 Profile.tests_missing.block_on。"""
    cfg = profile.tests_missing
    if not cfg.enabled:
        return []

    test_dir_glob = profile.toolchain.test_dir_glob
    if not test_dir_glob:
        return []

    root = code_root.resolve()
    test_files = _glob_test_files(root, test_dir_glob)
    test_stems = _test_stems(test_files)
    source_paths = _collect_source_paths(
        scope=cfg.scope,
        dev_manifest=dev_manifest,
        design=design,
    )
    if not source_paths:
        return []

    language = profile.language or profile.id
    missing = [
        path
        for path in source_paths
        if _requires_matching_test(path, language=language)
        and not _has_matching_test(
            path,
            test_stems,
            language=language,
            code_root=root,
            inline_tests=cfg.inline_tests or cfg.detector == "rust",
        )
    ]
    return missing
