"""Profile 编码规范 snippet 路径解析。"""

from __future__ import annotations

from pathlib import Path

from multi_agent_code_factory._paths import profiles_dir
from multi_agent_code_factory.profile_config import ProfileConfig

_DEV_PRINCIPLES_SNIPPET = (
    profiles_dir() / "_shared" / "prompts" / "dev-principles-snippet.txt"
)


def load_dev_principles_snippet() -> str | None:
    """读取跨语言 Developer 工程原则 snippet。"""
    if not _DEV_PRINCIPLES_SNIPPET.is_file():
        return None
    return _DEV_PRINCIPLES_SNIPPET.read_text(encoding="utf-8")


def style_snippet_candidates(profile: ProfileConfig) -> tuple[Path, ...]:
    """按优先级返回可能的 ``{language}-style-snippet.txt`` 路径。"""
    language = (profile.language or profile.id).strip().lower()
    return (
        profile.prompts_dir / f"{language}-style-snippet.txt",
        profile.prompts_dir / "style-snippet.txt",
    )


def style_snippet_path(profile: ProfileConfig) -> Path | None:
    """返回存在的 style snippet 文件路径，不存在则 ``None``。"""
    for path in style_snippet_candidates(profile):
        if path.is_file():
            return path
    return None


def load_style_snippet(profile: ProfileConfig) -> str | None:
    """读取 profile 编码规范 snippet 文本。"""
    path = style_snippet_path(profile)
    if path is None:
        return None
    return path.read_text(encoding="utf-8")
