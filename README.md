# multi-agent-code-factory

A **LangGraph** pipeline (PM, Architect, Developer, QA, Reviewer) that turns natural-language requirements into **testable code**, with a full audit trail under `docs/runs/<task-id>/` (spec, design, test_report, review, and more).

**V1** is a domain-agnostic engine: language and toolchain come from a **Profile** (`python`, `go`, `java`, `rust`, `solidity`). Domain packs are planned for **V2** in [`domains/`](domains/README.md) (out of V1 scope).

## Requirements

- Python **3.11+**
- An LLM provider API key (DeepSeek, OpenAI, Anthropic) or a local [Ollama](https://ollama.com/) setup
- **Language toolchains** for the profile you run (e.g. Python 3 + pytest for `python`; [Rust](https://rustup.rs/) + Cargo for `rust`; [Foundry](https://book.getfoundry.sh/getting-started/installation) for `solidity`)

## Quick Start

### 1. Configure API key

```bash
pip install -e ".[llm]"
cp .env.example .env
```

Edit `.env` — set provider, model, and the matching API key:

```env
FACTORY_LLM_PROVIDER=deepseek
FACTORY_LLM_MODEL=deepseek-v4-pro
DEEPSEEK_API_KEY=sk-your-key-here
```

For Ollama or other providers, see [`.env.example`](.env.example) and [docs/operations.md](docs/operations.md).

### 2. Run the pipeline

```bash
python -m multi_agent_code_factory run \
  --profile python \
  --task-id calculator \
  --live \
  --code-root "../generated/calculator" \
  "Build a calculator with add, subtract, multiply, and divide"
```

Success when the terminal prints `status=completed`.

### 3. Continue from existing artifacts

If a run failed or stopped, resume from `docs/runs/<task-id>/` without re-running PM/Architect:

```bash
python -m multi_agent_code_factory continue \
  --task-id calculator \
  --live
```

The pipeline re-runs the gate for the inferred stage first (e.g. QA re-tests code), then calls LLM agents only if needed. Re-running the same `task-id` with `run` is rejected unless you pass `--force-new`.

Design spec: [docs/design/pipeline/artifact-continue-design.md](docs/design/pipeline/artifact-continue-design.md).

## Where outputs go

| What | Path |
|------|------|
| Audit artifacts (JSON + human-readable MD) | `docs/runs/<task-id>/` |
| Generated code | Profile `code_root` (default outside repo: `../generated/<profile-id>/`) |

Override the code directory with `--code-root`, e.g. `--code-root ../generated/calculator`.

## Configuration

| What to configure | Where |
|-------------------|--------|
| LLM provider, API keys | [`.env`](.env.example) (CLI loads it; shell env wins) |
| Language stack, test commands, validation rules | [`multi_agent_code_factory/profiles/`](multi_agent_code_factory/profiles/) → [profiles/README.md](multi_agent_code_factory/profiles/README.md) |
| Loop limits and factory defaults | [`config/autonomy_policy.yaml`](config/autonomy_policy.yaml); override with `FACTORY_*` or CLI |
| This run’s task | `--task-id` + natural-language request in quotes |

### Profile and language selection

`--profile` is **required**. It selects the **language stack** (test commands, prompts, etc.; in V1, profile id matches the language name). Use **`python`** for your first run. Separate projects with `--task-id` + `--code-root`. Details: [profiles/README.md](multi_agent_code_factory/profiles/README.md).

| Profile | Toolchain (local QA) |
|---------|----------------------|
| `python` | Python 3 + `pytest` |
| `rust` | Rust toolchain (`cargo test --message-format=json`) |
| `solidity` | Foundry (`forge test --json`) |
| `java` | JDK + Maven or Gradle |
| `go` | Go + `go test` (parser `go_json` still P1) |

Common CLI flags: `--live`, `--log-level`, `--code-root`, `--max-impl-retries`, etc.

```bash
python -m multi_agent_code_factory run --help
```

Ollama tuning, GCP VM scripts, and troubleshooting: [docs/operations.md](docs/operations.md).

## Development

```bash
pip install -e ".[dev]"
pre-commit install          # once per clone; runs ruff on every commit
pre-commit run --all-files  # optional: verify entire tree before push
python -m pytest -q
python -m mypy multi_agent_code_factory
```

On Windows, if `pre-commit` is not on `PATH`, use `python -m pre_commit install` / `python -m pre_commit run --all-files`.

`pre-commit` mirrors CI lint/format gates locally. If a hook fixes files, stage the changes and commit again.

Run the pipeline in **stub mode** (default; no API key, uses JSON fixtures) to exercise the full graph and write audit artifacts under `docs/runs/<task-id>/`:

```bash
python -m multi_agent_code_factory run --profile python --task-id demo "hello"
```

Integration test (needs API key; skipped in CI by default):

```bash
pytest tests/integration/test_todo_cli_e2e.py -m integration
```

Python style guide: [docs/design/pipeline/python-style.md](docs/design/pipeline/python-style.md)

## Documentation

| Doc | Purpose |
|-----|---------|
| [docs/README.md](docs/README.md) | Doc index and run artifact map |
| [docs/design/pipeline/multi-agent-pipeline-design.md](docs/design/pipeline/multi-agent-pipeline-design.md) | Pipeline architecture, routing, artifacts |
| [docs/design/pipeline/artifact-continue-design.md](docs/design/pipeline/artifact-continue-design.md) | Artifact-based `continue` resume |
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
