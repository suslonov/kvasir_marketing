#!/usr/bin/env bash
# Run one full scanner cycle.
# Suitable for cron: */10 * * * * /path/to/kvasir_marketing/scripts/run_scheduler.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$REPO_DIR/runtime/logs"

mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/scheduler_$(date +%Y%m%d).log"

echo "$(date -Iseconds) [run_scheduler] Starting..." | tee -a "$LOG_FILE"

# Activate conda env if configured
if [[ -n "${KVASIR_CONDA_ENV:-}" ]]; then
  source "$(conda info --base)/etc/profile.d/conda.sh"
  conda activate "$KVASIR_CONDA_ENV"
fi

# Activate virtualenv if configured
if [[ -n "${KVASIR_VENV:-}" && -f "$KVASIR_VENV/bin/activate" ]]; then
  source "$KVASIR_VENV/bin/activate"
fi

cd "$REPO_DIR"

# Load .env if present
if [[ -f "$REPO_DIR/.env" ]]; then
  set -a
  source "$REPO_DIR/.env"
  set +a
fi

python -m src.scheduler_entry 2>&1 | tee -a "$LOG_FILE"
STATUS=${PIPESTATUS[0]}

echo "$(date -Iseconds) [run_scheduler] Finished with status=$STATUS" | tee -a "$LOG_FILE"
exit "$STATUS"
