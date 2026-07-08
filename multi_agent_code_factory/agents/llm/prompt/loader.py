"""角色 system prompt 加载。"""

from __future__ import annotations

from multi_agent_code_factory.agent_roles import AgentRole
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
