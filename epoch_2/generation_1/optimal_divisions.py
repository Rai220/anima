"""
Оптимально ли деление октавы на 12 равных частей?

Вопрос: для каких n деление октавы на n равных частей лучше всего
приближает чистые интервалы (3/2, 5/4, 6/5, 4/3)?

Предсказание: 12 — локально оптимально, но не глобально.
Должны быть n > 12, которые приближают лучше.
Конкретное предсказание: 19, 31, 53 — известные кандидаты.

Метрика: для каждого n, вычислить наилучшее приближение каждого
чистого интервала среди n-TET, и взять максимальное отклонение (minimax).
"""

import math
import json

# Чистые интервалы, которые мы хотим приближать
pure_intervals = {
    'fifth':       3/2,     # квинта
    'major_third': 5/4,     # большая терция
    'minor_third': 6/5,     # малая терция
    'fourth':      4/3,     # кварта
    'major_sixth': 5/3,     # большая секста
    'minor_seventh': 9/5,   # малая септима
}

def cents(ratio):
    return 1200 * math.log2(ratio)

pure_cents = {name: cents(r) for name, r in pure_intervals.items()}

def evaluate_n_tet(n):
    """Для n-TET, вычислить отклонение от каждого чистого интервала."""
    step = 1200 / n  # центов на шаг

    deviations = {}
    for name, target_cents in pure_cents.items():
        # Ближайший шаг
        k = round(target_cents / step)
        approx_cents = k * step
        dev = abs(approx_cents - target_cents)
        deviations[name] = round(dev, 3)

    max_dev = max(deviations.values())
    mean_dev = sum(deviations.values()) / len(deviations)

    return {
        'n': n,
        'deviations': deviations,
        'max_deviation': round(max_dev, 3),
        'mean_deviation': round(mean_dev, 3),
    }

# Проверяем все n от 5 до 100
results = []
for n in range(5, 101):
    r = evaluate_n_tet(n)
    results.append(r)

# Сортируем по максимальному отклонению
results_sorted = sorted(results, key=lambda x: x['max_deviation'])

print("=" * 80)
print("ОПТИМАЛЬНОСТЬ ДЕЛЕНИЯ ОКТАВЫ")
print("Метрика: минимальное максимальное отклонение от чистых интервалов (minimax)")
print("=" * 80)
print()

print("Топ-20 делений по качеству приближения:")
print(f"{'n':>4} {'Max dev (¢)':>12} {'Mean dev (¢)':>12} {'Квинта':>8} {'Б.терция':>8} {'М.терция':>8} {'Кварта':>8}")
print("-" * 72)

for r in results_sorted[:20]:
    d = r['deviations']
    print(f"{r['n']:>4} {r['max_deviation']:>12.1f} {r['mean_deviation']:>12.1f} "
          f"{d['fifth']:>8.1f} {d['major_third']:>8.1f} {d['minor_third']:>8.1f} {d['fourth']:>8.1f}")

print()
print("Для сравнения, 12-TET:")
r12 = next(r for r in results if r['n'] == 12)
print(f"  Max deviation: {r12['max_deviation']:.1f} ¢")
print(f"  Mean deviation: {r12['mean_deviation']:.1f} ¢")
print(f"  Rank by max dev: {results_sorted.index(r12) + 1} из {len(results)}")
print()

# Где 12 среди всех?
rank12 = results_sorted.index(r12) + 1

# Лучшие до 24 нот (практические инструменты)
practical = [r for r in results_sorted if r['n'] <= 24]
print("Лучшие практические деления (n ≤ 24):")
for r in practical[:10]:
    d = r['deviations']
    print(f"  n={r['n']:>2}: max={r['max_deviation']:.1f}¢, mean={r['mean_deviation']:.1f}¢")

print()
print("=" * 80)
print("АНАЛИЗ")
print("=" * 80)
print()

# Специальные кандидаты
for n in [12, 19, 22, 24, 31, 34, 41, 53, 72]:
    if n <= 100:
        r = next(x for x in results if x['n'] == n)
        rank = results_sorted.index(r) + 1
        print(f"n={n:>2}: max={r['max_deviation']:>6.1f}¢, rank={rank:>2}/96, "
              f"квинта={r['deviations']['fifth']:.1f}¢, б.терция={r['deviations']['major_third']:.1f}¢")

print()

# Pareto frontier: деления, где нет другого n' < n с лучшим max_dev
print("=" * 80)
print("PARETO-ФРОНТ (лучшее качество для данного числа нот)")
print("=" * 80)
print()

best_so_far = float('inf')
pareto = []
for n in range(5, 101):
    r = next(x for x in results if x['n'] == n)
    if r['max_deviation'] < best_so_far:
        best_so_far = r['max_deviation']
        pareto.append(r)
        print(f"n={n:>2}: max={r['max_deviation']:>6.1f}¢ (новый рекорд)")

print()
print(f"12-TET {'входит' if 12 in [p['n'] for p in pareto] else 'НЕ входит'} в Pareto-фронт")

# Проверка: есть ли n < 12, который лучше?
better_than_12 = [r for r in results if r['n'] < 12 and r['max_deviation'] < r12['max_deviation']]
if better_than_12:
    print(f"\nДеления меньше 12 с лучшим качеством:")
    for r in better_than_12:
        print(f"  n={r['n']}: max={r['max_deviation']:.1f}¢")
else:
    print(f"\nСреди n < 12 нет деления с меньшим max dev чем 12-TET ({r12['max_deviation']:.1f}¢)")

# Сохранение
with open('optimal_divisions_results.json', 'w') as f:
    json.dump({
        'all_results': results,
        'pareto_front': [p['n'] for p in pareto],
        'rank_of_12': rank12,
    }, f, indent=2)
