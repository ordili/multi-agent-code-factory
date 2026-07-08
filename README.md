# multi-agent-code-factory

A **LangGraph** pipeline (PM, Architect, Developer, QA, Reviewer) that turns natural-language requirements into **testable code**, with a full audit trail under `docs/runs/<task-id>/` (spec, design, test_report, review, and more).

**V1** is a domain-agnostic engine: language and toolchain come from a **Profile** (`python`, `go`, `java`, `rust`, `solidity`). Domain packs are planned for **V2** in [`domains/`](domains/README.md) (out of V1 scope).

## Requirements

- Python **3.11+**
- **Stub mode** (default) needs no API key; **Live mode** needs LLM config (below)

## Quick Start (Stub)

```bash
pip install -e ".[dev]"

python -m multi_agent_code_factory run \
  --profile python \
  --task-id calculator \
  "Build a calculator with add, subtract, multiply, and divide"
```

Success when the terminal prints `status=completed`.

> **Windows (PowerShell):** Do not use bash `\` line continuation; use a single line or backtick `` ` `` continuation.

## Where outputs go

| What | Path |
|------|------|
| Audit artifacts (JSON + human-readable MD) | `docs/runs/<task-id>/` |
| Generated code | Profile `code_root` (default outside repo: `../generated/<profile-id>/`) |

Override the code directory with `--code-root`, e.g. `--code-root ../generated/calculator`.

## Configuration

| What to configure | Where |
|-------------------|--------|
| Language stack, test commands, validation rules | [`multi_agent_code_factory/profiles/`](multi_agent_code_factory/profiles/) → [profiles/README.md](multi_agent_code_factory/profiles/README.md) |
| LLM provider, API keys | Copy [`.env.example`](.env.example) to `.env` (CLI loads it; shell env wins) |
| Loop limits and factory defaults | [`config/autonomy_policy.yaml`](config/autonomy_policy.yaml); override with `FACTORY_*` or CLI |
| This run’s task | `--task-id` + natural-language request in quotes |

### Profile and language selection

`--profile` is **required**. It selects the **language stack** (test commands, prompts, etc.; in V1, profile id matches the language name). Use **`python`** for your first run. Separate projects with `--task-id` + `--code-root`. Details: [profiles/README.md](multi_agent_code_factory/profiles/README.md).

## Live LLM (optional)

```bash
pip install -e ".[llm]"
cp .env.example .env   # Windows: copy .env.example .env
# Edit .env: FACTORY_LLM_PROVIDER, FACTORY_LLM_MODEL, and the matching API key
```

```bash
python -m multi_agent_code_factory run \
  --profile python \
  --task-id calculator \
  --live \
  --code-root "../generated/calculator" \
  "Build a calculator with add, subtract, multiply, and divide"
```

Common flags: `--stub` (default), `--live`, `--log-level`, `--code-root`, `--max-impl-retries`, etc. Full list:

```bash
python -m multi_agent_code_factory run --help
```

Ollama, GCP VM, integration tests, and troubleshooting: [docs/operations.md](docs/operations.md).

## Development

```bash
pip install -e ".[dev]"
python -m ruff check . && python -m ruff format --check .
python -m pytest -q
python -m mypy multi_agent_code_factory
```

Live integration test (needs API key; skipped in CI by default):

```bash
pytest tests/integration/test_todo_cli_e2e.py -m integration
```

Python style guide: [docs/design/pipeline/python-style.md](docs/design/pipeline/python-style.md)

## Documentation

| Doc | Purpose |
|-----|---------|
| [docs/README.md](docs/README.md) | Doc index and run artifact map |
| [docs/design/pipeline/multi-agent-pipeline-design.md](docs/design/pipeline/multi-agent-pipeline-design.md) | Pipeline architecture, routing, artifacts |
| [multi_agent_code_factory/profiles/README.md](multi_agent_code_factory/profiles/README.md) | Profile fields and built-in language stacks |
| [docs/design/pipeline/P1-backlog.md](docs/design/pipeline/P1-backlog.md) | Maintainers: P1 backlog checklist |

Repository layout:

```text
multi-agent-code-factory/
├── multi_agent_code_factory/   # Engine (graph, agents, validators, profiles)
├── config/                     # autonomy_policy.yaml
├── docs/design/                # Design specs
├── docs/runs/<task_id>/        # Per-run audit artifacts
└── scripts/                    # VM run scripts
```
