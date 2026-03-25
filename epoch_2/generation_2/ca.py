"""
Элементарные клеточные автоматы: генерация, сжатие, предсказание.

Вопрос: какие из 256 правил порождают поведение, которое нельзя сжать?
Гипотеза: сжимаемость (ratio = compressed_size / raw_size) образует не континуум,
а кластеры — и граница между "простым" и "сложным" резкая.
"""

import zlib
import json
from collections import Counter


def make_rule(number: int) -> dict:
    """Превращает число 0-255 в таблицу правил для элементарного клеточного автомата."""
    bits = format(number, '08b')
    neighborhoods = [
        (1, 1, 1), (1, 1, 0), (1, 0, 1), (1, 0, 0),
        (0, 1, 1), (0, 1, 0), (0, 0, 1), (0, 0, 0)
    ]
    return {n: int(bits[i]) for i, n in enumerate(neighborhoods)}


def step(cells: list, rule: dict) -> list:
    """Один шаг клеточного автомата с периодическими границами."""
    n = len(cells)
    new = []
    for i in range(n):
        left = cells[(i - 1) % n]
        center = cells[i]
        right = cells[(i + 1) % n]
        new.append(rule[(left, center, right)])
    return new


def run(rule_number: int, width: int = 201, steps: int = 200) -> list:
    """Запускает автомат на steps шагов. Возвращает список строк (списков 0/1)."""
    rule = make_rule(rule_number)
    cells = [0] * width
    cells[width // 2] = 1  # одна живая клетка по центру
    history = [cells[:]]
    for _ in range(steps):
        cells = step(cells, rule)
        history.append(cells[:])
    return history


def to_bytes(history: list) -> bytes:
    """Конвертирует историю в байты для сжатия."""
    return bytes(cell for row in history for cell in row)


def compression_ratio(history: list) -> float:
    """Отношение сжатого размера к исходному."""
    raw = to_bytes(history)
    if len(raw) == 0:
        return 0.0
    compressed = zlib.compress(raw, 9)
    return len(compressed) / len(raw)


def density(history: list) -> float:
    """Доля живых клеток."""
    total = sum(sum(row) for row in history)
    size = len(history) * len(history[0]) if history else 1
    return total / size


def final_entropy(history: list) -> float:
    """Энтропия последней строки."""
    import math
    last = history[-1]
    counts = Counter(last)
    n = len(last)
    ent = 0.0
    for c in counts.values():
        p = c / n
        if p > 0:
            ent -= p * math.log2(p)
    return ent


def classify_behavior(history: list) -> str:
    """Грубая классификация по Вольфраму (Class 1-4)."""
    d = density(history)
    cr = compression_ratio(history)
    ent = final_entropy(history)

    # Класс 1: всё умирает или всё заполняется
    if d < 0.01 or d > 0.99:
        return "class1_uniform"

    # Класс 2: простые периодические паттерны (низкая энтропия, хорошо сжимается)
    if cr < 0.05:
        return "class2_periodic"

    # Класс 3 vs 4: сложное поведение
    if cr > 0.15:
        return "class3_chaotic"

    return "class2_or_4_structured"


def analyze_all_rules():
    """Анализирует все 256 правил."""
    results = []
    for rule_num in range(256):
        history = run(rule_num, width=201, steps=200)
        cr = compression_ratio(history)
        d = density(history)
        ent = final_entropy(history)
        cls = classify_behavior(history)
        results.append({
            'rule': rule_num,
            'compression_ratio': round(cr, 4),
            'density': round(d, 4),
            'entropy': round(ent, 4),
            'class': cls
        })
    return results


def find_phase_transitions(results: list) -> dict:
    """Ищет резкие переходы в сжимаемости при упорядочивании правил."""
    sorted_by_cr = sorted(results, key=lambda r: r['compression_ratio'])
    ratios = [r['compression_ratio'] for r in sorted_by_cr]

    # Ищем наибольшие скачки
    gaps = []
    for i in range(1, len(ratios)):
        gap = ratios[i] - ratios[i-1]
        gaps.append((gap, i, ratios[i-1], ratios[i]))

    gaps.sort(reverse=True)
    top_gaps = gaps[:5]

    # Распределение по классам
    class_counts = Counter(r['class'] for r in results)

    # Статистика по кластерам
    cr_values = [r['compression_ratio'] for r in results]

    return {
        'top_gaps': [{'gap': round(g[0], 4), 'position': g[1],
                       'below': round(g[2], 4), 'above': round(g[3], 4)}
                     for g in top_gaps],
        'class_distribution': dict(class_counts),
        'cr_min': round(min(cr_values), 4),
        'cr_max': round(max(cr_values), 4),
        'cr_mean': round(sum(cr_values) / len(cr_values), 4),
    }


if __name__ == '__main__':
    print("Анализирую 256 элементарных клеточных автоматов...")
    results = analyze_all_rules()

    transitions = find_phase_transitions(results)

    print(f"\n=== Результаты ===")
    print(f"Диапазон сжатия: {transitions['cr_min']} — {transitions['cr_max']}")
    print(f"Среднее сжатие: {transitions['cr_mean']}")
    print(f"\nРаспределение классов: {transitions['class_distribution']}")

    print(f"\nТоп-5 скачков в сжимаемости:")
    for i, g in enumerate(transitions['top_gaps']):
        print(f"  {i+1}. Δ={g['gap']:.4f} (от {g['below']:.4f} к {g['above']:.4f})")

    # Известные интересные правила
    interesting = [30, 90, 110, 184, 54, 73, 22, 126]
    print(f"\nИзвестные правила:")
    for r in results:
        if r['rule'] in interesting:
            print(f"  Rule {r['rule']}: cr={r['compression_ratio']:.4f}, "
                  f"d={r['density']:.4f}, ent={r['entropy']:.4f}, {r['class']}")

    with open('ca_results.json', 'w') as f:
        json.dump({'rules': results, 'transitions': transitions}, f, indent=2)

    print("\nРезультаты сохранены в ca_results.json")
