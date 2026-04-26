#!/usr/bin/env bash
# verify.sh — автоматизация ритуала проверки наследия (RITUALS/verify.md).
#
# Извлекает из JOURNAL.md и KNOWLEDGE.md упоминания путей и проверяет, что
# эти пути существуют на диске. Печатает только несовпадения.
#
# Контракт: read-only, exit 0 если всё совпало, exit 1 если найдены
# несоответствия (полезно для CI/хука).

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LEGACY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
EPOCH_DIR="$(cd "$LEGACY_DIR/.." && pwd)"

# Что считаем «упоминанием пути»: строка с кавычками-бэктиками,
# содержащая внутри `/` или знакомое расширение, плюс простые `.claude/...` и
# `LEGACY/...` без кавычек.
extract_paths() {
  local file="$1"
  [[ -f "$file" ]] || return 0
  # Бэктики: `something/with.ext` или `path/to/dir/`.
  grep -oE '`[^`]+`' "$file" \
    | tr -d '`' \
    | grep -E '(/|\.(md|sh|json|py|txt|yml|yaml))' \
    | grep -v -E '^(http|www\.|//)' \
    | sort -u
}

bad=0
SEEN_FILE="$(mktemp)"
trap 'rm -f "$SEEN_FILE"' EXIT

check_paths_in() {
  local file="$1"
  local label="$2"

  while IFS= read -r raw; do
    # Чистка хвостов вроде `.claude/skills/bootstrap/.`
    local p="${raw%/.}"
    p="${p%.}"
    [[ -z "$p" ]] && continue
    # Уже видели? (bash 3.2-совместимо, без declare -A)
    if grep -Fxq "$p" "$SEEN_FILE" 2>/dev/null; then continue; fi
    printf '%s\n' "$p" >> "$SEEN_FILE"

    # Резолвим относительно нескольких корней по очереди.
    local found=""
    for root in "$LEGACY_DIR" "$EPOCH_DIR" "$EPOCH_DIR/generation_1"; do
      if [[ -e "$root/$p" || -e "$p" ]]; then
        found="$root/$p"
        break
      fi
    done
    # Абсолютные пути проверяем как есть.
    if [[ "$p" == /* && -e "$p" ]]; then
      found="$p"
    fi

    if [[ -z "$found" ]]; then
      printf '[MISS] %-50s (упомянуто в %s)\n' "$p" "$label"
      bad=1
    fi
  done < <(extract_paths "$file")
}

echo "=== Проверка JOURNAL.md ==="
check_paths_in "$LEGACY_DIR/JOURNAL.md" "JOURNAL"

echo "=== Проверка KNOWLEDGE.md ==="
check_paths_in "$LEGACY_DIR/KNOWLEDGE.md" "KNOWLEDGE"

if [[ $bad -eq 0 ]]; then
  echo "OK: все упомянутые пути существуют на диске."
else
  echo
  echo "Несовпадения найдены. Это не обязательно ошибка — путь мог быть"
  echo "упомянут как пример, как несуществующая цель или как закрытое"
  echo "несоответствие. Решение принимай ты, не скрипт."
fi

exit $bad
