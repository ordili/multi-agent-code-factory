"""CLI 入口：``python -m multi_agent_code_factory run|continue ...``"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from multi_agent_code_factory._paths import run_dir
from multi_agent_code_factory.checkpoint import ContinueError
from multi_agent_code_factory.config import load_factory_config
from multi_agent_code_factory.env import load_env_file
from multi_agent_code_factory.graph import continue_pipeline, run_pipeline
from multi_agent_code_factory.llm import LlmConfigError
from multi_agent_code_factory.log import configure_logging, get_logger
from multi_agent_code_factory.profile_config import ProfileLoadError, load_profile
from multi_agent_code_factory.runtime.stub_mode import resolve_stub_mode
from multi_agent_code_factory.schemas.run_meta import RunStatus

logger = get_logger("cli")


def _add_runtime_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--task-id",
        required=True,
        help="Task id for docs/runs/<task_id>/ artifacts",
    )
    parser.add_argument(
        "--stub",
        action="store_true",
        help="Use fixture stub agents (default)",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use real LLM agents (requires API key for FACTORY_LLM_PROVIDER)",
    )
    parser.add_argument(
        "--code-root",
        default=None,
        help="Override profile code_root for this run",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        help="Log level (default: INFO, or FACTORY_LOG_LEVEL from .env)",
    )


def build_parser() -> argparse.ArgumentParser:
    """构建 ``run`` / ``continue`` 子命令及参数定义。"""
    parser = argparse.ArgumentParser(prog="multi_agent_code_factory")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run the multi-agent pipeline")
    run_parser.add_argument(
        "--profile",
        required=True,
        help="Profile id (see multi_agent_code_factory/profiles/)",
    )
    _add_runtime_flags(run_parser)
    run_parser.add_argument(
        "--force-new",
        action="store_true",
        help="Overwrite an existing docs/runs/<task_id>/ directory",
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
        "--max-prd-revisions",
        type=int,
        default=None,
        help="Override FACTORY_MAX_PRD_REVISIONS for this run",
    )
    run_parser.add_argument(
        "user_request",
        nargs="+",
        help="Natural-language task description",
    )

    continue_parser = subparsers.add_parser(
        "continue",
        help="Continue pipeline from existing run artifacts",
    )
    _add_runtime_flags(continue_parser)
    continue_parser.add_argument(
        "--reenter",
        default=None,
        help="Explicit reentry node (prd_validate, design_validate, qa, architect)",
    )
    continue_parser.add_argument(
        "--no-reset-loops",
        action="store_true",
        help="Do not reset loop counters that hit limits on failed runs",
    )
    return parser


def _print_run_summary(
    *,
    task_id: str,
    profile_id: str,
    code_root: object,
    test_parser: str,
    user_request: str | None,
    stub: bool,
    loop_limits: dict[str, object],
    result_run_dir: object,
    status: RunStatus,
) -> None:
    mode = "stub" if stub else "live"
    print(f"task_id={task_id}")
    print(f"profile={profile_id}")
    print(f"code_root={code_root}")
    print(f"test_parser={test_parser}")
    if user_request is not None:
        print(f"user_request={user_request!r}")
    print(f"mode={mode}")
    if not stub:
        from multi_agent_code_factory.llm import resolve_llm_runtime_config

        llm_cfg = resolve_llm_runtime_config()
        print(f"llm_provider={llm_cfg.factory_provider}")
        print(f"llm_model={llm_cfg.model}")
    print(f"loop_limits={loop_limits}")
    print(f"run_dir={result_run_dir}")
    print(f"status={status.value}")


def _print_budget_usage(run_dir_path: object) -> None:
    from pathlib import Path

    meta_path = Path(str(run_dir_path)) / "run_meta.json"
    if meta_path.is_file():
        meta_data = json.loads(meta_path.read_text(encoding="utf-8"))
        budget = meta_data.get("budget")
        if isinstance(budget, dict):
            print(
                "llm_budget="
                f"calls={budget.get('used_llm_calls')} "
                f"tokens={budget.get('used_tokens')}"
            )
    usage_path = Path(str(run_dir_path)) / "llm_usage.json"
    if usage_path.is_file():
        usage_data = json.loads(usage_path.read_text(encoding="utf-8"))
        totals = usage_data.get("totals") or {}
        print(
            "llm_usage="
            f"prompt_tokens={totals.get('prompt_tokens')} "
            f"completion_tokens={totals.get('completion_tokens')} "
            f"total_tokens={totals.get('total_tokens')}"
        )


def cmd_run(args: argparse.Namespace) -> int:
    """解析配置、Live 预检、调用 ``run_pipeline`` 并打印摘要。"""
    user_request = " ".join(args.user_request).strip()
    if not user_request:
        print("error: user_request must not be empty", file=sys.stderr)
        return 2

    existing = run_dir(args.task_id) / "run_meta.json"
    if existing.is_file() and not args.force_new:
        print(
            f"error: run directory already exists for task_id={args.task_id!r}; "
            "use `continue` or `run --force-new`",
            file=sys.stderr,
        )
        return 2

    try:
        stub = resolve_stub_mode(stub=args.stub, live=args.live)
        factory_config = load_factory_config(
            max_impl_retries=args.max_impl_retries,
            max_design_revisions=args.max_design_revisions,
            max_prd_revisions=args.max_prd_revisions,
        )
        profile = load_profile(
            args.profile,
            code_root_override=args.code_root,
        )
    except (ProfileLoadError, ValueError, FileNotFoundError, LlmConfigError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not stub:
        from multi_agent_code_factory.llm import preflight_live_llm

        try:
            preflight_live_llm()
        except LlmConfigError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    result = run_pipeline(
        task_id=args.task_id,
        user_request=user_request,
        profile=profile,
        factory_config=factory_config,
        stub=stub,
    )
    _print_run_summary(
        task_id=args.task_id,
        profile_id=profile.id,
        code_root=profile.code_root,
        test_parser=profile.toolchain.test_parser,
        user_request=user_request,
        stub=stub,
        loop_limits=factory_config.loop_limits.model_dump(),
        result_run_dir=result.run_dir,
        status=result.status,
    )
    _print_budget_usage(result.run_dir)
    return 0 if result.status == RunStatus.COMPLETED else 1


def cmd_continue(args: argparse.Namespace) -> int:
    """从已有产物续跑流水线。"""
    try:
        stub = resolve_stub_mode(stub=args.stub, live=args.live)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if stub:
        logger.warning(
            "continue with --stub; use --live if the original run used real LLM agents"
        )

    if not stub:
        from multi_agent_code_factory.llm import preflight_live_llm

        try:
            preflight_live_llm()
        except LlmConfigError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    try:
        result = continue_pipeline(
            task_id=args.task_id,
            reenter=args.reenter,
            reset_loops=not args.no_reset_loops,
            stub=stub,
            code_root_override=args.code_root,
        )
    except ContinueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    meta_path = result.run_dir / "run_meta.json"
    profile_id = "unknown"
    loop_limits: dict[str, object] = {}
    if meta_path.is_file():
        meta_data = json.loads(meta_path.read_text(encoding="utf-8"))
        profile_block = meta_data.get("profile") or {}
        if isinstance(profile_block, dict):
            profile_id = str(profile_block.get("id", profile_id))
        raw_limits = meta_data.get("loop_limits")
        if isinstance(raw_limits, dict):
            loop_limits = raw_limits

    profile = load_profile(
        profile_id,
        code_root_override=args.code_root,
    )
    _print_run_summary(
        task_id=args.task_id,
        profile_id=profile_id,
        code_root=profile.code_root,
        test_parser=profile.toolchain.test_parser,
        user_request=None,
        stub=stub,
        loop_limits=loop_limits,
        result_run_dir=result.run_dir,
        status=result.status,
    )
    _print_budget_usage(result.run_dir)
    return 0 if result.status == RunStatus.COMPLETED else 1


def main(argv: Sequence[str] | None = None) -> int:
    """加载 .env、初始化日志、分发子命令。"""
    load_env_file()
    configure_logging()
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.log_level is not None:
        configure_logging(level=args.log_level, force=True)
    if args.command == "run":
        return cmd_run(args)
    if args.command == "continue":
        return cmd_continue(args)
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
