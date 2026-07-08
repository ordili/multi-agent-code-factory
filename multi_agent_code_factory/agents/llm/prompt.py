"""LLM 角色 prompt 加载与消息组装。"""

from __future__ import annotations

import json
from typing import Any

from multi_agent_code_factory.agent_roles import STYLE_SNIPPET_ROLES, AgentRole
from multi_agent_code_factory.profiles import ProfileConfig


def load_role_prompt(profile: ProfileConfig, role_id: AgentRole) -> str:
    """加载角色 system prompt；优先 ``{role_id}.txt``，否则回退到通用 snippet。"""
    path = profile.prompts_dir / f"{role_id}.txt"
    if path.is_file():
        return path.read_text(encoding="utf-8")
    fallback = profile.prompts_dir / "python-style-snippet.txt"
    if fallback.is_file():
        return fallback.read_text(encoding="utf-8")
    return (
        f"You are the {role_id} agent. Output must match the requested JSON schema."
    )


def build_llm_messages(
    profile: ProfileConfig,
    *,
    role_id: AgentRole,
    context: dict[str, Any],
    extra_system: str | None,
) -> tuple[str, str]:
    """组装 system/user 消息：角色 prompt + 可选风格 snippet + JSON 化上下文。"""
    system_parts = [load_role_prompt(profile, role_id)]
    style = profile.prompts_dir / "python-style-snippet.txt"
    if role_id in STYLE_SNIPPET_ROLES and style.is_file():
        system_parts.append(style.read_text(encoding="utf-8"))
    if extra_system:
        system_parts.append(extra_system)
    system_prompt = "\n\n".join(
        part.strip() for part in system_parts if part.strip()
    )
    user_prompt = json.dumps(context, ensure_ascii=False, indent=2)
    return system_prompt, user_prompt
