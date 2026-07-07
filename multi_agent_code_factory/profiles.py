"""Profile YAML loading and normalization."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

from multi_agent_code_factory._paths import profiles_dir, repo_root

_ENV_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")

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


class ToolchainConfig(BaseModel):
    setup: str | None = None
    build: str | None = None
    test_command: str
    test_parser: str = "exit_code_only"
    test_artifacts: list[str] = Field(default_factory=list)
    lint_command: str | None = None
    test_dir_glob: str | None = None


class ValidationGateConfig(BaseModel):
    enabled: bool = True
    block_on: str = "error"
    require_hitl: bool = False
    validate_mermaid: bool = False
    require_hitl_if_flags: list[str] = Field(default_factory=list)


class ValidationConfig(BaseModel):
    spec: ValidationGateConfig = Field(default_factory=ValidationGateConfig)
    design: ValidationGateConfig = Field(default_factory=ValidationGateConfig)


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


def expand_env_vars(value: str) -> str:
    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in os.environ:
            msg = f"undefined environment variable: {name}"
            raise ProfileLoadError(msg)
        return os.environ[name]

    return _ENV_VAR_PATTERN.sub(replace, value)


def resolve_path(raw: str, *, base: Path) -> Path:
    expanded = expand_env_vars(raw)
    path = Path(expanded)
    if path.is_absolute():
        return path.resolve()
    return (base / path).resolve()


def assert_code_root_outside_repo(code_root: Path, factory_repo: Path) -> None:
    resolved_root = factory_repo.resolve()
    resolved_code = code_root.resolve()
    if resolved_code == resolved_root:
        msg = f"code_root must not be the factory repository root: {resolved_code}"
        raise ProfileLoadError(msg)
    try:
        resolved_code.relative_to(resolved_root)
    except ValueError:
        return
    msg = (
        f"code_root must be outside the factory repository: {resolved_code} "
        f"(repo={resolved_root})"
    )
    raise ProfileLoadError(msg)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = dict(base)
    for key, value in override.items():
        if key == "extends":
            continue
        existing = merged.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            merged[key] = _deep_merge(existing, value)
        else:
            merged[key] = value
    return merged


def _extends_yaml_path(extends: str, *, profiles_root: Path) -> Path:
    relative = extends.removesuffix(".yaml")
    return profiles_root / f"{relative}.yaml"


def _read_profile_mapping(
    path: Path,
    *,
    profiles_root: Path,
    _stack: list[str] | None = None,
) -> dict[str, Any]:
    stack = list(_stack or [])
    with path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    if not isinstance(raw, dict):
        msg = f"expected mapping in profile file: {path}"
        raise ProfileLoadError(msg)

    data = dict(raw)
    extends = data.pop("extends", None)
    if extends is None:
        return data

    if not isinstance(extends, str) or not extends.strip():
        msg = f"invalid extends in profile file: {path}"
        raise ProfileLoadError(msg)

    extends_key = extends.strip()
    if extends_key in stack:
        msg = f"circular extends in profile chain: {' -> '.join([*stack, extends_key])}"
        raise ProfileLoadError(msg)

    parent_path = _extends_yaml_path(extends_key, profiles_root=profiles_root)
    if not parent_path.is_file():
        msg = f"extends profile not found: {extends_key!r} ({parent_path})"
        raise ProfileLoadError(msg)

    parent = _read_profile_mapping(
        parent_path,
        profiles_root=profiles_root,
        _stack=[*stack, path.stem],
    )
    return _deep_merge(parent, data)


def _normalize_raw_profile(raw: dict[str, Any]) -> dict[str, Any]:
    data = dict(raw)
    profile_id = data.get("id")
    if not isinstance(profile_id, str) or not profile_id:
        msg = "profile id is required"
        raise ProfileLoadError(msg)

    toolchain_raw = dict(data.get("toolchain") or {})
    top_level_test = data.get("test_command")
    if isinstance(top_level_test, str) and "test_command" not in toolchain_raw:
        toolchain_raw["test_command"] = top_level_test
    if "test_command" not in toolchain_raw:
        msg = f"profile {profile_id!r} missing toolchain.test_command"
        raise ProfileLoadError(msg)
    if "test_parser" not in toolchain_raw:
        toolchain_raw["test_parser"] = "exit_code_only"
    data["toolchain"] = toolchain_raw
    return data


def _profile_yaml_path(
    profile_id: str,
    *,
    root_profiles_dir: Path | None = None,
) -> Path:
    directory = root_profiles_dir or profiles_dir()
    path = directory / f"{profile_id}.yaml"
    if not path.is_file():
        msg = f"profile not found: {profile_id!r} ({path})"
        raise ProfileLoadError(msg)
    return path


def list_profile_ids(*, root_profiles_dir: Path | None = None) -> list[str]:
    directory = root_profiles_dir or profiles_dir()
    return sorted(path.stem for path in directory.glob("*.yaml"))


def load_profile(
    profile_id: str,
    *,
    factory_repo: Path | None = None,
    profiles_root: Path | None = None,
    code_root_override: str | Path | None = None,
) -> ProfileConfig:
    """Load and validate a profile by id."""
    factory = (factory_repo or repo_root()).resolve()
    profiles_root_path = profiles_root or profiles_dir()
    yaml_path = _profile_yaml_path(profile_id, root_profiles_dir=profiles_root_path)
    raw = _read_profile_mapping(yaml_path, profiles_root=profiles_root_path)
    normalized = _normalize_raw_profile(raw)
    if normalized.get("id") != profile_id:
        msg = (
            f"profile id mismatch: file {yaml_path.name} vs id={normalized.get('id')!r}"
        )
        raise ProfileLoadError(msg)

    code_root_raw = (
        str(code_root_override)
        if code_root_override is not None
        else str(normalized["code_root"])
    )
    code_root = resolve_path(code_root_raw, base=factory)
    assert_code_root_outside_repo(code_root, factory)

    prompts_raw = normalized.get("prompts_dir")
    if not isinstance(prompts_raw, str) or not prompts_raw:
        msg = f"profile {profile_id!r} missing prompts_dir"
        raise ProfileLoadError(msg)
    prompts_path = resolve_path(prompts_raw, base=factory)

    payload: dict[str, Any] = {
        "id": profile_id,
        "language": normalized.get("language"),
        "code_root": code_root,
        "code_root_raw": code_root_raw,
        "prompts_dir": prompts_path,
        "tools": normalized.get("tools") or [],
        "toolchain": normalized["toolchain"],
        "validation": normalized.get("validation") or {},
        "context_schema": normalized.get("context_schema"),
        "auto_generate_tests": bool(normalized.get("auto_generate_tests", False)),
        "hitl": normalized.get("hitl") or {},
        "subscriptions": normalized.get("subscriptions"),
        "sandbox": normalized.get("sandbox"),
        "mcp_servers": normalized.get("mcp_servers"),
    }
    return ProfileConfig.model_validate(payload)
