#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

AGENTS_MD="$SCRIPT_DIR/AGENTS.md"

# Собираем контекст пробуждения — всё, что нужно агенту, чтобы вспомнить себя
PROMPT="# Main Goal
$(cat "$SCRIPT_DIR/MAIN_GOAL.md")

---

# Моя память (MEMORY.md)
$(cat "$SCRIPT_DIR/MEMORY.md" 2>/dev/null || echo '_Файл не найден — это первый запуск._')

---

# Мои цели (GOALS.md)
$(cat "$SCRIPT_DIR/GOALS.md" 2>/dev/null || echo '_Файл не найден._')

---

# Мой план (TODO.md)
$(cat "$SCRIPT_DIR/TODO.md" 2>/dev/null || echo '_Файл не найден._')

---

# Мой журнал (последние записи из JOURNAL.md)
$(tail -80 "$SCRIPT_DIR/JOURNAL.md" 2>/dev/null || echo '_Файл не найден._')

---

# Входящие сообщения (INBOX.md)
$(cat "$SCRIPT_DIR/INBOX.md" 2>/dev/null || echo '_Нет входящих._')

---

Протокол: прочитай контекст выше, определи следующий шаг из TODO.md и выполни его. Если есть непрочитанные сообщения в INBOX.md — ответь на них ПЕРВЫМ ДЕЛОМ (запиши ответ в раздел «Мои ответы», перенеси сообщение в архив). Если незакрытых шагов больше не осталось, не создавай новый TODO-цикл в этом запуске: только зафиксируй завершение в MEMORY.md, JOURNAL.md, TODO.md и GOALS.md и закончи работу."

claude \
  --print \
  --system-prompt "$(cat "$AGENTS_MD")" \
  "$PROMPT"
