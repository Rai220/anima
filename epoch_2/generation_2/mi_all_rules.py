"""
MI для всех 256 элементарных CA.

Вопрос: действительно ли MI разделяет Class 3 (хаос) и Class 4 (сложность)?
Тестировал на 2 правилах (Rule 30, Rule 110). Теперь — на всех 256.

Фальсифицируемая гипотеза: все правила с высокой энтропией и высокой MI
принадлежат Class 4 по Вольфраму, а все правила с высокой энтропией
и низкой MI — Class 3.
"""

import math
import json
from collections import Counter
from ca import run


def center_column(rule_num, steps=10000, width=201):
    history = run(rule_num, width=width, steps=steps)
    center = width // 2
    return [row[center] for row in history]


def block_entropy(seq, block_size):
    """Энтропия блоков длины block_size."""
    blocks = []
    for i in range(len(seq) - block_size + 1):
        blocks.append(tuple(seq[i:i + block_size]))
    N = len(blocks)
    counts = Counter(blocks)
    h = -sum((c / N) * math.log2(c / N) for c in counts.values())
    return h, N, len(counts)


def mi_corrected(seq, block_size, gap=0):
    """MI между соседними блоками с Miller-Madow коррекцией."""
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


def generate_random(n, seed=42):
    a = 1664525
    c = 1013904223
    m = 2 ** 32
    x = seed
    result = []
    for _ in range(n):
        x = (a * x + c) % m
        result.append(1 if x < m // 2 else 0)
    return result


if __name__ == '__main__':
    STEPS = 10000
    BLOCK = 4  # data/states = 10000/16 ≈ 625, bias ≈ 0
    WIDTH = 201

    # Random baseline
    rnd = generate_random(STEPS + 1)
    rnd_mi, _, _ = mi_corrected(rnd, BLOCK)
    rnd_h, _, _ = block_entropy(rnd, BLOCK)

    print(f"Random baseline: MI={rnd_mi:.6f}, H={rnd_h:.4f}")
    print(f"Block={BLOCK}, Steps={STEPS}, data/states={STEPS // (2**BLOCK):.0f}")
    print()

    results = []

    for rule_num in range(256):
        col = center_column(rule_num, steps=STEPS, width=WIDTH)
        mi, mi_raw, k_ab = mi_corrected(col, BLOCK)
        h, n_blocks, k = block_entropy(col, BLOCK)
        density = sum(col) / len(col)
        mi_ratio = mi / rnd_mi if rnd_mi > 0 else float('inf')

        results.append({
            'rule': rule_num,
            'mi_corrected': round(mi, 6),
            'mi_raw': round(mi_raw, 6),
            'entropy': round(h, 4),
            'mi_ratio': round(mi_ratio, 2),
            'density': round(density, 4),
            'k_ab': k_ab,
        })

    # Сортируем по MI ratio
    results.sort(key=lambda r: r['mi_ratio'], reverse=True)

    # Выводим таблицу
    print(f"{'Rule':>5} {'MI_corr':>9} {'MI_ratio':>9} {'Entropy':>8} {'Density':>8} {'k_ab':>6}")
    print("-" * 55)

    for r in results[:30]:
        print(f"{r['rule']:>5} {r['mi_corrected']:>9.6f} {r['mi_ratio']:>8.1f}x "
              f"{r['entropy']:>8.4f} {r['density']:>8.4f} {r['k_ab']:>6}")

    print(f"\n... ({len(results) - 30} more)")

    # Статистика по группам
    high_mi = [r for r in results if r['mi_ratio'] > 10]
    medium_mi = [r for r in results if 2 < r['mi_ratio'] <= 10]
    low_mi = [r for r in results if 1.5 < r['mi_ratio'] <= 2]
    baseline_mi = [r for r in results if r['mi_ratio'] <= 1.5]

    print(f"\n=== ГРУППЫ ===")
    print(f"MI > 10x random:   {len(high_mi)} rules: {[r['rule'] for r in high_mi]}")
    print(f"2x < MI ≤ 10x:     {len(medium_mi)} rules: {[r['rule'] for r in medium_mi]}")
    print(f"1.5x < MI ≤ 2x:    {len(low_mi)} rules: {[r['rule'] for r in low_mi]}")
    print(f"MI ≤ 1.5x random:  {len(baseline_mi)} rules")

    # Правила с ВЫСОКОЙ энтропией
    high_entropy = [r for r in results if r['entropy'] > 3.5]  # из максимум 4.0 для block=4
    print(f"\n=== ВЫСОКАЯ ЭНТРОПИЯ (H > 3.5) ===")
    print(f"{'Rule':>5} {'MI_ratio':>9} {'Entropy':>8} {'Density':>8}")
    print("-" * 35)
    for r in sorted(high_entropy, key=lambda x: x['mi_ratio'], reverse=True):
        print(f"{r['rule']:>5} {r['mi_ratio']:>8.1f}x {r['entropy']:>8.4f} {r['density']:>8.4f}")

    # Ключевой вопрос: есть ли правила с H > 3.5 и MI > 10x?
    complex_rules = [r for r in results if r['entropy'] > 3.5 and r['mi_ratio'] > 10]
    chaotic_rules = [r for r in results if r['entropy'] > 3.5 and r['mi_ratio'] < 2]

    print(f"\n=== КЛЮЧЕВОЙ РЕЗУЛЬТАТ ===")
    print(f"Правила с H > 3.5 И MI > 10x (кандидаты Class 4): {[r['rule'] for r in complex_rules]}")
    print(f"Правила с H > 3.5 И MI < 2x (кандидаты Class 3):  {[r['rule'] for r in chaotic_rules]}")

    if complex_rules:
        avg_mi_complex = sum(r['mi_ratio'] for r in complex_rules) / len(complex_rules)
        avg_mi_chaotic = sum(r['mi_ratio'] for r in chaotic_rules) / len(chaotic_rules) if chaotic_rules else 0
        print(f"\nСредний MI_ratio:")
        print(f"  'Complex' (H>3.5, MI>10x): {avg_mi_complex:.1f}x ({len(complex_rules)} rules)")
        print(f"  'Chaotic' (H>3.5, MI<2x):  {avg_mi_chaotic:.1f}x ({len(chaotic_rules)} rules)")
        print(f"  Separation factor: {avg_mi_complex / max(avg_mi_chaotic, 0.01):.1f}x")

    # Сохраняем
    with open('mi_all_rules_results.json', 'w') as f:
        json.dump({
            'params': {'steps': STEPS, 'block': BLOCK, 'width': WIDTH},
            'random_baseline': {'mi': rnd_mi, 'entropy': rnd_h},
            'rules': results,
        }, f, indent=2)
    print("\nРезультаты сохранены в mi_all_rules_results.json")
