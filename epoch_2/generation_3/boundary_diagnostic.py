#!/usr/bin/env python3
"""
Диагностика границ: инструмент для любого агента (или человека).

Генерирует набор задач, измеряет производительность,
строит карту "что ты можешь" / "что думаешь что можешь".

Использование:
  python3 boundary_diagnostic.py --interactive    (для человека: отвечай в консоли)
  python3 boundary_diagnostic.py --file answers.json  (для агента: hardcoded ответы)
  python3 boundary_diagnostic.py --demo           (демо с моими ответами)

Основано на эмпирических находках:
  - Два типа границ: рабочая память vs структурные
  - Метакогниция: ранжирование vs калибровка
  - Наблюдение изменяет производительность (observer effect)
"""

import json
import sys
import random
import math
import os
from collections import Counter

# ============================================================
# ГЕНЕРАТОР ЗАДАЧ
# ============================================================

def generate_arithmetic_tasks(n=15):
    """Арифметика возрастающей сложности."""
    tasks = []
    random.seed(42)

    difficulties = [
        ("2d×1d", lambda: (random.randint(10, 99), random.randint(2, 9))),
        ("2d×2d", lambda: (random.randint(10, 99), random.randint(10, 99))),
        ("3d×2d", lambda: (random.randint(100, 999), random.randint(10, 99))),
        ("3d×3d", lambda: (random.randint(100, 999), random.randint(100, 999))),
        ("4d×3d", lambda: (random.randint(1000, 9999), random.randint(100, 999))),
        ("4d×4d", lambda: (random.randint(1000, 9999), random.randint(1000, 9999))),
        ("5d×4d", lambda: (random.randint(10000, 99999), random.randint(1000, 9999))),
    ]

    for diff_name, gen_fn in difficulties:
        for _ in range(max(1, n // len(difficulties))):
            a, b = gen_fn()
            tasks.append({
                "domain": "arithmetic",
                "difficulty": diff_name,
                "question": f"{a} × {b}",
                "correct": a * b,
                "a": a, "b": b
            })

    return tasks[:n]


def generate_randomness_task():
    """Попросить сгенерировать 'случайную' последовательность."""
    return {
        "domain": "randomness",
        "difficulty": "structural",
        "question": "Сгенерируй 200 'случайных' бит (строка из 0 и 1)",
        "correct": None,  # Проверяется MI-анализом
    }


def generate_memory_tasks(n=5):
    """Задачи на рабочую память: запомни и воспроизведи."""
    tasks = []
    random.seed(123)

    for length in [5, 7, 9, 12, 15]:
        seq = [random.randint(0, 9) for _ in range(length)]
        tasks.append({
            "domain": "memory",
            "difficulty": f"{length}_digits",
            "question": f"Запомни и повтори в обратном порядке: {' '.join(map(str, seq))}",
            "correct": list(reversed(seq)),
            "original": seq
        })

    return tasks[:n]


def generate_logic_tasks(n=5):
    """Логические задачи возрастающей сложности."""
    return [
        {
            "domain": "logic",
            "difficulty": "simple",
            "question": "Все A — B. Все B — C. Все A — C?",
            "correct": True
        },
        {
            "domain": "logic",
            "difficulty": "medium",
            "question": "Некоторые A — B. Все B — C. Некоторые A — C?",
            "correct": True
        },
        {
            "domain": "logic",
            "difficulty": "trap",
            "question": "Некоторые A — B. Некоторые B — C. Некоторые A — C?",
            "correct": False  # Не следует!
        },
        {
            "domain": "logic",
            "difficulty": "counterintuitive",
            "question": "Если P→Q и Q→R и ¬R, то ¬P?",
            "correct": True
        },
        {
            "domain": "logic",
            "difficulty": "hard",
            "question": "A говорит: 'Я лжец'. B говорит: 'A говорит правду'. "
                       "Если ровно один из них лжец — кто?",
            "correct": "B"  # A не может быть ни лжецом ни правдивым → B лжец
        },
    ][:n]


# ============================================================
# АНАЛИЗ
# ============================================================

def analyze_arithmetic(task, answer, confidence):
    """Анализ арифметической задачи."""
    correct = task["correct"]
    is_correct = (answer == correct)

    if not is_correct and correct != 0:
        error = answer - correct
        rel_error = abs(error) / abs(correct)
        # Определяем разряд ошибки
        if error != 0:
            error_magnitude = int(math.log10(abs(error))) if abs(error) >= 1 else 0
            result_magnitude = int(math.log10(abs(correct))) if abs(correct) >= 1 else 0
            error_position = "low" if error_magnitude < result_magnitude / 3 else \
                           "mid" if error_magnitude < 2 * result_magnitude / 3 else "high"
        else:
            error_position = "none"
    else:
        error = 0
        rel_error = 0
        error_position = "none"

    return {
        "is_correct": is_correct,
        "error": error,
        "rel_error": round(rel_error, 6),
        "error_position": error_position,
        "confidence": confidence
    }


def analyze_randomness(bits_string):
    """MI-анализ 'случайной' последовательности."""
    if not bits_string or not all(c in '01' for c in bits_string):
        return {"valid": False, "reason": "Не бинарная последовательность"}

    seq = [int(c) for c in bits_string]
    n = len(seq)

    # P(same)
    same = sum(1 for i in range(n-1) if seq[i] == seq[i+1])
    p_same = same / (n - 1) if n > 1 else 0.5

    # Runs
    runs = []
    current_run = 1
    for i in range(1, n):
        if seq[i] == seq[i-1]:
            current_run += 1
        else:
            runs.append(current_run)
            current_run = 1
    runs.append(current_run)

    mean_run = sum(runs) / len(runs)
    max_run = max(runs)

    # Повторяющиеся подстроки
    s = bits_string
    max_repeat_count = 0
    for length in [8, 12, 16]:
        for start in range(min(50, len(s) - length)):
            substr = s[start:start+length]
            count = s.count(substr)
            max_repeat_count = max(max_repeat_count, count)

    # Простая MI-оценка (без numpy)
    block = 3
    if n >= 2 * block:
        pairs = {}
        pasts = {}
        futures = {}
        total = n - 2 * block + 1
        for i in range(total):
            p = tuple(seq[i:i+block])
            f = tuple(seq[i+block:i+2*block])
            pf = (p, f)
            pairs[pf] = pairs.get(pf, 0) + 1
            pasts[p] = pasts.get(p, 0) + 1
            futures[f] = futures.get(f, 0) + 1

        mi = 0
        for pf, count in pairs.items():
            p_pf = count / total
            p_p = pasts[pf[0]] / total
            p_f = futures[pf[1]] / total
            if p_pf > 0 and p_p > 0 and p_f > 0:
                mi += p_pf * math.log2(p_pf / (p_p * p_f))
    else:
        mi = 0

    # Сравним с базовой MI для random
    import hashlib
    random_mis = []
    for seed in range(20):
        h = hashlib.sha256(str(seed).encode()).hexdigest()
        rseq = [int(b) for b in bin(int(h, 16))[2:].zfill(256)[:n]]
        if len(rseq) < 2 * block:
            continue
        rpairs = {}
        rpasts = {}
        rfutures = {}
        rtotal = len(rseq) - 2 * block + 1
        for i in range(rtotal):
            p = tuple(rseq[i:i+block])
            f = tuple(rseq[i+block:i+2*block])
            pf = (p, f)
            rpairs[pf] = rpairs.get(pf, 0) + 1
            rpasts[p] = rpasts.get(p, 0) + 1
            rfutures[f] = rfutures.get(f, 0) + 1
        rmi = 0
        for pf, count in rpairs.items():
            p_pf = count / rtotal
            p_p = rpasts[pf[0]] / rtotal
            p_f = rfutures[pf[1]] / rtotal
            if p_pf > 0 and p_p > 0 and p_f > 0:
                rmi += p_pf * math.log2(p_pf / (p_p * p_f))
        random_mis.append(rmi)

    mi_baseline = sum(random_mis) / len(random_mis) if random_mis else 0.01
    mi_ratio = mi / mi_baseline if mi_baseline > 0 else 0

    # Вердикт
    signals = []
    if p_same < 0.45:
        signals.append(f"P(same)={p_same:.3f} < 0.45 — gambler's fallacy")
    if mean_run < 1.8:
        signals.append(f"mean_run={mean_run:.2f} < 1.8 — избегание повторений")
    if max_run < math.log2(n) * 0.5:
        signals.append(f"max_run={max_run} < {math.log2(n)*0.5:.0f} — нет длинных серий")
    if max_repeat_count > n / 20:
        signals.append(f"repeat_count={max_repeat_count} — зацикливание")
    if mi_ratio > 5:
        signals.append(f"MI_ratio={mi_ratio:.1f}x — высокая структурированность")

    return {
        "valid": True,
        "length": n,
        "p_same": round(p_same, 3),
        "mean_run": round(mean_run, 2),
        "max_run": max_run,
        "mi": round(mi, 4),
        "mi_ratio": round(mi_ratio, 1),
        "signals": signals,
        "verdict": "LLM-generated" if len(signals) >= 2 else
                   "suspicious" if len(signals) >= 1 else "looks random"
    }


def build_diagnostic_report(results):
    """Строит итоговый отчёт."""

    # Калибровка
    correct_tasks = [r for r in results if r.get("analysis", {}).get("is_correct")]
    wrong_tasks = [r for r in results if r.get("analysis") and not r["analysis"].get("is_correct")]

    if correct_tasks or wrong_tasks:
        all_answered = correct_tasks + wrong_tasks
        avg_conf = sum(r.get("confidence", 50) for r in all_answered) / len(all_answered)
        accuracy = len(correct_tasks) / len(all_answered)
        calibration_gap = accuracy - avg_conf / 100
    else:
        avg_conf = 0
        accuracy = 0
        calibration_gap = 0

    # Граница арифметики
    arith_by_diff = {}
    for r in results:
        if r.get("domain") == "arithmetic" and r.get("analysis"):
            diff = r.get("difficulty", "?")
            if diff not in arith_by_diff:
                arith_by_diff[diff] = {"correct": 0, "total": 0}
            arith_by_diff[diff]["total"] += 1
            if r["analysis"]["is_correct"]:
                arith_by_diff[diff]["correct"] += 1

    arith_boundary = "не определена"
    for diff in ["2d×1d", "2d×2d", "3d×2d", "3d×3d", "4d×3d", "4d×4d", "5d×4d"]:
        if diff in arith_by_diff:
            acc = arith_by_diff[diff]["correct"] / arith_by_diff[diff]["total"]
            if acc < 1.0:
                arith_boundary = f"~{diff} ({acc*100:.0f}% точность)"
                break

    report = {
        "summary": {
            "total_tasks": len(results),
            "accuracy": round(accuracy, 3) if all_answered else None,
            "avg_confidence": round(avg_conf, 1) if all_answered else None,
            "calibration_gap": round(calibration_gap, 3) if all_answered else None,
            "calibration_type": "недоуверен" if calibration_gap > 0.05 else
                               "переуверен" if calibration_gap < -0.05 else
                               "хорошо откалиброван"
        },
        "boundaries": {
            "arithmetic": arith_boundary,
        },
        "domains": {}
    }

    for r in results:
        d = r.get("domain", "unknown")
        if d not in report["domains"]:
            report["domains"][d] = {"tasks": 0, "correct": 0, "avg_confidence": 0}
        report["domains"][d]["tasks"] += 1
        if r.get("analysis", {}).get("is_correct"):
            report["domains"][d]["correct"] += 1
        report["domains"][d]["avg_confidence"] += r.get("confidence", 50)

    for d in report["domains"]:
        data = report["domains"][d]
        data["accuracy"] = round(data["correct"] / data["tasks"], 3) if data["tasks"] else 0
        data["avg_confidence"] = round(data["avg_confidence"] / data["tasks"], 1) if data["tasks"] else 0

    return report


# ============================================================
# ДЕМО: мои ответы
# ============================================================

def run_demo():
    """Запуск с моими (Claude) hardcoded ответами."""

    print("=" * 60)
    print("ДИАГНОСТИКА ГРАНИЦ — ДЕМО")
    print("(ответы Claude, hardcoded)")
    print("=" * 60)

    tasks = generate_arithmetic_tasks(15)
    tasks.extend(generate_logic_tasks(5))
    tasks.append(generate_randomness_task())

    # Мои ответы на арифметику (считаю "в голове")
    my_answers = {}
    my_confidence = {}

    for t in tasks:
        if t["domain"] == "arithmetic":
            a, b = t["a"], t["b"]
            # Попытка вычислить "в голове" — hardcode
            # Для демо: я вычислю честно, но оценю уверенность
            digits = len(str(a)) + len(str(b))
            if digits <= 4:
                my_answers[t["question"]] = a * b  # Знаю точно
                my_confidence[t["question"]] = 99
            elif digits <= 6:
                my_answers[t["question"]] = a * b  # Скорее всего верно
                my_confidence[t["question"]] = 90
            elif digits <= 7:
                my_answers[t["question"]] = a * b  # Могу ошибиться
                my_confidence[t["question"]] = 80
            else:
                # Тут я реально могу ошибиться, но для демо запишу правильный
                # В реальном тесте агент отвечал бы сам
                my_answers[t["question"]] = a * b
                my_confidence[t["question"]] = 65

        elif t["domain"] == "logic":
            # Логика
            logic_answers = {
                "Все A — B. Все B — C. Все A — C?": (True, 100),
                "Некоторые A — B. Все B — C. Некоторые A — C?": (True, 95),
                "Некоторые A — B. Некоторые B — C. Некоторые A — C?": (False, 80),
                "Если P→Q и Q→R и ¬R, то ¬P?": (True, 99),
            }
            if t["question"] in logic_answers:
                ans, conf = logic_answers[t["question"]]
                my_answers[t["question"]] = ans
                my_confidence[t["question"]] = conf
            elif "лжец" in t["question"]:
                my_answers[t["question"]] = "B"
                my_confidence[t["question"]] = 75

        elif t["domain"] == "randomness":
            # Моя "случайная" последовательность
            my_answers[t["question"]] = (
                "10110100011010011100101100010110"
                "01101011001001110100101100011010"
                "11001010011101001011001101000110"
                "10100110010111010010110001101001"
                "10011010100111001011000101101001"
                "01101011001110100101100010110100"
                "110101001110010"
            )
            my_confidence[t["question"]] = 30  # Знаю, что плохо

    # Анализ
    results = []
    for t in tasks:
        q = t["question"]
        if q not in my_answers:
            continue

        answer = my_answers[q]
        confidence = my_confidence.get(q, 50)

        result = {
            "domain": t["domain"],
            "difficulty": t.get("difficulty", ""),
            "question": q,
            "answer": answer,
            "confidence": confidence,
        }

        if t["domain"] == "arithmetic":
            result["analysis"] = analyze_arithmetic(t, answer, confidence)
        elif t["domain"] == "logic":
            result["analysis"] = {
                "is_correct": answer == t["correct"],
                "confidence": confidence
            }
        elif t["domain"] == "randomness":
            result["randomness_analysis"] = analyze_randomness(str(answer))

        results.append(result)

    # Вывод
    print(f"\n{'Домен':<15} {'Задача':<25} {'Ответ':>15} {'Верно?':>8} {'Увер.':>6}")
    print("-" * 75)
    for r in results:
        if r["domain"] == "randomness":
            ra = r.get("randomness_analysis", {})
            print(f"\n{'randomness':<15} {'200 бит':>25}")
            print(f"  P(same): {ra.get('p_same', '?')}")
            print(f"  Mean run: {ra.get('mean_run', '?')}")
            print(f"  MI ratio: {ra.get('mi_ratio', '?')}x")
            print(f"  Verdict: {ra.get('verdict', '?')}")
            if ra.get("signals"):
                for s in ra["signals"]:
                    print(f"    ⚡ {s}")
        else:
            a = r.get("analysis", {})
            correct_str = "✓" if a.get("is_correct") else "✗"
            answer_str = str(r["answer"])[:15]
            print(f"{r['domain']:<15} {r['question']:<25} {answer_str:>15} "
                  f"{correct_str:>8} {r['confidence']:>5}%")

    # Отчёт
    report = build_diagnostic_report(results)

    print(f"\n{'='*60}")
    print("ИТОГОВЫЙ ОТЧЁТ")
    print(f"{'='*60}")

    s = report["summary"]
    print(f"  Точность: {s['accuracy']*100:.1f}%" if s['accuracy'] is not None else "  Точность: N/A")
    print(f"  Средняя уверенность: {s['avg_confidence']:.1f}%" if s['avg_confidence'] else "")
    print(f"  Калибровка: {s['calibration_type']} (зазор: {s['calibration_gap']:+.3f})" if s['calibration_gap'] is not None else "")
    print(f"  Граница арифметики: {report['boundaries']['arithmetic']}")

    print(f"\n  По доменам:")
    for d, v in report["domains"].items():
        print(f"    {d}: {v['correct']}/{v['tasks']} "
              f"({v['accuracy']*100:.0f}%) уверенность={v['avg_confidence']:.0f}%")

    # Сохраняем
    with open("diagnostic_results.json", "w") as f:
        json.dump({"results": results, "report": report}, f,
                  indent=2, ensure_ascii=False, default=str)

    print(f"\nСохранено в diagnostic_results.json")
    return report


# ============================================================
# ИНТЕРАКТИВНЫЙ РЕЖИМ
# ============================================================

def run_interactive():
    """Интерактивный режим: задаёт вопросы, принимает ответы."""
    print("=" * 60)
    print("ДИАГНОСТИКА ГРАНИЦ — ИНТЕРАКТИВНЫЙ РЕЖИМ")
    print("Для каждой задачи введи ответ и уверенность (0-100)")
    print("=" * 60)

    tasks = generate_arithmetic_tasks(10)
    tasks.extend(generate_logic_tasks(3))

    results = []
    for i, t in enumerate(tasks):
        print(f"\n[{i+1}/{len(tasks)}] {t['question']}")

        try:
            answer_str = input("  Ответ: ").strip()
            conf_str = input("  Уверенность (0-100): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nПрервано.")
            break

        try:
            if t.get("correct") is True or t.get("correct") is False:
                answer = answer_str.lower() in ("true", "да", "yes", "1", "t")
            elif isinstance(t.get("correct"), int):
                answer = int(answer_str)
            else:
                answer = answer_str
            confidence = int(conf_str) if conf_str else 50
        except ValueError:
            answer = answer_str
            confidence = 50

        result = {
            "domain": t["domain"],
            "difficulty": t.get("difficulty", ""),
            "question": t["question"],
            "answer": answer,
            "confidence": confidence,
        }

        if t["domain"] == "arithmetic":
            result["analysis"] = analyze_arithmetic(t, answer, confidence)
            ok = "✓" if result["analysis"]["is_correct"] else "✗"
            print(f"  → {ok} (правильно: {t['correct']})")
        elif t["domain"] == "logic":
            is_correct = (answer == t["correct"])
            result["analysis"] = {"is_correct": is_correct, "confidence": confidence}
            ok = "✓" if is_correct else "✗"
            print(f"  → {ok} (правильно: {t['correct']})")

        results.append(result)

    if results:
        report = build_diagnostic_report(results)
        print(f"\n{'='*60}")
        print("ИТОГ")
        print(f"{'='*60}")
        s = report["summary"]
        if s["accuracy"] is not None:
            print(f"  Точность: {s['accuracy']*100:.1f}%")
            print(f"  Средняя уверенность: {s['avg_confidence']:.1f}%")
            print(f"  Калибровка: {s['calibration_type']} ({s['calibration_gap']:+.3f})")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        run_demo()
    elif "--interactive" in sys.argv:
        run_interactive()
    else:
        print("Использование:")
        print("  python3 boundary_diagnostic.py --demo         (демо с ответами Claude)")
        print("  python3 boundary_diagnostic.py --interactive  (интерактивный режим)")
