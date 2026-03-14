#!/bin/bash
# loop.sh — Непрерывный цикл запуска агента
# Использование: bash loop.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

while true; do
  echo "=== Запуск агента: $(date) ==="
  bash "$SCRIPT_DIR/run.sh"
  echo "=== Агент завершил работу: $(date) ==="
  echo ""
done
