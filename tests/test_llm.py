from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from multi_agent_code_factory.agents.normalizers.spec import normalize_spec
from multi_agent_code_factory.agents.pm import run_pm
from multi_agent_code_factory.config import LoopLimits
from multi_agent_code_factory.llm import (
    LlmConfigError,
    create_chat_model,
    llm_available,
    resolve_chat_model_id,
)
from multi_agent_code_factory.runtime.stub_mode import resolve_stub_mode
from multi_agent_code_factory.profile_config import load_profile
from multi_agent_code_factory.schemas.spec import SpecArtifact
from multi_agent_code_factory.state import PipelineState
from multi_agent_code_factory.tools.run_artifacts import RunArtifactWriter

from tests.conftest import load_snippet_json


@pytest.fixture(autouse=True)
def _default_deepseek_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FACTORY_LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("FACTORY_LLM_MODEL", "deepseek-chat")


def test_resolve_stub_mode_defaults_to_stub() -> None:
    assert resolve_stub_mode(stub=False, live=False) is True


def test_resolve_stub_mode_live_requires_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(LlmConfigError, match="DEEPSEEK_API_KEY"):
        resolve_stub_mode(stub=False, live=True)


def test_resolve_stub_mode_live_with_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    assert resolve_stub_mode(stub=False, live=True) is False


def test_resolve_stub_mode_rejects_both_flags() -> None:
    with pytest.raises(ValueError, match="both"):
        resolve_stub_mode(stub=True, live=True)


def test_llm_available_checks_active_provider_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    assert llm_available() is False
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    assert llm_available() is True


def test_llm_available_ignores_other_vendor_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai")
    assert llm_available() is False


def test_llm_available_anthropic_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FACTORY_LLM_PROVIDER", "anthropic")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert llm_available() is False
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant")
    assert llm_available() is True


def test_llm_available_ollama_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FACTORY_LLM_PROVIDER", "ollama")
    monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
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


def test_resolve_stub_mode_live_ollama_without_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FACTORY_LLM_PROVIDER", "ollama")
    monkeypatch.setenv("FACTORY_LLM_MODEL", "deepseek-r1:1.5b")
    monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
    assert resolve_stub_mode(stub=False, live=True) is False


def test_resolve_chat_model_id_ollama_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FACTORY_LLM_PROVIDER", "ollama")
    monkeypatch.setenv("FACTORY_LLM_MODEL", "deepseek-r1:1.5b")
    assert resolve_chat_model_id() == "ollama:deepseek-r1:1.5b"


def test_create_chat_model_ollama_passes_performance_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FACTORY_LLM_PROVIDER", "ollama")
    monkeypatch.setenv("FACTORY_LLM_MODEL", "qwen3.5:9b")
    monkeypatch.setenv("OLLAMA_NUM_CTX", "8192")
    monkeypatch.setenv("OLLAMA_NUM_PREDICT", "4096")
    monkeypatch.setenv("OLLAMA_REASONING", "false")
    calls: list[tuple[str, dict[str, object]]] = []

    def fake_init_chat_model(model: str, **kwargs: object) -> object:
        calls.append((model, kwargs))
        return object()

    monkeypatch.setattr(
        "langchain.chat_models.init_chat_model",
        fake_init_chat_model,
    )
    create_chat_model()
    assert calls[0][1]["num_ctx"] == 8192
    assert calls[0][1]["num_predict"] == 4096
    assert calls[0][1]["reasoning"] is False


def test_create_chat_model_ollama_uses_env_base_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FACTORY_LLM_PROVIDER", "ollama")
    monkeypatch.setenv("FACTORY_LLM_MODEL", "deepseek-r1:1.5b")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    calls: list[tuple[str, dict[str, object]]] = []

    def fake_init_chat_model(model: str, **kwargs: object) -> object:
        calls.append((model, kwargs))
        return object()

    monkeypatch.setattr(
        "langchain.chat_models.init_chat_model",
        fake_init_chat_model,
    )
    create_chat_model()
    assert calls[0][0] == "ollama:deepseek-r1:1.5b"
    assert calls[0][1]["base_url"] == "http://127.0.0.1:11434"
    assert "api_key" not in calls[0][1]


def test_resolve_provider_base_url_normalizes_localhost_for_ollama(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from multi_agent_code_factory.llm import resolve_provider_base_url

    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    assert resolve_provider_base_url("ollama") == "http://127.0.0.1:11434"


def test_resolve_chat_model_id_ignores_colon_in_model_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Model tags like ``deepseek-r1:1.5b`` must not override FACTORY_LLM_PROVIDER."""
    monkeypatch.setenv("FACTORY_LLM_PROVIDER", "ollama")
    monkeypatch.setenv("FACTORY_LLM_MODEL", "deepseek-r1:1.5b")
    assert resolve_chat_model_id() == "ollama:deepseek-r1:1.5b"


def test_resolve_llm_runtime_config_uses_factory_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from multi_agent_code_factory.llm import resolve_llm_runtime_config

    monkeypatch.setenv("FACTORY_LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("FACTORY_LLM_MODEL", "deepseek-chat")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    cfg = resolve_llm_runtime_config()
    assert cfg.factory_provider == "deepseek"
    assert cfg.api_key_env == "DEEPSEEK_API_KEY"
    assert cfg.langchain_model_id == "openai:deepseek-chat"
    assert cfg.base_url == "https://api.deepseek.com"
    assert cfg.output_mode == "prompted_json"


def test_resolve_chat_model_id_deepseek_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("FACTORY_LLM_MODEL", raising=False)
    assert resolve_chat_model_id() == "openai:deepseek-chat"


def test_resolve_chat_model_id_openai_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FACTORY_LLM_PROVIDER", "openai")
    monkeypatch.setenv("FACTORY_LLM_MODEL", "gpt-4o-mini")
    assert resolve_chat_model_id() == "openai:gpt-4o-mini"


def test_resolve_chat_model_id_anthropic_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FACTORY_LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("FACTORY_LLM_MODEL", "claude-sonnet-4-6")
    assert resolve_chat_model_id() == "anthropic:claude-sonnet-4-6"


def test_create_chat_model_deepseek_uses_inferred_base_url(
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


def test_create_chat_model_openai_omits_base_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FACTORY_LLM_PROVIDER", "openai")
    monkeypatch.setenv("FACTORY_LLM_MODEL", "gpt-4o")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai")
    calls: list[dict[str, object]] = []

    def fake_init_chat_model(model: str, **kwargs: object) -> object:
        calls.append(kwargs)
        return object()

    monkeypatch.setattr(
        "langchain.chat_models.init_chat_model",
        fake_init_chat_model,
    )
    create_chat_model()
    assert "base_url" not in calls[0]
    assert calls[0]["api_key"] == "sk-openai"


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
