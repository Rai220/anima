#!/usr/bin/env python3
"""
Эксперимент: структура vs случайность.

Гипотеза: система с семантическими полями и шаблонами
производит больше строк, которые читаются как осмысленные,
чем случайная комбинация тех же слов.

Метод: генерируем 50 строк структурированно и 50 случайно.
Оцениваем "грамматическую корректность" автоматически
и "семантическую плотность" — сколько строк содержат
слова, образующие хотя бы одну известную семантическую связь.
"""

import random
import json
from datetime import datetime
from generator import Generator, NOUNS, VERBS, ADJ, Word


def all_nom_nouns():
    result = []
    for field in NOUNS.values():
        for w in field:
            result.append(w.nom)
    return result


def all_verbs():
    result = []
    for field in VERBS.values():
        result.extend(field)
    return result


def random_line():
    """Случайная строка из того же лексикона, без структуры."""
    nouns = all_nom_nouns()
    verbs = all_verbs()

    pattern = random.choice([
        lambda: f"{random.choice(nouns)} {random.choice(verbs)}",
        lambda: f"{random.choice(nouns)} {random.choice(verbs)}, как {random.choice(nouns)}",
        lambda: f"{random.choice(nouns)} — это {random.choice(nouns)}",
        lambda: f"между {random.choice(nouns)} и {random.choice(nouns)} — только {random.choice(nouns)}",
        lambda: f"{random.choice(nouns)} не {random.choice(verbs)}. {random.choice(nouns)} {random.choice(verbs)}.",
        lambda: f"что {random.choice(verbs)} в {random.choice(nouns)}?",
    ])
    return pattern()


# Семантические пары, которые "имеют смысл" — слова, которые
# усиливают друг друга, а не просто стоят рядом
SEMANTIC_AFFINITIES = [
    # Тело + время
    ("рука", "помнит"), ("кость", "длится"), ("дыхание", "обрывается"),
    ("голос", "тает"), ("кожа", "светится"), ("глаз", "ищет"),
    # Вещество + пространство
    ("стекло", "отражает"), ("вода", "течёт"), ("лёд", "крошится"),
    ("дым", "сужается"), ("глина", "затвердевает"), ("пепел", "оседает"),
    # Знание + время
    ("имя", "стирается"), ("формула", "длится"), ("ошибка", "повторяется"),
    ("граница", "сдвигается"), ("точка", "исчезает"), ("карта", "стирается"),
    # Тело + вещество
    ("кость", "крошится"), ("кожа", "горит"), ("палец", "тает"),
    # Пространство + время
    ("комната", "пустеет"), ("дверь", "замыкается"), ("окно", "светится"),
    ("порог", "раскалывается"), ("стена", "длится"),
    # Кросс-полевые метафоры, которые работают
    ("тишина", "плавится"), ("разрыв", "горит"), ("ритм", "крошится"),
    ("ошибка", "светится"), ("число", "тает"), ("имя", "горит"),
    ("соль", "помнит"), ("железо", "молчит"), ("воск", "помнит"),
]


def semantic_density(line):
    """
    Сколько семантических пар присутствует в строке?
    Это грубая мера того, 'работает' ли строка.
    """
    count = 0
    for word1, word2 in SEMANTIC_AFFINITIES:
        if word1 in line and word2 in line:
            count += 1
    return count


def has_self_repeat(line):
    """Содержит ли строка повтор одного и того же слова
    (не считая структурного повтора в шаблоне 'X не V. X V2.')"""
    words = line.replace(".", "").replace(",", "").replace("?", "").replace("!", "").split()
    # Убираем служебные
    content_words = [w for w in words if w not in ("—", "это", "как", "там", "где", "не", "что", "в", "и", "только", "между")]
    return len(content_words) != len(set(content_words))


def run_experiment(n=100, seed=42):
    random.seed(seed)

    gen = Generator()

    structured = [gen.generate() for _ in range(n)]
    random_lines = [random_line() for _ in range(n)]

    results = {
        "structured": {
            "lines": structured,
            "semantic_density": [semantic_density(l) for l in structured],
            "self_repeats": sum(1 for l in structured if has_self_repeat(l)),
        },
        "random": {
            "lines": random_lines,
            "semantic_density": [semantic_density(l) for l in random_lines],
            "self_repeats": sum(1 for l in random_lines if has_self_repeat(l)),
        }
    }

    # Агрегаты
    for key in ["structured", "random"]:
        densities = results[key]["semantic_density"]
        results[key]["avg_density"] = sum(densities) / len(densities)
        results[key]["lines_with_affinity"] = sum(1 for d in densities if d > 0)
        results[key]["max_density"] = max(densities)

    return results


def main():
    results = run_experiment(100, seed=2025)

    print("=" * 60)
    print("ЭКСПЕРИМЕНТ: СТРУКТУРА vs СЛУЧАЙНОСТЬ")
    print("=" * 60)
    print()

    for label, key in [("Структурированные", "structured"), ("Случайные", "random")]:
        r = results[key]
        print(f"  {label}:")
        print(f"    Средняя семантическая плотность: {r['avg_density']:.2f}")
        print(f"    Строки с хотя бы одной связью:   {r['lines_with_affinity']}/100")
        print(f"    Макс. плотность:                  {r['max_density']}")
        print(f"    Самоповторы (одно слово дважды):  {r['self_repeats']}/100")
        print()

    # Топ-5 по плотности из каждой группы
    for label, key in [("СТРУКТУРИРОВАННЫЕ", "structured"), ("СЛУЧАЙНЫЕ", "random")]:
        print(f"  Топ-5 {label}:")
        paired = list(zip(results[key]["lines"], results[key]["semantic_density"]))
        paired.sort(key=lambda x: -x[1])
        for line, density in paired[:5]:
            print(f"    [{density}] {line}")
        print()

    # Сохранение
    output = {
        "timestamp": datetime.now().isoformat(),
        "structured_avg_density": results["structured"]["avg_density"],
        "random_avg_density": results["random"]["avg_density"],
        "structured_affinity_count": results["structured"]["lines_with_affinity"],
        "random_affinity_count": results["random"]["lines_with_affinity"],
        "structured_self_repeats": results["structured"]["self_repeats"],
        "random_self_repeats": results["random"]["self_repeats"],
        "hypothesis_confirmed": results["structured"]["avg_density"] > results["random"]["avg_density"],
    }

    with open("/Users/krestnikov/giga/anima/epoch_2/generation_1/experiment_results.json", "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    confirmed = "ДА" if output["hypothesis_confirmed"] else "НЕТ"
    print(f"  Гипотеза подтверждена: {confirmed}")
    print(f"  (структурная плотность {results['structured']['avg_density']:.2f} "
          f"vs случайная {results['random']['avg_density']:.2f})")


if __name__ == "__main__":
    main()
