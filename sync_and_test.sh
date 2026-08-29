#!/bin/bash
# sync_and_test.sh — Sync production code into the pytest plugin copy and the
# HA test system, then run the tests with the project venv.
# Usage: ./sync_and_test.sh [any pytest arguments]
#
# Examples:
#   ./sync_and_test.sh                                   # all tests
#   ./sync_and_test.sh --cov=custom_components/whenhub   # with coverage
#   ./sync_and_test.sh tests/test_config_flow.py         # single file
#
# rsync --delete keeps tests/custom_components/whenhub/ an exact mirror of the
# production code (cp -r would leave behind files deleted in production).
#
# Always uses ./.venv/bin/python: a bare `pytest` on this machine may resolve
# to another environment (e.g. PlatformIO) and fail on unrelated imports.

set -e

INTEGRATION="whenhub"
HA_TEST_DIR="/home/privathoff/Dokumente/Software/HomeAssistant/_HA Testsystem/ha_config/custom_components/$INTEGRATION"

echo "=== Sync custom_components/$INTEGRATION -> tests/custom_components/$INTEGRATION ==="
rsync -a --delete \
  --exclude="__pycache__" \
  "custom_components/$INTEGRATION/" "tests/custom_components/$INTEGRATION/"

if [ -d "$(dirname "$HA_TEST_DIR")" ]; then
  echo "=== Sync custom_components/$INTEGRATION -> HA test system ==="
  rsync -a --delete \
    --exclude="__pycache__" \
    "custom_components/$INTEGRATION/" "$HA_TEST_DIR/"
else
  echo "=== HA test system not found, skipping ==="
fi
echo "=== Sync done ==="

echo ""
echo "=== Running tests ==="
./.venv/bin/python -m pytest "$@"
