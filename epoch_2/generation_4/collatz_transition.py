"""
Глубокий анализ переходной зоны a=5.

Вопросы:
1. Какова плотность сходящихся значений при a=5, b=1?
2. Есть ли структура (не случайная) в множестве сходящихся значений?
3. Как плотность меняется с масштабом? Убывает? Стабилизируется?
4. Можно ли предсказать по начальному значению, сходится ли оно?
"""

import json
from collections import defaultdict
import math

def collatz_step(n, a, b):
    if n % 2 == 0:
        return n // 2
    else:
        return a * n + b

def classify(start, a, b, max_steps=200_000, threshold=10**18):
    """Классифицировать: converge/diverge. Вернуть (тип, цикл_или_None, шаги)."""
    seen = {}
    n = start
    for step in range(max_steps):
        if n in seen:
            cycle_start = seen[n]
            cycle_len = step - cycle_start
            cycle = []
            curr = n
            for _ in range(cycle_len):
                cycle.append(curr)
                curr = collatz_step(curr, a, b)
            return ('cycle', tuple(sorted(cycle)), step)
        if abs(n) > threshold:
            return ('diverge', None, step)
        seen[n] = step
        n = collatz_step(n, a, b)
    return ('timeout', None, max_steps)


def main():
    print("=" * 60)
    print("ПЕРЕХОДНАЯ ЗОНА: a=5, b=1")
    print("=" * 60)

    a, b = 5, 1

    # 1. Плотность сходящихся в окнах
    print("\n--- 1. Плотность сходящихся по блокам по 100 ---")
    window = 100
    max_n = 2000
    densities = []

    all_converging = set()
    all_cycles = {}

    for block_start in range(1, max_n + 1, window):
        conv = 0
        for s in range(block_start, min(block_start + window, max_n + 1)):
            result = classify(s, a, b)
            if result[0] == 'cycle':
                conv += 1
                all_converging.add(s)
                cycle_key = result[1]
                if cycle_key not in all_cycles:
                    all_cycles[cycle_key] = {'min': min(cycle_key), 'len': len(cycle_key), 'count': 0}
                all_cycles[cycle_key]['count'] += 1
        density = conv / window
        densities.append((block_start, density))
        print(f"  [{block_start:5d}, {block_start+window-1:5d}]: {density:.2%} ({conv}/{window})")

    total_conv = len(all_converging)
    print(f"\nИтого: {total_conv}/{max_n} = {total_conv/max_n:.2%}")
    print(f"Различных циклов: {len(all_cycles)}")

    # 2. Характеристики циклов
    print("\n--- 2. Циклы (a=5, b=1) ---")
    for cycle_key in sorted(all_cycles.keys(), key=lambda c: len(c)):
        info = all_cycles[cycle_key]
        elements = list(cycle_key)
        if len(elements) <= 15:
            print(f"  Длина {info['len']}, мин={info['min']}, "
                  f"притягивает {info['count']} значений: {elements}")
        else:
            print(f"  Длина {info['len']}, мин={info['min']}, "
                  f"притягивает {info['count']} значений")

    # 3. Модулярная структура сходящихся
    print("\n--- 3. Модулярная структура сходящихся чисел ---")
    for mod in [2, 3, 4, 5, 6, 8, 10, 12, 16]:
        residue_counts = defaultdict(int)
        residue_total = defaultdict(int)
        for s in range(1, max_n + 1):
            r = s % mod
            residue_total[r] += 1
            if s in all_converging:
                residue_counts[r] += 1

        # Показать только если есть существенная разница
        rates = {r: residue_counts[r] / residue_total[r] if residue_total[r] > 0 else 0
                 for r in range(mod)}
        max_rate = max(rates.values())
        min_rate = min(rates.values())
        if max_rate - min_rate > 0.15:  # существенная разница
            print(f"\n  mod {mod} (разброс {max_rate-min_rate:.2%}):")
            for r in range(mod):
                bar = '█' * int(rates[r] * 30)
                print(f"    {r:3d}: {rates[r]:.2%} {bar}")

    # 4. Плотность при больших масштабах (выборочно)
    print("\n--- 4. Плотность при больших масштабах ---")
    import random
    random.seed(42)

    for magnitude in [1000, 5000, 10000, 50000]:
        sample_size = 200
        sample = random.sample(range(1, magnitude + 1), min(sample_size, magnitude))
        conv = sum(1 for s in sample if classify(s, a, b)[0] == 'cycle')
        print(f"  N ≤ {magnitude:6d}: ~{conv/len(sample):.1%} "
              f"({conv}/{len(sample)} в выборке)")

    # 5. Heuristic: средний рост за шаг
    print("\n--- 5. Эвристический анализ среднего роста ---")
    # Для нечётного n: шаг = 5n+1 (нечётный шаг), затем делим на 2 k раз
    # Средний рост = (5n+1) * (1/2)^k, где k — среднее число делений
    # Для случайного числа, P(делится на 2^k) = 1/2^k
    # Среднее число делений до нечётного: сумма k * 1/2^k = 2
    # Значит средний рост за "цикл" ≈ 5/4 = 1.25 (больше 1 → расходимость!)
    # Для a=3: 3/4 = 0.75 (меньше 1 → сходимость)

    print("  Эвристика: для f(n) = an+b if odd, n/2 if even:")
    print("  Среднее число делений на 2 до нечётного = 2")
    print("  Средний рост за 'один нечётный шаг + деления' ≈ a/4")
    print()
    for a_test in [1, 3, 5, 7, 9, 11]:
        ratio = a_test / 4
        prediction = "сходится" if ratio < 1 else "расходится"
        print(f"  a={a_test:2d}: a/4 = {ratio:.2f} → ожидаем {prediction}")

    print()
    print("  Критический порог: a = 4 (a/4 = 1)")
    print("  Но a должно быть нечётным → переход между a=3 (0.75) и a=5 (1.25)")
    print("  Это объясняет фазовый переход!")

    # 6. Точное вычисление: доля нечётных шагов
    print("\n--- 6. Доля нечётных шагов для сходящихся траекторий ---")
    for test_start in [1, 7, 13, 17, 27]:
        n = test_start
        odd_steps = 0
        even_steps = 0
        seen = set()
        while n not in seen and abs(n) < 10**15:
            seen.add(n)
            if n % 2 == 0:
                even_steps += 1
            else:
                odd_steps += 1
            n = collatz_step(n, a, b)

        if n in seen:
            total = odd_steps + even_steps
            odd_frac = odd_steps / total if total > 0 else 0
            # Для сходимости нужно: a^(odd_frac) * (1/2)^(even_frac) < 1
            # log(a) * odd_frac - log(2) * even_frac < 0
            log_ratio = math.log(a) * odd_steps - math.log(2) * even_steps
            print(f"  start={test_start:4d}: odd={odd_steps}, even={even_steps}, "
                  f"odd_frac={odd_frac:.3f}, "
                  f"ln(5)·odd - ln(2)·even = {log_ratio:.2f} "
                  f"({'<0 shrinks' if log_ratio < 0 else '>0 grows'})")

    # 7. Самое интересное: a=5, b=-1 (все сходятся к одному циклу?)
    print("\n\n--- 7. Сравнение: a=5, b=-1 vs b=1 ---")
    for b_test in [-1, 1]:
        cycles_found = set()
        conv = 0
        for s in range(1, 1001):
            result = classify(s, 5, b_test)
            if result[0] == 'cycle':
                conv += 1
                cycles_found.add(result[1])
        print(f"  a=5, b={b_test:+d}: {conv}/1000 converge, "
              f"{len(cycles_found)} distinct cycles")
        for c in sorted(cycles_found, key=len):
            if len(c) <= 10:
                print(f"    len={len(c)}: {list(c)}")

    print("\n\n" + "=" * 60)
    print("ИТОГО: ФАЛЬСИФИЦИРУЕМЫЕ УТВЕРЖДЕНИЯ")
    print("=" * 60)

    claims = [
        ("Фазовый переход между a=3 и a=5 объясняется эвристикой a/4",
         "a/4 < 1 → сходимость, a/4 > 1 → расходимость. "
         "a=3: 3/4=0.75 (сходится). a=5: 5/4=1.25 (расходится в среднем). "
         "Критический a=4, но нечётные a → переход между 3 и 5."),

        ("Плотность сходящихся при a=5 b=1 убывает с масштабом",
         "Если a/4 > 1, большие числа имеют больше шансов уйти в бесконечность. "
         "Предсказание: плотность → 0 при N → ∞."),

        ("Чётные a всегда расходятся (для положительных начальных)",
         "Для чётного a: a*n+b с нечётным n даёт чётное число. "
         "Оно делится на 2 ровно один раз (a*n+b = even, (a*n+b)/2 ≥ n для a≥2). "
         "Средний рост > 1."),

        ("Модулярная структура определяет сходимость при a=5",
         "Числа с определёнными остатками mod 8/16/32 имеют значимо разную "
         "вероятность сходимости. Это не случайно."),
    ]

    for i, (claim, evidence) in enumerate(claims, 1):
        print(f"\n{i}. {claim}")
        print(f"   Основание: {evidence}")


if __name__ == '__main__':
    main()
