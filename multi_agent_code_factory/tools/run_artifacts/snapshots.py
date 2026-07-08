"""Run 目录快照序列化。"""

from __future__ import annotations

from typing import Any

from multi_agent_code_factory.config import LoopLimits
from multi_agent_code_factory.profile_config import ProfileConfig


def profile_snapshot(profile: ProfileConfig) -> dict[str, Any]:
    """将 Profile 配置序列化为可写入 run_meta 的快照字典。"""
    return {
        "id": profile.id,
        "language": profile.language,
        "code_root": str(profile.code_root),
        "toolchain": profile.toolchain.model_dump(),
    }


def loop_limits_snapshot(limits: LoopLimits) -> dict[str, Any]:
    """将循环限制配置序列化为 JSON 兼容字典。"""
    return limits.model_dump(mode="json")
