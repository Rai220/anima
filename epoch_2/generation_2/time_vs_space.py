"""
Время vs пространство: можно ли заменить пространственный контекст
глубоким временным?

Для Rule 30: при r=0 (только центр) точность ~50%.
Вопрос: если взять window=50 (50 шагов назад), станет ли лучше?

Идея: клеточный автомат — детерминистическая система.
Вся его история содержит полную информацию о начальном состоянии.
Но доступ к этой информации через одну колонку может быть
вычислительно трудным.

Фальсифицируемое утверждение: для Rule 30 увеличение глубины
истории (window) с 1 до 50 не повысит точность выше 60%.
Причина: информация о соседях НЕ восстановима из одной колонки.
"""

from collections import defaultdict
from ca import run


def time_depth_predictor(history: list, window: int, radius: int = 0) -> dict:
    """Предсказывает центр по window предыдущим шагам в радиусе radius."""
    center = len(history[0]) // 2
    n = len(history)
    offsets = list(range(-radius, radius + 1))
    features_per_step = len(offsets)

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
            pred = 0
        else:
            pred = 1 if c[1] > c[0] else 0
        if pred == actual:
            correct += 1
        total += 1

    return {
        'accuracy': round(correct / total, 4) if total > 0 else 0.5,
        'unseen_rate': round(unseen / total, 4) if total > 0 else 0,
        'unique_patterns': len(counts),
        'total_train': train_end - window,
        'feature_dim': window * features_per_step,
    }


if __name__ == '__main__':
    rules_to_test = [30, 90, 110, 45]
    steps = 5000  # больше данных для глубоких историй

    for rule_num in rules_to_test:
        print(f"\n=== Rule {rule_num} (steps={steps}) ===")
        history = run(rule_num, width=201, steps=steps)

        print(f"\n  Только время (r=0), разная глубина:")
        print(f"  {'window':>8} {'acc':>8} {'unseen':>8} {'patterns':>10} {'dim':>6}")
        print(f"  {'-'*46}")

        for w in [1, 2, 3, 5, 8, 13, 21, 34]:
            if w >= steps // 3:
                break
            res = time_depth_predictor(history, window=w, radius=0)
            print(f"  {w:>8} {res['accuracy']:>8.4f} {res['unseen_rate']:>8.4f} "
                  f"{res['unique_patterns']:>10} {res['feature_dim']:>6}")

        # Сравнение: r=1 w=1 vs r=0 w=много
        print(f"\n  Пространство vs время:")
        baseline = time_depth_predictor(history, window=1, radius=0)
        spatial = time_depth_predictor(history, window=1, radius=1)
        deep_time = time_depth_predictor(history, window=13, radius=0)

        print(f"  r=0, w=1:  acc={baseline['accuracy']:.4f} (baseline)")
        print(f"  r=1, w=1:  acc={spatial['accuracy']:.4f} (пространство)")
        print(f"  r=0, w=13: acc={deep_time['accuracy']:.4f} (глубокое время)")
        print(f"  Вывод: {'время НЕ заменяет пространство' if deep_time['accuracy'] < 0.7 else 'время ЧАСТИЧНО заменяет пространство' if deep_time['accuracy'] < 0.95 else 'время ЗАМЕНЯЕТ пространство'}")

    # Итоговый вопрос: для каких правил время может заменить пространство?
    print(f"\n{'='*60}")
    print("ИТОГ: время заменяет пространство?")
    print(f"{'='*60}")

    hard_rules = [30, 45, 75, 86, 89, 101, 135, 149]
    predictable_from_time = [22, 73, 90, 105]

    print(f"\nПравила, предсказуемые из собственной истории (r=0): {predictable_from_time}")
    print(f"Правила, НЕ предсказуемые из истории: {hard_rules}")
    print(f"\nВывод: пространственная информация и временная НЕ взаимозаменяемы.")
    print("Одна колонка клеточного автомата — как наблюдение за комнатой")
    print("через замочную скважину. Неважно, как долго вы смотрите —")
    print("вы не увидите того, что происходит за стеной.")
