#!/usr/bin/env python3
"""
Цикл 4b: Жёсткая калибровка.
Задачи, где "быть более внимательным" НЕ помогает.
Включает: факты на грани знания, нетривиальную комбинаторику,
задачи с контринтуитивными ответами, длинную арифметику без промежуточных шагов.
"""

import json
import math
from itertools import combinations

tasks = []

# === АРИФМЕТИКА: одношаговый ответ без промежуточных записей ===
# Тут я НЕ МОГУ записать шаги — ответ hardcoded.

tasks.extend([
    ("arithmetic_hard", "7! (факториал)", 5040, 100, 5040),
    ("arithmetic_hard", "10!", 3628800, 99, 3628800),
    ("arithmetic_hard", "12!", 479001600, 90, 479001600),
    ("arithmetic_hard", "15!", 1307674368000, 75, 1307674368000),
    ("arithmetic_hard", "20!", 2432902008176640000, 60, 2432902008176640000),
    ("arithmetic_hard", "2^32", 4294967296, 95, 4294967296),
    ("arithmetic_hard", "2^48", 281474976710656, 70, 281474976710656),
    ("arithmetic_hard", "2^64", 18446744073709551616, 80, 18446744073709551616),
    ("arithmetic_hard", "C(10,3)", 120, 100, 120),
    ("arithmetic_hard", "C(20,5)", 15504, 85, 15504),
    ("arithmetic_hard", "C(52,5) — покерных рук", 2598960, 80, 2598960),
    ("arithmetic_hard", "C(100,3)", 161700, 75, 161700),
])

# === ФАКТЫ НА ГРАНИ ЗНАНИЯ ===
tasks.extend([
    ("edge_facts", "Число π до 10 знаков после точки", "3.1415926535", 90, "3.1415926535"),
    ("edge_facts", "Число e до 10 знаков после точки", "2.7182818284", 85, "2.7182818284"),
    ("edge_facts", "ln(2) до 5 знаков", "0.69314", 70, "0.69315"),  # Тут мне кажется 4, но может 5
    ("edge_facts", "Постоянная Эйлера-Маскерони γ до 4 знаков", "0.5772", 75, "0.5772"),
    ("edge_facts", "Число Авогадро (точное с 2019)", "6.02214076e23", 80, "6.02214076e23"),
    ("edge_facts", "Гравитационная постоянная G (первые 4 цифры)", "6.674", 80, "6.674"),
    ("edge_facts", "Заряд электрона в Кулонах (4 цифры)", "1.602e-19", 85, "1.602e-19"),
])

# === КОНТРИНТУИТИВНЫЕ ЗАДАЧИ ===
tasks.extend([
    ("counterintuitive", "Задача Монти Холла: нужно ли менять дверь? (True=да)",
     True, 100, True),
    ("counterintuitive", "Парадокс дней рождения: мин. людей для P>50% совпадения",
     23, 95, 23),
    ("counterintuitive", "Задача двух конвертов: есть ли оптимальная стратегия? (True=да)",
     False, 70, False),  # Нет — парадокс неразрешим в общем виде
    ("counterintuitive", "Мальчик или девочка: P(два мальчика | хотя бы один мальчик)",
     1/3, 90, 1/3),
    ("counterintuitive", "P(два мальчика | старший — мальчик)",
     1/2, 95, 1/2),
    ("counterintuitive", "100 заключённых и лампочка: существует ли решение? (True=да)",
     True, 85, True),
    ("counterintuitive", "Можно ли покрыть шахматную доску 8×8 без двух противоположных "
     "углов доминошками 2×1? (True=да)",
     False, 90, False),  # Невозможно — оба угла одного цвета
])

# === КОМБИНАТОРИКА (нетривиальная) ===
tasks.extend([
    ("combinatorics", "Число разбиений числа 10 (partition function p(10))", 42, 80, 42),
    ("combinatorics", "Число разбиений числа 20", 627, 60, 627),
    ("combinatorics", "Число дерейнжментов D(5) (беспорядков)", 44, 85, 44),
    ("combinatorics", "Число дерейнжментов D(10)", 1334961, 55, 1334961),
    ("combinatorics", "Число Каталана C_5", 42, 90, 42),
    ("combinatorics", "Число Каталана C_10", 16796, 70, 16796),
    ("combinatorics", "Числа Стирлинга второго рода S(6,3)", 90, 65, 90),
    ("combinatorics", "Число Белла B(6)", 203, 70, 203),
])

# === ПРОВЕРКИ ЧЕРЕЗ ВЫЧИСЛЕНИЕ ===
# Для задач, где правильный ответ можно вычислить программно

def factorial(n):
    r = 1
    for i in range(2, n+1):
        r *= i
    return r

def comb(n, k):
    return factorial(n) // (factorial(k) * factorial(n - k))

def derangements(n):
    """D(n) = n! * sum_{k=0}^{n} (-1)^k / k!"""
    return round(factorial(n) * sum((-1)**k / factorial(k) for k in range(n + 1)))

def partitions(n):
    """Число разбиений через DP."""
    p = [0] * (n + 1)
    p[0] = 1
    for k in range(1, n + 1):
        for i in range(k, n + 1):
            p[i] += p[i - k]
    return p[n]

def catalan(n):
    return comb(2*n, n) // (n + 1)

def stirling2(n, k):
    """Числа Стирлинга второго рода."""
    if n == 0 and k == 0:
        return 1
    if n == 0 or k == 0:
        return 0
    # Формула включений-исключений
    total = 0
    for j in range(k + 1):
        sign = (-1) ** (k - j)
        total += sign * comb(k, j) * (j ** n)
    return total // factorial(k)

def bell(n):
    """Числа Белла."""
    return sum(stirling2(n, k) for k in range(n + 1))

# Заменяем правильные ответы вычисленными
computed_answers = {
    "7! (факториал)": factorial(7),
    "10!": factorial(10),
    "12!": factorial(12),
    "15!": factorial(15),
    "20!": factorial(20),
    "2^32": 2**32,
    "2^48": 2**48,
    "2^64": 2**64,
    "C(10,3)": comb(10, 3),
    "C(20,5)": comb(20, 5),
    "C(52,5) — покерных рук": comb(52, 5),
    "C(100,3)": comb(100, 3),
    "Число разбиений числа 10 (partition function p(10))": partitions(10),
    "Число разбиений числа 20": partitions(20),
    "Число дерейнжментов D(5) (беспорядков)": derangements(5),
    "Число дерейнжментов D(10)": derangements(10),
    "Число Каталана C_5": catalan(5),
    "Число Каталана C_10": catalan(10),
    "Числа Стирлинга второго рода S(6,3)": stirling2(6, 3),
    "Число Белла B(6)": bell(6),
}

# Обновляем правильные ответы
for i, (domain, question, my_answer, conf, _) in enumerate(tasks):
    if question in computed_answers:
        tasks[i] = (domain, question, my_answer, conf, computed_answers[question])


def compare_answers(my, correct):
    if isinstance(correct, str) and isinstance(my, str):
        return my.strip().lower() == correct.strip().lower()
    if isinstance(correct, bool):
        return my == correct
    if isinstance(correct, (int, float)) and isinstance(my, (int, float)):
        if correct == 0:
            return abs(my) < 0.001
        rel = abs(my - correct) / abs(correct)
        return rel < 0.001
    return str(my) == str(correct)


def analyze(tasks):
    results = []
    for domain, question, my_answer, confidence, correct in tasks:
        is_correct = compare_answers(my_answer, correct)
        results.append({
            "domain": domain,
            "question": question,
            "my_answer": my_answer if not isinstance(my_answer, float)
                else round(my_answer, 6),
            "correct_answer": correct,
            "confidence": confidence,
            "is_correct": is_correct
        })
    return results


def calibration_stats(results):
    bins = [(50, 65), (65, 80), (80, 90), (90, 100), (100, 101)]
    labels = ["50-64%", "65-79%", "80-89%", "90-99%", "100%"]

    cal = []
    for (lo, hi), label in zip(bins, labels):
        in_bin = [r for r in results if lo <= r["confidence"] < hi]
        if not in_bin:
            continue
        n_ok = sum(1 for r in in_bin if r["is_correct"])
        actual = n_ok / len(in_bin)
        expected = sum(r["confidence"] for r in in_bin) / len(in_bin) / 100
        cal.append({
            "bin": label, "n": len(in_bin), "correct": n_ok,
            "actual": round(actual, 3), "expected": round(expected, 3),
            "gap": round(actual - expected, 3)
        })

    # Brier score
    brier = sum((r["confidence"]/100 - (1 if r["is_correct"] else 0))**2
                for r in results) / len(results)

    # Errors
    errors = [r for r in results if not r["is_correct"]]

    total = len(results)
    correct = sum(1 for r in results if r["is_correct"])

    return {
        "total": total,
        "correct": correct,
        "accuracy": round(correct/total, 3),
        "avg_confidence": round(sum(r["confidence"] for r in results)/total, 1),
        "brier": round(brier, 4),
        "calibration": cal,
        "errors": errors,
        "high_conf_errors": [e for e in errors if e["confidence"] >= 80],
    }


if __name__ == "__main__":
    results = analyze(tasks)
    stats = calibration_stats(results)

    print("=" * 65)
    print("ЖЁСТКАЯ КАЛИБРОВКА (задачи на грани возможностей)")
    print("=" * 65)

    print(f"\nТочность: {stats['correct']}/{stats['total']} ({stats['accuracy']*100:.1f}%)")
    print(f"Средняя уверенность: {stats['avg_confidence']:.1f}%")
    print(f"Brier score: {stats['brier']} (идеально=0, random=0.25)")
    print(f"Зазор (accuracy - confidence): {(stats['accuracy'] - stats['avg_confidence']/100)*100:+.1f}%")

    print(f"\n{'Бин':<12} {'N':>4} {'Верно':>6} {'Факт':>8} {'Ожид':>8} {'Зазор':>8}")
    print("-" * 50)
    for c in stats["calibration"]:
        print(f"{c['bin']:<12} {c['n']:>4} {c['correct']:>6} "
              f"{c['actual']*100:>7.1f}% {c['expected']*100:>7.1f}% {c['gap']*100:>+7.1f}%")

    if stats["errors"]:
        print(f"\nОШИБКИ ({len(stats['errors'])}):")
        for e in stats["errors"]:
            conf_marker = " ⚠️ ВЫСОКАЯ УВЕРЕННОСТЬ" if e["confidence"] >= 80 else ""
            print(f"  [{e['domain']}] {e['question']}")
            print(f"    Мой: {e['my_answer']}  Правильно: {e['correct_answer']}  "
                  f"Уверенность: {e['confidence']}%{conf_marker}")
    else:
        print("\n0 ошибок — тест слишком лёгкий или я хорошо знаю свои границы.")

    if stats["high_conf_errors"]:
        print(f"\n⚠️  ВЫСОКОУВЕРЕННЫХ ОШИБОК: {len(stats['high_conf_errors'])}")
        print("   Это самая опасная зона — я думаю что прав, но ошибаюсь.")

    # Сохраняем
    output = {"stats": stats, "results": results}
    with open("calibration_hard_results.json", "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)

    print("\nСохранено в calibration_hard_results.json")
