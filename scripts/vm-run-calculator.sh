#!/usr/bin/env bash
# Run the calculator live pipeline on the VM (pull latest code, then pipeline).
exec "$(dirname "${BASH_SOURCE[0]}")/vm-run-pipeline.sh" \
  --log-level DEBUG \
  --task-id calculator \
  "实现计算器"
