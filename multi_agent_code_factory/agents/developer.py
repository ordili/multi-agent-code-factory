"""Developer agent node."""

from __future__ import annotations

from multi_agent_code_factory.agents.base import (
    agent_context,
    default_stub_fixtures,
    load_json_fixture,
)
from multi_agent_code_factory.agents.llm_runner import LlmRunner
from multi_agent_code_factory.agents.llm_schemas import DeveloperLLMOutput
from multi_agent_code_factory.profiles import ProfileConfig
from multi_agent_code_factory.schemas.dev_manifest import (
    ChangedFile,
    ChangeType,
    DevManifest,
)
from multi_agent_code_factory.state import PipelineState
from multi_agent_code_factory.tools.linter import run_linter
from multi_agent_code_factory.tools.write_artifact import RunArtifactWriter
from multi_agent_code_factory.tools.write_file import write_file


def _manifest_from_output(output: DeveloperLLMOutput) -> DevManifest:
    changed = [
        ChangedFile(path=item.path, change_type=ChangeType.CREATE)
        for item in output.source_files
    ]
    return DevManifest(
        version="1",
        tasks_completed=output.tasks_completed,
        changed_files=changed,
        notes=output.notes,
    )


def run_developer(
    state: PipelineState,
    profile: ProfileConfig,
    writer: RunArtifactWriter,
    *,
    stub: bool = True,
    llm_runner: LlmRunner | None = None,
) -> dict[str, object]:
    if stub:
        manifest = DevManifest.model_validate(
            load_json_fixture(default_stub_fixtures().dev_manifest)
        )
    else:
        if llm_runner is None:
            msg = "llm_runner is required when stub=False"
            raise ValueError(msg)
        if state.spec is None or state.design is None:
            msg = "developer requires spec and design in live mode"
            raise ValueError(msg)
        output = llm_runner.invoke_structured(
            role_id="developer",
            schema=DeveloperLLMOutput,
            context=agent_context("developer", state, profile),
        )
        code_root = profile.code_root
        code_root.mkdir(parents=True, exist_ok=True)
        for source_file in output.source_files:
            write_file(code_root, source_file.path, source_file.content)
        manifest = _manifest_from_output(output)
        if "linter" in profile.tools:
            manifest = manifest.model_copy(
                update={"lint_passed": run_linter(profile).passed}
            )

    writer.write_model("dev_manifest.json", manifest)
    return {"dev_manifest": manifest}
