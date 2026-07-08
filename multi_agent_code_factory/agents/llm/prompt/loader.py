"""角色 system prompt 加载。"""

from __future__ import annotations

from pathlib import Path

from multi_agent_code_factory._paths import profiles_dir
from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.profile_config import ProfileConfig

_SHARED_PROMPTS_DIR = profiles_dir() / "_shared" / "prompts"

# 与实现语言无关：PM / Architect / Reviewer 产出 JSON 或 Mermaid，共用 _shared/prompts。
_LANGUAGE_AGNOSTIC_ROLES = frozenset(
    {
        AgentRole.PM,
        AgentRole.ARCHITECT,
        AgentRole.REVIEWER,
    }
)


def _read_prompt(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_role_prompt(profile: ProfileConfig, role_id: AgentRole) -> str:
    """加载角色 system prompt。

    查找顺序：
    1. ``{profile.prompts_dir}/{role_id}.txt``（语言或领域覆盖）
    2. ``profiles/_shared/prompts/{role_id}.txt``（PM/Architect/Reviewer 默认）
    3. 通用 fallback 一行说明
    """
    profile_path = profile.prompts_dir / f"{role_id}.txt"
    if profile_path.is_file():
        return _read_prompt(profile_path)

    shared_path = _SHARED_PROMPTS_DIR / f"{role_id}.txt"
    if shared_path.is_file() and role_id in _LANGUAGE_AGNOSTIC_ROLES:
        return _read_prompt(shared_path)

    return (
        f"You are the {role_id} agent. Output must match the requested JSON schema."
    )
