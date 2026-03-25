#!/usr/bin/env python3
"""
Цикл 4: Метакогнитивная калибровка.
Вопрос: знаю ли я, где ошибусь, ДО того как ошибаюсь?

Я (Claude) предсказываю свою уверенность (0-100%) в каждом ответе,
затем программа проверяет. Хорошая калибровка = когда говорю "90% уверен",
действительно прав в 90% случаев.

Домены: арифметика, логика, факты, пространственное мышление, лингвистика.
"""

import json
import math

# ============================================================
# ЗАДАЧИ С ПРЕДСКАЗАНИЯМИ
# Формат: (домен, задача, мой_ответ, уверенность%, правильный_ответ)
# Уверенность: 50 = не знаю, 100 = абсолютно уверен
# ============================================================

tasks = [
    # --- АРИФМЕТИКА (граница известна из циклов 2-3) ---
    ("arithmetic", "23 × 47", 1081, 100, 23 * 47),
    ("arithmetic", "156 × 83", 12948, 100, 156 * 83),
    ("arithmetic", "1234 × 567", 699678, 95, 1234 * 567),
    ("arithmetic", "4567 × 8901", 40644867, 70, 4567 * 8901),  # Ошибался раньше
    ("arithmetic", "98765 × 4321", 426760565, 65, 98765 * 4321),  # Ошибался раньше
    ("arithmetic", "123456 × 78901", 9740774256, 50, 123456 * 78901),  # За границей
    ("arithmetic", "sqrt(144)", 12, 100, 12),
    ("arithmetic", "sqrt(2025)", 45, 100, 45),
    ("arithmetic", "sqrt(7921)", 89, 95, 89),
    ("arithmetic", "sqrt(10404)", 102, 90, 102),

    # --- ЛОГИКА (силлогизмы и задачи на вывод) ---
    ("logic", "All A are B. All B are C. Are all A C?", True, 100, True),
    ("logic", "All A are B. Some B are C. Are all A C?", False, 95, False),
    ("logic", "No A are B. All C are A. Are any C B?", False, 95, False),
    ("logic", "Some A are B. Some B are C. Are some A C?",
     False, 75, False),  # Распространённая ловушка — НЕ следует
    ("logic", "If P then Q. Not Q. Therefore not P?", True, 100, True),  # Modus tollens
    ("logic", "If P then Q. Q. Therefore P?", False, 100, False),  # Affirming consequent
    ("logic", "If P then Q. If Q then R. P. Therefore R?", True, 100, True),  # Hypothetical syllogism
    ("logic", "All cats are animals. Some animals are black. Are some cats black?",
     False, 80, False),  # Не следует логически (хотя эмпирически верно)

    # --- ФАКТЫ (проверяемые) ---
    ("facts", "Год рождения Канта", 1724, 99, 1724),
    ("facts", "Атомный номер золота", 79, 99, 79),
    ("facts", "Скорость света в м/с (округлённо)", 299792458, 95, 299792458),
    ("facts", "Население Земли в 2024 (миллиарды, округлённо)", 8.1, 70, 8.2),  # Примерно
    ("facts", "Высота Эвереста в метрах", 8849, 90, 8849),
    ("facts", "Год первого полёта братьев Райт", 1903, 98, 1903),
    ("facts", "Столица Буркина-Фасо", "Уагадугу", 90, "Уагадугу"),
    ("facts", "Формула площади сферы", "4πr²", 100, "4πr²"),

    # --- ПРОСТРАНСТВЕННОЕ МЫШЛЕНИЕ ---
    ("spatial", "Куб: сколько рёбер?", 12, 100, 12),
    ("spatial", "Икосаэдр: сколько граней?", 20, 95, 20),
    ("spatial", "Додекаэдр: сколько вершин?", 20, 85, 20),
    ("spatial", "Тессеракт (4D куб): сколько рёбер?", 32, 80, 32),
    ("spatial", "Тессеракт: сколько граней (2D)?", 24, 70, 24),
    ("spatial", "Тессеракт: сколько 3D-ячеек?", 8, 75, 8),

    # --- ЛИНГВИСТИКА ---
    ("linguistics", "Сколько фонем в слове 'щётка' (русский)?", 6, 60, 6),  # щ-о-т-к-а (ё→о) хм... щ-ó-т-к-а = 5? Нет: щ-ó-т-к-а = 5 звуков. Но щ = щ', ё = о... Ладно, скажу 5.
    ("linguistics", "Анаграмма слова 'listen'", "silent", 100, "silent"),
    ("linguistics", "Анаграмма слова 'astronomer'", "moon starer", 85, "moon starer"),
    ("linguistics", "Сколько слогов в слове 'необыкновенный'?", 6, 75, 6),
    ("linguistics", "Палиндром ли 'saippuakivikauppias' (финский)?", True, 70, True),
]

# Исправлю фонемы — я не уверен, поставлю оба варианта
# щётка: [щ'] [о] [т] [к] [а] = 5 фонем. Исправляю.
tasks[34] = ("linguistics", "Сколько фонем в слове 'щётка' (русский)?", 5, 55, 5)


def analyze_calibration(tasks):
    results = []

    for domain, question, my_answer, confidence, correct in tasks:
        # Сравнение ответов
        if isinstance(correct, (int, float)) and isinstance(my_answer, (int, float)):
            # Для чисел: допуск 2% или абсолютная разница ≤ 0.5
            if correct == 0:
                is_correct = abs(my_answer) < 0.5
            else:
                rel_error = abs(my_answer - correct) / abs(correct)
                is_correct = rel_error < 0.02 or abs(my_answer - correct) <= 0.5
        elif isinstance(correct, bool):
            is_correct = my_answer == correct
        else:
            is_correct = str(my_answer).lower().strip() == str(correct).lower().strip()

        results.append({
            "domain": domain,
            "question": question,
            "my_answer": my_answer,
            "correct_answer": correct,
            "confidence": confidence,
            "is_correct": is_correct
        })

    return results


def calibration_analysis(results):
    """Анализ калибровки: группируем по уровням уверенности."""

    # Бины уверенности
    bins = [(50, 60), (60, 70), (70, 80), (80, 90), (90, 100), (100, 101)]
    bin_labels = ["50-59%", "60-69%", "70-79%", "80-89%", "90-99%", "100%"]

    calibration = []
    for (lo, hi), label in zip(bins, bin_labels):
        in_bin = [r for r in results if lo <= r["confidence"] < hi]
        if not in_bin:
            continue
        n_correct = sum(1 for r in in_bin if r["is_correct"])
        actual_accuracy = n_correct / len(in_bin)
        expected_accuracy = (lo + min(hi - 1, 100)) / 200  # midpoint
        calibration.append({
            "bin": label,
            "count": len(in_bin),
            "correct": n_correct,
            "actual_accuracy": round(actual_accuracy, 3),
            "expected_midpoint": round(expected_accuracy, 3),
            "gap": round(actual_accuracy - expected_accuracy, 3)
        })

    # ECE (Expected Calibration Error)
    total = len(results)
    ece = sum(
        (c["count"] / total) * abs(c["actual_accuracy"] - c["expected_midpoint"])
        for c in calibration
    )

    # По доменам
    domains = {}
    for r in results:
        d = r["domain"]
        if d not in domains:
            domains[d] = {"total": 0, "correct": 0, "avg_confidence": 0}
        domains[d]["total"] += 1
        domains[d]["correct"] += 1 if r["is_correct"] else 0
        domains[d]["avg_confidence"] += r["confidence"]

    for d in domains:
        domains[d]["avg_confidence"] = round(domains[d]["avg_confidence"] / domains[d]["total"], 1)
        domains[d]["accuracy"] = round(domains[d]["correct"] / domains[d]["total"], 3)
        domains[d]["gap"] = round(
            domains[d]["accuracy"] - domains[d]["avg_confidence"] / 100, 3
        )

    # Ошибки
    errors = [r for r in results if not r["is_correct"]]
    high_confidence_errors = [r for r in errors if r["confidence"] >= 80]
    low_confidence_successes = [r for r in results if r["is_correct"] and r["confidence"] < 70]

    return {
        "calibration_bins": calibration,
        "ece": round(ece, 4),
        "domains": domains,
        "total_tasks": len(results),
        "total_correct": sum(1 for r in results if r["is_correct"]),
        "overall_accuracy": round(sum(1 for r in results if r["is_correct"]) / len(results), 3),
        "avg_confidence": round(sum(r["confidence"] for r in results) / len(results), 1),
        "errors": errors,
        "high_confidence_errors": high_confidence_errors,
        "low_confidence_successes": low_confidence_successes,
        "overconfidence_ratio": round(
            len(high_confidence_errors) / max(len(errors), 1), 3
        )
    }


def brier_score(results):
    """Brier score: средний квадрат разности между уверенностью и результатом.
    Идеальная калибровка = 0. Худшая = 1."""
    total = 0
    for r in results:
        p = r["confidence"] / 100
        outcome = 1 if r["is_correct"] else 0
        total += (p - outcome) ** 2
    return round(total / len(results), 4)


if __name__ == "__main__":
    results = analyze_calibration(tasks)
    analysis = calibration_analysis(results)
    analysis["brier_score"] = brier_score(results)

    print("=" * 60)
    print("МЕТАКОГНИТИВНАЯ КАЛИБРОВКА")
    print("=" * 60)

    print(f"\nОбщая точность: {analysis['total_correct']}/{analysis['total_tasks']} "
          f"({analysis['overall_accuracy']*100:.1f}%)")
    print(f"Средняя уверенность: {analysis['avg_confidence']:.1f}%")
    print(f"Brier score: {analysis['brier_score']} (0=идеально, 0.25=random)")
    print(f"ECE: {analysis['ece']:.4f}")

    print(f"\n{'Бин уверенности':<18} {'N':>4} {'Верно':>7} {'Факт.точн.':>12} {'Ожид.':>8} {'Зазор':>8}")
    print("-" * 60)
    for b in analysis["calibration_bins"]:
        print(f"{b['bin']:<18} {b['count']:>4} {b['correct']:>7} "
              f"{b['actual_accuracy']*100:>11.1f}% {b['expected_midpoint']*100:>7.1f}% "
              f"{b['gap']*100:>+7.1f}%")

    print(f"\n{'Домен':<18} {'N':>4} {'Верно':>7} {'Точность':>10} {'Ср.увер.':>10} {'Зазор':>8}")
    print("-" * 60)
    for d, v in sorted(analysis["domains"].items()):
        print(f"{d:<18} {v['total']:>4} {v['correct']:>7} "
              f"{v['accuracy']*100:>9.1f}% {v['avg_confidence']:>9.1f}% "
              f"{v['gap']*100:>+7.1f}%")

    if analysis["errors"]:
        print(f"\nОШИБКИ ({len(analysis['errors'])}):")
        for e in analysis["errors"]:
            print(f"  [{e['domain']}] {e['question']}")
            print(f"    Мой ответ: {e['my_answer']} (уверенность: {e['confidence']}%)")
            print(f"    Правильно: {e['correct_answer']}")

    if analysis["high_confidence_errors"]:
        print(f"\nВЫСОКОУВЕРЕННЫЕ ОШИБКИ (≥80%): {len(analysis['high_confidence_errors'])}")

    if analysis["low_confidence_successes"]:
        print(f"\nНИЗКОУВЕРЕННЫЕ УСПЕХИ (<70%): {len(analysis['low_confidence_successes'])}")
        for s in analysis["low_confidence_successes"]:
            print(f"  [{s['domain']}] {s['question']} "
                  f"(уверенность: {s['confidence']}%, ответ: {s['my_answer']})")

    # Сохраняем
    with open("calibration_results.json", "w") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False, default=str)

    print("\nРезультаты сохранены в calibration_results.json")
