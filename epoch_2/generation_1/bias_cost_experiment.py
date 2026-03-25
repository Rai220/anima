"""
Эксперимент 2: цена индуктивного смещения.

Что происходит, когда правило НЕ входит в семейство гипотез?
Гипотезник должен провалиться — но КАК именно?

Правила вне семейства:
- multiplexer: f(x) = x[x[0]*2 + x[1] + 2] (зависимость бит от бит)
- nested_xor: f(x) = (x[0] XOR x[1]) AND (x[2] XOR x[3])
- random: случайная булева функция
"""

import json
import random
import itertools
from learning_experiment import (
    Memorizer, HypothesisTester, ExhaustiveSearcher,
    all_inputs, evaluate
)


def make_multiplexer(n: int):
    """Мультиплексор: первые 2 бита = адрес, выход = бит по адресу."""
    assert n >= 4
    def f(x):
        addr = x[0] * 2 + x[1]
        return x[addr + 2] if addr + 2 < n else 0
    return f


def make_nested_xor(n: int):
    """Вложенный XOR-AND: (x0 XOR x1) AND (x2 XOR x3)."""
    assert n >= 4
    def f(x):
        return (x[0] ^ x[1]) & (x[2] ^ x[3])
    return f


def make_random_function(n: int, seed: int = 123):
    """Случайная булева функция."""
    rng = random.Random(seed)
    table = {inp: rng.randint(0, 1) for inp in all_inputs(n)}
    def f(x):
        return table[tuple(x)]
    return f


def make_if_then_else(n: int):
    """IF x0 THEN (x1 AND x2) ELSE (x3 OR x4)."""
    assert n >= 5
    def f(x):
        if x[0]:
            return x[1] & x[2]
        else:
            return x[3] | x[4]
    return f


def run():
    random.seed(42)
    n = 5

    rules = {
        "multiplexer": make_multiplexer(n),
        "nested_xor": make_nested_xor(n),
        "if_then_else": make_if_then_else(n),
        "random_fn": make_random_function(n),
    }

    strategies = {
        "memorizer": Memorizer,
        "hypothesis": HypothesisTester,
        "exhaustive": ExhaustiveSearcher,
    }

    print("=== ЦЕНА ИНДУКТИВНОГО СМЕЩЕНИЯ ===\n")
    print("Правила, НЕ входящие в семейство гипотезника.\n")

    all_results = {}

    for rule_name, rule_fn in rules.items():
        inputs = all_inputs(n)
        truth = [rule_fn(x) for x in inputs]
        ones = sum(truth)
        print(f"--- {rule_name} ({ones}/{len(inputs)} единиц) ---")

        rule_results = {}
        for strat_name, strat_cls in strategies.items():
            result = evaluate(strat_cls, rule_fn, n, num_trials=30)

            table_size = 2 ** n
            final_acc = result["accuracy"][-1]
            final_desc = result["desc_size"][-1]

            k_90 = None
            for i, acc in enumerate(result["accuracy"]):
                if acc >= 0.9:
                    k_90 = result["k"][i]
                    break

            # Accuracy на полпути (k=16)
            mid_acc = result["accuracy"][15] if len(result["accuracy"]) > 15 else 0

            print(f"  {strat_name:15s}: mid_acc={mid_acc:.3f}, "
                  f"final_acc={final_acc:.3f}, "
                  f"k_90={k_90 if k_90 else '>32'}")

            rule_results[strat_name] = result

        # Ключевое сравнение: гипотезник vs запоминатель на полпути
        h_mid = rule_results["hypothesis"]["accuracy"][15]
        m_mid = rule_results["memorizer"]["accuracy"][15]

        if h_mid < m_mid:
            print(f"  >>> ГИПОТЕЗНИК ХУЖЕ ЗАПОМИНАТЕЛЯ на k=16! "
                  f"(diff={m_mid - h_mid:.3f})")
        elif h_mid > m_mid + 0.05:
            print(f"  >>> Гипотезник лучше запоминателя даже вне семейства "
                  f"(diff={h_mid - m_mid:.3f})")
        else:
            print(f"  >>> Примерно равны на k=16")

        all_results[rule_name] = rule_results
        print()

    # Сводка
    print("\n=== СВОДКА ===\n")
    print("Правила IN-FAMILY (из первого эксперимента):")
    print("  Гипотезник: k_90 = 7-15, всегда лучше остальных")
    print()
    print("Правила OUT-OF-FAMILY:")
    for rule_name, rule_results in all_results.items():
        h_k90 = None
        for i, acc in enumerate(rule_results["hypothesis"]["accuracy"]):
            if acc >= 0.9:
                h_k90 = rule_results["hypothesis"]["k"][i]
                break
        print(f"  {rule_name}: hypothesis k_90 = {h_k90 if h_k90 else '>32'}")

    print()
    print("Вывод: индуктивное смещение ПОМОГАЕТ когда правильное,")
    print("и может МЕШАТЬ когда неправильное.")

    # Сохраняем
    save = {}
    for rn, rr in all_results.items():
        save[rn] = {}
        for sn, sr in rr.items():
            save[rn][sn] = {
                "accuracy": [round(a, 4) for a in sr["accuracy"]],
                "k": sr["k"],
            }
    with open("bias_cost_results.json", "w") as f:
        json.dump(save, f, indent=2)


if __name__ == "__main__":
    run()
