# Artifact Continue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or executing-plans.

**Goal:** Add `continue` CLI to resume pipeline from `docs/runs/<task_id>/` artifacts (gate-first, budget/loop reset).

**Architecture:** `loader.hydrate_state` + `checkpoint.infer_reentry_node` + explicit gate (`run_qa`/`run_*_validate`) + `update_state` + `invoke`. Profile from `load_profile(meta.profile.id)` with snapshot `code_root`.

**Tech Stack:** Python 3.11, LangGraph, langgraph-checkpoint-sqlite, Pydantic, pytest.

**Spec:** [2026-07-10-artifact-continue-design.md](../specs/2026-07-10-artifact-continue-design.md)

---

### Task 1: Schema & run_meta

- `schemas/run_meta.py`: `user_request`, `last_continue_at`, `last_reentry_node`
- `meta.py`: `init(..., user_request=)`, `prepare_continue(reset_loops=True)`
- `runner.run_pipeline`: pass `user_request` to `init_run_meta`

### Task 2: loader + infer

- `tools/run_artifacts/loader.py`: hydrate with stale filter
- `checkpoint.py`: `infer_reentry_node`, `ContinueError`, `state_to_graph_dict`

### Task 3: continue_pipeline + graph

- `graph_builder.build_graph(checkpointer=...)`
- `graph/runner.continue_pipeline`: gate → update_state → invoke
- `pyproject.toml`: `langgraph-checkpoint-sqlite`

### Task 4: CLI

- `__main__.py`: `continue` subcommand; `run` rejects existing run dir without `--force-new`

### Task 5: Tests

- `tests/test_continue_infer.py`, `tests/test_continue_loader.py`, `tests/test_continue_pipeline.py`
