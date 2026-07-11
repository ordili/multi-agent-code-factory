from __future__ import annotations

from pathlib import Path

from multi_agent_code_factory.profile_config import ProfileConfig, ToolchainConfig
from multi_agent_code_factory.tools.test_parsers._types import CommandResult
from multi_agent_code_factory.tools.test_parsers.cargo_json import parse_cargo_json
from multi_agent_code_factory.tools.test_parsers.registry import get_parser


def _profile(parser_id: str, language: str) -> ProfileConfig:
    return ProfileConfig(
        id=language,
        language=language,
        code_root=Path("."),
        code_root_raw=".",
        prompts_dir=Path("."),
        tools=[],
        toolchain=ToolchainConfig(
            test_command="cargo test --message-format=json",
            test_parser=parser_id,
        ),
    )


def test_cargo_json_parser_reads_failures() -> None:
    stdout = (Path(__file__).parent / "fixtures" / "cargo_test_stdout.jsonl").read_text(
        encoding="utf-8"
    )
    profile = _profile("cargo_json", "rust")
    report = parse_cargo_json(
        CommandResult(
            exit_code=101,
            stdout=stdout,
            stderr="",
            duration_sec=1.2,
            command="cargo test --message-format=json",
        ),
        profile,
        Path("."),
    )
    assert report.passed is False
    assert report.parser == "cargo_json"
    assert report.summary.total == 2
    assert report.summary.passed == 1
    assert report.summary.failed == 1
    assert len(report.failures) == 1
    assert report.failures[0].test_id == "mylib::tests::test_sub"


def test_cargo_json_parser_all_pass() -> None:
    stdout = "\n".join(
        [
            '{"reason":"test","type":"test","event":"ok","name":"mylib::tests::ok"}',
        ]
    )
    profile = _profile("cargo_json", "rust")
    report = parse_cargo_json(
        CommandResult(0, stdout, "", 0.3, "cargo test --message-format=json"),
        profile,
        Path("."),
    )
    assert report.passed is True
    assert report.summary.passed == 1
    assert report.failures == []


def test_rust_profile_parser_is_registered() -> None:
    assert get_parser("cargo_json") is parse_cargo_json
