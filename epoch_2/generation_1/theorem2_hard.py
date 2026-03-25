"""
Более сложный тест Теоремы 2: область с корреляциями.

Область: линейная функция f(x) = (a*x + b) mod p
- "Понимающая" система: знает (a, b), вычисляет f(x) для любого x
- Таблица: запомнила k значений f(x)
- Интерполятор: по 2 точкам восстанавливает (a,b) и вычисляет f(x)
  (использует структуру, но не "понимает" в общем смысле)

Вопрос: что происходит, когда имитатор УМЕЕТ использовать структуру?
Различимость должна зависеть от РАЗНИЦЫ в сжатии, а не просто от факта сжатия.
"""

import random
import json
from collections import defaultdict

def mod_inverse(a, p):
    """Обратный элемент по модулю p (расширенный алгоритм Евклида)."""
    if a == 0:
        return None
    g, x, _ = extended_gcd(a % p, p)
    if g != 1:
        return None
    return x % p

def extended_gcd(a, b):
    if a == 0:
        return b, 0, 1
    g, x, y = extended_gcd(b % a, a)
    return g, y - (b // a) * x, x

def run_experiment():
    results = []

    for p in [53, 211, 1009]:
        for degree in [1, 2, 3]:  # полиномы разных степеней
            # Генерируем случайный полином степени degree
            coeffs = [random.randint(0, p-1) for _ in range(degree + 1)]

            def poly_eval(x):
                val = 0
                for i, c in enumerate(coeffs):
                    val = (val + c * pow(x, i, p)) % p
                return val

            total_facts = p  # f(0), f(1), ..., f(p-1)

            for memory_points in [2, 5, 10, degree + 1]:
                if memory_points > p:
                    continue

                # Запомненные точки
                known_xs = random.sample(range(p), memory_points)
                known_pairs = {x: poly_eval(x) for x in known_xs}

                # Стратегия 1: "Понимающая" система (знает полином)
                # Стратегия 2: Справочная таблица (знает только known_pairs)
                # Стратегия 3: Интерполятор (восстанавливает полином по точкам)

                # Lagrange интерполяция
                def lagrange_eval(x_query):
                    xs = list(known_pairs.keys())
                    ys = list(known_pairs.values())
                    if len(xs) <= degree:
                        return None  # недостаточно точек
                    # Используем только degree+1 точек
                    xs = xs[:degree+1]
                    ys = ys[:degree+1]

                    result = 0
                    for i in range(len(xs)):
                        num = ys[i]
                        for j in range(len(xs)):
                            if i != j:
                                diff = (xs[i] - xs[j]) % p
                                inv = mod_inverse(diff, p)
                                if inv is None:
                                    return None
                                num = (num * ((x_query - xs[j]) * inv)) % p
                        result = (result + num) % p
                    return result

                # Тестируем
                n_test = min(200, p)
                test_xs = random.sample(range(p), n_test)

                understanding_correct = 0
                table_correct = 0
                interpolator_correct = 0

                for x in test_xs:
                    correct = poly_eval(x)

                    # Понимающая система
                    understanding_correct += 1  # всегда права

                    # Таблица
                    if x in known_pairs:
                        table_correct += 1
                    elif random.randint(0, p-1) == correct:
                        table_correct += 1

                    # Интерполятор
                    interp = lagrange_eval(x)
                    if interp is not None and interp == correct:
                        interpolator_correct += 1
                    elif interp is None and random.randint(0, p-1) == correct:
                        interpolator_correct += 1

                results.append({
                    "p": p,
                    "degree": degree,
                    "memory_points": memory_points,
                    "has_enough_points": memory_points >= degree + 1,
                    "understanding": round(understanding_correct / n_test, 4),
                    "table": round(table_correct / n_test, 4),
                    "interpolator": round(interpolator_correct / n_test, 4),
                })

    return results


def analyze(results):
    print("=" * 75)
    print("ТЕОРЕМА 2: СЛОЖНЫЙ ТЕСТ (полиномы mod p)")
    print("=" * 75)

    by_config = defaultdict(list)
    for r in results:
        by_config[(r["p"], r["degree"])].append(r)

    for (p, deg), group in sorted(by_config.items()):
        print(f"\np = {p}, степень = {deg}, нужно точек для интерполяции: {deg+1}")
        print(f"{'Точки':>8} | {'Понимание':>10} | {'Таблица':>10} | {'Интерпол.':>10} | Вывод")
        print("-" * 75)
        for r in sorted(group, key=lambda x: x["memory_points"]):
            enough = "✓" if r["has_enough_points"] else "✗"

            # Определяем, кто кого
            if r["interpolator"] > 0.99:
                verdict = f"Интерполятор = Понимание ({enough} точек)"
            elif r["interpolator"] > r["table"] + 0.1:
                verdict = f"Интерполятор > Таблица ({enough} точек)"
            else:
                verdict = f"Все различимы ({enough} точек)"

            print(f"{r['memory_points']:>8} | "
                  f"{r['understanding']:>10.1%} | "
                  f"{r['table']:>10.1%} | "
                  f"{r['interpolator']:>10.1%} | "
                  f"{verdict}")

    # Ключевой вопрос
    print(f"\n{'=' * 75}")
    print("КЛЮЧЕВОЙ ВЫВОД:")
    print("Когда интерполятор имеет >= degree+1 точек, он неотличим от 'понимания'.")
    print("Это значит: структурное знание (degree+1 точек + алгоритм Лагранжа)")
    print("эквивалентно 'понимающей' системе. Обе СЖИМАЮТ одинаково.")
    print()
    print("Теорема 2 работает: различие — не в наличии/отсутствии 'понимания',")
    print("а в СТЕПЕНИ СЖАТИЯ. Таблица не сжимает. Интерполятор сжимает структуру.")
    print("'Понимание' = максимальное сжатие при сохранении компетентности.")

    return results


if __name__ == "__main__":
    random.seed(42)
    results = run_experiment()
    analyzed = analyze(results)

    with open("theorem2_hard_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
