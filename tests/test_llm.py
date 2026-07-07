from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from multi_agent_code_factory.agents.live_helpers import normalize_spec
from multi_agent_code_factory.agents.pm import run_pm
from multi_agent_code_factory.config import LoopLimits
from multi_agent_code_factory.llm import (
    LlmConfigError,
    create_chat_model,
    llm_available,
    resolve_chat_model_id,
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
    profile = load_profile("python")
    raw = load_snippet_json(snippets_dir, "spec-default.json")
    raw["profile"] = "wrong"
    spec = SpecArtifact.model_validate(raw)
    state = PipelineState(user_request="todo")
    normalized = normalize_spec(spec, profile, state)
    assert normalized.profile == "python"
    assert normalized.context.get("language") == "python"
    assert normalized.revision == 1


def test_resolve_chat_model_id_defaults_to_openai_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("FACTORY_CHAT_MODEL", raising=False)
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-chat")
    assert resolve_chat_model_id() == "openai:deepseek-chat"


def test_resolve_chat_model_id_factory_chat_model_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FACTORY_CHAT_MODEL", "openai:gpt-4o-mini")
    assert resolve_chat_model_id() == "openai:gpt-4o-mini"


def test_create_chat_model_uses_init_chat_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    fake_model = object()
    calls: list[tuple[str, dict[str, object]]] = []

    def fake_init_chat_model(model: str, **kwargs: object) -> object:
        calls.append((model, kwargs))
        return fake_model

    monkeypatch.setattr(
        "langchain.chat_models.init_chat_model",
        fake_init_chat_model,
    )
    result = create_chat_model()
    assert result is fake_model
    assert calls[0][0] == "openai:deepseek-chat"
    assert calls[0][1]["api_key"] == "sk-test"
    assert calls[0][1]["base_url"] == "https://api.deepseek.com"


def test_pm_live_invokes_llm_runner(
    tmp_path: Path,
    snippets_dir: Path,
) -> None:
    profile = load_profile("python")
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
    assert result["spec"].profile == "python"
    assert (tmp_path / "spec.json").is_file()
