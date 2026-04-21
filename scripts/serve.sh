#!/usr/bin/env bash
# Serve the rendered HTML report on a local HTTP server.
# Usage: bash scripts/serve.sh [--port 8765]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Activate conda environment if available
if command -v conda &>/dev/null; then
  CONDA_ENV="${CONDA_ENV:-ai-news}"
  eval "$(conda shell.bash hook)"
  conda activate "$CONDA_ENV" 2>/dev/null || true
fi

cd "$PROJECT_ROOT"

# Load .env if present
if [ -f "$PROJECT_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$PROJECT_ROOT/.env"
  set +a
fi

PORT=8765
while [[ $# -gt 0 ]]; do
  case "$1" in
    --port) PORT="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

REPORT_DIR="$HOME/social_scanner/rendered"
mkdir -p "$REPORT_DIR"

if [ ! -f "$REPORT_DIR/index.html" ]; then
  echo "No report found. Run 'bash scripts/run.sh' first." >&2
  exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Serving report at http://localhost:$PORT/"
exec python -m http.server "$PORT" --directory "$REPORT_DIR"
