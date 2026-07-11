"""Profile 配置模型与 YAML 加载。"""

from multi_agent_code_factory._paths import profiles_dir
from multi_agent_code_factory.profile_config.loader import (
    assert_code_root_outside_repo,
    expand_env_vars,
    list_profile_ids,
    load_profile,
    resolve_path,
)
from multi_agent_code_factory.profile_config.models import (
    V1_PROFILE_IDS,
    CoverageConfig,
    CoverageThresholds,
    HitlConfig,
    ProfileConfig,
    ProfileLoadError,
    TestsMissingConfig,
    ToolchainConfig,
    ValidationBlockOn,
    ValidationConfig,
    ValidationGateConfig,
)

__all__ = [
    "V1_PROFILE_IDS",
    "CoverageConfig",
    "CoverageThresholds",
    "HitlConfig",
    "ProfileConfig",
    "ProfileLoadError",
    "TestsMissingConfig",
    "ToolchainConfig",
    "ValidationBlockOn",
    "ValidationConfig",
    "ValidationGateConfig",
    "assert_code_root_outside_repo",
    "expand_env_vars",
    "list_profile_ids",
    "load_profile",
    "profiles_dir",
    "resolve_path",
]
