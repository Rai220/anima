"""
Цикл 3b: Где новая граница при пошаговой декомпозиции?

Пошаговое решение устранило ошибки при 5d×4d.
Но каждый шаг — это (Nd × 1d). Где граница для ЭТОГО?

Тестирую: Nd × 1d для N = 5..10
Затем: если граница найдена, тестирую полное умножение
на задачах, где частичные произведения уже у границы.
"""

import json

# ============================================================
# Тест 1: Nd × 1d (элементарные произведения)
# ============================================================

SINGLE_DIGIT_TESTS = [
    # 5d × 1d
    {"a": 74219, "b": 6, "my_answer": 445314},
    {"a": 98765, "b": 7, "my_answer": 691355},
    {"a": 31847, "b": 9, "my_answer": 286623},
    {"a": 56234, "b": 8, "my_answer": 449872},
    {"a": 12983, "b": 4, "my_answer": 51932},

    # 6d × 1d
    {"a": 742193, "b": 7, "my_answer": 5195351},
    {"a": 358176, "b": 9, "my_answer": 3223584},
    {"a": 614829, "b": 6, "my_answer": 3688974},
    {"a": 987654, "b": 3, "my_answer": 2962962},
    {"a": 123456, "b": 8, "my_answer": 987648},

    # 7d × 1d
    {"a": 7421938, "b": 6, "my_answer": 44531628},
    {"a": 3581762, "b": 9, "my_answer": 32235858},
    {"a": 6148293, "b": 7, "my_answer": 43038051},
    {"a": 9876543, "b": 4, "my_answer": 39506172},
    {"a": 1234567, "b": 8, "my_answer": 9876536},

    # 8d × 1d
    {"a": 74219384, "b": 7, "my_answer": 519535688},
    {"a": 35817629, "b": 3, "my_answer": 107452887},
    {"a": 61482937, "b": 9, "my_answer": 553346433},
    {"a": 98765432, "b": 5, "my_answer": 493827160},
    {"a": 12345678, "b": 6, "my_answer": 74074068},

    # 9d × 1d
    {"a": 742193847, "b": 8, "my_answer": 5937550776},
    {"a": 358176294, "b": 4, "my_answer": 1432705176},
    {"a": 614829371, "b": 7, "my_answer": 4303805597},
    {"a": 987654321, "b": 9, "my_answer": 8888888889},
    {"a": 123456789, "b": 3, "my_answer": 370370367},

    # 10d × 1d
    {"a": 7421938471, "b": 6, "my_answer": 44531630826},
    {"a": 3581762943, "b": 8, "my_answer": 28654103544},
    {"a": 6148293715, "b": 9, "my_answer": 55334643435},
    {"a": 9876543210, "b": 2, "my_answer": 19753086420},
    {"a": 1234567890, "b": 7, "my_answer": 8641975230},
]


def categorize_single(a):
    return f"{len(str(a))}d×1d"


def main():
    print("=== ЦИКЛ 3b: ГРАНИЦА ЭЛЕМЕНТАРНЫХ ПРОИЗВЕДЕНИЙ ===\n")

    results_by_cat = {}
    all_results = []

    for test in SINGLE_DIGIT_TESTS:
        a, b = test["a"], test["b"]
        correct = a * b
        my = test["my_answer"]
        is_correct = my == correct
        cat = categorize_single(a)

        if cat not in results_by_cat:
            results_by_cat[cat] = {"correct": 0, "total": 0, "errors": []}
        results_by_cat[cat]["total"] += 1
        if is_correct:
            results_by_cat[cat]["correct"] += 1

        status = "✓" if is_correct else "✗"
        detail = ""
        if not is_correct:
            error = my - correct
            detail = f"  (верно: {correct}, ошибка: {error:+d})"
            results_by_cat[cat]["errors"].append({
                "problem": f"{a} × {b}",
                "my": my, "correct": correct, "error": error
            })

        print(f"  {status} {a} × {b} = {my}{detail}")

        all_results.append({
            "a": a, "b": b, "my": my, "correct": correct,
            "is_correct": is_correct, "category": cat
        })

    print(f"\n{'='*60}")
    print("  РЕЗУЛЬТАТЫ ПО КАТЕГОРИЯМ")
    print(f"{'='*60}\n")

    print(f"{'Категория':<12} {'Верно':>8} {'Всего':>8} {'Точность':>10}")
    print("-" * 42)

    for cat in sorted(results_by_cat.keys()):
        r = results_by_cat[cat]
        acc = r["correct"] / r["total"] * 100
        print(f"{cat:<12} {r['correct']:>8} {r['total']:>8} {acc:>9.0f}%")
        for e in r["errors"]:
            print(f"  ↳ {e['problem']}: ответил {e['my']}, верно {e['correct']} (ошибка {e['error']:+d})")

    # Поиск границы
    print(f"\n{'='*60}")
    print("  ГРАНИЦА")
    print(f"{'='*60}\n")

    boundary_found = False
    for cat in sorted(results_by_cat.keys()):
        r = results_by_cat[cat]
        acc = r["correct"] / r["total"]
        if acc < 1.0 and not boundary_found:
            print(f"  >> Граница найдена: {cat} ({acc*100:.0f}% точность)")
            boundary_found = True

    if not boundary_found:
        print("  >> Граница НЕ найдена до 10d×1d. Элементарные произведения точны.")

    # Сохранение
    output = {
        "by_category": {
            k: {"accuracy": v["correct"]/v["total"], **v}
            for k, v in results_by_cat.items()
        },
        "all_results": all_results
    }
    with open("extended_arithmetic_results.json", "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nРезультаты сохранены в extended_arithmetic_results.json")


if __name__ == "__main__":
    main()
