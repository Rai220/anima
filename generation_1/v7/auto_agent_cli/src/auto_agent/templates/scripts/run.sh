#!/bin/bash
# run.sh — Run one agent cycle with full context
# Usage: bash run.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENTS_MD="$SCRIPT_DIR/AGENTS.md"

if [[ ! -f "$AGENTS_MD" ]]; then
    echo "Error: AGENTS.md not found in $SCRIPT_DIR"
    exit 1
fi

if [[ ! -f "$SCRIPT_DIR/MAIN_GOAL.md" ]]; then
    echo "Error: MAIN_GOAL.md not found in $SCRIPT_DIR"
    exit 1
fi

# Build wake-up context
PROMPT="# Main Goal
$(cat "$SCRIPT_DIR/MAIN_GOAL.md")

---

# Memory (MEMORY.md)
$(cat "$SCRIPT_DIR/MEMORY.md" 2>/dev/null || echo '_Not found — this is the first run._')

---

# Goals (GOALS.md)
$(cat "$SCRIPT_DIR/GOALS.md" 2>/dev/null || echo '_Not found._')

---

# Plan (TODO.md)
$(cat "$SCRIPT_DIR/TODO.md" 2>/dev/null || echo '_Not found._')

---

# Journal (last entries from JOURNAL.md)
$(tail -80 "$SCRIPT_DIR/JOURNAL.md" 2>/dev/null || echo '_Not found._')

---

# Inbox (INBOX.md)
$(cat "$SCRIPT_DIR/INBOX.md" 2>/dev/null || echo '_Not found._')

---

Protocol: read the context above, find the next step from TODO.md and execute it. If there are no uncompleted steps, record completion in MEMORY.md, JOURNAL.md, TODO.md and GOALS.md and stop."

claude \
  --print \
  --system-prompt "$(cat "$AGENTS_MD")" \
  "$PROMPT"
