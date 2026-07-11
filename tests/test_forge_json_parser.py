from __future__ import annotations

from pathlib import Path

from multi_agent_code_factory.profile_config import ProfileConfig, ToolchainConfig
from multi_agent_code_factory.tools.test_parsers._types import CommandResult
from multi_agent_code_factory.tools.test_parsers.forge_json import parse_forge_json
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
            test_command="forge test --json",
            test_parser=parser_id,
        ),
    )


def test_forge_json_parser_reads_failures() -> None:
    stdout = (Path(__file__).parent / "fixtures" / "forge_test_stdout.json").read_text(
        encoding="utf-8"
    )
    profile = _profile("forge_json", "solidity")
    report = parse_forge_json(
        CommandResult(
            exit_code=1,
            stdout=stdout,
            stderr="",
            duration_sec=2.0,
            command="forge test --json",
        ),
        profile,
        Path("."),
    )
    assert report.passed is False
    assert report.parser == "forge_json"
    assert report.summary.total == 2
    assert report.summary.passed == 1
    assert report.summary.failed == 1
    assert report.failures[0].test_id == "test/Counter.t.sol:CounterTest::testFail()"
    assert report.failures[0].message == "EvmError: Revert"


def test_forge_json_parser_legacy_success_field() -> None:
    stdout = """{
  "test/Foo.t.sol:FooTest": {
    "test_results": {
      "testBar()": {"success": true, "reason": null},
      "testBaz()": {"success": false, "reason": "panic"}
    }
  }
}"""
    profile = _profile("forge_json", "solidity")
    report = parse_forge_json(
        CommandResult(1, stdout, "", 0.5, "forge test --json"),
        profile,
        Path("."),
    )
    assert report.summary.passed == 1
    assert report.summary.failed == 1


def test_forge_json_parser_tolerates_trailing_human_text() -> None:
    payload = (Path(__file__).parent / "fixtures" / "forge_test_stdout.json").read_text(
        encoding="utf-8"
    )
    stdout = payload + "\n\nFailing tests:\nEncountered 1 failing test\n"
    profile = _profile("forge_json", "solidity")
    report = parse_forge_json(
        CommandResult(1, stdout, "", 0.5, "forge test --json"),
        profile,
        Path("."),
    )
    assert report.summary.failed == 1


def test_solidity_profile_parser_is_registered() -> None:
    assert get_parser("forge_json") is parse_forge_json
