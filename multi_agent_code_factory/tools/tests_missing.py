"""对照 Profile.toolchain.test_dir_glob 检测缺测源码路径。"""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.schemas.dev_manifest import ChangeType, DevManifest

_TEST_DIR_MARKERS = ("tests/", "test/", "__tests__/")
_TEST_NAME_MARKERS = ("test_", "_test")


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


def _has_matching_test(
    source_path: str, test_stems: set[str], *, language: str
) -> bool:
    stem = _source_stem(source_path)
    if stem in {"__init__", "main", "mod", "lib"}:
        return True
    candidates = {stem, f"test_{stem}", f"{stem}_test"}
    if language == "go":
        candidates.add(f"{stem}_test")
    if language == "rust":
        candidates.update({stem, f"{stem}_tests"})
    if language == "java":
        candidates.update({f"{stem}test", f"test{stem}"})
    return bool(candidates & test_stems)


def _collect_source_paths(
    *,
    dev_manifest: DevManifest | None,
    design: DesignArtifact | None,
) -> list[str]:
    paths: list[str] = []
    if dev_manifest is not None:
        for item in dev_manifest.changed_files:
            if item.change_type == ChangeType.DELETE:
                continue
            if not _is_test_path(item.path):
                paths.append(_posix(item.path))
    elif design is not None:
        for entry in design.file_plan:
            action = entry.get("action")
            path = entry.get("path")
            if not isinstance(path, str) or action == "delete":
                continue
            if not _is_test_path(path):
                paths.append(_posix(path))
    return sorted(set(paths))


def detect_tests_missing(
    profile: ProfileConfig,
    code_root: Path,
    *,
    dev_manifest: DevManifest | None = None,
    design: DesignArtifact | None = None,
) -> list[str]:
    """返回 dev_manifest / design 中尚无对应测试文件的源码相对路径。"""
    test_dir_glob = profile.toolchain.test_dir_glob
    if not test_dir_glob:
        return []

    root = code_root.resolve()
    test_files = _glob_test_files(root, test_dir_glob)
    test_stems = _test_stems(test_files)
    source_paths = _collect_source_paths(dev_manifest=dev_manifest, design=design)
    if not source_paths:
        return []

    language = profile.language or profile.id
    missing = [
        path
        for path in source_paths
        if not _has_matching_test(path, test_stems, language=language)
    ]
    return missing
