from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from multi_agent_code_factory._paths import repo_root
from multi_agent_code_factory.profiles import (
    V1_PROFILE_IDS,
    ProfileLoadError,
    assert_code_root_outside_repo,
    list_profile_ids,
    load_profile,
    profiles_dir,
)


@pytest.mark.parametrize("profile_id", sorted(V1_PROFILE_IDS))
def test_v1_matrix_profiles_load(profile_id: str) -> None:
    profile = load_profile(profile_id)
    assert profile.id == profile_id
    assert profile.toolchain.test_command
    assert profile.toolchain.test_parser
    assert profile.prompts_dir.is_absolute()
    assert profile.code_root.is_absolute()
    assert_code_root_outside_repo(profile.code_root, repo_root())


def test_default_profile_normalizes_toolchain() -> None:
    profile = load_profile("default")
    assert profile.language == "python"
    assert profile.toolchain.test_parser == "junit_xml"
    assert "junit.xml" in profile.toolchain.test_artifacts[0]
    assert profile.validation.design.validate_mermaid is False


def test_list_profile_ids_includes_default() -> None:
    ids = list_profile_ids()
    assert "default" in ids


def test_rejects_code_root_inside_factory_repo(tmp_path: Path) -> None:
    bad_root = repo_root() / "generated" / "inside"
    profile_yaml = tmp_path / "bad.yaml"
    profile_yaml.write_text(
        yaml.safe_dump(
            {
                "id": "bad",
                "code_root": str(bad_root),
                "prompts_dir": "multi_agent_code_factory/profiles/default/prompts",
                "tools": ["read_file"],
                "toolchain": {"test_command": "true"},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ProfileLoadError, match="outside the factory repository"):
        load_profile("bad", profiles_root=tmp_path, factory_repo=repo_root())


def test_resolve_relative_code_root() -> None:
    profile = load_profile("default")
    expected = (repo_root() / "../generated/default").resolve()
    assert profile.code_root == expected


def test_expand_env_vars_for_code_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    generated = tmp_path / "generated" / "custom"
    generated.mkdir(parents=True)
    monkeypatch.setenv("FACTORY_CODE_ROOT", str(tmp_path / "generated"))

    profiles_root = tmp_path / "profiles"
    profiles_root.mkdir()
    profile_yaml = profiles_root / "env-root.yaml"
    profile_yaml.write_text(
        yaml.safe_dump(
            {
                "id": "env-root",
                "code_root": "${FACTORY_CODE_ROOT}/custom",
                "prompts_dir": "multi_agent_code_factory/profiles/default/prompts",
                "tools": ["read_file"],
                "toolchain": {"test_command": "true", "test_parser": "exit_code_only"},
            }
        ),
        encoding="utf-8",
    )
    profile = load_profile(
        "env-root",
        profiles_root=profiles_root,
        factory_repo=repo_root(),
    )
    assert profile.code_root == generated.resolve()


def test_missing_profile_raises() -> None:
    with pytest.raises(ProfileLoadError, match="profile not found"):
        load_profile("does-not-exist-profile")


def test_top_level_test_command_shorthand(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    profile_yaml = tmp_path / "shorthand.yaml"
    profile_yaml.write_text(
        yaml.safe_dump(
            {
                "id": "shorthand",
                "code_root": str(out_dir),
                "prompts_dir": "multi_agent_code_factory/profiles/default/prompts",
                "tools": [],
                "test_command": "pytest -q",
            }
        ),
        encoding="utf-8",
    )
    profile = load_profile(
        "shorthand",
        profiles_root=tmp_path,
        factory_repo=repo_root(),
    )
    assert profile.toolchain.test_command == "pytest -q"
    assert profile.toolchain.test_parser == "exit_code_only"


def test_profiles_dir_points_at_package() -> None:
    assert (profiles_dir() / "default.yaml").is_file()
