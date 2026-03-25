"""
Цикл 4: Робастность фазового перехода MI к начальным условиям.

Вопрос: фазовый переход (пустая зона 2-10x при высокой энтропии) получен
при одной живой клетке в центре. Сохраняется ли он при случайных начальных условиях?

Фальсифицируемые гипотезы:
12. Пустая зона 2-10x сохраняется при случайных начальных условиях.
13. Список Class 4 правил (110, 124, 137, 193) не изменяется.
14. MI_ratio Class 4 правил при случайных начальных условиях ≈ MI_ratio при одной клетке (±50%).
"""

import math
import json
from collections import Counter


def make_rule(number):
    bits = format(number, '08b')
    neighborhoods = [
        (1, 1, 1), (1, 1, 0), (1, 0, 1), (1, 0, 0),
        (0, 1, 1), (0, 1, 0), (0, 0, 1), (0, 0, 0)
    ]
    return {n: int(bits[i]) for i, n in enumerate(neighborhoods)}


def step(cells, rule):
    n = len(cells)
    new = []
    for i in range(n):
        left = cells[(i - 1) % n]
        center = cells[i]
        right = cells[(i + 1) % n]
        new.append(rule[(left, center, right)])
    return new


def run_random_init(rule_number, width=201, steps=10000, seed=42):
    """Запускает CA со случайным начальным условием."""
    rule = make_rule(rule_number)
    # LCG для генерации начального условия
    a, c, m = 1664525, 1013904223, 2**32
    x = seed
    cells = []
    for _ in range(width):
        x = (a * x + c) % m
        cells.append(1 if x < m // 2 else 0)

    history = [cells[:]]
    for _ in range(steps):
        cells = step(cells, rule)
        history.append(cells[:])
    return history


def center_column(history, width):
    center = width // 2
    return [row[center] for row in history]


def mi_corrected(seq, block_size, gap=0):
    n = len(seq)
    pairs = []
    for i in range(0, n - 2 * block_size - gap + 1):
        a = tuple(seq[i:i + block_size])
        b = tuple(seq[i + block_size + gap:i + 2 * block_size + gap])
        pairs.append((a, b))

    N = len(pairs)
    if N == 0:
        return 0.0, 0.0, 0

    a_counts = Counter(p[0] for p in pairs)
    b_counts = Counter(p[1] for p in pairs)
    ab_counts = Counter(pairs)

    h_a = -sum((c / N) * math.log2(c / N) for c in a_counts.values())
    h_b = -sum((c / N) * math.log2(c / N) for c in b_counts.values())
    h_ab = -sum((c / N) * math.log2(c / N) for c in ab_counts.values())
    mi_raw = h_a + h_b - h_ab

    k_a = len(a_counts)
    k_b = len(b_counts)
    k_ab = len(ab_counts)

    bias = ((k_a - 1) + (k_b - 1) - (k_ab - 1)) / (2 * N * math.log(2))
    mi_corr = max(0, mi_raw - bias)

    return mi_corr, mi_raw, k_ab


def block_entropy(seq, block_size):
    blocks = []
    for i in range(len(seq) - block_size + 1):
        blocks.append(tuple(seq[i:i + block_size]))
    N = len(blocks)
    counts = Counter(blocks)
    h = -sum((c / N) * math.log2(c / N) for c in counts.values())
    return h, N, len(counts)


def generate_random(n, seed=42):
    a, c, m = 1664525, 1013904223, 2**32
    x = seed
    result = []
    for _ in range(n):
        x = (a * x + c) % m
        result.append(1 if x < m // 2 else 0)
    return result


if __name__ == '__main__':
    STEPS = 10000
    BLOCK = 4
    WIDTH = 201
    N_SEEDS = 5  # среднее по 5 случайным начальным условиям

    # Random baseline
    rnd = generate_random(STEPS + 1)
    rnd_mi, _, _ = mi_corrected(rnd, BLOCK)
    rnd_h, _, _ = block_entropy(rnd, BLOCK)

    print(f"Random baseline: MI={rnd_mi:.6f}, H={rnd_h:.4f}")
    print(f"Block={BLOCK}, Steps={STEPS}, Seeds={N_SEEDS}")
    print()

    # Правила с высокой энтропией из цикла 3
    # Class 4: 110, 124, 137, 193
    # Class 3: 30, 45, 75, 86, 89, 101, 135, 149
    # + несколько промежуточных для проверки
    test_rules = list(range(256))

    results = []

    for rule_num in test_rules:
        mi_values = []
        h_values = []

        for seed in range(N_SEEDS):
            history = run_random_init(rule_num, WIDTH, STEPS, seed=seed * 1000 + 17)
            col = center_column(history, WIDTH)
            mi, _, k_ab = mi_corrected(col, BLOCK)
            h, _, _ = block_entropy(col, BLOCK)
            mi_values.append(mi)
            h_values.append(h)

        mi_mean = sum(mi_values) / len(mi_values)
        mi_std = (sum((v - mi_mean)**2 for v in mi_values) / len(mi_values)) ** 0.5
        h_mean = sum(h_values) / len(h_values)
        mi_ratio = mi_mean / rnd_mi if rnd_mi > 0 else 0

        results.append({
            'rule': rule_num,
            'mi_mean': round(mi_mean, 6),
            'mi_std': round(mi_std, 6),
            'mi_ratio': round(mi_ratio, 2),
            'entropy': round(h_mean, 4),
            'mi_values': [round(v, 6) for v in mi_values],
        })

    # Сортируем по MI ratio
    results.sort(key=lambda r: r['mi_ratio'], reverse=True)

    print(f"{'Rule':>5} {'MI_mean':>9} {'MI_std':>9} {'MI_ratio':>9} {'Entropy':>8}")
    print("-" * 50)
    for r in results[:30]:
        print(f"{r['rule']:>5} {r['mi_mean']:>9.6f} {r['mi_std']:>9.6f} {r['mi_ratio']:>8.1f}x {r['entropy']:>8.4f}")

    # Группы
    high_entropy = [r for r in results if r['entropy'] > 3.5]

    print(f"\n=== ВЫСОКАЯ ЭНТРОПИЯ (H > 3.5), random init ===")
    print(f"{'Rule':>5} {'MI_ratio':>9} {'MI_std':>9} {'Entropy':>8}")
    print("-" * 40)
    for r in sorted(high_entropy, key=lambda x: x['mi_ratio'], reverse=True):
        print(f"{r['rule']:>5} {r['mi_ratio']:>8.1f}x {r['mi_std']:>9.6f} {r['entropy']:>8.4f}")

    # Зона 2-10x
    zone_2_10 = [r for r in results if r['entropy'] > 3.5 and 2 < r['mi_ratio'] <= 10]
    complex_r = [r for r in results if r['entropy'] > 3.5 and r['mi_ratio'] > 10]
    chaotic_r = [r for r in results if r['entropy'] > 3.5 and r['mi_ratio'] < 2]

    print(f"\n=== КЛЮЧЕВОЙ РЕЗУЛЬТАТ ===")
    print(f"Class 4 (MI > 10x, H > 3.5): {[r['rule'] for r in complex_r]}")
    print(f"Zone 2-10x (H > 3.5):         {[r['rule'] for r in zone_2_10]}")
    print(f"Class 3 (MI < 2x, H > 3.5):   {[r['rule'] for r in chaotic_r]}")

    if complex_r and chaotic_r:
        avg_c4 = sum(r['mi_ratio'] for r in complex_r) / len(complex_r)
        avg_c3 = sum(r['mi_ratio'] for r in chaotic_r) / len(chaotic_r)
        print(f"\nСредний MI_ratio Class 4: {avg_c4:.1f}x ({len(complex_r)} rules)")
        print(f"Средний MI_ratio Class 3: {avg_c3:.1f}x ({len(chaotic_r)} rules)")
        print(f"Separation factor: {avg_c4 / max(avg_c3, 0.01):.1f}x")
        print(f"Зона 2-10x: {'ПУСТА' if not zone_2_10 else f'{len(zone_2_10)} правил'}")

    # Сравнение с результатами цикла 3 (single cell init)
    print(f"\n=== СРАВНЕНИЕ С SINGLE CELL INIT (цикл 3) ===")
    try:
        with open('mi_all_rules_results.json') as f:
            old = json.load(f)
        old_rules = {r['rule']: r for r in old['rules']}

        print(f"{'Rule':>5} {'Single':>9} {'Random':>9} {'Ratio':>8}")
        print("-" * 35)
        for r in results:
            if r['rule'] in old_rules and r['entropy'] > 3.0:
                old_ratio = old_rules[r['rule']]['mi_ratio']
                change = r['mi_ratio'] / old_ratio if old_ratio > 0 else float('inf')
                if old_ratio > 5 or r['mi_ratio'] > 5:
                    print(f"{r['rule']:>5} {old_ratio:>8.1f}x {r['mi_ratio']:>8.1f}x {change:>7.2f}")
    except FileNotFoundError:
        print("(нет данных для сравнения)")

    # Сохраняем
    with open('mi_random_init_results.json', 'w') as f:
        json.dump({
            'params': {'steps': STEPS, 'block': BLOCK, 'width': WIDTH, 'n_seeds': N_SEEDS},
            'random_baseline': {'mi': rnd_mi, 'entropy': rnd_h},
            'results': results,
        }, f, indent=2)
    print("\nРезультаты сохранены в mi_random_init_results.json")
