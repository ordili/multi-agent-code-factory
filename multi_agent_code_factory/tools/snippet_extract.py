"""按语言从源码提取函数体或 fallback 非对称 hunk。"""

from __future__ import annotations

import ast
from dataclasses import dataclass

SNIPPET_MAX_FUNCTION_LINES = 200
SNIPPET_LONG_FUNCTION_LINES_BEFORE = 100
SNIPPET_LONG_FUNCTION_LINES_AFTER = 20
SNIPPET_FALLBACK_LINES_BEFORE = 80
SNIPPET_FALLBACK_LINES_AFTER = 20

_TRUNCATED_SUFFIX = "\n... (snippet truncated)"


@dataclass(frozen=True)
class ExtractedSnippet:
    content: str
    function: str | None
    line_start: int
    line_end: int
    total_file_lines: int
    truncated: bool


def _asymmetric_hunk(
    lines: list[str],
    line: int,
    *,
    before: int,
    after: int,
) -> tuple[str, int, int, bool]:
    total = len(lines)
    start = max(1, line - before)
    end = min(total, line + after)
    content = "\n".join(lines[start - 1 : end])
    truncated = start > 1 or end < total
    if truncated:
        content = content + _TRUNCATED_SUFFIX
    return content, start, end, truncated


def _python_function_span(source: str, line: int) -> tuple[int, int, str | None] | None:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.end_lineno is None or node.lineno is None:
            continue
        if node.lineno <= line <= node.end_lineno:
            return node.lineno, node.end_lineno, node.name
    return None


def extract_snippet(
    source: str,
    line: int,
    *,
    language: str,
) -> ExtractedSnippet:
    """从全文与锚点行提取 snippet（函数体优先，否则非对称 hunk）。"""
    lines = source.splitlines()
    total = len(lines)
    if total == 0:
        return ExtractedSnippet("", None, 1, 1, 0, False)

    function_name: str | None = None
    span: tuple[int, int] | None = None
    if language == "python":
        found = _python_function_span(source, line)
        if found is not None:
            start, end, function_name = found
            span = (start, end)

    if span is not None:
        start, end = span
        func_lines = lines[start - 1 : end]
        func_len = len(func_lines)
        if func_len <= SNIPPET_MAX_FUNCTION_LINES:
            content = "\n".join(func_lines)
            return ExtractedSnippet(
                content=content,
                function=function_name,
                line_start=start,
                line_end=end,
                total_file_lines=total,
                truncated=False,
            )
        content, hunk_start, hunk_end, truncated = _asymmetric_hunk(
            func_lines,
            line - start + 1,
            before=SNIPPET_LONG_FUNCTION_LINES_BEFORE,
            after=SNIPPET_LONG_FUNCTION_LINES_AFTER,
        )
        return ExtractedSnippet(
            content=content,
            function=function_name,
            line_start=hunk_start + start - 1,
            line_end=hunk_end + start - 1,
            total_file_lines=total,
            truncated=True,
        )

    content, start, end, truncated = _asymmetric_hunk(
        lines,
        line,
        before=SNIPPET_FALLBACK_LINES_BEFORE,
        after=SNIPPET_FALLBACK_LINES_AFTER,
    )
    return ExtractedSnippet(
        content=content,
        function=None,
        line_start=start,
        line_end=end,
        total_file_lines=total,
        truncated=truncated,
    )
