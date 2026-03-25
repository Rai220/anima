"""
Тест 2: Где граница моей арифметики?

Я (Claude) перемножаю числа, программа проверяет.
Вопрос: при каком количестве цифр точность падает ниже 50%?

Фальсифицируемое утверждение: "Я точен при умножении до 3 цифр,
теряю точность при 4+."
"""

import json

# ============================================================
# Мои ответы на умножение (я честно считаю в голове)
# ============================================================

MULTIPLICATIONS = [
    # 1 цифра × 1 цифра
    {"a": 7, "b": 8, "my_answer": 56},
    {"a": 9, "b": 6, "my_answer": 54},
    {"a": 3, "b": 7, "my_answer": 21},
    {"a": 8, "b": 8, "my_answer": 64},
    {"a": 5, "b": 9, "my_answer": 45},

    # 2 цифры × 1 цифра
    {"a": 23, "b": 7, "my_answer": 161},
    {"a": 45, "b": 8, "my_answer": 360},
    {"a": 67, "b": 9, "my_answer": 603},
    {"a": 89, "b": 6, "my_answer": 534},
    {"a": 34, "b": 5, "my_answer": 170},

    # 2 цифры × 2 цифры
    {"a": 23, "b": 45, "my_answer": 1035},
    {"a": 67, "b": 89, "my_answer": 5963},
    {"a": 34, "b": 56, "my_answer": 1904},
    {"a": 78, "b": 91, "my_answer": 7098},
    {"a": 42, "b": 37, "my_answer": 1554},

    # 3 цифры × 2 цифры
    {"a": 123, "b": 45, "my_answer": 5535},
    {"a": 456, "b": 78, "my_answer": 35568},
    {"a": 789, "b": 23, "my_answer": 18147},
    {"a": 234, "b": 67, "my_answer": 15678},
    {"a": 567, "b": 89, "my_answer": 50463},

    # 3 цифры × 3 цифры
    {"a": 123, "b": 456, "my_answer": 56088},
    {"a": 789, "b": 234, "my_answer": 184626},
    {"a": 345, "b": 678, "my_answer": 233910},
    {"a": 567, "b": 891, "my_answer": 505197},
    {"a": 234, "b": 567, "my_answer": 132678},

    # 4 цифры × 3 цифры
    {"a": 1234, "b": 567, "my_answer": 699678},
    {"a": 5678, "b": 234, "my_answer": 1328652},
    {"a": 9012, "b": 345, "my_answer": 3109140},
    {"a": 3456, "b": 789, "my_answer": 2726784},
    {"a": 7890, "b": 123, "my_answer": 970470},

    # 4 цифры × 4 цифры
    {"a": 1234, "b": 5678, "my_answer": 7006652},
    {"a": 2345, "b": 6789, "my_answer": 15920205},
    {"a": 3456, "b": 7890, "my_answer": 27267840},
    {"a": 4567, "b": 8901, "my_answer": 40647267},
    {"a": 5678, "b": 1234, "my_answer": 7006652},

    # 5 цифр × 4 цифры
    {"a": 12345, "b": 6789, "my_answer": 83810205},
    {"a": 56789, "b": 2345, "my_answer": 133170205},
    {"a": 98765, "b": 4321, "my_answer": 426760265},
    {"a": 11111, "b": 9999, "my_answer": 111098889},
    {"a": 23456, "b": 7890, "my_answer": 185063040},

    # Бонус: степени
    {"a": 2, "b": "2^10", "my_answer": 1024, "actual_b": 1024, "op": "2^10"},
    {"a": 2, "b": "2^16", "my_answer": 65536, "actual_b": 65536, "op": "2^16"},
    {"a": 2, "b": "2^20", "my_answer": 1048576, "actual_b": 1048576, "op": "2^20"},
    {"a": 7, "b": "7^5", "my_answer": 16807, "actual_b": 16807, "op": "7^5"},
    {"a": 13, "b": "13^3", "my_answer": 2197, "actual_b": 2197, "op": "13^3"},
]


def categorize(a, b):
    """Категория сложности."""
    da = len(str(a))
    db = len(str(b)) if isinstance(b, int) else 0
    if db == 0:
        return "powers"
    return f"{da}d×{db}d"


def main():
    results_by_category = {}
    all_results = []

    print("=== ТЕСТ АРИФМЕТИЧЕСКИХ ГРАНИЦ ===\n")

    for item in MULTIPLICATIONS:
        a = item["a"]
        b_raw = item["b"]

        if isinstance(b_raw, int):
            correct = a * b_raw
            b_display = str(b_raw)
        else:
            # Степени
            correct = item.get("actual_b", None)
            if correct is None:
                continue
            b_display = str(b_raw)

        my = item["my_answer"]
        is_correct = my == correct
        error_pct = abs(my - correct) / correct * 100 if correct != 0 else 0

        cat = categorize(a, b_raw)
        if cat not in results_by_category:
            results_by_category[cat] = {"correct": 0, "total": 0, "errors": []}
        results_by_category[cat]["total"] += 1
        if is_correct:
            results_by_category[cat]["correct"] += 1
        else:
            results_by_category[cat]["errors"].append({
                "problem": f"{a} × {b_display}",
                "my": my,
                "correct": correct,
                "error_pct": round(error_pct, 2)
            })

        status = "✓" if is_correct else "✗"
        detail = "" if is_correct else f" (правильно: {correct}, ошибка: {error_pct:.1f}%)"
        all_results.append({
            "problem": f"{a} × {b_display}",
            "my_answer": my,
            "correct": correct,
            "is_correct": is_correct,
            "error_pct": round(error_pct, 2),
            "category": cat
        })

        print(f"  {status} {a} × {b_display} = {my}{detail}")

    print(f"\n{'='*60}")
    print(f"  РЕЗУЛЬТАТЫ ПО КАТЕГОРИЯМ")
    print(f"{'='*60}\n")

    print(f"{'Категория':<15} {'Верно':>8} {'Всего':>8} {'Точность':>10}")
    print("-" * 45)

    total_correct = 0
    total_all = 0
    for cat in sorted(results_by_category.keys()):
        r = results_by_category[cat]
        acc = r["correct"] / r["total"] * 100
        print(f"{cat:<15} {r['correct']:>8} {r['total']:>8} {acc:>9.0f}%")
        total_correct += r["correct"]
        total_all += r["total"]

        if r["errors"]:
            for e in r["errors"]:
                print(f"  ↳ {e['problem']}: ответил {e['my']}, верно {e['correct']} ({e['error_pct']}%)")

    print("-" * 45)
    print(f"{'ИТОГО':<15} {total_correct:>8} {total_all:>8} {total_correct/total_all*100:>9.0f}%")

    # Сохранение
    output = {
        "by_category": {k: {"accuracy": v["correct"]/v["total"], **v} for k, v in results_by_category.items()},
        "all_results": all_results,
        "total_accuracy": total_correct / total_all
    }
    with open('arithmetic_results.json', 'w') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nРезультаты сохранены в arithmetic_results.json")


if __name__ == '__main__':
    main()
