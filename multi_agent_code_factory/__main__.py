"""CLI entry: python -m multi_agent_code_factory run ..."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from multi_agent_code_factory.config import load_factory_config
from multi_agent_code_factory.profiles import ProfileLoadError, load_profile


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
        factory_config = load_factory_config(
            max_impl_retries=args.max_impl_retries,
            max_design_revisions=args.max_design_revisions,
            max_spec_revisions=args.max_spec_revisions,
        )
        profile = load_profile(args.profile)
    except (ProfileLoadError, ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"task_id={args.task_id}")
    print(f"profile={profile.id}")
    print(f"code_root={profile.code_root}")
    print(f"test_parser={profile.toolchain.test_parser}")
    print(f"user_request={user_request!r}")
    print(f"loop_limits={factory_config.loop_limits.model_dump()}")
    print("status=not_implemented (pipeline graph is P1+)")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.command == "run":
        return cmd_run(args)
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
