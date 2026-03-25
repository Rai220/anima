"""
Можно ли предсказать центральную клетку клеточного автомата
на шаге N без полной симуляции?

Метод: строю простые предикторы (XOR-формула, линейная рекуррентность,
корреляция с предыдущими шагами) и измеряю, для каких правил
они работают.

Фальсифицируемое утверждение: правила с compression_ratio > 0.05
НЕ предсказуемы никаким полиномиальным предиктором от последних k шагов
(для k ≤ 10).
"""

import json
from ca import run


def extract_center_column(history: list) -> list:
    """Извлекает центральную колонку — последовательность состояний центральной клетки."""
    center = len(history[0]) // 2
    return [row[center] for row in history]


def xor_predictor(sequence: list, window: int = 3) -> float:
    """Предиктор на основе XOR последних window элементов.
    Возвращает точность на шагах window..end."""
    if len(sequence) <= window:
        return 0.5
    correct = 0
    total = 0
    for i in range(window, len(sequence)):
        pred = 0
        for j in range(1, window + 1):
            pred ^= sequence[i - j]
        if pred == sequence[i]:
            correct += 1
        total += 1
    return correct / total if total > 0 else 0.5


def linear_predictor(sequence: list, window: int = 5) -> float:
    """Предиктор: мажоритарное голосование последних window элементов.
    Если сумма > window/2, предсказываем 1, иначе 0."""
    if len(sequence) <= window:
        return 0.5
    correct = 0
    total = 0
    for i in range(window, len(sequence)):
        s = sum(sequence[i - window:i])
        pred = 1 if s > window / 2 else 0
        if pred == sequence[i]:
            correct += 1
        total += 1
    return correct / total if total > 0 else 0.5


def period_predictor(sequence: list, max_period: int = 20) -> tuple:
    """Ищет период в последовательности. Возвращает (лучший_период, точность)."""
    best_period = 1
    best_accuracy = 0.0

    for p in range(1, min(max_period + 1, len(sequence) // 2)):
        correct = 0
        total = 0
        for i in range(p, len(sequence)):
            if sequence[i] == sequence[i - p]:
                correct += 1
            total += 1
        acc = correct / total if total > 0 else 0.0
        if acc > best_accuracy:
            best_accuracy = acc
            best_period = p
    return best_period, best_accuracy


def autocorrelation_predictor(sequence: list, lag: int = 1) -> float:
    """Простейший: предсказываем sequence[i] = sequence[i - lag]."""
    if len(sequence) <= lag:
        return 0.5
    correct = sum(1 for i in range(lag, len(sequence))
                  if sequence[i] == sequence[i - lag])
    total = len(sequence) - lag
    return correct / total if total > 0 else 0.5


def best_predictor(sequence: list) -> dict:
    """Запускает все предикторы и возвращает лучший результат."""
    results = {}

    # XOR с разными окнами
    for w in [2, 3, 4, 5]:
        acc = xor_predictor(sequence, w)
        results[f'xor_{w}'] = acc

    # Мажоритарный
    for w in [3, 5, 7]:
        acc = linear_predictor(sequence, w)
        results[f'majority_{w}'] = acc

    # Периодический
    period, period_acc = period_predictor(sequence)
    results[f'period_{period}'] = period_acc

    # Автокорреляция
    for lag in [1, 2, 3, 5]:
        acc = autocorrelation_predictor(sequence, lag)
        results[f'autocorr_{lag}'] = acc

    # Константный предиктор (baseline)
    ones = sum(sequence)
    zeros = len(sequence) - ones
    results['const_majority'] = max(ones, zeros) / len(sequence)

    best_name = max(results, key=results.get)
    return {
        'best_method': best_name,
        'best_accuracy': results[best_name],
        'all_methods': results,
        'baseline': results['const_majority']
    }


def analyze_predictability():
    """Анализирует предсказуемость центральной колонки для всех 256 правил."""
    # Загружаем данные о сжатии
    with open('ca_results.json') as f:
        ca_data = json.load(f)
    cr_by_rule = {r['rule']: r['compression_ratio'] for r in ca_data['rules']}

    results = []
    for rule_num in range(256):
        history = run(rule_num, width=201, steps=500)
        center = extract_center_column(history)

        # Пропускаем тривиальные (все 0 или все 1)
        if sum(center) == 0 or sum(center) == len(center):
            results.append({
                'rule': rule_num,
                'trivial': True,
                'best_accuracy': 1.0,
                'best_method': 'trivial',
                'compression_ratio': cr_by_rule.get(rule_num, 0),
            })
            continue

        pred = best_predictor(center)
        results.append({
            'rule': rule_num,
            'trivial': False,
            'best_accuracy': round(pred['best_accuracy'], 4),
            'best_method': pred['best_method'],
            'baseline': round(pred['baseline'], 4),
            'lift': round(pred['best_accuracy'] - pred['baseline'], 4),
            'compression_ratio': cr_by_rule.get(rule_num, 0),
        })

    return results


if __name__ == '__main__':
    print("Анализирую предсказуемость центральной колонки для 256 правил...")
    print("(500 шагов на каждое правило)\n")

    results = analyze_predictability()

    # Разделяем на предсказуемые и непредсказуемые
    nontrivial = [r for r in results if not r.get('trivial', False)]
    predictable = [r for r in nontrivial if r['best_accuracy'] > 0.9]
    moderate = [r for r in nontrivial if 0.7 < r['best_accuracy'] <= 0.9]
    hard = [r for r in nontrivial if r['best_accuracy'] <= 0.7]

    print(f"Тривиальные (всё 0 или всё 1): {sum(1 for r in results if r.get('trivial'))}")
    print(f"Предсказуемые (>90%): {len(predictable)}")
    print(f"Средние (70-90%): {len(moderate)}")
    print(f"Непредсказуемые (≤70%): {len(hard)}")

    # Проверяем гипотезу: связь compression_ratio и предсказуемости
    print(f"\n=== Проверка гипотезы ===")
    print("Связь compression_ratio и предсказуемости центральной колонки:")

    high_cr = [r for r in nontrivial if r['compression_ratio'] > 0.05]
    low_cr = [r for r in nontrivial if r['compression_ratio'] <= 0.05]

    if high_cr:
        avg_acc_high = sum(r['best_accuracy'] for r in high_cr) / len(high_cr)
        print(f"  CR > 0.05: {len(high_cr)} правил, средняя точность = {avg_acc_high:.4f}")
    if low_cr:
        avg_acc_low = sum(r['best_accuracy'] for r in low_cr) / len(low_cr)
        print(f"  CR ≤ 0.05: {len(low_cr)} правил, средняя точность = {avg_acc_low:.4f}")

    # Самые непредсказуемые
    print(f"\nТоп-10 самых непредсказуемых (нетривиальных) правил:")
    nontrivial.sort(key=lambda r: r['best_accuracy'])
    for r in nontrivial[:10]:
        lift_str = f"lift={r.get('lift', 0):+.4f}" if 'lift' in r else ""
        print(f"  Rule {r['rule']}: acc={r['best_accuracy']:.4f}, "
              f"method={r['best_method']}, cr={r['compression_ratio']:.4f}, {lift_str}")

    # Известные правила
    interesting = [30, 90, 110, 54, 73, 22, 126, 150, 45, 105]
    print(f"\nИзвестные правила:")
    for r in results:
        if r['rule'] in interesting and not r.get('trivial'):
            lift_str = f"lift={r.get('lift', 0):+.4f}" if 'lift' in r else ""
            print(f"  Rule {r['rule']}: acc={r['best_accuracy']:.4f}, "
                  f"method={r['best_method']}, cr={r['compression_ratio']:.4f}, {lift_str}")

    with open('predictor_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("\nРезультаты сохранены в predictor_results.json")
