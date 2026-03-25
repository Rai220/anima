"""
Корректировка оценки взаимной информации для конечных выборок.

Проблема: при block=8 получаем MI≈3 для ВСЕХ последовательностей.
Это артефакт: 2^8 = 256 возможных паттернов, но только ~1000 блоков.
MI переоценивается из-за случайных корреляций в малой выборке.

Метод коррекции: bias ≈ (|A| - 1)(|B| - 1) / (2N ln2)
(Miller-Madow correction)

Реальный вопрос: при КАКОМ размере блока Rule 30 начинает
отличаться от Random? И отличается ли вообще?

Контраст: Rule 110 имеет NMI≈0.95, что ЯВНО не артефакт.
Что делает Rule 110 структурированной, а Rule 30 — нет?
"""

import math
from collections import Counter
from ca import run


def center_column(rule_num, steps=10000, width=201):
    history = run(rule_num, width=width, steps=steps)
    center = width // 2
    return [row[center] for row in history]


def mi_corrected(seq, block_size, gap=0):
    """MI с коррекцией Miller-Madow."""
    n = len(seq)
    pairs = []
    for i in range(0, n - 2 * block_size - gap + 1):
        a = tuple(seq[i:i + block_size])
        b = tuple(seq[i + block_size + gap:i + 2 * block_size + gap])
        pairs.append((a, b))

    N = len(pairs)
    if N == 0:
        return {'mi_raw': 0, 'mi_corrected': 0, 'bias': 0}

    a_counts = Counter(p[0] for p in pairs)
    b_counts = Counter(p[1] for p in pairs)
    ab_counts = Counter(pairs)

    # Raw MI
    h_a = -sum((c / N) * math.log2(c / N) for c in a_counts.values())
    h_b = -sum((c / N) * math.log2(c / N) for c in b_counts.values())
    h_ab = -sum((c / N) * math.log2(c / N) for c in ab_counts.values())
    mi_raw = h_a + h_b - h_ab

    # Miller-Madow bias correction
    # bias ≈ (k_a - 1)(k_b - 1) / (2N ln2)  [in bits]
    k_a = len(a_counts)
    k_b = len(b_counts)
    k_ab = len(ab_counts)
    # More accurate: bias for H(A,B) - bias for H(A) - bias for H(B)
    # bias_H ≈ (k - 1) / (2N ln2)
    bias_h_a = (k_a - 1) / (2 * N * math.log(2))
    bias_h_b = (k_b - 1) / (2 * N * math.log(2))
    bias_h_ab = (k_ab - 1) / (2 * N * math.log(2))
    # MI_bias = bias_H(A) + bias_H(B) - bias_H(AB)
    # = [(k_a-1) + (k_b-1) - (k_ab-1)] / (2N ln2)
    mi_bias = bias_h_a + bias_h_b - bias_h_ab
    mi_corrected = mi_raw - mi_bias

    return {
        'mi_raw': round(mi_raw, 6),
        'mi_corrected': round(max(0, mi_corrected), 6),
        'bias': round(mi_bias, 6),
        'N': N,
        'k_a': k_a,
        'k_b': k_b,
        'k_ab': k_ab,
        'h_a': round(h_a, 4),
        'h_b': round(h_b, 4),
        'ratio_data_to_states': round(N / (2 ** block_size), 2),
    }


def generate_random(n, bias=0.5, seed=42):
    a = 1664525
    c = 1013904223
    m = 2 ** 32
    x = seed
    result = []
    threshold = int(bias * m)
    for _ in range(n):
        x = (a * x + c) % m
        result.append(1 if x < threshold else 0)
    return result


if __name__ == '__main__':
    STEPS = 20000  # больше данных для надёжной оценки

    print("Генерирую последовательности...\n")
    seqs = {
        'rule_30': center_column(30, STEPS),
        'rule_45': center_column(45, STEPS),
        'rule_110': center_column(110, STEPS),
        'random_1': generate_random(STEPS + 1, seed=42),
        'random_2': generate_random(STEPS + 1, seed=137),
    }

    print(f"{'name':>12} {'block':>5} {'MI_raw':>8} {'MI_corr':>8} {'bias':>8} "
          f"{'k_ab':>6} {'N':>6} {'data/states':>11}")
    print("-" * 75)

    for bs in [2, 3, 4, 5, 6, 7, 8]:
        for name in ['rule_30', 'rule_45', 'rule_110', 'random_1', 'random_2']:
            r = mi_corrected(seqs[name], bs, gap=0)
            print(f"{name:>12} {bs:>5} {r['mi_raw']:>8.4f} {r['mi_corrected']:>8.4f} "
                  f"{r['bias']:>8.4f} {r['k_ab']:>6} {r['N']:>6} {r['ratio_data_to_states']:>11.1f}")
        print()

    # Точная проверка: Rule 30 vs Random при маленьких блоках
    print("=" * 60)
    print("ТОЧНАЯ ПРОВЕРКА (маленькие блоки, bias ≈ 0)")
    print("=" * 60)

    for bs in [2, 3, 4]:
        print(f"\nBlock size = {bs}:")
        for name in sorted(seqs.keys()):
            r = mi_corrected(seqs[name], bs, gap=0)
            print(f"  {name:>12}: MI_corrected = {r['mi_corrected']:.6f}")

    # Как MI зависит от gap (расстояния между блоками)?
    print(f"\n{'=' * 60}")
    print("MI vs GAP (затухание корреляций)")
    print("=" * 60)

    print(f"\n{'gap':>4}", end="")
    for name in ['rule_30', 'rule_110', 'random_1']:
        print(f"  {name:>12}", end="")
    print()
    print("-" * 45)

    for gap in [0, 1, 2, 4, 8, 16, 32, 64, 128]:
        print(f"{gap:>4}", end="")
        for name in ['rule_30', 'rule_110', 'random_1']:
            r = mi_corrected(seqs[name], block_size=4, gap=gap)
            print(f"  {r['mi_corrected']:>12.6f}", end="")
        print()

    print(f"\n{'=' * 60}")
    print("ИТОГ")
    print("=" * 60)

    r30_b4 = mi_corrected(seqs['rule_30'], 4)
    r110_b4 = mi_corrected(seqs['rule_110'], 4)
    rnd_b4 = mi_corrected(seqs['random_1'], 4)

    print(f"\nПри block=4 (bias ≈ 0):")
    print(f"  Rule 30:  MI = {r30_b4['mi_corrected']:.6f}")
    print(f"  Rule 110: MI = {r110_b4['mi_corrected']:.6f}")
    print(f"  Random:   MI = {rnd_b4['mi_corrected']:.6f}")

    ratio_30 = r30_b4['mi_corrected'] / rnd_b4['mi_corrected'] if rnd_b4['mi_corrected'] > 0 else float('inf')
    ratio_110 = r110_b4['mi_corrected'] / rnd_b4['mi_corrected'] if rnd_b4['mi_corrected'] > 0 else float('inf')

    print(f"\n  Rule 30 / Random  = {ratio_30:.2f}x")
    print(f"  Rule 110 / Random = {ratio_110:.2f}x")

    if ratio_30 < 2.0:
        print(f"\n  ВЫВОД: Rule 30 неотличима от случайной.")
        print(f"  Центральная колонка — эффективный PRNG.")
    else:
        print(f"\n  ВЫВОД: Rule 30 содержит детектируемую структуру.")

    if ratio_110 > 10:
        print(f"\n  Rule 110 содержит СИЛЬНУЮ временну́ю структуру.")
        print(f"  Class 3 (хаос) ≠ Class 4 (сложность) — это РАЗНЫЕ ВЕЩИ:")
        print(f"  - Class 3: высокая энтропия, нулевая MI → случайность")
        print(f"  - Class 4: высокая энтропия, высокая MI → структура + сложность")
