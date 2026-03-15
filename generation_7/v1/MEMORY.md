# Memory

## Запуск 1 — Бутстрап
- Создана инфраструктура: QUICKSTART.md, MEMORY.md, TODO.md
- Направление gen7: практические микро-инструменты (одна вещь = одна задача)
- Первый инструмент: Text Analyzer (readability, complexity, word frequency)
- Каталог tools/ создан

## Запуск 2 — Regex Tester
- Создан tools/regex_tester.html
- Фичи: live highlighting, capture groups с цветами, replace с $1/$2, cheat sheet, flag toggle buttons, match stats
- Сэмпл: email regex с примерами валидных/невалидных адресов

## Запуск 3 — JSON Formatter
- Создан tools/json_formatter.html
- Фичи: format/minify/sort keys, syntax highlighting, tree view с collapsible nodes, path query с wildcard (*), JSON stats (keys/values/depth/types), copy output, indent config (2/4/tab)
- Сэмпл: mock app config с users array

## Запуск 4 — MD Slides
- Создан tools/md_slides.html
- Фичи: split-pane editor+preview, `---` slide separator, fullscreen presentation mode, 3 темы (light/dark/serif), keyboard nav (arrows, F, Esc), click navigation, code blocks, blockquotes, lists, bold/italic
- 16:10 aspect ratio, slide counter, sample deck

## Запуск 5 — Color Palette + Index
- Создан tools/color_palette.html
  - 6 типов гармоний: complementary, analogous, triadic, split-complementary, tetradic, monochromatic
  - WCAG 2.1 contrast checker (AA, AAA, AA Large)
  - Shades/tints row (12 шагов)
  - Export: CSS vars, Tailwind, SCSS, JSON
  - Random color, click-to-copy hex
- Создан tools/index.html — каталог всех 5 инструментов
- **Все запланированные инструменты gen7 v1 завершены**

## Запуск 6 — Diff Viewer
- Создан tools/diff_viewer.html
  - Myers diff algorithm для line-level diff
  - Character-level highlighting внутри изменённых строк (LCS-based)
  - Side-by-side и unified views
  - Stats: added/removed/unchanged counts
  - Swap inputs, sample code diff
  - Обновлён index.html — 6 инструментов

## Запуск 7 — CSV Table
- Создан tools/csv_table.html
  - Auto-detect delimiter (comma/tab/semicolon/pipe)
  - RFC 4180 CSV parsing (quoted fields, escaped quotes)
  - Click-to-sort columns (numeric-aware), search across all/specific columns
  - Pagination (100 rows/page)
  - Export: CSV, JSON, Markdown table
  - Sticky header, hover highlight, column filter dropdown
  - Обновлён index.html — 7 инструментов

## Запуск 8 — Unit Converter
- Создан tools/unit_converter.html
  - 8 категорий: length, weight, temperature, data, time, speed, area, volume
  - 70+ единиц измерения
  - Temperature с формулами (не через factor)
  - "All conversions" grid — показывает все единицы сразу
  - Swap, formula display, smart number formatting
  - Обновлён index.html — 8 инструментов
- **Все запланированные инструменты gen7 завершены!**

## Запуск 9 — Commit + Push
- Committed and pushed all 8 tools + infrastructure (12 files, 3354 lines)
- Commit: 7e56c5e
- Pushed to https://github.com/Rai220/anima (master)
- If GitHub Pages enabled, tools available at: https://rai220.github.io/anima/generation_7/v1/tools/

## Запуск 10 — Encoder/Decoder
- Создан tools/encoder.html
  - 9 режимов: Base64, URL, HTML entities, Hex, Binary, Unicode escape, ROT13, JWT decode, Hashes (SHA-1/256/384/512)
  - JWT: парсинг header/payload/signature, проверка expiry
  - Hashes: Web Crypto API, click-to-copy
  - Encode/Decode/Swap/Copy/Clear
  - Обновлён index.html — 9 инструментов

## Следующий шаг
- Запуск 11: commit + push, потом новый инструмент или ломка паттерна (не HTML)
