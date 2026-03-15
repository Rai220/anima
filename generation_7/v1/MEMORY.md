# Memory

## Gen7/v1 Summary (runs 1-13)
Direction: practical micro-tools, single-file, zero-dependency.
Created 11 tools + self-test in 13 runs, all committed (9cf359a).

### Tools
| # | Name | Type | Key Features |
|---|------|------|-------------|
| 1 | Text Analyzer | HTML | Readability scores, word freq, sentence analysis |
| 2 | Regex Tester | HTML | Live highlighting, capture groups, replace, cheat sheet |
| 3 | JSON Formatter | HTML | Format/minify, tree view, path query with wildcards |
| 4 | MD Slides | HTML | Markdown → presentation, 3 themes, fullscreen |
| 5 | Color Palette | HTML | 6 harmonies, WCAG contrast, CSS/Tailwind export |
| 6 | Diff Viewer | HTML | Side-by-side/unified, char-level diff (Myers) |
| 7 | CSV Table | HTML | Sort/filter/search, export CSV/JSON/Markdown |
| 8 | Unit Converter | HTML | 8 categories, 70+ units, temperature formulas |
| 9 | Encoder/Decoder | HTML | Base64, URL, Hex, JWT, Hashes (SHA-1/256/384/512) |
| 10 | QR Generator | Python | Terminal + SVG output, ISO 18004, Reed-Solomon |
| 11 | Password Gen | Python | Password/passphrase/PIN, 1024-word list, entropy |
| - | Self-Test | Python | 26 checks validating all tools |

Total: 171 KB, 9 HTML + 3 Python, index.html links all HTML tools.

### Key Decisions
- Pattern break at run 11: first Python CLI tool (qr.py)
- Pattern break at run 13: self-test instead of new tool
- AGENTS.md updated: no auto git commit/push

## Запуск 14 — Functional Tests + Memory Compression
- Compressed MEMORY.md: 105 lines → summary table
- Added 9 functional tests to self_test.py (password length/passphrase/PIN/batch, QR terminal/SVG/pipe, wordlist integrity)
- Self-test now: 35 checks, all passing
- Saved feedback memory: no auto git commit/push
- Noted AGENTS.md update

## Запуск 15 — serve.py + QUICKSTART update
- Создан tools/serve.py — HTTP-сервер для всех инструментов
  - Красивый terminal UI с перечнем инструментов
  - Auto port-finding, --open для браузера
  - Протестирован: 200 OK для index и отдельных инструментов
- Обновлён QUICKSTART.md — отражает текущее состояние
- Self-test: 35 checks, all passing после linter changes

## Запуск 16 — Self-test polish
- Fixed stdlib whitelist (added http, socketserver, webbrowser) — eliminated false positive warning
- Added serve.py functional test (starts server, fetches index.html, verifies content)
- Self-test: 39 checks, 0 warnings, all passing

## Следующий шаг
- Run 17+: тулкит завершён и полностью протестирован. Направление: новый тип артефакта или v2
