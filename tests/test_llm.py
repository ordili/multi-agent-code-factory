from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from multi_agent_code_factory.agents.live_helpers import normalize_spec
from multi_agent_code_factory.agents.pm import run_pm
from multi_agent_code_factory.config import LoopLimits
from multi_agent_code_factory.llm import (
    LlmConfigError,
    llm_available,
    resolve_stub_mode,
)
from multi_agent_code_factory.profiles import load_profile
from multi_agent_code_factory.schemas.spec import SpecArtifact
from multi_agent_code_factory.state import PipelineState
from multi_agent_code_factory.tools.write_artifact import RunArtifactWriter

from tests.conftest import load_snippet_json


def test_resolve_stub_mode_defaults_to_stub() -> None:
    assert resolve_stub_mode(stub=False, live=False) is True


def test_resolve_stub_mode_live_requires_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(LlmConfigError):
        resolve_stub_mode(stub=False, live=True)


def test_resolve_stub_mode_live_with_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    assert resolve_stub_mode(stub=False, live=True) is False


def test_resolve_stub_mode_rejects_both_flags() -> None:
    with pytest.raises(ValueError, match="both"):
        resolve_stub_mode(stub=True, live=True)


def test_llm_available_reads_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    assert llm_available() is False
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    assert llm_available() is True


def test_normalize_spec_sets_profile_and_language(
    snippets_dir: Path,
) -> None:
    profile = load_profile("default")
    raw = load_snippet_json(snippets_dir, "spec-default.json")
    raw["profile"] = "wrong"
    spec = SpecArtifact.model_validate(raw)
    state = PipelineState(user_request="todo")
    normalized = normalize_spec(spec, profile, state)
    assert normalized.profile == "default"
    assert normalized.context.get("language") == "python"
    assert normalized.revision == 1


def test_pm_live_invokes_llm_runner(
    tmp_path: Path,
    snippets_dir: Path,
) -> None:
    profile = load_profile("default")
    writer = RunArtifactWriter("t", base_dir=tmp_path)
    writer.init_run_meta(profile, LoopLimits())
    spec = SpecArtifact.model_validate(
        load_snippet_json(snippets_dir, "spec-default.json")
    )
    llm_runner = MagicMock()
    llm_runner.invoke_structured.return_value = spec
    state = PipelineState(user_request="实现命令行 Todo", task_id="t")
    result = run_pm(
        state,
        profile,
        writer,
        stub=False,
        llm_runner=llm_runner,
    )
    llm_runner.invoke_structured.assert_called_once()
    assert result["spec"].profile == "default"
    assert (tmp_path / "spec.json").is_file()
