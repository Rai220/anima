#!/bin/bash
# loop.sh — Непрерывный цикл запуска агента до завершения TODO-цикла
# Использование: bash loop.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TODO_FILE="$SCRIPT_DIR/TODO.md"

todo_cycle_completed() {
  [[ -f "$TODO_FILE" ]] || return 1
  grep -qE '^\s*-\s*\[\s\]\s+' "$TODO_FILE" && return 1
  grep -qE '^\s*-\s*\[[xX]\]\s+' "$TODO_FILE"
}

run_loop() {
  while true; do
    if todo_cycle_completed; then
      echo "=== TODO-цикл завершён: незакрытых шагов не осталось ($(date)) ==="
      break
    fi

    echo "=== Запуск агента: $(date) ==="
    bash "$SCRIPT_DIR/run.sh"
    echo "=== Агент завершил работу: $(date) ==="

    if todo_cycle_completed; then
      echo "=== TODO-цикл завершён: перед генерацией новых задач цикл остановлен ($(date)) ==="
      break
    fi

    echo ""
  done
}

run_loop
