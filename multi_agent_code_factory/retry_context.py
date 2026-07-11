"""Developer 重试：failure_contexts 构建、失败闭包与预算分配。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.schemas.dev_manifest import DevManifest
from multi_agent_code_factory.schemas.retry_context import (
    FailureContext,
    FunctionSnippet,
    OmittedFrame,
    OmittedFrameReason,
    StackFrame,
)
from multi_agent_code_factory.schemas.review import Finding, FindingRouting
from multi_agent_code_factory.schemas.test_report import TestFailure, TestReport
from multi_agent_code_factory.tools.read_file import read_file
from multi_agent_code_factory.tools.snippet_extract import extract_snippet
from multi_agent_code_factory.tools.traceback import parse_traceback

SNIPPET_MAX_TOTAL_LINES = 2000
SNIPPET_MAX_FUNCTIONS = 12
SNIPPET_MAX_FILES = 8


@dataclass
class _Budget:
    lines_used: int = 0
    functions_used: int = 0
    files_seen: set[str] = field(default_factory=set)
    omitted_paths: list[str] = field(default_factory=list)


def _is_test_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    name = PurePosixPath(normalized).name
    if normalized.startswith("tests/") or "/tests/" in normalized:
        return True
    if name.startswith("test_") and name.endswith(".py"):
        return True
    return name.endswith("_test.go") or name.endswith("_test.rs")


def _stem_from_test(path: str) -> str:
    name = PurePosixPath(path.replace("\\", "/")).stem
    if name.startswith("test_"):
        return name[5:]
    if name.endswith("_test"):
        return name[:-5]
    return name


def _stem_from_src(path: str) -> str:
    return PurePosixPath(path.replace("\\", "/")).stem


def _stems_match(test_stem: str, other_stem: str) -> bool:
    if test_stem == other_stem:
        return True
    return test_stem in other_stem or other_stem in test_stem


def paired_paths(
    path: str,
    *,
    known_paths: list[str],
    code_root: Path,
) -> list[tuple[str, int | None]]:
    """test ↔ src 同 stem 配对；仅返回 code_root 内存在的路径。"""
    del code_root  # existence checked via known_paths only per spec
    normalized = path.replace("\\", "/")
    candidates: list[str] = []
    if _is_test_path(normalized):
        stem = _stem_from_test(normalized)
        for candidate in known_paths:
            if _is_test_path(candidate):
                continue
            if _stems_match(stem, _stem_from_src(candidate)):
                candidates.append(candidate)
    else:
        stem = _stem_from_src(normalized)
        for candidate in known_paths:
            if not _is_test_path(candidate):
                continue
            if _stems_match(_stem_from_test(candidate), stem):
                candidates.append(candidate)

    seen: set[str] = set()
    result: list[tuple[str, int | None]] = []
    for candidate in candidates:
        if candidate in seen or candidate == normalized:
            continue
        seen.add(candidate)
        result.append((candidate, None))
    return result


def _known_paths(
    design: DesignArtifact | None,
    dev_manifest: DevManifest | None,
) -> list[str]:
    paths: list[str] = []
    if design is not None:
        paths.extend(item.path for item in design.file_plan if item.path)
    if dev_manifest is not None:
        paths.extend(item.path for item in dev_manifest.changed_files if item.path)
    seen: set[str] = set()
    ordered: list[str] = []
    for path in paths:
        if path not in seen:
            seen.add(path)
            ordered.append(path)
    return ordered


def _traceback_text(
    failure: TestFailure,
    *,
    raw_output_tail: str | None,
) -> str:
    parts: list[str] = []
    if failure.output:
        parts.append(failure.output)
    if failure.message:
        parts.append(failure.message)
    if raw_output_tail:
        parts.append(raw_output_tail)
    return "\n".join(parts)


def _closure_frames(
    failure: TestFailure,
    *,
    known_paths: list[str],
    code_root: Path,
) -> list[tuple[str, int | None]]:
    frames: list[tuple[str, int | None]] = []
    if failure.file:
        frames.append((failure.file, failure.line))
    if failure.file:
        for paired, line in paired_paths(
            failure.file,
            known_paths=known_paths,
            code_root=code_root,
        ):
            frames.append((paired, line))
    seen: set[tuple[str, int | None]] = set()
    unique: list[tuple[str, int | None]] = []
    for item in frames:
        if item in seen:
            continue
        seen.add(item)
        unique.append(item)
    return unique


def _finding_frames(findings: list[Finding]) -> list[tuple[str, int | None]]:
    frames: list[tuple[str, int | None]] = []
    for item in findings:
        if not item.file:
            continue
        if item.routing == FindingRouting.DEVELOPER_FIX or item.blocking:
            frames.append((item.file, None))
    return frames


def _snippet_line_count(content: str) -> int:
    return len(content.splitlines()) if content else 0


def _try_extract_frame(
    frame: StackFrame | tuple[str, int | None],
    *,
    language: str,
    code_root: Path,
    budget: _Budget,
    frame_order: int,
) -> FunctionSnippet | OmittedFrame:
    if isinstance(frame, StackFrame):
        file_path = frame.file
        line = frame.line
        function = frame.function
    else:
        file_path, line = frame
        function = None
        line = line or 1

    if budget.functions_used >= SNIPPET_MAX_FUNCTIONS:
        return OmittedFrame(
            file=file_path,
            function=function,
            line=line,
            reason=OmittedFrameReason.BUDGET_EXHAUSTED,
        )
    if (
        file_path not in budget.files_seen
        and len(budget.files_seen) >= SNIPPET_MAX_FILES
    ):
        budget.omitted_paths.append(file_path)
        return OmittedFrame(
            file=file_path,
            function=function,
            line=line,
            reason=OmittedFrameReason.BUDGET_EXHAUSTED,
        )

    try:
        source = read_file(code_root, file_path)
    except (OSError, ValueError):
        return OmittedFrame(
            file=file_path,
            function=function,
            line=line,
            reason=OmittedFrameReason.READ_FAILED,
        )

    extracted = extract_snippet(source, line, language=language)
    line_count = _snippet_line_count(extracted.content)
    if budget.lines_used + line_count > SNIPPET_MAX_TOTAL_LINES:
        budget.omitted_paths.append(file_path)
        return OmittedFrame(
            file=file_path,
            function=function,
            line=line,
            reason=OmittedFrameReason.BUDGET_EXHAUSTED,
        )

    budget.lines_used += line_count
    budget.functions_used += 1
    budget.files_seen.add(file_path)
    return FunctionSnippet(
        path=file_path,
        function=extracted.function or function,
        frame_order=frame_order,
        line_start=extracted.line_start,
        line_end=extracted.line_end,
        total_file_lines=extracted.total_file_lines,
        truncated=extracted.truncated,
        content=extracted.content,
    )


def _build_one_failure_context(
    *,
    test_id: str,
    message: str,
    traceback_text: str,
    language: str,
    code_root: Path,
    closure_frames: list[tuple[str, int | None]],
    budget: _Budget,
) -> FailureContext:
    call_path = parse_traceback(traceback_text, language=language, code_root=code_root)
    traceback_parse_ok = bool(call_path)

    snippets: list[FunctionSnippet] = []
    omitted: list[OmittedFrame] = []

    frames_to_process: list[StackFrame | tuple[str, int | None]]
    if call_path:
        frames_to_process = list(call_path)
    else:
        frames_to_process = [(path, line or 1) for path, line in closure_frames if path]

    for order, frame in enumerate(frames_to_process):
        result = _try_extract_frame(
            frame,
            language=language,
            code_root=code_root,
            budget=budget,
            frame_order=order,
        )
        if isinstance(result, FunctionSnippet):
            snippets.append(result)
        else:
            omitted.append(result)

    return FailureContext(
        test_id=test_id,
        message=message,
        traceback_parse_ok=traceback_parse_ok,
        call_path=call_path,
        snippets=snippets,
        omitted_frames=omitted,
    )


def build_failure_contexts(
    *,
    test_report: TestReport | None,
    language: str,
    code_root: Path,
    design: DesignArtifact | None = None,
    dev_manifest: DevManifest | None = None,
    review_findings: list[Finding] | None = None,
) -> tuple[list[FailureContext], list[str]]:
    """从 test failures 与 review findings 构建 failure_contexts。"""
    budget = _Budget()
    contexts: list[FailureContext] = []
    known = _known_paths(design, dev_manifest)
    raw_tail = test_report.raw_output_tail if test_report else None

    if test_report is not None:
        for failure in test_report.failures:
            tb_text = _traceback_text(failure, raw_output_tail=raw_tail)
            closure = _closure_frames(failure, known_paths=known, code_root=code_root)
            contexts.append(
                _build_one_failure_context(
                    test_id=failure.test_id,
                    message=failure.message,
                    traceback_text=tb_text,
                    language=language,
                    code_root=code_root,
                    closure_frames=closure,
                    budget=budget,
                )
            )

        if test_report.tests_missing:
            for path in test_report.tests_missing:
                if budget.functions_used >= SNIPPET_MAX_FUNCTIONS:
                    budget.omitted_paths.append(path)
                    continue
                result = _try_extract_frame(
                    (path, 1),
                    language=language,
                    code_root=code_root,
                    budget=budget,
                    frame_order=0,
                )
                if isinstance(result, FunctionSnippet):
                    contexts.append(
                        FailureContext(
                            test_id=f"tests_missing:{path}",
                            message=f"tests missing for {path}",
                            traceback_parse_ok=False,
                            snippets=[result],
                        )
                    )

    if review_findings:
        for file_path, line in _finding_frames(review_findings):
            if budget.functions_used >= SNIPPET_MAX_FUNCTIONS:
                budget.omitted_paths.append(file_path)
                continue
            result = _try_extract_frame(
                (file_path, line or 1),
                language=language,
                code_root=code_root,
                budget=budget,
                frame_order=0,
            )
            if isinstance(result, FunctionSnippet):
                contexts.append(
                    FailureContext(
                        test_id=f"review:{file_path}",
                        message="review finding requires fix",
                        traceback_parse_ok=False,
                        snippets=[result],
                    )
                )

    return contexts, budget.omitted_paths
