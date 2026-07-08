"""Agent 共享辅助：LLM 调用上下文构建。"""

from __future__ import annotations

from typing import Any

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.prompt_context import build_prompt_context
from multi_agent_code_factory.state import PipelineState


def agent_context(
    role_id: AgentRole,
    state: PipelineState,
    profile: ProfileConfig,
) -> dict[str, Any]:
    """为指定 Agent 角色构建 LLM 调用上下文。"""
    return build_prompt_context(role_id, state, profile)
