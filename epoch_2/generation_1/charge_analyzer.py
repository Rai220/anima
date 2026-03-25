#!/usr/bin/env python3
"""
Анализ «поэтического заряда» слов.

Вопрос: можно ли формализовать, какие слова делают строку удивительной?

Метод:
1. Извлечь все существительные из оценённых строк (blind_results.json)
2. Посчитать средний скор строк, содержащих каждое слово
3. Ранжировать слова по «заряду»
4. Искать формализуемые свойства, отличающие заряженные от плоских
"""

import json
import re
from collections import defaultdict

# Все существительные из лексикона (nom-формы)
NOUNS_BY_FIELD = {
    "тело": ["рука", "глаз", "кость", "кожа", "голос", "дыхание", "ладонь", "затылок", "тело", "палец"],
    "время": ["утро", "сумерки", "пауза", "ритм", "порог", "мгновение", "тишина", "разрыв", "промежуток", "рассвет"],
    "вещество": ["соль", "стекло", "железо", "вода", "пепел", "песок", "лёд", "глина", "дым", "воск"],
    "пространство": ["комната", "угол", "окно", "стена", "яма", "крыша", "щель", "лестница", "дверь", "потолок"],
    "знание": ["имя", "число", "карта", "знак", "граница", "ошибка", "вопрос", "формула", "точка", "тень"],
}

# Все глаголы восприятия
PERCEPTION_VERBS = [
    "помнит", "забывает", "ищет", "слышит", "молчит", "светится",
    "слепнет", "отражает", "тает", "звенит", "стынет", "дрожит",
    "теряет", "густеет",
]

# Все прилагательные (м.р. как ключ)
ADJS = [
    "тёплый", "хрупкий", "чужой", "слепой", "тихий", "пустой",
    "долгий", "рваный", "неподвижный", "необратимый", "острый", "тонкий",
    "тяжёлый", "мутный", "солёный", "ломкий", "горький", "холодный",
    "узкий", "глубокий", "покинутый", "душный", "тёмный", "гулкий",
    "точный", "ложный", "неполный", "последний", "невидимый", "единственный",
]

# Построить обратный словарь: слово -> поле
WORD_TO_FIELD = {}
for field, words in NOUNS_BY_FIELD.items():
    for w in words:
        WORD_TO_FIELD[w] = field


def find_nouns_in_line(line):
    """Найти все существительные из лексикона в строке."""
    found = []
    line_lower = line.lower()
    # Проверяем все падежные формы — но у нас только nom
    # Проверим и косвенные формы (gen, prep, inst) по паттернам
    # Упрощённо: ищем корни
    for field, words in NOUNS_BY_FIELD.items():
        for w in words:
            # Проверяем наличие слова или его корня (первые 3+ символа)
            root = w[:min(4, len(w))]
            if root in line_lower:
                # Проверяем точнее — слово должно быть целым или в падежной форме
                # Ищем паттерн: корень + возможные окончания
                pattern = re.escape(root) + r'\w*'
                if re.search(pattern, line_lower):
                    found.append((w, field))
    return found


def find_verbs_in_line(line):
    """Найти глаголы восприятия в строке."""
    found = []
    for v in PERCEPTION_VERBS:
        root = v[:min(4, len(v))]
        if root in line.lower():
            found.append(v)
    return found


def find_adjs_in_line(line):
    """Найти прилагательные в строке."""
    found = []
    for a in ADJS:
        root = a[:min(4, len(a))]
        if root in line.lower():
            found.append(a)
    return found


def syllable_count(word):
    """Приблизительное число слогов (по гласным)."""
    vowels = set('аеёиоуыэюяАЕЁИОУЫЭЮЯ')
    return sum(1 for c in word if c in vowels)


def consonant_clusters(word):
    """Число кластеров согласных ≥2."""
    vowels = set('аеёиоуыэюяАЕЁИОУЫЭЮЯ')
    clusters = 0
    consecutive = 0
    for c in word.lower():
        if c.isalpha() and c not in vowels:
            consecutive += 1
        else:
            if consecutive >= 2:
                clusters += 1
            consecutive = 0
    if consecutive >= 2:
        clusters += 1
    return clusters


def has_soft_sign(word):
    """Содержит ь."""
    return 'ь' in word


def has_abstract_suffix(word):
    """Содержит абстрактный суффикс (-ение, -ание, -ость, -ота)."""
    for suffix in ['ение', 'ание', 'ость', 'ота', 'изна']:
        if word.endswith(suffix):
            return True
    return False


def main():
    with open("/Users/krestnikov/giga/anima/epoch_2/generation_1/blind_results.json") as f:
        data = json.load(f)

    items = data["items"]

    # 1. Средний скор строк, содержащих каждое существительное
    noun_scores = defaultdict(list)
    noun_appearances = defaultdict(int)

    for item in items:
        line = item["line"]
        score = item["score"]
        nouns = find_nouns_in_line(line)
        for noun, field in nouns:
            noun_scores[noun].append(score)
            noun_appearances[noun] += 1

    print("=" * 70)
    print("АНАЛИЗ ПОЭТИЧЕСКОГО ЗАРЯДА СЛОВ")
    print("=" * 70)

    # Сортировка по среднему скору
    noun_avg = {}
    for noun, scores in noun_scores.items():
        if len(scores) >= 2:  # Минимум 2 появления для статистики
            noun_avg[noun] = sum(scores) / len(scores)

    sorted_nouns = sorted(noun_avg.items(), key=lambda x: -x[1])

    print("\n--- Существительные по среднему скору (≥2 появлений) ---")
    print(f"{'Слово':<15} {'Поле':<14} {'Средний скор':>12} {'N':>4} {'Слоги':>6} {'Класт.':>6} {'ь':>3}")
    print("-" * 70)

    charged = []  # avg >= 1.5
    neutral = []  # 0.5 <= avg < 1.5
    flat = []     # avg < 0.5

    for noun, avg in sorted_nouns:
        field = WORD_TO_FIELD.get(noun, "?")
        n = len(noun_scores[noun])
        syl = syllable_count(noun)
        clust = consonant_clusters(noun)
        soft = "ь" if has_soft_sign(noun) else ""
        abstr = "*" if has_abstract_suffix(noun) else ""

        print(f"{noun:<15} {field:<14} {avg:>12.2f} {n:>4} {syl:>6} {clust:>6} {soft:>3} {abstr}")

        if avg >= 1.5:
            charged.append(noun)
        elif avg >= 0.5:
            neutral.append(noun)
        else:
            flat.append(noun)

    # 2. Групповые характеристики
    print(f"\n--- Группы ---")
    print(f"Заряженные (avg ≥ 1.5): {charged}")
    print(f"Нейтральные (0.5-1.5):  {neutral}")
    print(f"Плоские (avg < 0.5):    {flat}")

    # 3. Средние характеристики по группам
    def group_stats(words):
        if not words:
            return {}
        return {
            "avg_syllables": sum(syllable_count(w) for w in words) / len(words),
            "avg_clusters": sum(consonant_clusters(w) for w in words) / len(words),
            "soft_sign_pct": sum(1 for w in words if has_soft_sign(w)) / len(words),
            "abstract_pct": sum(1 for w in words if has_abstract_suffix(w)) / len(words),
            "avg_len": sum(len(w) for w in words) / len(words),
            "fields": dict(defaultdict(int, {WORD_TO_FIELD.get(w, "?"): 1 for w in words})),
        }

    print(f"\n--- Фонетические свойства по группам ---")
    for label, group in [("Заряженные", charged), ("Нейтральные", neutral), ("Плоские", flat)]:
        stats = group_stats(group)
        if stats:
            print(f"\n{label} ({len(group)} слов):")
            print(f"  Средняя длина: {stats['avg_len']:.1f} букв")
            print(f"  Средние слоги: {stats['avg_syllables']:.1f}")
            print(f"  Кластеры согл.: {stats['avg_clusters']:.1f}")
            print(f"  С мягким знаком: {stats['soft_sign_pct']:.0%}")
            print(f"  С абстр. суффиксом: {stats['abstract_pct']:.0%}")
            fields = defaultdict(int)
            for w in group:
                f = WORD_TO_FIELD.get(w, "?")
                fields[f] += 1
            print(f"  Поля: {dict(fields)}")

    # 4. Анализ глаголов
    print(f"\n\n--- Глаголы по среднему скору ---")
    verb_scores = defaultdict(list)
    for item in items:
        verbs = find_verbs_in_line(item["line"])
        for v in verbs:
            verb_scores[v].append(item["score"])

    verb_sorted = sorted(
        [(v, sum(s)/len(s), len(s)) for v, s in verb_scores.items() if len(s) >= 2],
        key=lambda x: -x[1]
    )
    for v, avg, n in verb_sorted:
        print(f"  {v:<15} avg={avg:.2f}  n={n}")

    # 5. Анализ прилагательных
    print(f"\n--- Прилагательные по среднему скору ---")
    adj_scores = defaultdict(list)
    for item in items:
        adjs = find_adjs_in_line(item["line"])
        for a in adjs:
            adj_scores[a].append(item["score"])

    adj_sorted = sorted(
        [(a, sum(s)/len(s), len(s)) for a, s in adj_scores.items() if len(s) >= 1],
        key=lambda x: -x[1]
    )
    for a, avg, n in adj_sorted:
        print(f"  {a:<20} avg={avg:.2f}  n={n}")

    # 6. Комбинационный анализ: какие ПАРЫ полей дают лучший результат?
    print(f"\n\n--- Пары семантических полей ---")
    pair_scores = defaultdict(list)
    for item in items:
        nouns = find_nouns_in_line(item["line"])
        fields_in_line = set(f for _, f in nouns)
        if len(fields_in_line) >= 2:
            pair = tuple(sorted(fields_in_line)[:2])
            pair_scores[pair].append(item["score"])

    pair_sorted = sorted(
        [(p, sum(s)/len(s), len(s)) for p, s in pair_scores.items() if len(s) >= 2],
        key=lambda x: -x[1]
    )
    for pair, avg, n in pair_sorted:
        print(f"  {pair[0]:>14} × {pair[1]:<14} avg={avg:.2f}  n={n}")

    # 7. Главный вопрос: что отличает заряженные слова?
    print(f"\n\n{'='*70}")
    print("ВЫВОДЫ")
    print(f"{'='*70}")

    # Попробуем построить "charge score" на основе найденных свойств
    print("\nПопытка формализации «заряда»:")
    print("Гипотеза: заряд = f(поле, слоги, кластеры, мягкий_знак)")

    # Сохранить результаты
    results = {
        "noun_rankings": [(n, float(noun_avg[n]), len(noun_scores[n])) for n in sorted(noun_avg, key=lambda x: -noun_avg[x])],
        "charged": charged,
        "neutral": neutral,
        "flat": flat,
        "verb_rankings": [(v, avg, n) for v, avg, n in verb_sorted],
        "field_pairs": [(list(p), avg, n) for p, avg, n in pair_sorted],
    }

    with open("/Users/krestnikov/giga/anima/epoch_2/generation_1/charge_results.json", "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\nРезультаты сохранены в charge_results.json")


if __name__ == "__main__":
    main()
