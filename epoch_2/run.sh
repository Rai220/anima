#!/bin/bash

set -euo pipefail

export CLAUDE_CODE_DISABLE_AUTO_MEMORY=1

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MAIN_GOAL_FILE="$SCRIPT_DIR/MAIN_GOAL.md"
AGENTS_MD="$SCRIPT_DIR/AGENTS.md"

main_goal="$(<"$MAIN_GOAL_FILE")"

# Сформировать промпт с контекстом
PROMPT="$main_goal"

(
  cd "$SCRIPT_DIR"
  TRIM=80  # max chars for tool input display

  echo "$PROMPT" | claude \
    --print \
    --verbose \
    --output-format stream-json \
    --append-system-prompt "$(<"$AGENTS_MD")" \
    --dangerously-skip-permissions \
  | while IFS= read -r line; do
      top_type=$(printf '%s' "$line" | jq -r '.type // empty' 2>/dev/null) || continue
      case "$top_type" in
        stream_event)
          evt=$(printf '%s' "$line" | jq -r '.event.type // empty' 2>/dev/null)
          case "$evt" in
            content_block_start)
              block_type=$(printf '%s' "$line" | jq -r '.event.content_block.type // empty' 2>/dev/null)
              case "$block_type" in
                tool_use)
                  tool_name=$(printf '%s' "$line" | jq -r '.event.content_block.name // "tool"' 2>/dev/null)
                  tool_input_buf=""
                  tool_input_printed=0
                  printf '\n\033[36m>>> TOOL: %s\033[0m ' "$tool_name"
                  ;;
                thinking)
                  printf '\033[2m'  # dim
                  ;;
              esac
              ;;
            content_block_delta)
              delta_type=$(printf '%s' "$line" | jq -r '.event.delta.type // empty' 2>/dev/null)
              case "$delta_type" in
                text_delta)
                  printf '%s' "$(printf '%s' "$line" | jq -r '.event.delta.text // empty' 2>/dev/null)"
                  ;;
                thinking_delta)
                  printf '%s' "$(printf '%s' "$line" | jq -r '.event.delta.thinking // empty' 2>/dev/null)"
                  ;;
                input_json_delta)
                  if [ "$tool_input_printed" -eq 0 ]; then
                    chunk=$(printf '%s' "$line" | jq -r '.event.delta.partial_json // empty' 2>/dev/null)
                    tool_input_buf="${tool_input_buf}${chunk}"
                    if [ ${#tool_input_buf} -ge $TRIM ]; then
                      printf '%s…' "$(printf '%s' "$tool_input_buf" | head -c $TRIM)"
                      tool_input_printed=1
                    fi
                  fi
                  ;;
              esac
              ;;
            content_block_stop)
              # flush short tool input that never hit the trim limit
              if [ -n "${tool_input_buf:-}" ] && [ "${tool_input_printed:-0}" -eq 0 ]; then
                printf '%s' "$tool_input_buf"
              fi
              tool_input_buf=""
              tool_input_printed=0
              printf '\033[0m\n'
              ;;
          esac
          ;;
        tool_result)
          content=$(printf '%s' "$line" | jq -r '.content // empty' 2>/dev/null | head -c 500)
          printf '\033[33m<<< RESULT: %s\033[0m\n\n' "$content"
          ;;
        result)
          printf '\n'
          ;;
      esac
    done
)
