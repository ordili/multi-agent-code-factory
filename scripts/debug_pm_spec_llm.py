#!/usr/bin/env python3
"""
PM — SpecArtifact LLM 调试（独立运行）

改本文件里的常量即可调试，无需走 pipeline：
  - SYSTEM_PROMPT — 内联 system（与 pm.txt + 语言 snippet 对齐）
  - REQUIRED_FORMAT_SNIPPET — 输出 JSON（也是 system 末尾 Example）
  - USER_CONTEXT — user 消息（pipeline 的 context）

修改 pipeline prompt 时请同步更新本文件内 SYSTEM_PROMPT（与 pm.txt 保持一致）。

运行（请在仓库根目录，或用下方 .bat）::

    python scripts/debug_pm_spec_llm.py --dry-run
    python scripts/debug_pm_spec_llm.py --show-prompts
    scripts\\run_debug_pm_spec_llm.bat --dry-run

Code Runner 若报「系统找不到指定的路径」，是扩展未找到 python 可执行文件；
请用集成终端运行，或配置 code-runner.executorMap 指向本机 python 全路径。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# 无论从 scripts/ 还是 Code Runner 启动，都切到仓库根并保证可 import 包
_REPO_ROOT = Path(__file__).resolve().parent.parent
os.chdir(_REPO_ROOT)
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# ruff: noqa: E402
import argparse
import json

from langchain_core.messages import HumanMessage, SystemMessage
from multi_agent_code_factory.agents.llm.strategies.prompted_json import (
    extract_json_text,
)
from multi_agent_code_factory.env import load_env_file
from multi_agent_code_factory.llm import (
    create_chat_model,
    resolve_llm_runtime_config,
)
from multi_agent_code_factory.schemas.spec import SpecArtifact
from pydantic import ValidationError

# ---------------------------------------------------------------------------
# 我们要求的 SpecArtifact 输出格式（= system 末尾 Example JSON shape）
# ---------------------------------------------------------------------------

REQUIRED_FORMAT_SNIPPET: dict = {
    "version": "1",
    "profile": "python",
    "revision": 1,
    "title": "CLI 四则运算计算器",
    "summary": "命令行四则运算",
    "context": {
        "language": "python",
        "interface": "cli",
        "storage": "none",
    },
    "success_metrics": [],
    "features": [
        {
            "id": "FEAT-1",
            "name": "四则运算",
            "description": "加减乘除",
            "priority": "P0",
            "user_story_ids": ["US-1"],
        }
    ],
    "user_stories": [
        {
            "id": "US-1",
            "as_a": "CLI 使用者",
            "want": "输入表达式并得到结果",
            "so_that": "完成基础计算",
        }
    ],
    "requirement_pool": [
        {"id": "REQ-1", "description": "表达式求值", "priority": "P0"}
    ],
    "scope_in": ["四则运算 CLI"],
    "scope_out": ["GUI"],
    "operational_profile": {
        "user_scale": "personal",
        "high_concurrency": False,
        "performance": {"tier": "best_effort"},
    },
    "consistency_profile": {
        "consistency_model": "local_only",
        "delivery": "best_effort",
        "multi_writer": False,
        "idempotency_required": False,
        "conflict_strategy": "not_applicable",
    },
    "acceptance_criteria": [
        {
            "id": "AC-1",
            "description": "pytest 测试全部通过（覆盖 US-1）",
            "verifiable_by": "automated_test",
        }
    ],
    "constraints": ["no_secrets_in_repo"],
}

_EXAMPLE_JSON = json.dumps(REQUIRED_FORMAT_SNIPPET, ensure_ascii=False, indent=2)

# ---------------------------------------------------------------------------
# User prompt — pipeline 里 agent_context(PM) 的 JSON（可直接改）
# ---------------------------------------------------------------------------

USER_CONTEXT: dict = {
    "user_request": ("Build a calculator with add, subtract, multiply, and divide"),
    "profile": {
        "id": "python",
        "language": "python",
        "code_root": "D:/code/generated/python",
    },
}

USER_PROMPT = json.dumps(USER_CONTEXT, ensure_ascii=False, indent=2)

# ---------------------------------------------------------------------------
# System prompt — 内联全文（= pm.txt + artifact-language-snippet + JSON 规则 + Example）
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = f"""You are the PM (product manager) agent for a code factory pipeline.

Produce a complete SpecArtifact JSON that matches the pipeline schema:
- version "1"; profile (match input context.profile.id); revision >= 1 (default 1)
- title, summary, context (context.language = implementation language, e.g. python)
- context.storage: required — declare persistence medium explicitly:
  local_file | json_file | database | none | memory | stateless
  (drives downstream design table_schemas / diagrams obligations)
- context.glossary: array of {{term, definition}} for domain terms and user personas
  — NOT plain strings; each entry needs non-empty term and definition
  (user_stories.as_a should reuse glossary role terms)
- context.audience / deployment (optional product-shape keys,
  e.g. audience: single_user) are NOT operational_profile.user_scale —
  user_scale MUST use personal | team | multi_tenant | internet
- features: non-empty list of objects
  {{id, name, description, priority, user_story_ids?}}
  — NOT plain strings; capability-level descriptions (not Connextra user-story wording)
  priority MUST be one of: P0 | P1 | P2
  P0 features should include user_story_ids with at least one US-* when possible
- user_stories: list of objects {{id, as_a, want, so_that}} — NOT plain strings
- requirement_pool: list of objects {{id, description, priority}} — NOT a nested dict
  priority MUST be one of: P0 | P1 | P2
- scope_in: non-empty string[]; scope_out: string[] (may be [])
- operational_profile: object with user_scale, high_concurrency (bool), performance.tier
  user_scale MUST be one of: personal | team | multi_tenant | internet
  performance.tier MUST be one of: best_effort | interactive | low_latency | custom
- consistency_profile: object with consistency_model, delivery, multi_writer,
  idempotency_required, conflict_strategy when relevant
  consistency_model: local_only | strong | eventual | session | custom
  delivery: best_effort | at_most_once | at_least_once | exactly_once
  conflict_strategy: not_applicable | single_writer | last_write_wins |
    versioned_merge | manual
  Stateless / no-persistence CLI (storage=none): prefer
  consistency_model=local_only, delivery=best_effort, multi_writer=false,
  idempotency_required=false, conflict_strategy=not_applicable
  Multi-writer or shared storage: set conflict_strategy (not not_applicable)
  consistency_model=custom requires non-empty consistency_profile.notes
- success_metrics: list of objects {{id, name, description, target, verifiable_by}}
  — NOT plain strings; may be [] when no business KPI (spec.md §4 renders as 无)
  verifiable_by: automated_test | manual | deploy_check | lint
  Small CLI / goals already in summary + acceptance_criteria: prefer success_metrics: []
  KPI = business outcome (spec.md §4); do NOT put engineering gates
  (pytest pass, lint clean) in success_metrics — put them in acceptance_criteria
- acceptance_criteria: non-empty list of objects {{id, description, verifiable_by}}
  — NOT plain strings
  each P0 user story should be traceable in AC description or a manual KPI;
  verifiable_by: automated_test | manual | deploy_check | lint
  include verifiable_by automated_test where profile test toolchain applies
- constraints (e.g. no_secrets_in_repo)

When spec_validation is present in the input context, fix every listed violation.
When review is present with next_stage pm, address scope issues from review findings.

Output only structured data matching the SpecArtifact schema.

Human-readable artifact language (spec.json, design.json, review.json,
and rendered spec.md / design.md / review.md):

- Write all descriptive and narrative text in Simplified Chinese (简体中文).
  Examples: title, summary, feature/user_story/requirement/AC descriptions,
  non_goals, architecture.solution_strategy, module responsibility,
  error_catalog user-facing messages, test case descriptions, review finding messages,
  Mermaid diagram node labels (sequence / flowchart).
- Keep machine identifiers in English: id fields (FEAT-*, US-*, AC-*, REQ-*, KPI-*,
  ERR-*, TC-*), error_catalog[].code (not id), code_domain, file paths,
  API/operation names, enum literal values.
- spec.context.language is the implementation programming language (e.g. python),
  NOT the prose language of PRD/design documents.

Output ONLY one JSON object. No markdown fences, no commentary.
Match field names and nested object shapes exactly.

Example JSON shape:
{_EXAMPLE_JSON}"""


def _print_prompts() -> None:
    print("\n--- SYSTEM PROMPT ---\n")
    print(SYSTEM_PROMPT)
    print("\n--- USER PROMPT ---\n")
    print(USER_PROMPT)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Debug PM SpecArtifact LLM call")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print prompts only; do not call LLM",
    )
    parser.add_argument(
        "--show-prompts",
        action="store_true",
        help="Also print system/user prompts before calling LLM",
    )

    args = parser.parse_args(argv)

    try:
        load_env_file()
        runtime = resolve_llm_runtime_config()
    except Exception as exc:
        print(f"Failed to load LLM config: {exc}", file=sys.stderr)
        print(
            "Hint: run from repo root; ensure .env exists and pip install -e '.[llm]'",
            file=sys.stderr,
        )
        return 1

    print(f"LLM: {runtime.factory_provider} / {runtime.model} / {runtime.output_mode}")

    system_prompt = SYSTEM_PROMPT

    if args.dry_run or args.show_prompts:
        _print_prompts()

    if args.dry_run:
        return 0

    print("\n--- LLM RESPONSE (raw) ---\n")

    model = create_chat_model()

    response = model.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=USER_PROMPT)]
    )
    raw = getattr(response, "content", response)
    if not isinstance(raw, str):
        raw = str(raw)
    print(raw)

    try:
        payload = json.loads(extract_json_text(raw))
    except json.JSONDecodeError as exc:
        print(f"\nJSON parse failed: {exc}")
        return 1

    print("\n--- PARSED JSON ---\n")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    try:
        spec = SpecArtifact.model_validate(payload)
    except ValidationError as exc:
        print("\nValidation failed:")
        print(exc)
        return 1

    print("\n--- VALIDATION OK ---")
    print(f"user_scale={spec.operational_profile.user_scale.value!r}")
    print(f"success_metrics={len(spec.success_metrics)} item(s)")
    print(f"title={spec.title!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
