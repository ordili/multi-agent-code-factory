"""Profile 配置 Pydantic 模型。"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

V1_PROFILE_IDS = frozenset(
    {
        "python",
        "go",
        "java",
        "rust",
        "solidity",
    }
)


class ProfileLoadError(ValueError):
    """Raised when a profile cannot be loaded or validated."""


class ValidationBlockOn(StrEnum):
    """校验门禁：达到何种严重级别时阻断流水线。"""

    ERROR = "error"
    WARN = "warn"
    NEVER = "never"


class ToolchainConfig(BaseModel):
    setup: str | None = None
    build: str | None = None
    test_command: str
    test_parser: str = "exit_code_only"
    test_artifacts: list[str] = Field(default_factory=list)
    lint_command: str | None = None
    test_dir_glob: str | None = None


class TestsMissingConfig(BaseModel):
    """QA 缺测检测：语言感知启发式，是否阻断由 block_on 控制。"""

    enabled: bool = True
    block_on: bool = True
    detector: str = "file_stem"
    inline_tests: bool = False
    scope: str = "dev_tasks"
    retry_hint: str | None = None


class CoverageThresholds(BaseModel):
    line_percent: float | None = Field(default=None, ge=0, le=100)
    branch_percent: float | None = Field(default=None, ge=0, le=100)


class CoverageConfig(BaseModel):
    enabled: bool = False
    block_on: bool = False
    command: str | None = None
    parser: str = "exit_code_only"
    tool: str | None = None
    artifacts: list[str] = Field(default_factory=list)
    thresholds: CoverageThresholds = Field(default_factory=CoverageThresholds)
    include_globs: list[str] = Field(default_factory=list)
    exclude_globs: list[str] = Field(default_factory=list)


class ValidationGateConfig(BaseModel):
    enabled: bool = True
    block_on: ValidationBlockOn = ValidationBlockOn.ERROR
    require_hitl: bool = False
    validate_mermaid: bool = False
    require_hitl_if_flags: list[str] = Field(default_factory=list)
    semantic_block_on: ValidationBlockOn | None = None

    @field_validator("block_on", "semantic_block_on", mode="before")
    @classmethod
    def _coerce_block_on(cls, value: object) -> object:
        if isinstance(value, str):
            return value.lower()
        return value


class ValidationConfig(BaseModel):
    prd: ValidationGateConfig = Field(default_factory=ValidationGateConfig)
    design: ValidationGateConfig = Field(default_factory=ValidationGateConfig)

    @model_validator(mode="before")
    @classmethod
    def _coerce_legacy_spec_key(cls, data: object) -> object:
        if isinstance(data, dict):
            payload = dict(data)
            if "spec" in payload and "prd" not in payload:
                payload["prd"] = payload.pop("spec")
            else:
                payload.pop("spec", None)
            return payload
        return data


class HitlConfig(BaseModel):
    sensitive_globs: list[str] = Field(default_factory=list)
    flags: list[str] = Field(default_factory=list)


class ProfileConfig(BaseModel):
    id: str
    language: str | None = None
    code_root: Path
    code_root_raw: str
    prompts_dir: Path
    tools: list[str]
    toolchain: ToolchainConfig
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    context_schema: dict[str, Any] | None = None
    auto_generate_tests: bool = False
    tests_missing: TestsMissingConfig = Field(default_factory=TestsMissingConfig)
    coverage: CoverageConfig = Field(default_factory=CoverageConfig)
    hitl: HitlConfig = Field(default_factory=HitlConfig)
    subscriptions: dict[str, list[str]] | None = None
    sandbox: str | None = None
    mcp_servers: list[dict[str, Any]] | None = None

    @field_validator("code_root", "prompts_dir", mode="before")
    @classmethod
    def _coerce_path(cls, value: object) -> object:
        if isinstance(value, str):
            return Path(value)
        return value
