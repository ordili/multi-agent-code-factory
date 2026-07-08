"""LLM message assembly."""

from __future__ import annotations

import json
from typing import Any

from multi_agent_code_factory.agent_roles import STYLE_SNIPPET_ROLES, AgentRole
from multi_agent_code_factory.agents.llm.prompt.loader import load_role_prompt
from multi_agent_code_factory.profiles import ProfileConfig


def build_llm_messages(
    profile: ProfileConfig,
    *,
    role_id: AgentRole,
    context: dict[str, Any],
    extra_system: str | None,
) -> tuple[str, str]:
    """Build system/user messages: role prompt + optional snippets + JSON context."""
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
