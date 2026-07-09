"""流水线 Agent 角色 ID（prompt 文件、日志、LLM 调用、watch 订阅共用）。"""

from __future__ import annotations

from enum import StrEnum


class AgentRole(StrEnum):
    """各 Agent 角色的唯一标识。"""

    PM = "pm"
    ARCHITECT = "architect"
    DEVELOPER = "developer"
    QA = "qa"
    REVIEWER = "reviewer"
    DEPLOY_HITL = "deploy_hitl"
    ESCALATION_HITL = "escalation_hitl"
    DEPLOY = "deploy"


# 组装 system prompt 时需附加 {language}-style-snippet 的角色（仅输出源码）。
STYLE_SNIPPET_ROLES: frozenset[AgentRole] = frozenset({AgentRole.DEVELOPER})

# 组装 system prompt 时需附加 artifact-language-snippet 的角色（人读产物 JSON 字段）。
ARTIFACT_LANGUAGE_ROLES: frozenset[AgentRole] = frozenset(
    {AgentRole.PM, AgentRole.ARCHITECT, AgentRole.REVIEWER}
)
