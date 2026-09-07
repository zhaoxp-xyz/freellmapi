#!/bin/bash
# APAMC → freellmapi catalog merge script
# Runs after APAMC scan completes

set -e

APAMC_RESULTS="${APAMC_RESULTS:-$HOME/all-platforms-all-models-check/results}"
DB_PATH="${DB_PATH:-$HOME/freellmapi/server/data/freeapi.db}"
SCRIPT_PATH="${SCRIPT_PATH:-$HOME/freellmapi/scripts/apamc_catalog_merge.py}"

echo "=== APAMC Catalog Merge ==="
echo "Results: $APAMC_RESULTS"
echo "DB: $DB_PATH"
echo ""

python3 "$SCRIPT_PATH" --db "$DB_PATH" --results "$APAMC_RESULTS"
