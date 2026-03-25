#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MAIN_GOAL_FILE="$SCRIPT_DIR/MAIN_GOAL.md"
AGENTS_MD="$SCRIPT_DIR/AGENTS.md"
THINKING_MODE="${CLAUDE_THINKING_MODE:-enabled}"

main_goal="$(<"$MAIN_GOAL_FILE")"

# Собрать контекст из журнала текущей генерации
JOURNAL_CONTEXT=""
if [[ -f "$SCRIPT_DIR/journal.md" ]]; then
  # Последние 200 строк журнала, чтобы не переполнить контекст
  JOURNAL_CONTEXT="$(tail -n 200 "$SCRIPT_DIR/journal.md")"
fi

# Сформировать промпт с контекстом
PROMPT="$main_goal"
if [[ -n "$JOURNAL_CONTEXT" ]]; then
  PROMPT="$PROMPT

---
Журнал текущей генерации (последние записи):
$JOURNAL_CONTEXT"
fi

(
  cd "$SCRIPT_DIR"

  echo "$PROMPT" | claude \
    --print \
    --thinking "$THINKING_MODE" \
    --append-system-prompt "$(<"$AGENTS_MD")" \
    --dangerously-skip-permissions \
    --tools default
)
