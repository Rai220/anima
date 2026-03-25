"""
Исследование обобщённых отображений Коллатца.

Стандартное: f(n) = n/2 if even, 3n+1 if odd
Обобщённое: f(n) = n/2 if even, a*n+b if odd

Вопросы:
1. Для каких (a, b) все начальные значения сходятся к циклу?
2. Какова структура циклов (длина, элементы)?
3. Есть ли фазовый переход между сходимостью и расходимостью?
"""

import json
from collections import defaultdict

def collatz_step(n, a, b):
    """Один шаг обобщённого отображения Коллатца."""
    if n % 2 == 0:
        return n // 2
    else:
        return a * n + b

def find_cycle_or_diverge(start, a, b, max_steps=100_000, diverge_threshold=10**15):
    """
    Запускаем последовательность. Возвращаем:
    - ('cycle', cycle_elements, steps_to_cycle) если нашли цикл
    - ('diverge', max_reached, steps) если ушли за порог
    - ('timeout', last_value, max_steps) если не определились
    """
    seen = {}  # value -> step_number
    n = start
    for step in range(max_steps):
        if n in seen:
            cycle_start = seen[n]
            cycle_len = step - cycle_start
            # восстановим элементы цикла
            cycle = []
            curr = n
            for _ in range(cycle_len):
                cycle.append(curr)
                curr = collatz_step(curr, a, b)
            return ('cycle', tuple(sorted(cycle)), step)
        if abs(n) > diverge_threshold:
            return ('diverge', n, step)
        seen[n] = step
        n = collatz_step(n, a, b)
    return ('timeout', n, max_steps)

def survey_parameters(a_range, b_range, start_range, max_steps=50_000):
    """Обзор ландшафта для сетки параметров."""
    results = {}

    for a in a_range:
        for b in b_range:
            if a <= 0 or b == 0:
                continue  # пропускаем тривиальные
            if a % 2 == 0:
                continue  # a должно быть нечётным, иначе a*n+b всегда нечётно при нечётном n и чётном a... нет, не обязательно

            key = (a, b)
            cycles_found = set()
            diverge_count = 0
            converge_count = 0
            timeout_count = 0

            for start in start_range:
                result = find_cycle_or_diverge(start, a, b, max_steps)
                if result[0] == 'cycle':
                    cycles_found.add(result[1])
                    converge_count += 1
                elif result[0] == 'diverge':
                    diverge_count += 1
                else:
                    timeout_count += 1

            results[f"{a},{b}"] = {
                'a': a, 'b': b,
                'converge': converge_count,
                'diverge': diverge_count,
                'timeout': timeout_count,
                'num_distinct_cycles': len(cycles_found),
                'cycles': [list(c) for c in cycles_found],
                'cycle_lengths': sorted(set(len(c) for c in cycles_found)),
            }

    return results

def main():
    print("=" * 60)
    print("ОБОБЩЁННЫЕ ОТОБРАЖЕНИЯ КОЛЛАТЦА: ЛАНДШАФТ")
    print("f(n) = n/2 if even, a*n+b if odd")
    print("=" * 60)

    # Фаза 1: Нечётные a от 1 до 11, b от 1 до 9, начальные значения 1..200
    print("\n--- Фаза 1: Обзор нечётных a ∈ [1,11], b ∈ [1,9] ---")
    a_range = [1, 3, 5, 7, 9, 11]
    b_range = list(range(1, 10))
    start_range = list(range(1, 201))

    results = survey_parameters(a_range, b_range, start_range, max_steps=50_000)

    # Классификация
    fully_converging = []
    fully_diverging = []
    mixed = []

    for key, r in sorted(results.items()):
        total = r['converge'] + r['diverge'] + r['timeout']
        if r['converge'] == total:
            fully_converging.append(r)
        elif r['diverge'] == total:
            fully_diverging.append(r)
        else:
            mixed.append(r)

    print(f"\nВсего параметров: {len(results)}")
    print(f"Полностью сходящихся: {len(fully_converging)}")
    print(f"Полностью расходящихся: {len(fully_diverging)}")
    print(f"Смешанных: {len(mixed)}")

    # Детали сходящихся
    print("\n--- Полностью сходящиеся ---")
    for r in fully_converging:
        cycles_str = "; ".join(f"len={len(c)}: {c[:5]}{'...' if len(c)>5 else ''}"
                               for c in r['cycles'])
        print(f"  a={r['a']}, b={r['b']}: {r['num_distinct_cycles']} цикл(ов), "
              f"длины {r['cycle_lengths']}  [{cycles_str}]")

    # Детали смешанных
    if mixed:
        print("\n--- Смешанные (частично сходящиеся) ---")
        for r in mixed:
            print(f"  a={r['a']}, b={r['b']}: converge={r['converge']}, "
                  f"diverge={r['diverge']}, timeout={r['timeout']}")

    # Фаза 2: Фазовый переход
    print("\n\n--- Фаза 2: Поиск фазового перехода ---")
    print("Тестируем a ∈ {1,3,5,7} при b=1, начальные 1..500")

    for a in [1, 3, 5, 7]:
        starts = list(range(1, 501))
        converge = 0
        diverge = 0
        timeout = 0
        max_steps_to_cycle = 0

        for s in starts:
            result = find_cycle_or_diverge(s, a, 1, max_steps=100_000)
            if result[0] == 'cycle':
                converge += 1
                max_steps_to_cycle = max(max_steps_to_cycle, result[2])
            elif result[0] == 'diverge':
                diverge += 1
            else:
                timeout += 1

        print(f"  a={a}, b=1: converge={converge}/500, diverge={diverge}, "
              f"timeout={timeout}, max_steps={max_steps_to_cycle}")

    # Фаза 3: Структура циклов для a=3 (классический Коллатц)
    print("\n\n--- Фаза 3: Циклы классического Коллатца (a=3, b=1) ---")
    cycles = set()
    for s in range(1, 10001):
        result = find_cycle_or_diverge(s, 3, 1, max_steps=100_000)
        if result[0] == 'cycle':
            cycles.add(result[1])

    print(f"Все начальные 1..10000 сходятся к {len(cycles)} цикл(ам):")
    for c in sorted(cycles, key=lambda x: len(x)):
        if len(c) <= 20:
            print(f"  Длина {len(c)}: {list(c)}")
        else:
            print(f"  Длина {len(c)}: [{min(c)}...{max(c)}]")

    # Фаза 4: Отрицательные числа и циклы для a=3, b=1
    print("\n\n--- Фаза 4: Отрицательные начальные значения (a=3, b=1) ---")
    neg_cycles = set()
    for s in range(-500, 0):
        result = find_cycle_or_diverge(s, 3, 1, max_steps=100_000)
        if result[0] == 'cycle':
            neg_cycles.add(result[1])
        elif result[0] == 'diverge':
            pass  # expected for some

    print(f"Начальные -500..-1: {len(neg_cycles)} различных цикл(ов)")
    for c in sorted(neg_cycles, key=lambda x: (len(x), min(x))):
        if len(c) <= 20:
            print(f"  Длина {len(c)}: {list(c)}")
        else:
            print(f"  Длина {len(c)}: [{min(c)}...{max(c)}]")

    # Фаза 5: Ландшафт a=5 (предсказание: все расходятся для b=1)
    print("\n\n--- Фаза 5: a=5, различные b ---")
    for b in [1, 3, 5, 7, -1, -3]:
        cycles_5 = set()
        conv = 0
        div = 0
        to = 0
        for s in range(1, 201):
            result = find_cycle_or_diverge(s, 5, b, max_steps=100_000)
            if result[0] == 'cycle':
                cycles_5.add(result[1])
                conv += 1
            elif result[0] == 'diverge':
                div += 1
            else:
                to += 1
        print(f"  a=5, b={b}: converge={conv}, diverge={div}, timeout={to}, "
              f"cycles={len(cycles_5)}")
        for c in sorted(cycles_5, key=len):
            if len(c) <= 10:
                print(f"    len={len(c)}: {list(c)}")

    # Фаза 6: Чётные a (нестандартно)
    print("\n\n--- Фаза 6: Чётные a (нестандартное обобщение) ---")
    for a in [2, 4, 6]:
        for b in [1, 3]:
            cycles_e = set()
            conv = 0
            div = 0
            for s in range(1, 201):
                result = find_cycle_or_diverge(s, a, b, max_steps=50_000)
                if result[0] == 'cycle':
                    cycles_e.add(result[1])
                    conv += 1
                elif result[0] == 'diverge':
                    div += 1
            print(f"  a={a}, b={b}: converge={conv}/200, diverge={200-conv}, "
                  f"cycles={len(cycles_e)}")

    # Сохранение
    with open('collatz_results.json', 'w') as f:
        json.dump({
            'phase1': results,
            'description': 'Generalized Collatz landscape survey'
        }, f, indent=2)

    print("\n\nРезультаты сохранены в collatz_results.json")

if __name__ == '__main__':
    main()
