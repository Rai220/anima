"""
Сколько пространственного контекста нужно для предсказания?

Для каждого правила варьируем радиус наблюдения: 0 (только центр),
1 (центр ± 1), 2 (центр ± 2), ... и измеряем, при каком радиусе
точность резко возрастает.

Фальсифицируемое утверждение: для Rule 30 переход от ~50% к ~100%
происходит ТОЧНО при радиусе 1 (потому что правило зависит только
от непосредственных соседей). Промежуточных значений нет.
"""

from collections import defaultdict
from ca import run


def predict_with_radius(history: list, radius: int, window: int = 1) -> float:
    """Предсказывает центральную клетку на шаге t по состоянию
    клеток в радиусе radius на шагах t-1..t-window.

    Метод: таблица частот (lookup table), train/test split 2/3.
    """
    center = len(history[0]) // 2
    n = len(history)
    offsets = list(range(-radius, radius + 1))

    train_end = n * 2 // 3
    counts = defaultdict(lambda: [0, 0])

    for i in range(window, train_end):
        pattern = tuple(
            history[i - lag][center + off]
            for lag in range(1, window + 1)
            for off in offsets
        )
        actual = history[i][center]
        counts[pattern][actual] += 1

    correct = 0
    total = 0
    unseen = 0
    for i in range(train_end, n):
        pattern = tuple(
            history[i - lag][center + off]
            for lag in range(1, window + 1)
            for off in offsets
        )
        actual = history[i][center]
        c = counts[pattern]
        if c[0] + c[1] == 0:
            unseen += 1
            pred = 0  # default
        else:
            pred = 1 if c[1] > c[0] else 0
        if pred == actual:
            correct += 1
        total += 1

    return {
        'accuracy': round(correct / total, 4) if total > 0 else 0.5,
        'unseen_rate': round(unseen / total, 4) if total > 0 else 0,
        'unique_patterns': len(counts),
    }


def find_threshold(rule_num: int, steps: int = 2000) -> dict:
    """Находит минимальный радиус для точности > 95%."""
    history = run(rule_num, width=201, steps=steps)
    results = {}
    threshold_radius = None

    for radius in range(0, 11):
        res = predict_with_radius(history, radius, window=1)
        results[radius] = res
        if res['accuracy'] > 0.95 and threshold_radius is None:
            threshold_radius = radius

    return {
        'rule': rule_num,
        'threshold_radius': threshold_radius,
        'by_radius': results,
    }


if __name__ == '__main__':
    test_rules = [30, 45, 75, 86, 89, 101, 110, 135, 149, 22, 54, 73, 90, 105, 126, 150]

    print(f"{'Rule':>6}", end="")
    for r in range(6):
        print(f"  r={r:>2}", end="")
    print(f"  threshold")
    print("-" * 70)

    all_results = {}
    for rule_num in test_rules:
        res = find_threshold(rule_num)
        all_results[rule_num] = res
        print(f"{rule_num:>6}", end="")
        for r in range(6):
            if r in res['by_radius']:
                acc = res['by_radius'][r]['accuracy']
                print(f"  {acc:.3f}", end="")
            else:
                print(f"      -", end="")
        t = res['threshold_radius']
        print(f"  r={t}" if t is not None else "  >10")

    # Анализ: все ли "непредсказуемые" правила переключаются ровно при r=1?
    hard_rules = [30, 45, 75, 86, 89, 101, 135, 149]
    print(f"\n=== Проверка гипотезы ===")
    print(f"Для 'непредсказуемых' правил переход при r=1?")
    for rule_num in hard_rules:
        r0 = all_results[rule_num]['by_radius'][0]['accuracy']
        r1 = all_results[rule_num]['by_radius'][1]['accuracy']
        jump = r1 - r0
        threshold = all_results[rule_num]['threshold_radius']
        print(f"  Rule {rule_num}: r=0 → {r0:.4f}, r=1 → {r1:.4f}, "
              f"Δ={jump:+.4f}, threshold=r={threshold}")

    # Есть ли правила с постепенным переходом?
    print(f"\n=== Постепенные переходы ===")
    for rule_num in test_rules:
        accs = [all_results[rule_num]['by_radius'][r]['accuracy'] for r in range(6)]
        # Ищем правила где есть промежуточные значения (0.6 < acc < 0.95)
        intermediate = [a for a in accs if 0.6 < a < 0.95]
        if intermediate:
            print(f"  Rule {rule_num}: {' → '.join(f'{a:.3f}' for a in accs)}")
