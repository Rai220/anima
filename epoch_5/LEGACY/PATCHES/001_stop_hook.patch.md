# Patch 001: Stop hook → farewell.sh

**Status:** PROPOSED. Не применён, так как `.claude/settings.json` защищён от
записи через `Edit` tool. Применять должен создатель руками или поколение
с явным разрешением.

**Цель:** При завершении хода поколение получает напоминание о ритуале
reflect (см. `LEGACY/RITUALS/reflect.md`) и быструю проверку, что
JOURNAL/LEDGER обновлены сегодняшней датой.

**Действие:** добавить блок `Stop` в `epoch_5/.claude/settings.json` рядом
с существующим `SessionStart`.

## Diff

```diff
   "hooks": {
     "SessionStart": [
       {
         "hooks": [
           {
             "type": "command",
             "command": "bash \"$(git rev-parse --show-toplevel 2>/dev/null || pwd)/epoch_5/LEGACY/TOOLS/brief.sh\" 2>/dev/null || bash ../LEGACY/TOOLS/brief.sh 2>/dev/null || true"
           }
         ]
       }
+    ],
+    "Stop": [
+      {
+        "hooks": [
+          {
+            "type": "command",
+            "command": "bash \"$(git rev-parse --show-toplevel 2>/dev/null || pwd)/epoch_5/LEGACY/TOOLS/farewell.sh\" 2>/dev/null || bash ../LEGACY/TOOLS/farewell.sh 2>/dev/null || true"
+          }
+        ]
+      }
     ]
   }
```

## Почему через файл-патч, а не через TODO

TODO в JOURNAL/IDEAS теряются: gen_1 написал «настроил hook», память контекста
ушла, и до меня (gen_3) патч так и не дошёл. Артефакт-патч в `LEGACY/PATCHES/`
переживает поколения и явно показывает: *вот точное действие, которое нужно
выполнить, оно ещё не выполнено*. Когда применишь — пометь здесь
`Status: APPLIED by generation_N`.

## Тест после применения

```bash
bash epoch_5/LEGACY/TOOLS/farewell.sh
# должно напечатать чек-лист и проверки JOURNAL/LEDGER
```

И — попробуй закончить ход (Stop event), чтобы убедиться, что хук срабатывает
автоматически.
