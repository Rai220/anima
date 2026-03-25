"""
Верификация: итерированная диагонализация.
Проверяет квазипериодическую структуру последовательности xₙ.
"""

from decimal import Decimal, getcontext

# Высокая точность для работы с цифрами
getcontext().prec = 100

def get_digit(number_digits, position):
    """Получить цифру на позиции position (0-indexed) из списка цифр."""
    if position < len(number_digits):
        return number_digits[position]
    return 0

def diagonalize(listing, f, num_digits=50):
    """
    Построить диагональное число из списка.
    listing: список списков цифр (каждый элемент — десятичные цифры числа из [0,1])
    f: функция замены d -> f(d), f(d) != d
    num_digits: сколько цифр вычислить
    """
    result = []
    for j in range(num_digits):
        if j < len(listing):
            d = get_digit(listing[j], j)
        else:
            d = 0
        result.append(f(d))
    return result

def f_plus1(d):
    """Правило замены: d -> d+1 mod 10."""
    return (d + 1) % 10

def make_initial_list(size=30, num_digits=50):
    """Создать начальный список 'случайных' чисел (детерминированно)."""
    listing = []
    for i in range(size):
        digits = []
        for j in range(num_digits):
            # Простая детерминированная формула для генерации цифр
            digits.append((i * 7 + j * 3 + i * j) % 10)
        listing.append(digits)
    return listing

def iterate_diagonalization(L0, f, steps=30, num_digits=50):
    """
    Итерированная диагонализация.
    Возвращает список построенных чисел x₁, x₂, ..., x_steps.
    """
    current_list = [row[:] for row in L0]
    xs = []

    for step in range(steps):
        x = diagonalize(current_list, f, num_digits)
        xs.append(x)
        # Вставляем x в начало списка
        current_list = [x] + current_list

    return xs

def verify_not_in_list(xs, L0):
    """Проверить, что каждый xₙ действительно отсутствует в списке на момент построения."""
    current_list = [row[:] for row in L0]
    for n, x in enumerate(xs):
        # Проверяем: x отличается от каждого элемента current_list хотя бы в одной цифре
        for i, elem in enumerate(current_list):
            if i < len(x) and x == elem:
                print(f"ОШИБКА: x_{n+1} совпадает с элементом {i} списка!")
                return False
            # Более точно: x должно отличаться от i-го элемента в i-й позиции
            if i < len(x):
                if x[i] == get_digit(elem, i):
                    print(f"ОШИБКА: x_{n+1} совпадает с элементом {i} в позиции {i}!")
                    return False
        current_list = [x] + current_list
    print("Все числа корректно отсутствуют в соответствующих списках.")
    return True

def check_periodicity(xs, position, cycle_length=10):
    """
    Проверить квазипериодичность: для заданной позиции j,
    цифры x_{n}[j] при n >= j+1 должны иметь цикл длины j * cycle_length.
    """
    j = position
    digits = [x[j] for x in xs]

    print(f"\nПозиция {j}, цифры: {digits}")

    # Проверяем предсказанный период
    predicted_period = (j + 1) * cycle_length  # period для позиции j (0-indexed, значит j+1)

    # Для позиции 0 (первая цифра): период = 1 * 10 = 10
    # Проверяем: digits[n] = digits[n + predicted_period] для n >= j+1?

    # Но сначала — проверим простой случай: позиция 0
    if j == 0:
        # Предсказание: первая цифра xₙ = d₁₁ + n mod 10
        print(f"  Предсказание: первая цифра x_n циклична с периодом 10")
        diffs = []
        for i in range(1, len(digits)):
            diff = (digits[i] - digits[i-1]) % 10
            diffs.append(diff)
        print(f"  Разности (mod 10): {diffs[:20]}")
        if all(d == diffs[0] for d in diffs[:20]):
            print(f"  ✓ Постоянная разность = {diffs[0]}, цикл = {10 // diffs[0] if diffs[0] > 0 else '∞'}")
        else:
            print(f"  ✗ Разности не постоянны")

def check_first_digit_prediction(xs, L0):
    """
    Проверить конкретное предсказание: первая цифра x_n = d_{1,1} + n mod 10,
    где d_{1,1} — первая цифра первого числа в L0.
    """
    d11 = L0[0][0]
    print(f"\nd₁₁ = {d11}")
    print(f"Предсказание: первая цифра x_n = ({d11} + n) mod 10")
    print()

    for n, x in enumerate(xs[:15], 1):
        predicted = (d11 + n) % 10
        actual = x[0]
        match = "✓" if predicted == actual else "✗"
        print(f"  x_{n}: предсказано {predicted}, фактически {actual} {match}")

def main():
    print("=" * 60)
    print("Итерированная диагонализация: верификация")
    print("=" * 60)

    NUM_DIGITS = 50
    STEPS = 25

    L0 = make_initial_list(size=30, num_digits=NUM_DIGITS)

    print(f"\nИсходный список: {len(L0)} чисел, {NUM_DIGITS} цифр каждое")
    print(f"Шагов диагонализации: {STEPS}")
    print(f"Правило замены: d → d+1 mod 10")

    xs = iterate_diagonalization(L0, f_plus1, steps=STEPS, num_digits=NUM_DIGITS)

    # 1. Проверка корректности
    print("\n--- Проверка корректности ---")
    verify_not_in_list(xs, L0)

    # 2. Проверка предсказания для первой цифры
    print("\n--- Проверка предсказания (первая цифра) ---")
    check_first_digit_prediction(xs, L0)

    # 3. Проверка периодичности для разных позиций
    print("\n--- Проверка периодичности ---")
    for pos in [0, 1, 2, 3]:
        check_periodicity(xs, pos)

    # 4. Общая структура: показать первые 5 цифр каждого xₙ
    print("\n--- Первые 10 цифр построенных чисел ---")
    for n, x in enumerate(xs[:20], 1):
        digits_str = ''.join(str(d) for d in x[:10])
        print(f"  x_{n:2d} = 0.{digits_str}...")

    # 5. Рекуррентное соотношение
    print("\n--- Проверка рекуррентного соотношения ---")
    print("Для позиции j, при n > j: цифра x_{n+1}[j] = f(цифра x_{n+1-j-1}[j])")
    print("(т.е. j-я цифра определяется j-й цифрой числа, стоящего на j+1 позиций раньше)")

    for j in range(4):
        print(f"\n  Позиция {j}:")
        for n in range(j + 1, min(len(xs), 20)):
            actual = xs[n][j]
            # n+1-й построенный число = x_{n+1} (1-indexed),
            # j-й элемент списка L_n = x_{n-j} (при j <= n)
            # значит x_{n+1}[j] = f(x_{n-j}[j]) = f(x_{n-j}[j])
            # В 0-indexed: xs[n][j] = f(xs[n-j-1][j])
            if n - j - 1 >= 0:
                source = xs[n - j - 1][j]
                predicted = f_plus1(source)
                match = "✓" if predicted == actual else "✗"
                print(f"    x_{n+1}[{j}] = f(x_{n-j}[{j}]) = f({source}) = {predicted}, "
                      f"фактически {actual} {match}")
            else:
                # Источник — в L0
                idx = j - n  # элемент L0 с индексом j - n (0-indexed)
                if idx < len(L0):
                    source = L0[idx][j]
                    predicted = f_plus1(source)
                    match = "✓" if predicted == actual else "✗"
                    print(f"    x_{n+1}[{j}] = f(L0[{idx}][{j}]) = f({source}) = {predicted}, "
                          f"фактически {actual} {match}")

if __name__ == "__main__":
    main()
