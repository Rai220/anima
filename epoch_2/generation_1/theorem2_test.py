"""
Эмпирическая проверка Теоремы 2:
Отличима ли "понимающая" система от справочной таблицы
через случайную подвыборку вопросов?

Область: умножение mod p.
- Полная таблица: p² записей
- "Понимающая" система: алгоритм умножения (O(log p) бит)
- Частичная таблица: случайные M записей из p²

Предсказание Теоремы 2: если M << p², то частичная таблица
не может правильно отвечать на случайные вопросы с высокой частотой,
а "понимающая" система — может.
"""

import random
import json
from collections import defaultdict

def run_experiment():
    results = []

    for p in [17, 53, 97, 211, 503, 1009]:
        total_facts = p * p  # размер полной таблицы

        for memory_fraction in [0.01, 0.05, 0.1, 0.25, 0.5]:
            M = int(total_facts * memory_fraction)  # размер частичной таблицы

            # Построить частичную таблицу: случайные M пар
            all_pairs = [(a, b) for a in range(p) for b in range(p)]
            memorized = set(random.sample(range(len(all_pairs)), min(M, len(all_pairs))))
            table = {}
            for idx in memorized:
                a, b = all_pairs[idx]
                table[(a, b)] = (a * b) % p

            # Тестировать на случайной подвыборке
            n_test = 200
            test_indices = random.sample(range(len(all_pairs)), min(n_test, len(all_pairs)))

            # "Понимающая" система
            understanding_correct = 0
            # Частичная таблица (отвечает случайно, если не знает)
            table_correct = 0

            for idx in test_indices:
                a, b = all_pairs[idx]
                correct = (a * b) % p

                # "Понимающая" система всегда права
                understanding_correct += 1

                # Таблица: знает или угадывает
                if (a, b) in table:
                    table_correct += 1
                elif random.randint(0, p - 1) == correct:
                    table_correct += 1  # случайное угадывание

            understanding_accuracy = understanding_correct / n_test
            table_accuracy = table_correct / n_test

            # Порог из Теоремы 2: M / (N * log|Y|)
            import math
            threshold = M / (total_facts * math.log2(p)) if total_facts * math.log2(p) > 0 else 0

            results.append({
                "p": p,
                "total_facts": total_facts,
                "memory_M": M,
                "memory_fraction": memory_fraction,
                "understanding_accuracy": round(understanding_accuracy, 4),
                "table_accuracy": round(table_accuracy, 4),
                "threshold": round(threshold, 4),
                "distinguishable": understanding_accuracy > table_accuracy + 0.1
            })

    return results


def analyze(results):
    print("=" * 70)
    print("ТЕОРЕМА 2: ЭМПИРИЧЕСКАЯ ПРОВЕРКА")
    print("Область: умножение mod p")
    print("=" * 70)

    by_p = defaultdict(list)
    for r in results:
        by_p[r["p"]].append(r)

    for p, group in sorted(by_p.items()):
        print(f"\np = {p}, область = {p}² = {p*p} фактов")
        print(f"{'Память':>10} | {'Понимание':>10} | {'Таблица':>10} | {'Порог Т2':>10} | {'Различимы?':>12}")
        print("-" * 65)
        for r in group:
            print(f"{r['memory_fraction']:>9.0%} | "
                  f"{r['understanding_accuracy']:>10.1%} | "
                  f"{r['table_accuracy']:>10.1%} | "
                  f"{r['threshold']:>10.4f} | "
                  f"{'ДА' if r['distinguishable'] else 'нет':>12}")

    # Общая статистика
    n_distinguishable = sum(1 for r in results if r["distinguishable"])
    print(f"\n{'=' * 70}")
    print(f"Различимы в {n_distinguishable}/{len(results)} случаев")

    # Ключевой вопрос: при какой доле памяти различие исчезает?
    print(f"\nПри какой доле памяти различие исчезает?")
    for frac in [0.01, 0.05, 0.1, 0.25, 0.5]:
        subset = [r for r in results if r["memory_fraction"] == frac]
        n_dist = sum(1 for r in subset if r["distinguishable"])
        print(f"  {frac:>5.0%} памяти: различимы в {n_dist}/{len(subset)} случаев")

    return results


if __name__ == "__main__":
    random.seed(42)
    results = run_experiment()
    analyzed = analyze(results)

    with open("theorem2_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\nРезультаты сохранены в theorem2_results.json")
