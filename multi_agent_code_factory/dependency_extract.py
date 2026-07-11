"""依赖文件摘要提取（task-batch dependency_artifacts）。"""

from __future__ import annotations

import ast
from pathlib import Path

from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.schemas.task_batch import DependencyArtifact


def _file_header_snippet(text: str, max_lines: int) -> tuple[str, int]:
    lines = text.splitlines()
    end = min(len(lines), max_lines)
    content = "\n".join(lines[:end])
    if end < len(lines):
        content += "\n... (truncated)"
    return content, end


def _python_signature_snippet(text: str, max_lines: int) -> tuple[str, int]:
    """Tier A：提取顶层 public 类/函数签名。"""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return _file_header_snippet(text, max_lines)

    chunks: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name.startswith("_"):
                continue
            line = text.splitlines()[node.lineno - 1].strip()
            chunks.append(line)

    if not chunks:
        return _file_header_snippet(text, max_lines)

    content = "\n".join(chunks[:max_lines])
    if len(chunks) > max_lines:
        content += "\n... (truncated)"
    return content, min(len(chunks), max_lines)


def _solidity_contract_snippet(text: str, max_lines: int) -> tuple[str, int]:
    """Tier C：合约与 function/event 行。"""
    picked: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if (
            stripped.startswith("contract ")
            or stripped.startswith("function ")
            or stripped.startswith("event ")
        ):
            picked.append(stripped)
        if len(picked) >= max_lines:
            break
    if not picked:
        return _file_header_snippet(text, max_lines)
    content = "\n".join(picked)
    if len(text.splitlines()) > len(picked):
        content += "\n... (truncated)"
    return content, len(picked)


def extract_dependency_artifacts(
    paths: list[str],
    profile: ProfileConfig,
    *,
    code_root: Path | None = None,
    max_lines: int = 60,
) -> tuple[list[DependencyArtifact], list[dict[str, str]]]:
    """读取已写盘依赖路径，返回摘要片段与读盘失败列表。"""
    root = code_root or profile.code_root
    artifacts: list[DependencyArtifact] = []
    omitted: list[dict[str, str]] = []

    for path in paths:
        full = root / path
        if not full.is_file():
            omitted.append({"path": path, "reason": "not_found"})
            continue
        text = full.read_text(encoding="utf-8", errors="replace")
        language = profile.language or profile.id
        if language == "python":
            content, end = _python_signature_snippet(text, max_lines)
            kind = "signature_stub"
        elif language == "solidity":
            content, end = _solidity_contract_snippet(text, max_lines)
            kind = "module_header"
        else:
            content, end = _file_header_snippet(text, max_lines)
            kind = "module_header"
        artifacts.append(
            DependencyArtifact(
                path=path,
                kind=kind,
                line_start=1,
                line_end=end,
                content=content,
            )
        )

    return artifacts, omitted
