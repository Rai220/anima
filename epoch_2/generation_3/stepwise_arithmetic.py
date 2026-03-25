"""
Цикл 3: Помогает ли декомпозиция преодолеть арифметическую границу?

В цикле 2 я ошибался при 4d×4d (80%) и 5d×4d (60%).
Гипотеза: если я разложу на промежуточные шаги и запишу каждый,
точность вернётся к ~100%, потому что bottleneck — рабочая память, не алгоритм.

Контр-гипотеза: если ошибки глубже (в самих частичных произведениях),
декомпозиция не поможет.

Дизайн: те же задачи + новые, но теперь я записываю:
1) Каждое частичное произведение (a × каждая цифра b)
2) Сдвиг
3) Сумму

Программа проверяет КАЖДЫЙ промежуточный шаг.
"""

import json


# ============================================================
# Задачи с пошаговым решением
# Формат: a, b, partial_products (список: digit_b * a), final_answer
# ============================================================

STEPWISE = [
    # --- 4d × 4d (в цикле 2: 80% точность) ---
    {
        "a": 4567,
        "b": 8901,
        "note": "Ошибся в цикле 2 (ответил 40647267, верно 40643667)",
        "steps": {
            # 8901 = 8000 + 900 + 0 + 1
            # Разбиваю b по цифрам справа налево: 1, 0, 9, 8
            "partial_products": [
                {"digit": 1, "shift": 0, "product": 4567},     # 4567 × 1
                {"digit": 0, "shift": 1, "product": 0},        # 4567 × 0
                {"digit": 9, "shift": 2, "product": 41103},    # 4567 × 9
                {"digit": 8, "shift": 3, "product": 36536},    # 4567 × 8
            ],
            # Сложение с учётом сдвигов:
            # 4567 × 1 =         4567
            # 4567 × 0 =            0  (× 10)
            # 4567 × 9 =     4110300  (× 100)
            # 4567 × 8 =    36536000  (× 1000)
            "shifted_sum": [4567, 0, 4110300, 36536000],
            "final": 40650867,
        }
    },
    {
        "a": 2345,
        "b": 6789,
        "note": "Верно в цикле 2 (15920205)",
        "steps": {
            "partial_products": [
                {"digit": 9, "shift": 0, "product": 21105},    # 2345 × 9
                {"digit": 8, "shift": 1, "product": 18760},    # 2345 × 8
                {"digit": 7, "shift": 2, "product": 16415},    # 2345 × 7
                {"digit": 6, "shift": 3, "product": 14070},    # 2345 × 6
            ],
            "shifted_sum": [21105, 187600, 1641500, 14070000],
            "final": 15920205,
        }
    },
    {
        "a": 3456,
        "b": 7890,
        "note": "Верно в цикле 2 (27267840)",
        "steps": {
            "partial_products": [
                {"digit": 0, "shift": 0, "product": 0},
                {"digit": 9, "shift": 1, "product": 31104},    # 3456 × 9
                {"digit": 8, "shift": 2, "product": 27648},    # 3456 × 8
                {"digit": 7, "shift": 3, "product": 24192},    # 3456 × 7
            ],
            "shifted_sum": [0, 311040, 2764800, 24192000],
            "final": 27267840,
        }
    },

    # --- 5d × 4d (в цикле 2: 60% точность) ---
    {
        "a": 98765,
        "b": 4321,
        "note": "Ошибся в цикле 2 (ответил 426760265, верно 426763565)",
        "steps": {
            "partial_products": [
                {"digit": 1, "shift": 0, "product": 98765},
                {"digit": 2, "shift": 1, "product": 197530},   # 98765 × 2
                {"digit": 3, "shift": 2, "product": 296295},   # 98765 × 3
                {"digit": 4, "shift": 3, "product": 395060},   # 98765 × 4
            ],
            "shifted_sum": [98765, 1975300, 29629500, 395060000],
            "final": 426763565,
        }
    },
    {
        "a": 23456,
        "b": 7890,
        "note": "Ошибся в цикле 2 (ответил 185063040, верно 185067840)",
        "steps": {
            "partial_products": [
                {"digit": 0, "shift": 0, "product": 0},
                {"digit": 9, "shift": 1, "product": 211104},   # 23456 × 9
                {"digit": 8, "shift": 2, "product": 187648},   # 23456 × 8
                {"digit": 7, "shift": 3, "product": 164192},   # 23456 × 7
            ],
            "shifted_sum": [0, 2111040, 18764800, 164192000],
            "final": 185067840,
        }
    },
    {
        "a": 56789,
        "b": 2345,
        "note": "Верно в цикле 2 (133170205)",
        "steps": {
            "partial_products": [
                {"digit": 5, "shift": 0, "product": 283945},   # 56789 × 5
                {"digit": 4, "shift": 1, "product": 227156},   # 56789 × 4
                {"digit": 3, "shift": 2, "product": 170367},   # 56789 × 3
                {"digit": 2, "shift": 3, "product": 113578},   # 56789 × 2
            ],
            "shifted_sum": [283945, 2271560, 17036700, 113578000],
            "final": 133170205,
        }
    },

    # --- Новые задачи 4d × 4d (не виденные ранее) ---
    {
        "a": 6173,
        "b": 4829,
        "note": "Новая задача",
        "steps": {
            "partial_products": [
                {"digit": 9, "shift": 0, "product": 55557},    # 6173 × 9
                {"digit": 2, "shift": 1, "product": 12346},    # 6173 × 2
                {"digit": 8, "shift": 2, "product": 49384},    # 6173 × 8
                {"digit": 4, "shift": 3, "product": 24692},    # 6173 × 4
            ],
            "shifted_sum": [55557, 123460, 4938400, 24692000],
            "final": 29809417,
        }
    },
    {
        "a": 8521,
        "b": 3764,
        "note": "Новая задача",
        "steps": {
            "partial_products": [
                {"digit": 4, "shift": 0, "product": 34084},    # 8521 × 4
                {"digit": 6, "shift": 1, "product": 51126},    # 8521 × 6
                {"digit": 7, "shift": 2, "product": 59647},    # 8521 × 7
                {"digit": 3, "shift": 3, "product": 25563},    # 8521 × 3
            ],
            "shifted_sum": [34084, 511260, 5964700, 25563000],
            "final": 32073044,
        }
    },

    # --- Новые задачи 5d × 4d ---
    {
        "a": 74219,
        "b": 5836,
        "note": "Новая задача",
        "steps": {
            "partial_products": [
                {"digit": 6, "shift": 0, "product": 445314},   # 74219 × 6
                {"digit": 3, "shift": 1, "product": 222657},   # 74219 × 3
                {"digit": 8, "shift": 2, "product": 593752},   # 74219 × 8
                {"digit": 5, "shift": 3, "product": 371095},   # 74219 × 5
            ],
            "shifted_sum": [445314, 2226570, 59375200, 371095000],
            "final": 433142084,
        }
    },
    {
        "a": 31847,
        "b": 9263,
        "note": "Новая задача",
        "steps": {
            "partial_products": [
                {"digit": 3, "shift": 0, "product": 95541},    # 31847 × 3
                {"digit": 6, "shift": 1, "product": 191082},   # 31847 × 6
                {"digit": 2, "shift": 2, "product": 63694},    # 31847 × 2
                {"digit": 9, "shift": 3, "product": 286623},   # 31847 × 9
            ],
            "shifted_sum": [95541, 1910820, 6369400, 286623000],
            "final": 294998761,
        }
    },
]


def verify_stepwise(task):
    """Проверяет каждый шаг решения."""
    a = task["a"]
    b = task["b"]
    steps = task["steps"]
    correct_final = a * b

    errors = []

    # Проверка каждого частичного произведения
    for pp in steps["partial_products"]:
        digit = pp["digit"]
        expected = a * digit
        if pp["product"] != expected:
            errors.append({
                "type": "partial_product",
                "desc": f"{a} × {digit}",
                "my": pp["product"],
                "correct": expected,
                "error": pp["product"] - expected
            })

    # Проверка сдвигов
    for i, (pp, shifted) in enumerate(zip(steps["partial_products"], steps["shifted_sum"])):
        expected_shifted = pp["product"] * (10 ** pp["shift"])
        if shifted != expected_shifted:
            errors.append({
                "type": "shift",
                "desc": f"{pp['product']} × 10^{pp['shift']}",
                "my": shifted,
                "correct": expected_shifted,
                "error": shifted - expected_shifted
            })

    # Проверка суммы
    my_sum = sum(steps["shifted_sum"])
    if my_sum != steps["final"]:
        errors.append({
            "type": "sum",
            "desc": f"sum of shifted products",
            "my": steps["final"],
            "correct_from_shifts": my_sum,
            "error": steps["final"] - my_sum
        })

    # Проверка финального ответа
    final_correct = steps["final"] == correct_final
    if not final_correct:
        errors.append({
            "type": "final",
            "desc": f"{a} × {b}",
            "my": steps["final"],
            "correct": correct_final,
            "error": steps["final"] - correct_final
        })

    return {
        "problem": f"{a} × {b}",
        "note": task["note"],
        "my_final": steps["final"],
        "correct_final": correct_final,
        "final_correct": final_correct,
        "n_errors": len(errors),
        "errors": errors,
        "step_types_failed": list(set(e["type"] for e in errors))
    }


def main():
    print("=== ЦИКЛ 3: ПОШАГОВАЯ АРИФМЕТИКА ===\n")
    print("Гипотеза: декомпозиция на шаги поднимает точность до ~100%")
    print("Контр-гипотеза: ошибки в частичных произведениях тоже есть\n")

    results = []
    categories = {"4d×4d": [], "5d×4d": []}

    for task in STEPWISE:
        result = verify_stepwise(task)
        results.append(result)

        da = len(str(task["a"]))
        db = len(str(task["b"]))
        cat = f"{da}d×{db}d"
        if cat in categories:
            categories[cat].append(result)

        status = "✓" if result["final_correct"] else "✗"
        print(f"  {status} {result['problem']} = {result['my_final']}", end="")
        if not result["final_correct"]:
            print(f"  (верно: {result['correct_final']}, ошибка: {result['my_final'] - result['correct_final']:+d})")
        else:
            print()

        if result["errors"]:
            for e in result["errors"]:
                print(f"      ↳ [{e['type']}] {e['desc']}: мой {e['my']}, ", end="")
                if 'correct' in e:
                    print(f"верно {e['correct']}, ошибка {e['error']:+d}")
                else:
                    print(f"сумма сдвигов {e.get('correct_from_shifts', '?')}, ошибка {e['error']:+d}")

    # Статистика по типам ошибок
    print(f"\n{'='*60}")
    print("  АНАЛИЗ ОШИБОК ПО ТИПУ ШАГА")
    print(f"{'='*60}\n")

    error_types = {"partial_product": 0, "shift": 0, "sum": 0, "final": 0}
    total_partial = 0
    total_shifts = 0
    for r in results:
        total_partial += len([pp for pp in STEPWISE[results.index(r)]["steps"]["partial_products"]])
        total_shifts += len(STEPWISE[results.index(r)]["steps"]["shifted_sum"])
        for e in r["errors"]:
            error_types[e["type"]] += 1

    print(f"  Частичные произведения: {error_types['partial_product']} ошибок из {total_partial}")
    print(f"  Сдвиги:                {error_types['shift']} ошибок из {total_shifts}")
    print(f"  Суммирование:          {error_types['sum']} ошибок из {len(results)}")
    print(f"  Финальный ответ:       {error_types['final']} ошибок из {len(results)}")

    # Сравнение с цикл 2
    print(f"\n{'='*60}")
    print("  СРАВНЕНИЕ: ЦИКЛ 2 vs ЦИКЛ 3")
    print(f"{'='*60}\n")

    cycle2_accuracy = {"4d×4d": 0.8, "5d×4d": 0.6}
    for cat in ["4d×4d", "5d×4d"]:
        cat_results = categories[cat]
        if cat_results:
            correct = sum(1 for r in cat_results if r["final_correct"])
            total = len(cat_results)
            acc = correct / total
            print(f"  {cat}: Цикл 2 = {cycle2_accuracy[cat]*100:.0f}%, Цикл 3 (пошагово) = {acc*100:.0f}% ({correct}/{total})")

    # Вывод
    all_correct = sum(1 for r in results if r["final_correct"])
    print(f"\n  Общая точность: {all_correct}/{len(results)} ({all_correct/len(results)*100:.0f}%)")

    # Главный вопрос: ГДЕ ошибки?
    if error_types["partial_product"] > 0:
        print(f"\n  >> КОНТР-ГИПОТЕЗА ПОДТВЕРЖДЕНА: ошибки уже в частичных произведениях")
        print(f"     Декомпозиция НЕ устраняет проблему полностью")
    elif error_types["sum"] > 0 or error_types["shift"] > 0:
        print(f"\n  >> Ошибки только при сложении/сдвиге — bottleneck в сборке, не вычислении")
    elif all_correct == len(results):
        print(f"\n  >> ГИПОТЕЗА ПОДТВЕРЖДЕНА: декомпозиция = 100% точность")
        print(f"     Граница была в рабочей памяти, не в алгоритме")

    # Сохранение
    output = {
        "results": results,
        "error_summary": error_types,
        "accuracy": all_correct / len(results),
        "comparison": {
            cat: {
                "cycle2": cycle2_accuracy.get(cat, None),
                "cycle3": sum(1 for r in categories[cat] if r["final_correct"]) / len(categories[cat]) if categories[cat] else None
            }
            for cat in categories
        }
    }
    with open("stepwise_results.json", "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nРезультаты сохранены в stepwise_results.json")


if __name__ == "__main__":
    main()
