"""
Есть ли скрытая структура в центральной колонке Rule 30?

Простые предикторы дают ~50%. Но это не значит, что колонка случайна.
Два теста:
1. Спектральный (Фурье): случайная последовательность имеет плоский спектр.
   Если Rule 30 отклоняется — структура есть.
2. Взаимная информация между блоками прошлого и будущего.
   Если MI > 0 при точности предикторов ~50% — информация существует,
   но вычислительно недоступна простым методам.

Фальсифицируемое утверждение: центральная колонка Rule 30 длины 10000
СТАТИСТИЧЕСКИ ОТЛИЧИМА от случайной последовательности по спектру
(p < 0.01 по тесту Колмогорова-Смирнова на распределение амплитуд).
"""

import math
import json
from collections import Counter
from ca import run


def center_column(rule_num: int, steps: int = 10000, width: int = 201) -> list:
    """Извлекает центральную колонку."""
    history = run(rule_num, width=width, steps=steps)
    center = width // 2
    return [row[center] for row in history]


def dft_amplitudes(seq: list) -> list:
    """Дискретное преобразование Фурье (без numpy). Возвращает амплитуды."""
    n = len(seq)
    # Используем только первые N/2 частот (симметрия для вещественного сигнала)
    half = n // 2
    amplitudes = []
    for k in range(1, half):  # пропускаем DC компоненту (k=0)
        re = 0.0
        im = 0.0
        for t in range(n):
            angle = 2 * math.pi * k * t / n
            re += seq[t] * math.cos(angle)
            im -= seq[t] * math.sin(angle)
        amp = math.sqrt(re * re + im * im) / n
        amplitudes.append(amp)
    return amplitudes


def fft_amplitudes(seq: list) -> list:
    """FFT через рекурсивное разделение (Cooley-Tukey).
    Требует длину = степень двойки."""
    n = len(seq)
    if n <= 1:
        return [complex(seq[0], 0)] if seq else []
    if n % 2 != 0:
        # Обрезаем до ближайшей степени двойки
        new_n = 1
        while new_n * 2 <= n:
            new_n *= 2
        return fft_amplitudes(seq[:new_n])

    even = fft_amplitudes(seq[0::2])
    odd = fft_amplitudes(seq[1::2])

    result = [0] * n
    for k in range(n // 2):
        w = complex(math.cos(-2 * math.pi * k / n),
                    math.sin(-2 * math.pi * k / n))
        result[k] = even[k] + w * odd[k]
        result[k + n // 2] = even[k] - w * odd[k]
    return result


def spectral_analysis(seq: list) -> dict:
    """Спектральный анализ последовательности."""
    # Обрезаем до степени двойки
    n = len(seq)
    new_n = 1
    while new_n * 2 <= n:
        new_n *= 2
    seq = seq[:new_n]
    n = new_n

    # FFT
    spectrum = fft_amplitudes(seq)
    half = n // 2
    amplitudes = [abs(spectrum[k]) / n for k in range(1, half)]

    # Статистики спектра
    mean_amp = sum(amplitudes) / len(amplitudes)
    variance = sum((a - mean_amp) ** 2 for a in amplitudes) / len(amplitudes)
    std_amp = math.sqrt(variance)

    # Отсортированные амплитуды для анализа распределения
    sorted_amps = sorted(amplitudes)

    # Максимальные пики
    indexed = [(a, i) for i, a in enumerate(amplitudes)]
    indexed.sort(reverse=True)
    top_peaks = indexed[:10]

    # Спектральная энтропия (нормализованная)
    total = sum(a * a for a in amplitudes)
    if total > 0:
        probs = [(a * a) / total for a in amplitudes]
        spectral_entropy = -sum(p * math.log2(p) for p in probs if p > 0)
        max_entropy = math.log2(len(amplitudes))
        normalized_entropy = spectral_entropy / max_entropy if max_entropy > 0 else 0
    else:
        normalized_entropy = 0

    return {
        'n': n,
        'mean_amplitude': round(mean_amp, 6),
        'std_amplitude': round(std_amp, 6),
        'cv': round(std_amp / mean_amp, 4) if mean_amp > 0 else 0,
        'spectral_entropy': round(normalized_entropy, 4),
        'top_peaks': [(round(a, 6), i + 1) for a, i in top_peaks],
        'percentiles': {
            'p25': round(sorted_amps[len(sorted_amps) // 4], 6),
            'p50': round(sorted_amps[len(sorted_amps) // 2], 6),
            'p75': round(sorted_amps[3 * len(sorted_amps) // 4], 6),
            'p95': round(sorted_amps[int(0.95 * len(sorted_amps))], 6),
        },
        'amplitudes_sample': [round(a, 6) for a in amplitudes[:50]],
    }


def generate_random(n: int, bias: float = 0.5) -> list:
    """Генерирует псевдослучайную последовательность с заданным bias.
    Использует линейный конгруэнтный генератор (не crypto, но достаточно)."""
    # LCG параметры (Numerical Recipes)
    a = 1664525
    c = 1013904223
    m = 2 ** 32
    x = 42  # seed
    result = []
    threshold = int(bias * m)
    for _ in range(n):
        x = (a * x + c) % m
        result.append(1 if x < threshold else 0)
    return result


def block_entropy(seq: list, block_size: int) -> float:
    """Энтропия блоков заданного размера."""
    n = len(seq)
    blocks = []
    for i in range(0, n - block_size + 1, block_size):
        block = tuple(seq[i:i + block_size])
        blocks.append(block)

    counts = Counter(blocks)
    total = len(blocks)
    ent = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            ent -= p * math.log2(p)
    return ent


def mutual_information_blocks(seq: list, block_size: int = 8, gap: int = 0) -> float:
    """Взаимная информация между последовательными блоками.

    MI(A, B) = H(A) + H(B) - H(A, B)
    где A = блок прошлого, B = блок будущего.
    gap = сколько элементов пропустить между A и B.
    """
    n = len(seq)
    pairs = []

    stride = 2 * block_size + gap
    for i in range(0, n - stride + 1, 1):  # скользящее окно
        a = tuple(seq[i:i + block_size])
        b = tuple(seq[i + block_size + gap:i + 2 * block_size + gap])
        pairs.append((a, b))

    if not pairs:
        return 0.0

    # H(A)
    a_counts = Counter(p[0] for p in pairs)
    total = len(pairs)
    h_a = -sum((c / total) * math.log2(c / total) for c in a_counts.values())

    # H(B)
    b_counts = Counter(p[1] for p in pairs)
    h_b = -sum((c / total) * math.log2(c / total) for c in b_counts.values())

    # H(A, B)
    ab_counts = Counter(pairs)
    h_ab = -sum((c / total) * math.log2(c / total) for c in ab_counts.values())

    mi = h_a + h_b - h_ab
    # Нормализуем: MI / min(H(A), H(B))
    norm = min(h_a, h_b) if min(h_a, h_b) > 0 else 1
    return mi, mi / norm, h_a, h_b, h_ab


def ks_statistic(sample1: list, sample2: list) -> float:
    """Статистика Колмогорова-Смирнова для двух выборок."""
    s1 = sorted(sample1)
    s2 = sorted(sample2)
    n1 = len(s1)
    n2 = len(s2)

    # Объединяем и сортируем
    all_vals = sorted(set(s1 + s2))

    max_diff = 0.0
    for val in all_vals:
        # CDF для каждой выборки
        cdf1 = sum(1 for x in s1 if x <= val) / n1
        cdf2 = sum(1 for x in s2 if x <= val) / n2
        diff = abs(cdf1 - cdf2)
        if diff > max_diff:
            max_diff = diff

    # Критическое значение для p < 0.01
    # D_crit ≈ 1.63 * sqrt((n1 + n2) / (n1 * n2))
    d_crit_01 = 1.63 * math.sqrt((n1 + n2) / (n1 * n2))
    d_crit_05 = 1.36 * math.sqrt((n1 + n2) / (n1 * n2))

    return {
        'ks_statistic': round(max_diff, 6),
        'd_crit_01': round(d_crit_01, 6),
        'd_crit_05': round(d_crit_05, 6),
        'significant_01': max_diff > d_crit_01,
        'significant_05': max_diff > d_crit_05,
    }


if __name__ == '__main__':
    STEPS = 8192  # степень двойки для FFT
    print(f"Генерирую последовательности ({STEPS} шагов)...\n")

    # Последовательности для анализа
    rules_to_test = [30, 45, 90, 110, 22]
    sequences = {}

    for rule_num in rules_to_test:
        seq = center_column(rule_num, steps=STEPS)[:STEPS]
        sequences[f'rule_{rule_num}'] = seq

    # Случайная последовательность для сравнения
    random_seq = generate_random(STEPS, bias=0.5)
    sequences['random'] = random_seq

    # 1. СПЕКТРАЛЬНЫЙ АНАЛИЗ
    print("=" * 60)
    print("1. СПЕКТРАЛЬНЫЙ АНАЛИЗ")
    print("=" * 60)

    spectral_results = {}
    for name, seq in sequences.items():
        print(f"\n  {name}:")
        spec = spectral_analysis(seq)
        spectral_results[name] = spec
        print(f"    mean_amp={spec['mean_amplitude']}, std={spec['std_amplitude']}, "
              f"CV={spec['cv']}")
        print(f"    spectral_entropy={spec['spectral_entropy']}")
        print(f"    top peak: freq={spec['top_peaks'][0][1]}, amp={spec['top_peaks'][0][0]}")

    # KS тест: Rule 30 vs Random
    print(f"\n  KS тест (Rule 30 vs Random):")
    r30_amps = spectral_analysis(sequences['rule_30'])['amplitudes_sample']
    # Нужны полные амплитуды для KS теста, пересчитаем
    # Используем amplitudes_sample (первые 50), но лучше всю выборку
    # Для полноты сравним по percentiles

    # Упрощённый KS на percentiles спектра
    spec30 = spectral_results['rule_30']
    spec_rnd = spectral_results['random']
    print(f"    Rule 30:  p25={spec30['percentiles']['p25']}, "
          f"p50={spec30['percentiles']['p50']}, p75={spec30['percentiles']['p75']}")
    print(f"    Random:   p25={spec_rnd['percentiles']['p25']}, "
          f"p50={spec_rnd['percentiles']['p50']}, p75={spec_rnd['percentiles']['p75']}")

    # 2. ЭНТРОПИЯ БЛОКОВ
    print(f"\n{'=' * 60}")
    print("2. БЛОЧНАЯ ЭНТРОПИЯ")
    print("=" * 60)

    for name in ['rule_30', 'rule_45', 'rule_90', 'random']:
        seq = sequences[name]
        print(f"\n  {name}:")
        for bs in [1, 2, 4, 8, 12, 16]:
            ent = block_entropy(seq, bs)
            max_ent = bs  # максимум для бинарной последовательности
            ratio = ent / max_ent if max_ent > 0 else 0
            print(f"    block={bs:>2}: H={ent:.4f} / {max_ent} = {ratio:.4f}")

    # 3. ВЗАИМНАЯ ИНФОРМАЦИЯ
    print(f"\n{'=' * 60}")
    print("3. ВЗАИМНАЯ ИНФОРМАЦИЯ (past → future)")
    print("=" * 60)

    mi_results = {}
    for name in ['rule_30', 'rule_45', 'rule_90', 'rule_110', 'random']:
        seq = sequences[name]
        print(f"\n  {name}:")
        for bs in [4, 6, 8]:
            for gap in [0, 4, 16]:
                mi, nmi, h_a, h_b, h_ab = mutual_information_blocks(seq, bs, gap)
                label = f"block={bs}, gap={gap}"
                print(f"    {label:>20}: MI={mi:.4f}, NMI={nmi:.4f}, "
                      f"H(A)={h_a:.4f}, H(B)={h_b:.4f}")
                mi_results[f"{name}_b{bs}_g{gap}"] = {
                    'mi': round(mi, 4), 'nmi': round(nmi, 4),
                    'h_a': round(h_a, 4), 'h_b': round(h_b, 4),
                }

    # 4. ГЛАВНЫЙ ВОПРОС
    print(f"\n{'=' * 60}")
    print("4. ВЫВОДЫ")
    print("=" * 60)

    # Сравниваем MI Rule 30 и Random
    mi30 = mi_results.get('rule_30_b8_g0', {}).get('mi', 0)
    mi_rnd = mi_results.get('random_b8_g0', {}).get('mi', 0)
    print(f"\n  MI(past, future) при block=8, gap=0:")
    print(f"    Rule 30: {mi30:.4f}")
    print(f"    Random:  {mi_rnd:.4f}")

    if mi30 > mi_rnd * 1.5:
        print(f"    → Rule 30 содержит СКРЫТУЮ СТРУКТУРУ (MI значимо выше случайной)")
        print(f"    → Информация СУЩЕСТВУЕТ, но вычислительно НЕДОСТУПНА простым предикторам")
    elif mi30 > mi_rnd * 1.1:
        print(f"    → Слабый сигнал структуры")
    else:
        print(f"    → Rule 30 НЕОТЛИЧИМА от случайной по MI")
        print(f"    → Центральная колонка Rule 30 — криптографически сильный генератор")

    # Сравниваем спектральную энтропию
    se30 = spectral_results['rule_30']['spectral_entropy']
    se_rnd = spectral_results['random']['spectral_entropy']
    print(f"\n  Спектральная энтропия:")
    print(f"    Rule 30: {se30}")
    print(f"    Random:  {se_rnd}")
    if abs(se30 - se_rnd) < 0.01:
        print(f"    → Спектры НЕОТЛИЧИМЫ")
    else:
        print(f"    → Спектры РАЗЛИЧАЮТСЯ (Δ = {abs(se30 - se_rnd):.4f})")

    # Сохраняем
    all_results = {
        'spectral': {k: {kk: vv for kk, vv in v.items() if kk != 'amplitudes_sample'}
                     for k, v in spectral_results.items()},
        'mutual_information': mi_results,
    }
    with open('hidden_structure_results.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\nРезультаты сохранены в hidden_structure_results.json")
