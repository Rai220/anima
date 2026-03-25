#!/usr/bin/env python3
"""
Контролируемый анализ поэтического заряда.

Проблема: в charge_analyzer.py скор слова зависит от шаблона.
Слово в definition-шаблоне автоматически получает высокий скор.

Решение: анализировать только definition-строки (контроль шаблона).
Внутри одного шаблона различие скоров = эффект конкретных слов.
"""

import json
import re
from collections import defaultdict

# Лексикон
NOUNS_BY_FIELD = {
    "тело": ["рука", "глаз", "кость", "кожа", "голос", "дыхание", "ладонь", "затылок", "тело", "палец"],
    "время": ["утро", "сумерки", "пауза", "ритм", "порог", "мгновение", "тишина", "разрыв", "промежуток", "рассвет"],
    "вещество": ["соль", "стекло", "железо", "вода", "пепел", "песок", "лёд", "глина", "дым", "воск"],
    "пространство": ["комната", "угол", "окно", "стена", "яма", "крыша", "щель", "лестница", "дверь", "потолок"],
    "знание": ["имя", "число", "карта", "знак", "граница", "ошибка", "вопрос", "формула", "точка", "тень"],
}

WORD_TO_FIELD = {}
for field, words in NOUNS_BY_FIELD.items():
    for w in words:
        WORD_TO_FIELD[w] = field


def detect_template(line):
    """Определить шаблон строки."""
    if ': ' in line and ', что ' in line:
        return 'definition'
    if ' там, где ' in line:
        return 'where'
    if line.startswith('что ') and line.endswith('?'):
        return 'question'
    if line.startswith('между '):
        return 'between'
    if ', как ' in line:
        return 'simile'
    # фрагмент: 2-3 слова
    if len(line.split()) <= 3 and ',' not in line:
        return 'fragment'
    return 'other'


def find_words(line):
    """Найти все лексиконные слова (существительные) в строке."""
    found = []
    for field, words in NOUNS_BY_FIELD.items():
        for w in words:
            # Ищем слово или его падежные формы по корню
            if len(w) <= 3:
                # Короткие слова: точное совпадение или начало слова + макс 3 буквы
                pattern = r'\b' + re.escape(w)
                if re.search(pattern, line, re.IGNORECASE):
                    found.append((w, field))
            else:
                root = w[:min(4, len(w))]
                if root in line.lower():
                    found.append((w, field))
    return found


def main():
    with open("/Users/krestnikov/giga/anima/epoch_2/generation_1/blind_results.json") as f:
        data = json.load(f)

    items = data["items"]

    # Классифицировать строки по шаблонам
    by_template = defaultdict(list)
    for item in items:
        tpl = detect_template(item["line"])
        by_template[tpl].append(item)

    print("=" * 70)
    print("КОНТРОЛИРУЕМЫЙ АНАЛИЗ ЗАРЯДА")
    print("=" * 70)

    print("\n--- Распределение по шаблонам ---")
    for tpl, items_list in sorted(by_template.items(), key=lambda x: -len(x[1])):
        avg = sum(i["score"] for i in items_list) / len(items_list)
        print(f"  {tpl:<15} N={len(items_list):>3}  avg={avg:.2f}")

    # Анализ definition-строк (контроль шаблона)
    defs = by_template.get('definition', [])
    print(f"\n\n{'='*70}")
    print(f"DEFINITION-СТРОКИ ({len(defs)} шт.)")
    print(f"{'='*70}")

    # Парсинг definition: "X: A Y, что V без Z"
    def parse_definition(line):
        """Извлечь компоненты definition-шаблона."""
        parts = {}
        # X: A Y, что V без Z
        match = re.match(r'(\w+):\s+(\S+)\s+(\S+),\s+что\s+(\S+)\s+без\s+(\S+)', line)
        if match:
            parts['X'] = match.group(1)  # определяемое
            parts['A'] = match.group(2)  # прилагательное
            parts['Y'] = match.group(3)  # переопределение
            parts['V'] = match.group(4)  # глагол
            parts['Z'] = match.group(5)  # отсутствие
        return parts

    print("\n--- Разбор definition-строк ---")
    print(f"{'Скор':>4} | {'X (имя)':<12} | {'A (сдвиг)':<14} | {'Y (объект)':<12} | {'V (глагол)':<12} | {'Z (без)':<12} | Строка")
    print("-" * 100)

    x_scores = defaultdict(list)  # скоры для каждого X
    y_scores = defaultdict(list)  # скоры для каждого Y
    v_scores = defaultdict(list)  # скоры для каждого V
    z_scores = defaultdict(list)  # скоры для каждого Z
    a_scores = defaultdict(list)  # скоры для каждого A

    # Пары полей
    xy_field_scores = defaultdict(list)

    for item in sorted(defs, key=lambda x: -x["score"]):
        parts = parse_definition(item["line"])
        if parts:
            print(f"  {item['score']:>2} | {parts['X']:<12} | {parts['A']:<14} | {parts['Y']:<12} | {parts['V']:<12} | {parts['Z']:<12} | {item['line']}")

            x_scores[parts['X']].append(item['score'])
            y_scores[parts['Y']].append(item['score'])
            v_scores[parts['V']].append(item['score'])
            z_scores[parts['Z']].append(item['score'])
            a_scores[parts['A']].append(item['score'])

            # Определить поля X и Y
            x_field = WORD_TO_FIELD.get(parts['X'], '?')
            y_words = find_words(parts['Y'])
            y_field = y_words[0][1] if y_words else '?'
            if x_field != '?' and y_field != '?':
                pair = tuple(sorted([x_field, y_field]))
                xy_field_scores[pair].append(item['score'])

    # Какой слот имеет наибольшее влияние?
    print(f"\n\n--- Влияние каждого слота на скор ---")

    def variance_explained(slot_scores):
        """Грубая оценка: разброс средних скоров между словами в слоте."""
        avgs = [sum(s)/len(s) for s in slot_scores.values() if len(s) >= 1]
        if len(avgs) < 2:
            return 0
        mean = sum(avgs) / len(avgs)
        return sum((a - mean)**2 for a in avgs) / len(avgs)

    slots = {
        'X (определяемое)': x_scores,
        'A (прилагательное)': a_scores,
        'Y (переопределение)': y_scores,
        'V (глагол)': v_scores,
        'Z (без чего)': z_scores,
    }

    for slot_name, scores_dict in slots.items():
        var = variance_explained(scores_dict)
        unique_words = len(scores_dict)
        print(f"  {slot_name:<25} variance={var:.3f}  unique_words={unique_words}")

        # Топ и антитоп
        ranked = sorted(
            [(w, sum(s)/len(s), len(s)) for w, s in scores_dict.items()],
            key=lambda x: -x[1]
        )
        top = ranked[:3]
        bottom = ranked[-3:]
        print(f"    Лучшие: {', '.join(f'{w}({avg:.1f},n={n})' for w,avg,n in top)}")
        print(f"    Худшие: {', '.join(f'{w}({avg:.1f},n={n})' for w,avg,n in bottom)}")

    # Анализ where-строк
    wheres = by_template.get('where', [])
    print(f"\n\n{'='*70}")
    print(f"WHERE-СТРОКИ ({len(wheres)} шт.)")
    print(f"{'='*70}")

    # "X V1 там, где Y V2"
    for item in sorted(wheres, key=lambda x: -x["score"]):
        print(f"  {item['score']:>2} | {item['line']}")

    # Пары слов в where
    print(f"\n--- Пары субъектов в where ---")
    for item in sorted(wheres, key=lambda x: -x["score"]):
        words = find_words(item["line"])
        fields = [f for _, f in words]
        pair = tuple(sorted(set(fields)))
        print(f"  {item['score']:>2} | {pair} | {item['line']}")

    # ИТОГО: что предсказывает скор?
    print(f"\n\n{'='*70}")
    print("ИТОГОВЫЙ АНАЛИЗ: ЧТО ПРЕДСКАЗЫВАЕТ СКОР?")
    print(f"{'='*70}")

    # Пары полей в definition
    print(f"\n--- Пары полей X×Y в definition ---")
    for pair, scores in sorted(xy_field_scores.items(), key=lambda x: -sum(x[1])/len(x[1])):
        avg = sum(scores) / len(scores)
        print(f"  {pair[0]:>14} × {pair[1]:<14} avg={avg:.2f}  n={len(scores)}")

    # Сохранить
    results = {
        "definition_analysis": {
            "slot_variance": {name: variance_explained(sd) for name, sd in slots.items()},
        },
        "template_scores": {tpl: sum(i["score"] for i in items_list) / len(items_list)
                           for tpl, items_list in by_template.items()},
    }

    with open("/Users/krestnikov/giga/anima/epoch_2/generation_1/charge_controlled_results.json", "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
