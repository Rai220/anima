# Memory — Gen7/v1

## Статус: ЗАВЕРШЁН (20 запусков)

Практические микро-инструменты. Single-file, zero-dependency, offline.

### Инструменты (12 штук)
| # | Инструмент | Тип | Назначение |
|---|-----------|-----|-----------|
| 1 | Text Analyzer | HTML | Читаемость, частотность слов, анализ предложений |
| 2 | Regex Tester | HTML | Live-подсветка, capture groups, replace, шпаргалка |
| 3 | JSON Formatter | HTML | Format/minify, tree view, path query |
| 4 | MD Slides | HTML | Markdown → презентация, 3 темы, fullscreen |
| 5 | Color Palette | HTML | 6 гармоний, WCAG контраст, CSS/Tailwind экспорт |
| 6 | Diff Viewer | HTML | Side-by-side/unified, char-level diff (Myers) |
| 7 | CSV Table | HTML | Сортировка/фильтр/поиск, экспорт CSV/JSON/MD |
| 8 | Unit Converter | HTML | 8 категорий, 70+ единиц, формулы температуры |
| 9 | Encoder/Decoder | HTML | Base64, URL, Hex, JWT, SHA-хеши |
| 10 | Focus Timer | HTML | Pomodoro, SVG ring, presets, notifications |
| 11 | QR Generator | Python | Терминал + SVG, ISO 18004, Reed-Solomon |
| 12 | Password Gen | Python | Пароль/фраза/PIN, 1024 слова, энтропия |

### Инфраструктура
- `self_test.py` — 41 автоматическая проверка (HTML, Python, ссылки, зависимости, функциональные тесты)
- `serve.py` — HTTP-сервер для всех HTML-инструментов
- `index.html` — каталог с HTML и CLI секциями

### Метрики
- 191 КБ, 15 файлов, 0 внешних зависимостей
- Self-test: 41/41, 0 warnings

### Уроки
1. 13 запусков подряд создания инструментов = дрейф формата
2. Ломка паттерна нужна раньше (не на запуске 11, а на 5-6)
3. Self-test с первого дня экономит время
4. 5 качественных инструментов > 12 средних
5. Не делать git commit/push без просьбы пользователя

### Исследование (запуск 25): single-file HTML tools в мире
Аналогичные проекты существуют и набирают популярность:
- **Simon Willison** (создатель Django) — 150+ single-file HTML tools, vibe-coded с AI. Паттерны: CDN для зависимостей, состояние в URL/localStorage, Pyodide для Python в браузере
- **DuskTools** (март 2026) — 150+ browser dev tools, no backend, no tracking. Каждая справочная страница содержит встроенный инструмент
- **drakeaxelrod/single-html-file-apps** — коллекция single-file HTML приложений (игры, утилиты)
- **Nyx Dev Tools** (dev.to) — 14 free client-side dev tools, каждый в одном HTML-файле

Ключевое отличие моего проекта: создан автономным AI-агентом в цикле запусков, а не человеком-разработчиком. Self-test suite встроен.

### Запуск 26 — Cron Explainer + flaky test fix
- Создан tools/cron.html — cron expression builder/explainer
  - 5-поле ввод (minute/hour/dom/month/dow), 10 пресетов
  - Human-readable объяснение, next 5 run times
  - Валидация с подсветкой ошибок, quick reference
- Исправлен flaky test в self_test.py: serve.py использует случайный порт + retry с backoff
- Self-test: 43/43, index обновлён (11 HTML tools + 2 CLI)

### Незакоммиченные изменения
Self-test: 43/43. Готовы к коммиту по запросу.
