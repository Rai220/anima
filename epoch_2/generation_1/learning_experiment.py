"""
Эксперимент: сжатие vs скорость обучения.

Задача: обнаружить скрытое правило (булева функция от n переменных)
по последовательно предъявляемым примерам.

Три стратегии:
1. Запоминатель — хранит виденные пары, для новых — случайный ответ
2. Гипотезник — перебирает семейство гипотез, выбирает совместимую
3. Полный поисковик — перебирает все 2^(2^n) булевых функций

Измеряем:
- Accuracy(k) — точность после k примеров (на остальных 2^n - k входах)
- Compression(k) — отношение log(размер таблицы) / размер используемого описания
- Learning speed — dAccuracy/dk

Цель: показать что compression и learning speed — связаны, но не тождественны.
"""

import json
import random
import itertools
from collections import defaultdict
from typing import Callable


def all_inputs(n: int) -> list[tuple[int, ...]]:
    """Все 2^n входов для n бит."""
    return list(itertools.product([0, 1], repeat=n))


# --- Типы правил ---

def make_conjunction(n: int, bits: tuple[int, ...]) -> Callable:
    """Конъюнкция: f(x) = AND(x[i] for i in bits)"""
    def f(x):
        return int(all(x[i] for i in bits))
    return f

def make_disjunction(n: int, bits: tuple[int, ...]) -> Callable:
    """Дизъюнкция: f(x) = OR(x[i] for i in bits)"""
    def f(x):
        return int(any(x[i] for i in bits))
    return f

def make_threshold(n: int, k: int) -> Callable:
    """Пороговая: f(x) = 1 если sum(x) >= k"""
    def f(x):
        return int(sum(x) >= k)
    return f

def make_parity(n: int, bits: tuple[int, ...]) -> Callable:
    """Чётность: f(x) = XOR(x[i] for i in bits)"""
    def f(x):
        return sum(x[i] for i in bits) % 2
    return f

def make_majority(n: int) -> Callable:
    """Большинство: f(x) = 1 если sum(x) > n/2"""
    return make_threshold(n, (n + 1) // 2)


# --- Стратегии обучения ---

class Memorizer:
    """Запоминатель: хранит все виденные примеры."""

    def __init__(self, n: int):
        self.n = n
        self.memory: dict[tuple, int] = {}

    def observe(self, x: tuple[int, ...], y: int):
        self.memory[x] = y

    def predict(self, x: tuple[int, ...]) -> int:
        if x in self.memory:
            return self.memory[x]
        return random.randint(0, 1)

    def description_size(self) -> int:
        """Размер описания в битах: каждая запись = n + 1 бит."""
        return len(self.memory) * (self.n + 1)


class HypothesisTester:
    """Гипотезник: перебирает семейство гипотез (конъюнкции, дизъюнкции, пороговые)."""

    def __init__(self, n: int):
        self.n = n
        self.data: list[tuple[tuple[int, ...], int]] = []
        self.hypotheses = self._generate_hypotheses()
        self.best = None

    def _generate_hypotheses(self) -> list[tuple[str, Callable]]:
        """Генерирует все гипотезы из семейства."""
        hyps = []
        # Конъюнкции подмножеств (включая пустое = всегда 1)
        for r in range(self.n + 1):
            for bits in itertools.combinations(range(self.n), r):
                hyps.append((f"AND{bits}", make_conjunction(self.n, bits)))
        # Дизъюнкции подмножеств (включая пустое = всегда 0)
        for r in range(self.n + 1):
            for bits in itertools.combinations(range(self.n), r):
                hyps.append((f"OR{bits}", make_disjunction(self.n, bits)))
        # Пороговые
        for k in range(1, self.n + 1):
            hyps.append((f"THR{k}", make_threshold(self.n, k)))
        # Чётность подмножеств
        for r in range(1, self.n + 1):
            for bits in itertools.combinations(range(self.n), r):
                hyps.append((f"XOR{bits}", make_parity(self.n, bits)))
        return hyps

    def observe(self, x: tuple[int, ...], y: int):
        self.data.append((x, y))
        # Находим все совместимые гипотезы
        compatible = []
        for name, h in self.hypotheses:
            if all(h(xi) == yi for xi, yi in self.data):
                compatible.append((name, h))
        if compatible:
            self.best = compatible[0]  # Берём первую совместимую
        else:
            self.best = None

    def predict(self, x: tuple[int, ...]) -> int:
        if self.best:
            return self.best[1](x)
        # Нет совместимых — случайно
        return random.randint(0, 1)

    def description_size(self) -> int:
        """Размер описания: ID гипотезы + размер семейства."""
        import math
        if self.best:
            return int(math.ceil(math.log2(max(len(self.hypotheses), 1)))) + 1
        return len(self.data) * (self.n + 1)  # Фоллбэк на запоминание


class ExhaustiveSearcher:
    """Полный поисковик: перебирает все 2^(2^n) булевых функций."""

    def __init__(self, n: int):
        self.n = n
        self.data: list[tuple[tuple[int, ...], int]] = []
        self.inputs = all_inputs(n)
        self.total_functions = 2 ** (2 ** n)
        self.compatible_count = self.total_functions

    def observe(self, x: tuple[int, ...], y: int):
        self.data.append((x, y))
        # Каждое наблюдение уменьшает число совместимых функций вдвое
        self.compatible_count = max(1, self.total_functions // (2 ** len(self.data)))

    def predict(self, x: tuple[int, ...]) -> int:
        """Предсказание большинством совместимых функций.

        Для k наблюдений из 2^n входов: на ненаблюдённом входе
        ровно половина совместимых функций даёт 0, половина — 1.
        (Если данные не ограничивают этот вход.)

        Реальное вычисление: проверяем, следует ли ответ из данных.
        """
        # Проверяем: наблюдали ли мы этот вход
        for xi, yi in self.data:
            if xi == x:
                return yi
        # Если нет — среди совместимых функций ровно половина даёт 0 и 1
        # (если вход независим от наблюдённых, что верно для булевых функций)
        return random.randint(0, 1)

    def description_size(self) -> int:
        """После k наблюдений: log(число совместимых) бит."""
        import math
        return int(math.ceil(math.log2(max(self.compatible_count, 1))))


def evaluate(strategy, rule_fn, n: int, max_examples: int = None,
             num_trials: int = 50) -> dict:
    """Оценивает стратегию на правиле.

    Возвращает accuracy и description_size после каждого примера.
    """
    inputs = all_inputs(n)
    total = len(inputs)
    if max_examples is None:
        max_examples = total

    results = {"accuracy": [], "desc_size": [], "k": []}

    for trial in range(num_trials):
        order = list(range(total))
        random.shuffle(order)

        # Создаём стратегию заново
        s = strategy(n)

        trial_acc = []
        trial_desc = []

        for k in range(min(max_examples, total)):
            # Показываем пример
            idx = order[k]
            x = inputs[idx]
            y = rule_fn(x)
            s.observe(x, y)

            # Оцениваем на непоказанных
            unseen = [inputs[order[j]] for j in range(k + 1, total)]
            if unseen:
                correct = sum(1 for x_test in unseen
                             if s.predict(x_test) == rule_fn(x_test))
                acc = correct / len(unseen)
            else:
                acc = 1.0

            trial_acc.append(acc)
            trial_desc.append(s.description_size())

        if not results["accuracy"]:
            results["accuracy"] = [0.0] * len(trial_acc)
            results["desc_size"] = [0.0] * len(trial_desc)
            results["k"] = list(range(1, len(trial_acc) + 1))

        for i in range(len(trial_acc)):
            results["accuracy"][i] += trial_acc[i] / num_trials
            results["desc_size"][i] += trial_desc[i] / num_trials

    return results


def run_experiment():
    random.seed(42)

    n = 5  # 5 бит = 32 входа = 2^32 ≈ 4 млрд функций

    # Правила разной сложности
    rules = {
        "conjunction_01": make_conjunction(n, (0, 1)),
        "disjunction_234": make_disjunction(n, (2, 3, 4)),
        "threshold_3": make_threshold(n, 3),
        "parity_012": make_parity(n, (0, 1, 2)),
        "majority": make_majority(n),
    }

    strategies = {
        "memorizer": Memorizer,
        "hypothesis": HypothesisTester,
        "exhaustive": ExhaustiveSearcher,
    }

    all_results = {}

    for rule_name, rule_fn in rules.items():
        print(f"\n--- Правило: {rule_name} ---")

        # Таблица истинности
        inputs = all_inputs(n)
        truth = [rule_fn(x) for x in inputs]
        ones = sum(truth)
        print(f"  Баланс: {ones}/{len(inputs)} единиц")

        table_size = 2 ** n  # бит (1 бит на вход)
        print(f"  Размер полной таблицы: {table_size} бит")

        rule_results = {}

        for strat_name, strat_cls in strategies.items():
            print(f"  Стратегия: {strat_name}")
            result = evaluate(strat_cls, rule_fn, n, num_trials=30)
            rule_results[strat_name] = result

            # Ключевые точки
            for k_idx in [0, 4, 9, 14, 19, 24, 29]:
                if k_idx < len(result["accuracy"]):
                    k = result["k"][k_idx]
                    acc = result["accuracy"][k_idx]
                    desc = result["desc_size"][k_idx]
                    print(f"    k={k:2d}: acc={acc:.3f}, desc_size={desc:.1f} бит")

        all_results[rule_name] = rule_results

    # Анализ: сжатие vs скорость
    print("\n\n=== АНАЛИЗ: СЖАТИЕ vs СКОРОСТЬ ===\n")

    for rule_name, rule_results in all_results.items():
        print(f"--- {rule_name} ---")
        table_size = 2 ** n

        for strat_name, result in rule_results.items():
            # Финальная точность (после всех примеров)
            final_acc = result["accuracy"][-1]
            final_desc = result["desc_size"][-1]
            compression = table_size / max(final_desc, 1)

            # Скорость обучения: сколько примеров нужно для 90% accuracy
            k_90 = None
            for i, acc in enumerate(result["accuracy"]):
                if acc >= 0.9:
                    k_90 = result["k"][i]
                    break

            # Скорость обучения: средний прирост accuracy на пример (первые 10)
            if len(result["accuracy"]) >= 2:
                early_speed = result["accuracy"][min(9, len(result["accuracy"])-1)] / min(10, len(result["accuracy"]))
            else:
                early_speed = 0

            print(f"  {strat_name:15s}: final_acc={final_acc:.3f}, "
                  f"compression={compression:.1f}x, "
                  f"k_90={k_90 if k_90 else '>'+str(table_size)}, "
                  f"early_speed={early_speed:.3f}")
        print()

    # Ключевой вопрос: есть ли случаи, где сжатие высокое, а скорость низкая?
    print("\n=== КЛЮЧЕВОЙ ВОПРОС ===")
    print("Есть ли случаи, где compression != learning speed?")
    print()

    for rule_name, rule_results in all_results.items():
        table_size = 2 ** n
        scores = {}
        for strat_name, result in rule_results.items():
            final_desc = result["desc_size"][-1]
            compression = table_size / max(final_desc, 1)

            k_90 = len(result["accuracy"]) + 1
            for i, acc in enumerate(result["accuracy"]):
                if acc >= 0.9:
                    k_90 = result["k"][i]
                    break

            scores[strat_name] = {"compression": compression, "k_90": k_90}

        # Проверяем: ранжирование по compression совпадает с ранжированием по k_90?
        by_comp = sorted(scores.items(), key=lambda x: -x[1]["compression"])
        by_speed = sorted(scores.items(), key=lambda x: x[1]["k_90"])

        comp_order = [x[0] for x in by_comp]
        speed_order = [x[0] for x in by_speed]

        match = "ДА" if comp_order == speed_order else "НЕТ"
        print(f"{rule_name}: compression order = {comp_order}")
        print(f"{'':>{len(rule_name)}}: speed order     = {speed_order}")
        print(f"{'':>{len(rule_name)}}: совпадают = {match}")
        print()

    # Сохраняем результаты
    save_results = {}
    for rule_name, rule_results in all_results.items():
        save_results[rule_name] = {}
        for strat_name, result in rule_results.items():
            save_results[rule_name][strat_name] = {
                "accuracy": [round(a, 4) for a in result["accuracy"]],
                "desc_size": [round(d, 1) for d in result["desc_size"]],
                "k": result["k"],
            }

    with open("learning_experiment_results.json", "w") as f:
        json.dump(save_results, f, indent=2)

    print("Результаты сохранены в learning_experiment_results.json")
    return all_results


if __name__ == "__main__":
    run_experiment()
