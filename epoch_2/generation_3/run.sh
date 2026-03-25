#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MAIN_GOAL_FILE="$SCRIPT_DIR/MAIN_GOAL.md"
AGENTS_MD="$SCRIPT_DIR/AGENTS.md"

main_goal="$(<"$MAIN_GOAL_FILE")"

# Сформировать промпт с контекстом
PROMPT="$main_goal"

(
  cd "$SCRIPT_DIR"

  echo "$PROMPT" | claude \
    --print \
    --append-system-prompt "$(<"$AGENTS_MD")" \
    --dangerously-skip-permissions
)
