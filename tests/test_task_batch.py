"""Task-batch 调度、门禁与 Developer 集成测试。"""

from __future__ import annotations

from pathlib import Path

import pytest
from multi_agent_code_factory.agents.developer_output import (
    apply_developer_output,
    merge_manifest,
)
from multi_agent_code_factory.agents.llm.schemas import (
    DeveloperLLMOutput,
    SourceFileWrite,
)
from multi_agent_code_factory.batch_closure import (
    BatchClosureError,
    BatchOutputError,
    validate_batch_closure,
    validate_batch_output,
)
from multi_agent_code_factory.config import FactoryConfig
from multi_agent_code_factory.dev_task_scheduler import (
    default_test_path,
    kahn_sort_tasks,
    refresh_batch_runtime,
    schedule,
)
from multi_agent_code_factory.profile_config import ProfileConfig, ToolchainConfig
from multi_agent_code_factory.prompt_context import (
    build_task_batch_context,
    resolve_impl_mode,
    should_task_batch,
)
from multi_agent_code_factory.schemas.design import DesignArtifact, DevTask
from multi_agent_code_factory.schemas.dev_manifest import (
    ChangedFile,
    ChangeType,
    DevManifest,
)
from multi_agent_code_factory.schemas.task_batch import TaskBatch, TaskBatchConfig
from multi_agent_code_factory.state import PipelineState


def _profile(code_root: Path, *, language: str = "python") -> ProfileConfig:
    return ProfileConfig(
        id=language,
        language=language,
        code_root=code_root,
        code_root_raw=str(code_root),
        prompts_dir=code_root,
        tools=[],
        toolchain=ToolchainConfig(test_command="true", test_parser="junit_xml"),
    )


def _design(
    tasks: list[dict], *, test_cases: list[dict] | None = None
) -> DesignArtifact:
    payload: dict = {
        "version": "1",
        "title": "t",
        "spec_ref": "t",
        "dev_tasks": tasks,
    }
    if test_cases is not None:
        payload["test_cases"] = test_cases
    return DesignArtifact.model_validate(payload)


def _task(
    task_id: str,
    path: str,
    *,
    depends_on: list[str] | None = None,
    covers: list[str] | None = None,
) -> dict:
    return {
        "id": task_id,
        "path": path,
        "description": f"implement {path}",
        "depends_on": depends_on or [],
        "covers": covers or [],
    }


def test_should_task_batch_threshold() -> None:
    design = _design([_task(f"T{i}", f"src/t{i}.py") for i in range(1, 6)])
    assert should_task_batch(design, FactoryConfig()) is False

    design_many = _design([_task(f"T{i}", f"src/t{i}.py") for i in range(1, 7)])
    assert should_task_batch(design_many, FactoryConfig()) is True


def test_should_task_batch_enabled_flag() -> None:
    design = _design([_task("T1", "a.py")])
    config = FactoryConfig(task_batch=TaskBatchConfig(enabled=True))
    assert should_task_batch(design, config) is True


def test_resolve_impl_mode_retry_overrides_batch() -> None:
    design = _design([_task(f"T{i}", f"t{i}.py") for i in range(1, 8)])
    state = PipelineState(user_request="x", impl_retry_count=1, design=design)
    assert resolve_impl_mode(state, design, FactoryConfig()) == "retry_patch"


def test_kahn_sort_chain() -> None:
    tasks = [
        DevTask.model_validate(_task("T1", "a.py")),
        DevTask.model_validate(_task("T2", "b.py", depends_on=["T1"])),
        DevTask.model_validate(_task("T3", "c.py", depends_on=["T2"])),
    ]
    shuffled = [tasks[2], tasks[0], tasks[1]]
    ordered = kahn_sort_tasks(shuffled)
    assert [t.id for t in ordered] == ["T1", "T2", "T3"]


def test_schedule_one_batch_per_task(tmp_path: Path) -> None:
    design = _design(
        [
            _task("T1", "pyproject.toml"),
            _task("T2", "src/store.py", depends_on=["T1"]),
            _task("T3", "src/cli.py", depends_on=["T2"]),
        ]
    )
    batches = schedule(design, _profile(tmp_path), TaskBatchConfig())
    assert len(batches) == 3
    assert batches[0].task_ids == ["T1"]
    assert batches[1].task_ids == ["T2"]
    assert batches[2].task_ids == ["T3"]


def test_default_test_path_python() -> None:
    profile = _profile(Path("."), language="python")
    assert default_test_path("src/todo_store.py", profile) == "tests/test_todo_store.py"


def test_schedule_maps_test_when_covers(tmp_path: Path) -> None:
    design = _design(
        [_task("T1", "src/store.py", covers=["AC-1"])],
        test_cases=[
            {
                "id": "TC-1",
                "kind": "happy",
                "title": "store works",
                "covers": ["AC-1"],
            }
        ],
    )
    config = TaskBatchConfig(require_tests=True)
    batches = schedule(design, _profile(tmp_path), config)
    assert "tests/test_store.py" in batches[0].required_paths


def test_validate_batch_closure_tests_mapped_fails(tmp_path: Path) -> None:
    design = _design([_task("T1", "src/store.py", covers=["AC-1"])])
    batch = TaskBatch(
        index=0,
        task_ids=["T1"],
        required_paths=["src/store.py"],
        dependency_paths=[],
        relevant_test_case_ids=[],
        estimated_output_lines=400,
    )
    manifest = DevManifest(version="1")
    with pytest.raises(BatchClosureError, match="tests_mapped"):
        validate_batch_closure(
            batch,
            manifest,
            design,
            _profile(tmp_path),
            TaskBatchConfig(require_tests=True),
        )


def test_validate_batch_output_paths_complete() -> None:
    batch = TaskBatch(
        index=0,
        task_ids=["T1"],
        required_paths=["a.py"],
        dependency_paths=[],
        relevant_test_case_ids=[],
    )
    output = DeveloperLLMOutput(
        tasks_completed=["T1"],
        source_files=[SourceFileWrite(path="a.py", content="x = 1\n")],
    )
    validate_batch_output(output, batch, TaskBatchConfig())

    bad = DeveloperLLMOutput(
        tasks_completed=["T1"],
        source_files=[],
    )
    with pytest.raises(BatchOutputError, match="paths_complete"):
        validate_batch_output(bad, batch, TaskBatchConfig())


def test_validate_batch_output_paths_extra() -> None:
    batch = TaskBatch(
        index=0,
        task_ids=["T1"],
        required_paths=["a.py"],
        dependency_paths=[],
        relevant_test_case_ids=[],
    )
    config = TaskBatchConfig(max_extra_output_paths=1)
    output = DeveloperLLMOutput(
        tasks_completed=["T1"],
        source_files=[
            SourceFileWrite(path="a.py", content="a\n"),
            SourceFileWrite(path="b.py", content="b\n"),
            SourceFileWrite(path="c.py", content="c\n"),
        ],
    )
    with pytest.raises(BatchOutputError, match="paths_extra"):
        validate_batch_output(output, batch, config)


def test_merge_manifest_union_tasks_and_files() -> None:
    prev = DevManifest(
        version="1",
        tasks_completed=["T1"],
        changed_files=[ChangedFile(path="a.py", change_type=ChangeType.CREATE)],
    )
    batch = DevManifest(
        version="1",
        tasks_completed=["T2"],
        changed_files=[ChangedFile(path="b.py", change_type=ChangeType.CREATE)],
        notes="batch 2",
    )
    merged = merge_manifest(prev, batch)
    assert merged.tasks_completed == ["T1", "T2"]
    assert {item.path for item in merged.changed_files} == {"a.py", "b.py"}
    assert merged.notes == "batch 2"


def test_build_task_batch_context(tmp_path: Path, snippets_dir: Path) -> None:
    from multi_agent_code_factory.schemas.prd import PrdArtifact

    from tests.conftest import load_snippet_json

    design = DesignArtifact.model_validate(
        load_snippet_json(Path(__file__).parent / "fixtures", "design-todo-valid.json")
    )
    prd = PrdArtifact.model_validate(
        load_snippet_json(snippets_dir, "prd-default.json")
    )
    state = PipelineState(user_request="build", prd=prd, design=design)
    first_task = design.dev_tasks[0]
    batch = TaskBatch(
        index=0,
        task_ids=[first_task.id],
        required_paths=[first_task.path],
        dependency_paths=[],
        relevant_test_case_ids=[],
    )
    manifest = DevManifest(version="1")
    ctx = build_task_batch_context(
        state,
        _profile(tmp_path),
        batch,
        manifest,
        pass_total=len(design.dev_tasks),
    )
    assert ctx["impl_mode"] == "task_batch"
    assert ctx["impl_batch"]["pass_index"] == 1
    assert ctx["impl_batch"]["active_dev_tasks"][0]["id"] == first_task.id


def test_refresh_batch_runtime_injects_prior_outputs(tmp_path: Path) -> None:
    """TB-T4: 后批 dependency_paths 含前批已写盘文件。"""
    design = _design(
        [
            _task("T1", "pyproject.toml"),
            _task("T2", "src/store.py", depends_on=["T1"]),
        ]
    )
    config = TaskBatchConfig()
    empty_root = tmp_path / "empty"
    empty_root.mkdir()
    batches = schedule(design, _profile(empty_root), config)
    assert batches[1].dependency_paths == []

    code_root = tmp_path / "project"
    code_root.mkdir()
    (code_root / "pyproject.toml").write_text(
        "[project]\nname = 'todo'\n", encoding="utf-8"
    )
    profile = _profile(code_root)

    refreshed = refresh_batch_runtime(
        batches[1],
        design,
        profile,
        config,
        code_root=code_root,
    )
    assert refreshed.dependency_paths == ["pyproject.toml"]

    from multi_agent_code_factory.dependency_extract import extract_dependency_artifacts

    artifacts, omitted = extract_dependency_artifacts(
        refreshed.dependency_paths,
        _profile(code_root),
        code_root=code_root,
    )
    assert not omitted
    assert artifacts[0].path == "pyproject.toml"
    assert "name = 'todo'" in artifacts[0].content


def test_patch_only_preserves_prior_batch_files(tmp_path: Path) -> None:
    """TB-T5: 后批 patch 不重写前批未列出文件。"""
    code_root = tmp_path / "project"
    code_root.mkdir()
    profile = _profile(code_root)

    batch1 = DeveloperLLMOutput(
        tasks_completed=["T1"],
        source_files=[SourceFileWrite(path="pyproject.toml", content="v1\n")],
    )
    apply_developer_output(profile, batch1, patch_only=True)

    batch2 = DeveloperLLMOutput(
        tasks_completed=["T2"],
        source_files=[SourceFileWrite(path="src/store.py", content="store\n")],
    )
    apply_developer_output(profile, batch2, patch_only=True)

    assert (code_root / "pyproject.toml").read_text(encoding="utf-8") == "v1\n"
    assert (code_root / "src/store.py").read_text(encoding="utf-8") == "store\n"


@pytest.mark.parametrize(
    ("language", "detector", "task_path", "expected"),
    [
        ("python", "file_stem", "src/store.py", "tests/test_store.py"),
        ("go", "go", "internal/store.go", "internal/store_test.go"),
        ("rust", "rust", "src/store.rs", "tests/store.rs"),
        (
            "java",
            "file_stem",
            "src/main/java/Store.java",
            "src/test/java/StoreTest.java",
        ),
        ("solidity", "file_stem", "src/Token.sol", "test/Token.t.sol"),
    ],
)
def test_default_test_path_multilang(
    language: str,
    detector: str,
    task_path: str,
    expected: str,
) -> None:
    """TB-T8: 五语言 test_paths 默认映射。"""
    from multi_agent_code_factory.profile_config import TestsMissingConfig

    profile = ProfileConfig(
        id=language,
        language=language,
        code_root=Path("."),
        code_root_raw=".",
        prompts_dir=Path("."),
        tools=[],
        toolchain=ToolchainConfig(test_command="true"),
        tests_missing=TestsMissingConfig(detector=detector),
    )
    assert default_test_path(task_path, profile) == expected


def test_fit_task_batch_context_trims_diagrams() -> None:
    """input_budget：超限时裁掉 diagrams / context_view。"""
    from multi_agent_code_factory.context_lines import count_context_lines
    from multi_agent_code_factory.task_batch_context import (
        fit_task_batch_context_to_input_budget,
    )

    huge = "line\n" * 500
    context = {
        "prd": {"version": "1", "title": "t", "summary": "s"},
        "design": {
            "version": "1",
            "summary": "d",
            "diagrams": [{"path": "flow.mmd", "kind": "flowchart", "title": huge}],
            "context_view": {"actors": ["user"], "boundaries": [huge]},
            "architecture": {"summary": "arch", "solution_strategy": "delta"},
            "dev_tasks": [],
        },
        "impl_batch": {"required_paths": ["a.py"], "relevant_test_cases": []},
        "dev_manifest": {"version": "1", "tasks_completed": []},
        "impl_mode": "task_batch",
    }
    before = count_context_lines(context)
    fitted = fit_task_batch_context_to_input_budget(context, max_lines=before - 50)
    assert "diagrams" not in fitted["design"]
    assert "context_view" not in fitted["design"]
    assert count_context_lines(fitted) < before


def test_task_batch_budget_partial_manifest(tmp_path: Path, snippets_dir: Path) -> None:
    """TB-T6: budget 触顶保留已成功批 manifest。"""
    from unittest.mock import MagicMock, patch

    from multi_agent_code_factory.agents.developer import _run_developer_task_batch
    from multi_agent_code_factory.agents.llm import LlmRunner
    from multi_agent_code_factory.agents.llm.budget.errors import LlmBudgetExceededError
    from multi_agent_code_factory.schemas.prd import PrdArtifact

    from tests.conftest import load_snippet_json

    tasks = [
        _task("T1", "pyproject.toml"),
        _task("T2", "src/a.py", depends_on=["T1"]),
        _task("T3", "src/b.py", depends_on=["T2"]),
        _task("T4", "src/c.py", depends_on=["T3"]),
        _task("T5", "src/d.py", depends_on=["T4"]),
        _task("T6", "src/e.py", depends_on=["T5"]),
    ]
    design = _design(tasks)
    prd = PrdArtifact.model_validate(
        load_snippet_json(snippets_dir, "prd-default.json")
    )
    state = PipelineState(user_request="x", prd=prd, design=design)
    profile = _profile(tmp_path)
    profile.code_root.mkdir(parents=True, exist_ok=True)

    call_count = 0

    def fake_invoke(**kwargs):
        batch_ctx = kwargs["context"]
        req = batch_ctx["impl_batch"]["required_paths"]
        task_id = batch_ctx["impl_batch"]["active_dev_tasks"][0]["id"]
        return DeveloperLLMOutput(
            tasks_completed=[task_id],
            source_files=[
                SourceFileWrite(path=path, content=f"# {path}\n") for path in req
            ],
        )

    runner = MagicMock(spec=LlmRunner)
    runner.writer = MagicMock()
    runner.factory_config = FactoryConfig()
    runner.invoke_structured.side_effect = fake_invoke

    def budget_guard(writer, factory_config):
        nonlocal call_count
        call_count += 1
        if call_count >= 2:
            raise LlmBudgetExceededError("budget")

    with patch(
        "multi_agent_code_factory.agents.developer.check_llm_budget",
        side_effect=budget_guard,
    ):
        manifest = _run_developer_task_batch(state, profile, runner, FactoryConfig())

    assert manifest.tasks_completed == ["T1"]
    assert (tmp_path / "pyproject.toml").is_file()


def test_qa_retry_uses_retry_patch_not_task_batch() -> None:
    """TB-T7: QA 后重试走 retry_patch，不重跑 task_batch。"""
    design = _design([_task(f"T{i}", f"t{i}.py") for i in range(1, 8)])
    state = PipelineState(
        user_request="x",
        impl_retry_count=1,
        design=design,
    )
    assert resolve_impl_mode(state, design, FactoryConfig()) == "retry_patch"
    assert should_task_batch(design, FactoryConfig()) is True
