"""LLM 消息组装。"""

from __future__ import annotations

import json
from typing import Any

from multi_agent_code_factory.agent_roles import STYLE_SNIPPET_ROLES, AgentRole
from multi_agent_code_factory.agents.llm.prompt.loader import load_role_prompt
from multi_agent_code_factory.agents.llm.prompt.style_snippet import (
    load_dev_principles_snippet,
    load_style_snippet,
)
from multi_agent_code_factory.profile_config import ProfileConfig


def build_llm_messages(
    profile: ProfileConfig,
    *,
    role_id: AgentRole,
    context: dict[str, Any],
    extra_system: str | None,
) -> tuple[str, str]:
    """组装 system/user 消息：角色 prompt、通用 dev 原则、语言 snippet、JSON 上下文。"""
    system_parts = [load_role_prompt(profile, role_id)]
    if role_id in STYLE_SNIPPET_ROLES:
        dev_principles = load_dev_principles_snippet()
        if dev_principles:
            system_parts.append(dev_principles)
        style_text = load_style_snippet(profile)
        if style_text:
            system_parts.append(style_text)
    if extra_system:
        system_parts.append(extra_system)
    system_prompt = "\n\n".join(part.strip() for part in system_parts if part.strip())
    user_prompt = json.dumps(context, ensure_ascii=False, indent=2)
    return system_prompt, user_prompt
