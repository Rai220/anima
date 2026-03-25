"""
Цепные дроби для log₂(3/2) и log₂(5/4).
Проверка: две цепочки оптимальных делений — это знаменатели подходящих дробей.
"""
import math

def continued_fraction(x, n_terms=15):
    """Вычислить цепную дробь для x."""
    terms = []
    for _ in range(n_terms):
        a = int(x)
        terms.append(a)
        frac = x - a
        if abs(frac) < 1e-12:
            break
        x = 1 / frac
    return terms

def convergents(cf_terms):
    """Вычислить подходящие дроби из цепной дроби."""
    h_prev, h_curr = 0, 1
    k_prev, k_curr = 1, 0
    results = []
    for a in cf_terms:
        h_prev, h_curr = h_curr, a * h_curr + h_prev
        k_prev, k_curr = k_curr, a * k_curr + k_prev
        results.append((h_curr, k_curr))
    return results

# Квинта: log₂(3/2)
x_fifth = math.log2(3/2)
cf_fifth = continued_fraction(x_fifth)
conv_fifth = convergents(cf_fifth)

print("=" * 70)
print(f"ЦЕПНАЯ ДРОБЬ ДЛЯ log₂(3/2) = {x_fifth:.10f}")
print(f"CF = {cf_fifth}")
print("=" * 70)
print()
print(f"{'p/q':>10} {'q (делений)':>12} {'Ошибка квинты (¢)':>20}")
print("-" * 45)

fifth_denominators = []
for p, q in conv_fifth:
    if q > 200:
        break
    approx = p / q
    error_cents = abs(1200 * (approx - x_fifth))
    print(f"{p}/{q:>4} {q:>12} {error_cents:>20.3f}")
    fifth_denominators.append(q)

print()

# Терция: log₂(5/4)
x_third = math.log2(5/4)
cf_third = continued_fraction(x_third)
conv_third = convergents(cf_third)

print("=" * 70)
print(f"ЦЕПНАЯ ДРОБЬ ДЛЯ log₂(5/4) = {x_third:.10f}")
print(f"CF = {cf_third}")
print("=" * 70)
print()
print(f"{'p/q':>10} {'q (делений)':>12} {'Ошибка терции (¢)':>20}")
print("-" * 45)

third_denominators = []
for p, q in conv_third:
    if q > 200:
        break
    approx = p / q
    error_cents = abs(1200 * (approx - x_third))
    print(f"{p}/{q:>4} {q:>12} {error_cents:>20.3f}")
    third_denominators.append(q)

print()

# Сравнение двух цепочек
print("=" * 70)
print("СРАВНЕНИЕ ЦЕПОЧЕК")
print("=" * 70)
print()
print(f"Квинтовые знаменатели (≤200): {fifth_denominators}")
print(f"Терцевые знаменатели  (≤200): {third_denominators}")
print()

common = set(fifth_denominators) & set(third_denominators)
print(f"Общие: {sorted(common) if common else 'НЕТ'}")
print()

# Расширенная проверка: семиконвергенты (промежуточные дроби)
# тоже дают хорошие приближения
print("=" * 70)
print("СЕМИКОНВЕРГЕНТЫ (промежуточные приближения)")
print("=" * 70)
print()

def semiconvergents(cf_terms, max_q=100):
    """Вычислить все семиконвергенты (включая подходящие дроби)."""
    h = [0, 1]
    k = [1, 0]
    results = []
    for i, a in enumerate(cf_terms):
        # Все промежуточные: от 1 до a (для i>0: от ceil(a/2) до a)
        start = 1 if i == 0 else 1
        for j in range(start, a + 1):
            p = j * h[-1] + h[-2]
            q = j * k[-1] + k[-2]
            if q > max_q:
                break
            results.append((p, q, j == a))  # True = convergent
        h.append(a * h[-1] + h[-2])
        k.append(a * k[-1] + k[-2])
        if k[-1] > max_q:
            break
    return results

semi_fifth = semiconvergents(cf_fifth, 100)
semi_third = semiconvergents(cf_third, 100)

print("Квинта — лучшие приближения (q ≤ 100):")
for p, q, is_conv in semi_fifth:
    approx = p / q
    err = abs(1200 * (approx - x_fifth))
    marker = " ← подходящая" if is_conv else ""
    print(f"  {p}/{q}: ошибка {err:.2f}¢{marker}")

print()
print("Терция — лучшие приближения (q ≤ 100):")
for p, q, is_conv in semi_third:
    approx = p / q
    err = abs(1200 * (approx - x_third))
    marker = " ← подходящая" if is_conv else ""
    print(f"  {p}/{q}: ошибка {err:.2f}¢{marker}")

# Парето-фронт: n, где ОБЕ ошибки ≤ предыдущего лучшего
print()
print("=" * 70)
print("ДВУМЕРНЫЙ PARETO-ФРОНТ (квинта И терция одновременно)")
print("=" * 70)
print()

best_max = float('inf')
for n in range(2, 101):
    step = 1200.0 / n
    fifth_err = abs(round(x_fifth * n) / n - x_fifth) * 1200
    third_err = abs(round(x_third * n) / n - x_third) * 1200
    max_err = max(fifth_err, third_err)
    if max_err < best_max:
        best_max = max_err
        in_fifth = n in fifth_denominators
        in_third = n in third_denominators
        chain = ""
        if in_fifth and in_third:
            chain = " [ОБЕ ЦЕПОЧКИ]"
        elif in_fifth:
            chain = " [квинтовая]"
        elif in_third:
            chain = " [терцевая]"
        print(f"  n={n:>3}: квинта {fifth_err:>6.1f}¢, терция {third_err:>6.1f}¢, max {max_err:>6.1f}¢{chain}")
