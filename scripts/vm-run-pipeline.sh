#!/usr/bin/env bash
# Pull latest code on a GCP (or other Linux) VM and run the live pipeline.
#
# Usage:
#   ./scripts/vm-run-pipeline.sh --task-id calculator "实现支持加减乘除的计算器"
#
# Optional env overrides:
#   REPO_DIR=/path/to/multi-agent-code-factory
#   CODE_ROOT=/data/generated/calculator
#   PROFILE=python
#   LOG_LEVEL=INFO
#
# Prerequisites on the VM:
#   - git, python3.11+, Ollama running with the model from .env
#   - .env configured at repo root (copy from .env.example)

set -euo pipefail

REPO_DIR="${REPO_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PROFILE="${PROFILE:-python}"
LOG_LEVEL="${LOG_LEVEL:-INFO}"
TASK_ID=""
CODE_ROOT=""
SKIP_PULL=0
SKIP_INSTALL=0
USER_REQUEST=""

usage() {
  cat <<'EOF'
Usage: vm-run-pipeline.sh [options] "natural language task"

Options:
  --task-id ID       Task id for docs/runs/<id>/ (required)
  --profile ID       Profile id (default: python)
  --code-root PATH   Generated code directory (default: /data/generated/<task-id>)
  --log-level LEVEL  Logging level (default: INFO)
  --skip-pull        Do not run git pull
  --skip-install     Do not pip install -e ".[llm]"
  -h, --help         Show this help

Environment:
  REPO_DIR           Repository root (auto-detected from script location)

Example:
  ./scripts/vm-run-pipeline.sh --task-id calculator "实现支持加减乘除的计算器"
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --task-id)
      TASK_ID="${2:?missing value for --task-id}"
      shift 2
      ;;
    --profile)
      PROFILE="${2:?missing value for --profile}"
      shift 2
      ;;
    --code-root)
      CODE_ROOT="${2:?missing value for --code-root}"
      shift 2
      ;;
    --log-level)
      LOG_LEVEL="${2:?missing value for --log-level}"
      shift 2
      ;;
    --skip-pull)
      SKIP_PULL=1
      shift
      ;;
    --skip-install)
      SKIP_INSTALL=1
      shift
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    --)
      shift
      USER_REQUEST="$*"
      break
      ;;
    -*)
      echo "error: unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      USER_REQUEST="$*"
      break
      ;;
  esac
done

if [[ -z "$TASK_ID" ]]; then
  echo "error: --task-id is required" >&2
  usage >&2
  exit 2
fi

if [[ -z "$USER_REQUEST" ]]; then
  echo "error: natural language task description is required" >&2
  usage >&2
  exit 2
fi

if [[ -z "$CODE_ROOT" ]]; then
  CODE_ROOT="/data/generated/${TASK_ID}"
fi

cd "$REPO_DIR"

if [[ "$SKIP_PULL" -eq 0 ]]; then
  echo "==> git pull (--ff-only)"
  git pull --ff-only
fi

if [[ ! -d .venv ]]; then
  echo "==> creating virtualenv .venv"
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

if [[ "$SKIP_INSTALL" -eq 0 ]]; then
  echo "==> pip install -e \".[llm]\""
  pip install -q -U pip setuptools wheel
  pip install -q -e ".[llm]"
fi

if [[ ! -f .env ]]; then
  echo "error: missing .env in $REPO_DIR (copy from .env.example and configure Ollama)" >&2
  exit 2
fi

mkdir -p "$CODE_ROOT"

echo "==> checking Ollama at http://127.0.0.1:11434"
if ! curl -sf --max-time 10 http://127.0.0.1:11434/api/tags >/dev/null; then
  echo "error: Ollama is not reachable. Try: sudo systemctl start ollama" >&2
  exit 2
fi

echo "==> running pipeline (profile=$PROFILE task-id=$TASK_ID code-root=$CODE_ROOT)"
python -m multi_agent_code_factory run \
  --profile "$PROFILE" \
  --task-id "$TASK_ID" \
  --live \
  --log-level "$LOG_LEVEL" \
  --code-root "$CODE_ROOT" \
  "$USER_REQUEST"
