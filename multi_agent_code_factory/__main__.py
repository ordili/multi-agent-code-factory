"""CLI entry: python -m multi_agent_code_factory run ..."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from multi_agent_code_factory.config import load_factory_config
from multi_agent_code_factory.env import load_env_file
from multi_agent_code_factory.graph import run_pipeline
from multi_agent_code_factory.llm import LlmConfigError, resolve_stub_mode
from multi_agent_code_factory.profiles import ProfileLoadError, load_profile
from multi_agent_code_factory.schemas.run_meta import RunStatus


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="multi_agent_code_factory")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run the multi-agent pipeline")
    run_parser.add_argument(
        "--profile",
        required=True,
        help="Profile id (see multi_agent_code_factory/profiles/)",
    )
    run_parser.add_argument(
        "--task-id",
        required=True,
        help="Task id for docs/runs/<task_id>/ artifacts",
    )
    run_parser.add_argument(
        "--stub",
        action="store_true",
        help="Use fixture stub agents (default)",
    )
    run_parser.add_argument(
        "--live",
        action="store_true",
        help="Use real LLM agents (requires API key for FACTORY_LLM_PROVIDER)",
    )
    run_parser.add_argument(
        "--code-root",
        default=None,
        help="Override profile code_root for this run",
    )
    run_parser.add_argument(
        "--max-impl-retries",
        type=int,
        default=None,
        help="Override FACTORY_MAX_IMPL_RETRIES for this run",
    )
    run_parser.add_argument(
        "--max-design-revisions",
        type=int,
        default=None,
        help="Override FACTORY_MAX_DESIGN_REVISIONS for this run",
    )
    run_parser.add_argument(
        "--max-spec-revisions",
        type=int,
        default=None,
        help="Override FACTORY_MAX_SPEC_REVISIONS for this run",
    )
    run_parser.add_argument(
        "user_request",
        nargs="+",
        help="Natural-language task description",
    )
    return parser


def cmd_run(args: argparse.Namespace) -> int:
    user_request = " ".join(args.user_request).strip()
    if not user_request:
        print("error: user_request must not be empty", file=sys.stderr)
        return 2

    try:
        stub = resolve_stub_mode(stub=args.stub, live=args.live)
        factory_config = load_factory_config(
            max_impl_retries=args.max_impl_retries,
            max_design_revisions=args.max_design_revisions,
            max_spec_revisions=args.max_spec_revisions,
        )
        profile = load_profile(
            args.profile,
            code_root_override=args.code_root,
        )
    except (ProfileLoadError, ValueError, FileNotFoundError, LlmConfigError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = run_pipeline(
        task_id=args.task_id,
        user_request=user_request,
        profile=profile,
        factory_config=factory_config,
        stub=stub,
    )
    mode = "stub" if stub else "live"
    print(f"task_id={args.task_id}")
    print(f"profile={profile.id}")
    print(f"code_root={profile.code_root}")
    print(f"test_parser={profile.toolchain.test_parser}")
    print(f"user_request={user_request!r}")
    print(f"mode={mode}")
    if not stub:
        from multi_agent_code_factory.llm import resolve_llm_runtime_config

        llm_cfg = resolve_llm_runtime_config()
        print(f"llm_provider={llm_cfg.factory_provider}")
        print(f"llm_model={llm_cfg.model}")
    print(f"loop_limits={factory_config.loop_limits.model_dump()}")
    print(f"run_dir={result.run_dir}")
    print(f"status={result.status.value}")
    return 0 if result.status == RunStatus.COMPLETED else 1


def main(argv: Sequence[str] | None = None) -> int:
    load_env_file()
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.command == "run":
        return cmd_run(args)
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
