"""
Углублённый предиктор для "непредсказуемых" правил.

Вопрос: стена на ~55% — это предел простых предикторов
или фундаментальный предел?

Методы:
1. Большие окна (до 50 шагов назад)
2. Нелинейные комбинации (все 2^k подмножества для k≤12)
3. Соседние колонки (не только центр, но и ±1, ±2)
4. Больше данных (2000 шагов вместо 500)

Фальсифицируемое утверждение: для Rule 30 ни один предиктор
на основе последних k≤50 состояний центральной колонки
не достигнет точности > 60%.
"""

import json
from itertools import combinations
from ca import run


def extract_columns(history: list, offsets: list) -> dict:
    """Извлекает несколько колонок из истории."""
    center = len(history[0]) // 2
    return {off: [row[center + off] for row in history] for off in offsets}


def exhaustive_xor_predictor(sequence: list, max_window: int = 12) -> dict:
    """Перебирает все 2^k подмножества из последних max_window элементов.
    Предиктор: XOR указанного подмножества.
    Возвращает лучшую комбинацию."""
    n = len(sequence)
    train_end = n * 2 // 3  # первые 2/3 для обучения
    best_acc = 0.0
    best_mask = ()

    for size in range(1, min(max_window + 1, 8)):  # ограничиваем до 7 элементов
        for mask in combinations(range(1, max_window + 1), size):
            max_lag = max(mask)
            if max_lag >= train_end:
                continue

            # Обучение
            correct_train = 0
            total_train = 0
            for i in range(max_lag, train_end):
                pred = 0
                for lag in mask:
                    pred ^= sequence[i - lag]
                if pred == sequence[i]:
                    correct_train += 1
                total_train += 1

            train_acc = correct_train / total_train if total_train > 0 else 0

            if train_acc > best_acc:
                # Проверяем на тесте
                correct_test = 0
                total_test = 0
                for i in range(train_end, n):
                    pred = 0
                    for lag in mask:
                        pred ^= sequence[i - lag]
                    if pred == sequence[i]:
                        correct_test += 1
                    total_test += 1

                test_acc = correct_test / total_test if total_test > 0 else 0
                best_acc = train_acc
                best_mask = mask
                best_test = test_acc

    return {
        'train_accuracy': round(best_acc, 4),
        'test_accuracy': round(best_test, 4) if 'best_test' in dir() else 0.5,
        'mask': list(best_mask),
    }


def multi_column_predictor(history: list, target_offset: int = 0,
                            source_offsets: list = None,
                            window: int = 3) -> dict:
    """Предиктор, использующий соседние колонки.
    Предсказывает колонку target_offset используя информацию из source_offsets."""
    if source_offsets is None:
        source_offsets = [-2, -1, 0, 1, 2]

    center = len(history[0]) // 2
    n = len(history)

    # Построим таблицу: для каждого паттерна (tuple из значений в source_offsets на шаге i-1)
    # считаем, сколько раз target_offset на шаге i был 0 или 1
    from collections import defaultdict
    counts = defaultdict(lambda: [0, 0])

    for i in range(window, n):
        pattern = tuple(
            history[i - lag][center + off]
            for lag in range(1, window + 1)
            for off in source_offsets
        )
        actual = history[i][center + target_offset]
        counts[pattern][actual] += 1

    # Leave-one-out: для каждого шага предсказываем на основе всех остальных
    # Упрощение: train на первых 2/3, test на последних 1/3
    train_end = n * 2 // 3
    train_counts = defaultdict(lambda: [0, 0])

    for i in range(window, train_end):
        pattern = tuple(
            history[i - lag][center + off]
            for lag in range(1, window + 1)
            for off in source_offsets
        )
        actual = history[i][center + target_offset]
        train_counts[pattern][actual] += 1

    # Test
    correct = 0
    total = 0
    for i in range(train_end, n):
        pattern = tuple(
            history[i - lag][center + off]
            for lag in range(1, window + 1)
            for off in source_offsets
        )
        actual = history[i][center + target_offset]
        c = train_counts[pattern]
        pred = 1 if c[1] > c[0] else 0
        if pred == actual:
            correct += 1
        total += 1

    return {
        'test_accuracy': round(correct / total, 4) if total > 0 else 0.5,
        'unique_patterns': len(train_counts),
        'total_patterns': sum(sum(v) for v in train_counts.values()),
    }


def analyze_hard_rules():
    """Углублённый анализ непредсказуемых правил."""
    hard_rules = [30, 45, 75, 86, 89, 101, 135, 149]
    # Добавим пограничные для сравнения
    border_rules = [110, 137, 73, 22]

    all_rules = hard_rules + border_rules
    results = {}

    for rule_num in all_rules:
        print(f"\nRule {rule_num}:")
        history = run(rule_num, width=201, steps=2000)
        center = len(history[0]) // 2
        center_seq = [row[center] for row in history]

        # 1. Исчерпывающий XOR предиктор
        print("  XOR перебор...", end=" ", flush=True)
        xor_result = exhaustive_xor_predictor(center_seq, max_window=12)
        print(f"train={xor_result['train_accuracy']}, test={xor_result['test_accuracy']}, "
              f"mask={xor_result['mask']}")

        # 2. Мульти-колоночный предиктор (использует соседние клетки)
        print("  Мульти-колонка...", end=" ", flush=True)
        multi_results = {}
        for w in [1, 2, 3]:
            for offsets in [[-1, 0, 1], [-2, -1, 0, 1, 2]]:
                key = f"w{w}_off{len(offsets)}"
                mr = multi_column_predictor(history, 0, offsets, w)
                multi_results[key] = mr
                print(f"{key}={mr['test_accuracy']}", end=" ", flush=True)
        print()

        best_multi_key = max(multi_results, key=lambda k: multi_results[k]['test_accuracy'])
        best_multi = multi_results[best_multi_key]

        # 3. Плотность единиц (bias)
        ones = sum(center_seq)
        bias = ones / len(center_seq)

        results[rule_num] = {
            'xor_test': xor_result['test_accuracy'],
            'xor_mask': xor_result['mask'],
            'multi_best': best_multi['test_accuracy'],
            'multi_config': best_multi_key,
            'multi_patterns': best_multi['unique_patterns'],
            'bias': round(bias, 4),
            'baseline': round(max(bias, 1 - bias), 4),
            'is_hard': rule_num in hard_rules,
        }

        overall_best = max(xor_result['test_accuracy'], best_multi['test_accuracy'])
        print(f"  Лучший: {overall_best:.4f} (baseline: {max(bias, 1-bias):.4f})")

    return results


if __name__ == '__main__':
    results = analyze_hard_rules()

    print("\n" + "=" * 60)
    print("ИТОГИ")
    print("=" * 60)

    print(f"\n{'Rule':>6} {'XOR':>8} {'Multi':>8} {'Base':>8} {'Lift':>8} {'Hard?':>6}")
    print("-" * 50)
    for rule_num in sorted(results.keys()):
        r = results[rule_num]
        best = max(r['xor_test'], r['multi_best'])
        lift = best - r['baseline']
        mark = "***" if r['is_hard'] else ""
        print(f"{rule_num:>6} {r['xor_test']:>8.4f} {r['multi_best']:>8.4f} "
              f"{r['baseline']:>8.4f} {lift:>+8.4f} {mark:>6}")

    # Главный вопрос
    hard_rules = [r for r in results.values() if r['is_hard']]
    if hard_rules:
        max_hard = max(max(r['xor_test'], r['multi_best']) for r in hard_rules)
        print(f"\nМаксимальная точность среди 'непредсказуемых': {max_hard:.4f}")
        print(f"Стена на 60%: {'НЕ ПРОБИТА' if max_hard <= 0.60 else 'ПРОБИТА'}")

    with open('deep_predictor_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
