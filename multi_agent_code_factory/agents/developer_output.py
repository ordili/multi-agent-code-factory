"""Developer LLM 输出落地：写源码、lint、构建 dev_manifest。"""

from __future__ import annotations

from multi_agent_code_factory.agents.llm.schemas import DeveloperLLMOutput
from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.schemas.dev_manifest import (
    ChangedFile,
    ChangeType,
    DevManifest,
)
from multi_agent_code_factory.tools.linter import run_linter
from multi_agent_code_factory.tools.write_file import write_file


def _manifest_from_output(
    output: DeveloperLLMOutput,
    *,
    patch_only: bool = False,
    change_types: dict[str, ChangeType] | None = None,
) -> DevManifest:
    changed: list[ChangedFile] = []
    for item in output.source_files:
        change_type = ChangeType.CREATE
        if patch_only and change_types is not None:
            change_type = change_types.get(item.path, ChangeType.CREATE)
        changed.append(ChangedFile(path=item.path, change_type=change_type))
    return DevManifest(
        version="1",
        tasks_completed=output.tasks_completed,
        changed_files=changed,
        notes=output.notes,
    )


def apply_developer_output(
    profile: ProfileConfig,
    output: DeveloperLLMOutput,
    *,
    patch_only: bool = False,
) -> DevManifest:
    """将 LLM 返回的源文件写入 code_root，可选跑 lint，返回 dev_manifest。"""
    code_root = profile.code_root
    code_root.mkdir(parents=True, exist_ok=True)
    change_types: dict[str, ChangeType] = {}
    for source_file in output.source_files:
        if patch_only:
            target = code_root / source_file.path
            change_types[source_file.path] = (
                ChangeType.MODIFY if target.is_file() else ChangeType.CREATE
            )
        write_file(code_root, source_file.path, source_file.content)
    manifest = _manifest_from_output(
        output,
        patch_only=patch_only,
        change_types=change_types,
    )
    if "linter" in profile.tools:
        manifest = manifest.model_copy(
            update={"lint_passed": run_linter(profile).passed}
        )
    return manifest
