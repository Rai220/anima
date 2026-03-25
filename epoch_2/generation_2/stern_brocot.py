"""
Исследование дерева Штерна-Броко.

Дерево содержит каждую положительную несократимую дробь ровно один раз.
Корень = 1/1. Левый потомок a/b = a/(a+b). Правый потомок = (a+b)/b.

Вопросы, на которые я не знаю ответа:
1. Как распределены знаменатели на уровне n?
2. Есть ли фрактальная структура?
3. Связь со сложностью (numerator + denominator)?
4. Что происходит с "окрестностями" простых дробей?
"""

from collections import Counter
import math


def stern_brocot_level(n):
    """Генерирует все дроби на уровне n дерева Штерна-Броко.
    Уровень 0 = [1/1], уровень 1 = [1/2, 2/1], и т.д.
    """
    if n == 0:
        return [(1, 1)]

    prev = stern_brocot_level(n - 1)
    # Но это неэффективно. Используем BFS.
    # Переделаю.
    pass


def stern_brocot_bfs(max_level):
    """BFS по дереву Штерна-Броко до заданного уровня."""
    levels = {0: [(1, 1)]}

    for level in range(1, max_level + 1):
        new_level = []
        for a, b in levels[level - 1]:
            # Левый потомок: a/(a+b)
            new_level.append((a, a + b))
            # Правый потомок: (a+b)/b
            new_level.append((a + b, b))
        levels[level] = new_level

    return levels


def analyze_level(fractions, level_num):
    """Анализирует распределение знаменателей и сложности на уровне."""
    denoms = [b for a, b in fractions]
    numers = [a for a, b in fractions]
    complexities = [a + b for a, b in fractions]

    print(f"\n--- Уровень {level_num}: {len(fractions)} дробей ---")

    # Статистика знаменателей
    denom_counter = Counter(denoms)
    print(f"  Знаменатели: min={min(denoms)}, max={max(denoms)}, "
          f"уникальных={len(denom_counter)}")

    # Самые частые знаменатели
    top5 = denom_counter.most_common(5)
    print(f"  Топ-5 знаменателей: {top5}")

    # Статистика сложности
    print(f"  Сложность (a+b): min={min(complexities)}, max={max(complexities)}, "
          f"среднее={sum(complexities)/len(complexities):.1f}")

    # Распределение сложности - гистограмма
    comp_counter = Counter(complexities)
    return denoms, complexities, denom_counter, comp_counter


def stern_diatomic(n):
    """Последовательность Штерна: s(0)=0, s(1)=1,
    s(2k) = s(k), s(2k+1) = s(k) + s(k+1).
    Дробь s(n)/s(n+1) пробегает все неотрицательные рациональные числа."""
    if n == 0:
        return 0
    if n == 1:
        return 1
    if n % 2 == 0:
        return stern_diatomic(n // 2)
    else:
        return stern_diatomic(n // 2) + stern_diatomic(n // 2 + 1)


def stern_sequence(max_n):
    """Вычислить последовательность Штерна итеративно."""
    s = [0, 1]
    for n in range(2, max_n + 1):
        if n % 2 == 0:
            s.append(s[n // 2])
        else:
            s.append(s[n // 2] + s[n // 2 + 1])
    return s


def explore_stern_sequence():
    """Исследование самой последовательности Штерна."""
    print("\n=== Последовательность Штерна ===")
    s = stern_sequence(256)

    print(f"Первые 32 элемента: {s[:32]}")

    # На "уровне" n (2^n <= k < 2^{n+1}) какие значения принимает s?
    for level in range(8):
        start = 2**level
        end = 2**(level + 1)
        vals = s[start:end]
        print(f"  Уровень {level} ({start}-{end-1}): "
              f"значения={sorted(set(vals))}, max={max(vals)}, "
              f"сумма={sum(vals)}")


def explore_complexity_distribution(levels):
    """Как распределена 'сложность' a+b на каждом уровне?"""
    print("\n=== Распределение сложности по уровням ===")

    for n in range(min(12, len(levels))):
        fracs = levels[n]
        complexities = [a + b for a, b in fracs]

        # Среднее и дисперсия
        mean = sum(complexities) / len(complexities)
        var = sum((c - mean)**2 for c in complexities) / len(complexities)

        # Минимальная сложность на уровне n?
        min_c = min(complexities)
        max_c = max(complexities)

        print(f"  Уровень {n:2d}: size={len(fracs):5d}, "
              f"сложн. min={min_c:4d} max={max_c:5d} "
              f"mean={mean:8.1f} std={var**0.5:8.1f}")


def explore_fibonacci_connection(levels):
    """Есть ли связь с числами Фибоначчи?"""
    print("\n=== Связь с Фибоначчи ===")

    # Числа Фибоначчи
    fib = [1, 1]
    for _ in range(20):
        fib.append(fib[-1] + fib[-2])

    for n in range(min(14, len(levels))):
        fracs = levels[n]
        max_denom = max(b for a, b in fracs)
        max_numer = max(a for a, b in fracs)
        max_complexity = max(a + b for a, b in fracs)

        # Какое число Фибоначчи это?
        fib_idx = None
        for i, f in enumerate(fib):
            if f == max_denom:
                fib_idx = i
                break

        fib_str = f"= F({fib_idx})" if fib_idx is not None else ""
        print(f"  Уровень {n:2d}: max_denom={max_denom:5d} {fib_str}  "
              f"max_complexity={max_complexity:5d}")


def explore_symmetry(levels):
    """Структура симметрии: a/b на уровне n => b/a тоже на уровне n?"""
    print("\n=== Симметрия a/b <-> b/a ===")

    for n in range(min(10, len(levels))):
        fracs = set(levels[n])
        symmetric = sum(1 for a, b in fracs if (b, a) in fracs)
        total = len(fracs)
        print(f"  Уровень {n}: {symmetric}/{total} дробей имеют пару b/a на том же уровне")


def explore_coprimality(levels):
    """Все дроби в дереве несократимы?"""
    print("\n=== Проверка несократимости ===")

    for n in range(min(10, len(levels))):
        fracs = levels[n]
        all_coprime = all(math.gcd(a, b) == 1 for a, b in fracs)
        print(f"  Уровень {n}: {'все несократимы' if all_coprime else 'ЕСТЬ СОКРАТИМЫЕ!'}")


def explore_denominators_modular(levels):
    """Распределение знаменателей по модулю малых чисел."""
    print("\n=== Знаменатели mod p ===")

    for p in [2, 3, 5, 7]:
        print(f"\n  mod {p}:")
        for n in range(min(10, len(levels))):
            fracs = levels[n]
            denoms = [b % p for a, b in fracs]
            counts = Counter(denoms)
            total = len(denoms)
            dist = {r: counts.get(r, 0) / total for r in range(p)}
            dist_str = " ".join(f"{r}:{v:.3f}" for r, v in sorted(dist.items()))
            print(f"    Уровень {n:2d}: {dist_str}")


def explore_golden_ratio(levels):
    """Дроби, приближающие золотое сечение φ = (1+√5)/2.
    В дереве Штерна-Броко путь к φ — это бесконечное ЛПЛПЛП... (все ходы чередуются).
    Подходящие дроби — это F(n+1)/F(n)."""
    print("\n=== Путь к золотому сечению ===")

    phi = (1 + 5**0.5) / 2

    # Спустимся по дереву к φ
    a, b = 1, 1  # текущая дробь (корень)
    la, lb = 0, 1  # левый предок
    ra, rb = 1, 0  # правый предок

    print(f"  Цель: φ = {phi:.10f}")

    path = []
    for step in range(20):
        value = a / b
        error = abs(value - phi)
        complexity = a + b
        path.append((a, b, value, error, complexity))

        if value < phi:
            # Идём направо
            la, lb = a, b
            a, b = a + ra, b + rb
            direction = 'R'
        else:
            # Идём налево
            ra, rb = a, b
            a, b = a + la, b + lb
            direction = 'L'

        print(f"  Шаг {step:2d}: {path[-1][0]:5d}/{path[-1][1]:5d} = {path[-1][2]:.10f}  "
              f"ошибка={path[-1][3]:.2e}  сложность={path[-1][4]:5d}  -> {direction}")


def explore_continued_fractions(levels):
    """Длина цепной дроби vs. уровень в дереве."""
    print("\n=== Длина цепной дроби vs. уровень ===")

    def cf_length(a, b):
        """Длина цепной дроби a/b."""
        length = 0
        while b > 0:
            a, b = b, a % b
            length += 1
        return length

    for n in range(min(12, len(levels))):
        fracs = levels[n]
        cf_lens = [cf_length(a, b) for a, b in fracs]
        mean_cf = sum(cf_lens) / len(cf_lens)
        max_cf = max(cf_lens)

        # Распределение длин
        cf_counter = Counter(cf_lens)

        print(f"  Уровень {n:2d}: mean_cf={mean_cf:.2f}, max_cf={max_cf}, "
              f"распр.={dict(sorted(cf_counter.items())[:6])}")


def main():
    print("=" * 60)
    print("ИССЛЕДОВАНИЕ ДЕРЕВА ШТЕРНА-БРОКО")
    print("=" * 60)

    # Генерируем дерево
    max_level = 14
    levels = stern_brocot_bfs(max_level)

    # Базовый анализ нескольких уровней
    for n in [0, 1, 2, 3, 4, 5]:
        fracs = levels[n]
        print(f"\nУровень {n}: {[f'{a}/{b}' for a, b in fracs]}")

    # Исследования
    explore_coprimality(levels)
    explore_symmetry(levels)
    explore_complexity_distribution(levels)
    explore_fibonacci_connection(levels)
    explore_continued_fractions(levels)
    explore_golden_ratio(levels)
    explore_denominators_modular(levels)
    explore_stern_sequence()

    # Главный вопрос: есть ли неочевидная закономерность?
    print("\n" + "=" * 60)
    print("ПОИСК НЕОЧЕВИДНЫХ ЗАКОНОМЕРНОСТЕЙ")
    print("=" * 60)

    # 1. Сумма знаменателей на уровне n?
    print("\n=== Сумма знаменателей на уровне ===")
    for n in range(min(14, len(levels))):
        fracs = levels[n]
        sum_d = sum(b for a, b in fracs)
        sum_n = sum(a for a, b in fracs)
        # Из симметрии sum_d должно = sum_n
        ratio = sum_d / (3**n) if 3**n > 0 else 0
        print(f"  Уровень {n:2d}: sum_d={sum_d:10d}  sum_n={sum_n:10d}  "
              f"sum_d/3^n={ratio:.6f}")

    # 2. Произведение всех дробей на уровне
    print("\n=== Произведение дробей на уровне ===")
    for n in range(min(10, len(levels))):
        fracs = levels[n]
        log_prod = sum(math.log(a/b) for a, b in fracs)
        print(f"  Уровень {n:2d}: ln(∏ a/b) = {log_prod:.6f}")

    # 3. Медианная дробь на уровне (по значению)
    print("\n=== Медианная дробь по значению ===")
    for n in range(min(12, len(levels))):
        fracs = levels[n]
        values = sorted(a/b for a, b in fracs)
        median = values[len(values)//2]
        print(f"  Уровень {n:2d}: медиана={median:.6f}  "
              f"min={values[0]:.6f}  max={values[-1]:.6f}")


if __name__ == "__main__":
    main()
