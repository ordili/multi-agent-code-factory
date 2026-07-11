"""Developer retry context: failure_contexts, patch mode, parsers."""

from __future__ import annotations

from pathlib import Path

import pytest
from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.developer_output import apply_developer_output
from multi_agent_code_factory.agents.llm.prompt.validation_feedback import (
    format_developer_retry_extra_system,
    format_review_retry_feedback,
)
from multi_agent_code_factory.agents.llm.schemas import (
    DeveloperLLMOutput,
    SourceFileWrite,
)
from multi_agent_code_factory.profile_config import ProfileConfig, ToolchainConfig
from multi_agent_code_factory.prompt_context import (
    build_prompt_context,
    build_retry_bundle,
)
from multi_agent_code_factory.retry_context import (
    SNIPPET_MAX_FUNCTIONS,
    build_failure_contexts,
    paired_paths,
)
from multi_agent_code_factory.schemas.dev_manifest import (
    ChangedFile,
    ChangeType,
    DevManifest,
)
from multi_agent_code_factory.schemas.review import (
    Finding,
    FindingCategory,
    FindingRouting,
    FindingSeverity,
    ReviewNextStage,
    ReviewReport,
)
from multi_agent_code_factory.schemas.test_report import (
    TestFailure,
    TestReport,
    TestSummary,
)
from multi_agent_code_factory.state import PipelineState
from multi_agent_code_factory.tools.snippet_extract import extract_snippet
from multi_agent_code_factory.tools.test_parsers._types import CommandResult
from multi_agent_code_factory.tools.test_parsers.go_json import parse_go_json
from multi_agent_code_factory.tools.test_parsers.registry import get_parser
from multi_agent_code_factory.tools.traceback.python import parse_python_traceback

from tests.conftest import load_snippet_json


def _profile(language: str = "python", code_root: Path | None = None) -> ProfileConfig:
    root = code_root or Path(".")
    return ProfileConfig(
        id=language,
        language=language,
        code_root=root,
        code_root_raw=str(root),
        prompts_dir=Path("."),
        tools=[],
        toolchain=ToolchainConfig(test_command="test", test_parser="junit_xml"),
    )


@pytest.fixture
def default_profile():
    from multi_agent_code_factory.profile_config import load_profile

    return load_profile("python")


def test_retry_bundle_slim_no_prd_design(
    default_profile,
    snippets_dir: Path,
    tmp_path: Path,
) -> None:
    from multi_agent_code_factory.schemas.design import DesignArtifact
    from multi_agent_code_factory.schemas.prd import PrdArtifact

    spec = PrdArtifact.model_validate(
        load_snippet_json(snippets_dir, "prd-default.json")
    )
    design = DesignArtifact.model_validate(
        load_snippet_json(Path(__file__).parent / "fixtures", "design-todo-valid.json")
    )
    report = TestReport(
        version="1",
        passed=False,
        exit_code=1,
        summary=TestSummary(total=1, passed=0, failed=1, skipped=0),
        failures=[],
        duration_sec=0.1,
        command="pytest",
        parser="junit_xml",
    )
    state = PipelineState(
        task_id="t",
        user_request="todo",
        prd=spec,
        design=design,
        test_report=report,
        dev_manifest=DevManifest(version="1", changed_files=[]),
        impl_retry_count=1,
    )
    bundle = build_retry_bundle(state, default_profile)
    assert bundle is not None
    dumped = bundle.model_dump(mode="json")
    assert "prd" not in dumped
    assert "design" not in dumped

    ctx = build_prompt_context(AgentRole.DEVELOPER, state, default_profile)
    assert ctx["impl_mode"] == "retry_patch"
    assert "prd" in ctx
    assert "design" in ctx
    assert "retry_bundle" in ctx
    assert "prd" not in ctx["retry_bundle"]
    assert "design" not in ctx["retry_bundle"]


def test_patch_only_writes_modify_change_type(tmp_path: Path) -> None:
    code_root = tmp_path / "code"
    code_root.mkdir()
    existing = code_root / "src" / "a.py"
    existing.parent.mkdir(parents=True)
    existing.write_text("old\n", encoding="utf-8")

    profile = _profile(code_root=code_root)
    output = DeveloperLLMOutput(
        tasks_completed=["T1"],
        source_files=[SourceFileWrite(path="src/a.py", content="new\n")],
    )
    manifest = apply_developer_output(profile, output, patch_only=True)
    assert existing.read_text(encoding="utf-8") == "new\n"
    assert manifest.changed_files == [
        ChangedFile(path="src/a.py", change_type=ChangeType.MODIFY)
    ]
    untouched = code_root / "src" / "b.py"
    untouched.parent.mkdir(parents=True, exist_ok=True)
    untouched.write_text("keep\n", encoding="utf-8")
    manifest2 = apply_developer_output(
        profile,
        DeveloperLLMOutput(
            tasks_completed=["T1"],
            source_files=[SourceFileWrite(path="src/c.py", content="created\n")],
        ),
        patch_only=True,
    )
    assert untouched.read_text(encoding="utf-8") == "keep\n"
    assert manifest2.changed_files[-1].change_type == ChangeType.CREATE


def test_python_traceback_call_path(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    tb = """Traceback (most recent call last):
  File "tests/test_calc.py", line 14, in test_mixed
  File "src/calc_core.py", line 45, in evaluate
  File "src/calc_core.py", line 102, in _parse
ValueError: bad
"""
    frames = parse_python_traceback(tb, code_root=tmp_path)
    assert len(frames) >= 2
    assert frames[0].role.value == "root_cause"
    assert frames[0].file == "src/calc_core.py"
    assert frames[0].line == 102


def test_long_function_truncated_asymmetric() -> None:
    lines = [f"line {i}" for i in range(1, 301)]
    source = "def big():\n" + "\n".join(f"    {line}" for line in lines)
    extracted = extract_snippet(source, 250, language="python")
    assert extracted.truncated is True
    content_lines = extracted.content.splitlines()
    assert len(content_lines) <= 121


def test_fallback_hunk_asymmetric() -> None:
    lines = [f"line {i}" for i in range(1, 201)]
    source = "\n".join(lines)
    extracted = extract_snippet(source, 150, language="java")
    assert extracted.truncated is True
    assert extracted.line_start == 70
    assert extracted.line_end == 170


def test_build_failure_contexts_budget(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    for index in range(SNIPPET_MAX_FUNCTIONS + 2):
        (src / f"f{index}.py").write_text(f"def f{index}():\n    return {index}\n")
    failures = [
        TestFailure(
            test_id=f"t{i}",
            message="err",
            file=f"src/f{i}.py",
            line=1,
        )
        for i in range(SNIPPET_MAX_FUNCTIONS + 2)
    ]
    report = TestReport(
        version="1",
        passed=False,
        exit_code=1,
        summary=TestSummary(
            total=len(failures), passed=0, failed=len(failures), skipped=0
        ),
        failures=failures,
        duration_sec=1.0,
        command="pytest",
        parser="junit_xml",
    )
    contexts, omitted = build_failure_contexts(
        test_report=report,
        language="python",
        code_root=tmp_path,
    )
    assert contexts
    assert any(ctx.omitted_frames for ctx in contexts) or omitted


def test_paired_paths_matches_src_from_test() -> None:
    pairs = paired_paths(
        "tests/test_calc.py",
        known_paths=["src/calc_core.py", "tests/test_calc.py"],
        code_root=Path("."),
    )
    assert ("src/calc_core.py", None) in pairs


def test_review_retry_feedback_and_bundle(tmp_path: Path) -> None:
    src = tmp_path / "src" / "bad.py"
    src.parent.mkdir(parents=True)
    src.write_text("x = 1\n", encoding="utf-8")
    review = ReviewReport(
        version="1",
        approved=False,
        next_stage=ReviewNextStage.DEVELOPER,
        summary="fix security issue",
        findings=[
            Finding(
                id="F1",
                severity=FindingSeverity.CRITICAL,
                category=FindingCategory.SECURITY,
                message="hardcoded secret",
                blocking=True,
                file="src/bad.py",
                routing=FindingRouting.DEVELOPER_FIX,
            )
        ],
    )
    state = PipelineState(
        user_request="x",
        impl_retry_count=1,
        dev_manifest=DevManifest(version="1", changed_files=[]),
        test_report=TestReport(
            version="1",
            passed=True,
            exit_code=0,
            summary=TestSummary(total=1, passed=1, failed=0, skipped=0),
            duration_sec=1.0,
            command="pytest",
            parser="junit_xml",
        ),
        review=review,
    )
    feedback = format_review_retry_feedback(state)
    assert feedback is not None
    assert "hardcoded secret" in feedback
    combined = format_developer_retry_extra_system(state, _profile(code_root=tmp_path))
    assert combined is not None
    bundle = build_retry_bundle(state, _profile(code_root=tmp_path))
    assert bundle is not None
    assert bundle.retry_cause == "review_rejection"
    assert bundle.failure_contexts


def test_go_json_parser_registered_and_parses_failures() -> None:
    stdout = "\n".join(
        [
            '{"Action":"run","Package":"mypkg","Test":"TestAdd"}',
            (
                '{"Action":"output","Package":"mypkg","Test":"TestAdd",'
                '"Output":"calc.go:12: panic\\n"}'
            ),
            '{"Action":"fail","Package":"mypkg","Test":"TestAdd"}',
        ]
    )
    profile = _profile("go")
    report = parse_go_json(
        CommandResult(1, stdout, "", 0.5, "go test -json ./..."),
        profile,
        Path("."),
    )
    assert get_parser("go_json") is parse_go_json
    assert report.passed is False
    assert len(report.failures) == 1
    assert report.failures[0].output is not None
    assert report.failures[0].file == "calc.go"
    assert report.failures[0].line == 12
