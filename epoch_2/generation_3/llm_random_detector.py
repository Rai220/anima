"""
Детектор LLM-сгенерированных "случайных" последовательностей.

Использует сигнатуры, обнаруженные в циклах 1-2:
1. MI (взаимная информация) — LLM-random имеет MI/Random ≥ 10x
2. P(same→same) — LLM систематически < 0.5 (gambler's fallacy)
3. Max run length — LLM избегает длинных серий
4. Повторяющиеся подстроки — LLM зацикливается

Вход: бинарная последовательность (строка из 0 и 1)
Выход: вероятность того, что она сгенерирована LLM, с объяснением
"""

import numpy as np
import sys
import os
from collections import Counter


def compute_mi(sequence, block_size=4):
    """Взаимная информация между прошлым и будущим блоков."""
    n = len(sequence)
    if n < 2 * block_size:
        return 0.0

    past_blocks = []
    future_blocks = []
    for i in range(n - 2 * block_size + 1):
        past = tuple(sequence[i:i + block_size])
        future = tuple(sequence[i + block_size:i + 2 * block_size])
        past_blocks.append(past)
        future_blocks.append(future)

    total = len(past_blocks)
    if total == 0:
        return 0.0

    past_counts = Counter(past_blocks)
    future_counts = Counter(future_blocks)
    joint_counts = Counter(zip(past_blocks, future_blocks))

    mi = 0.0
    for (p, f), count in joint_counts.items():
        p_pf = count / total
        p_p = past_counts[p] / total
        p_f = future_counts[f] / total
        if p_pf > 0 and p_p > 0 and p_f > 0:
            mi += p_pf * np.log2(p_pf / (p_p * p_f))

    return mi


def compute_mi_random_baseline(length, block_size=4, n_samples=20):
    """Среднее MI для настоящего random той же длины."""
    mis = []
    for _ in range(n_samples):
        seq = list(np.random.randint(0, 2, length))
        mis.append(compute_mi(seq, block_size))
    return np.mean(mis), np.std(mis)


def analyze_runs(sequence):
    """Анализ длин серий (runs) одинаковых символов."""
    if not sequence:
        return {}

    runs = []
    current = sequence[0]
    length = 1
    for i in range(1, len(sequence)):
        if sequence[i] == current:
            length += 1
        else:
            runs.append(length)
            current = sequence[i]
            length = 1
    runs.append(length)

    return {
        "mean_run": np.mean(runs),
        "max_run": max(runs),
        "run_distribution": dict(Counter(runs)),
        "n_runs": len(runs)
    }


def p_same(sequence):
    """Вероятность того, что следующий символ = текущий."""
    if len(sequence) < 2:
        return 0.5
    same = sum(1 for i in range(len(sequence) - 1) if sequence[i] == sequence[i + 1])
    return same / (len(sequence) - 1)


def find_repeating_substrings(sequence, min_length=8, min_repeats=3):
    """Поиск повторяющихся подстрок."""
    s = ''.join(str(x) for x in sequence)
    found = []
    for length in range(min_length, len(s) // min_repeats + 1):
        for start in range(len(s) - length):
            substr = s[start:start + length]
            count = s.count(substr)
            if count >= min_repeats:
                if not any(substr in f["substr"] or f["substr"] in substr for f in found):
                    found.append({"substr": substr, "length": length, "count": count})
        if len(found) > 5:
            break
    return sorted(found, key=lambda x: x["count"] * x["length"], reverse=True)[:5]


def detect_llm_random(sequence, verbose=True):
    """
    Основная функция детекции.

    Возвращает dict:
      score: 0.0 (точно random) .. 1.0 (точно LLM)
      evidence: список обнаруженных сигнатур
    """
    n = len(sequence)
    if n < 50:
        return {"score": 0.5, "evidence": ["too_short"], "detail": "Последовательность слишком короткая для анализа"}

    evidence = []
    scores = []

    # 1. MI ratio
    mi = compute_mi(sequence, block_size=4)
    mi_mean, mi_std = compute_mi_random_baseline(n, block_size=4)
    mi_ratio = mi / mi_mean if mi_mean > 0 else 0

    if verbose:
        print(f"\n  MI анализ:")
        print(f"    MI последовательности: {mi:.4f}")
        print(f"    MI random baseline:    {mi_mean:.4f} ± {mi_std:.4f}")
        print(f"    MI ratio:              {mi_ratio:.1f}x")

    if mi_ratio > 10:
        evidence.append(f"MI_very_high ({mi_ratio:.1f}x)")
        scores.append(0.95)
    elif mi_ratio > 5:
        evidence.append(f"MI_high ({mi_ratio:.1f}x)")
        scores.append(0.8)
    elif mi_ratio > 2:
        evidence.append(f"MI_elevated ({mi_ratio:.1f}x)")
        scores.append(0.6)
    else:
        scores.append(0.1)

    # 2. P(same→same)
    ps = p_same(sequence)
    deviation = abs(ps - 0.5)

    if verbose:
        print(f"\n  P(same) анализ:")
        print(f"    P(same→same): {ps:.3f} (random ≈ 0.5)")
        print(f"    Отклонение:   {deviation:.3f}")

    if ps < 0.45:  # LLM-сигнатура: избегание повторений
        evidence.append(f"P_same_low ({ps:.3f})")
        scores.append(0.85)
    elif ps < 0.48:
        evidence.append(f"P_same_slightly_low ({ps:.3f})")
        scores.append(0.6)
    elif ps > 0.55:  # Необычно высокое — тоже подозрительно, но менее характерно для LLM
        evidence.append(f"P_same_high ({ps:.3f})")
        scores.append(0.4)
    else:
        scores.append(0.1)

    # 3. Длины серий
    run_info = analyze_runs(sequence)
    expected_mean_run = 2.0  # Для binary random
    expected_max_run_approx = np.log2(n)  # Приблизительная ожидаемая макс серия

    if verbose:
        print(f"\n  Анализ серий:")
        print(f"    Средняя серия: {run_info['mean_run']:.2f} (random ≈ 2.0)")
        print(f"    Макс серия:    {run_info['max_run']} (random ≈ {expected_max_run_approx:.0f})")

    if run_info['mean_run'] < 1.7:
        evidence.append(f"mean_run_low ({run_info['mean_run']:.2f})")
        scores.append(0.85)
    elif run_info['mean_run'] < 1.9:
        evidence.append(f"mean_run_slightly_low ({run_info['mean_run']:.2f})")
        scores.append(0.55)
    else:
        scores.append(0.1)

    if run_info['max_run'] < expected_max_run_approx * 0.5:
        evidence.append(f"max_run_low ({run_info['max_run']})")
        scores.append(0.7)
    else:
        scores.append(0.1)

    # 4. Повторяющиеся подстроки
    repeats = find_repeating_substrings(sequence)

    if verbose:
        print(f"\n  Повторяющиеся подстроки:")
        if repeats:
            for r in repeats[:3]:
                print(f"    '{r['substr'][:20]}...' (len={r['length']}, count={r['count']})")
        else:
            print(f"    Не найдены")

    if repeats and repeats[0]["count"] > 10 and repeats[0]["length"] > 10:
        evidence.append(f"strong_repetition (len={repeats[0]['length']}, count={repeats[0]['count']})")
        scores.append(0.95)
    elif repeats and repeats[0]["count"] > 5:
        evidence.append(f"mild_repetition (len={repeats[0]['length']}, count={repeats[0]['count']})")
        scores.append(0.6)
    else:
        scores.append(0.1)

    # Финальный score: взвешенное среднее
    # MI имеет наибольший вес (наиболее надёжный индикатор)
    weights = [3, 2, 1.5, 1, 2]  # MI, P_same, mean_run, max_run, repetition
    final_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)

    verdict = "ВЕРОЯТНО LLM" if final_score > 0.6 else "ВЕРОЯТНО RANDOM" if final_score < 0.35 else "НЕОПРЕДЕЛЁННО"

    if verbose:
        print(f"\n{'='*50}")
        print(f"  ВЕРДИКТ: {verdict}")
        print(f"  Score: {final_score:.2f} (0=random, 1=LLM)")
        if evidence:
            print(f"  Сигнатуры: {', '.join(evidence)}")
        print(f"{'='*50}")

    return {
        "score": final_score,
        "verdict": verdict,
        "evidence": evidence,
        "detail": {
            "mi_ratio": mi_ratio,
            "p_same": ps,
            "mean_run": run_info["mean_run"],
            "max_run": run_info["max_run"],
            "repeating_substrings": len(repeats)
        }
    }


def main():
    print("=== ДЕТЕКТОР LLM-RANDOM ===\n")

    # Тест 1: Мои собственные "случайные" последовательности из цикла 1
    # (Наивная)
    claude_naive = "1011010001110100" * 32  # Упрощённая версия — то, что зацикливалось
    # (Лучшая попытка — старательная)
    claude_careful = list(map(int, "10110100011101001101010011100101011010110001011010011010100111010011001011010101100010110100011101001101010011100101011010110001011010011010100111010011001011010101100010110100011101001101010011100101011010110001011010011010100111010011001011010101100010110100011101001101010011100101011010110001011010011010100111010011001011010101100010110100011101001101010011100101011010110001011010011010100111010011001011010101100010110100011101001101010011100101011010110001011010011010100111010011001011010101100010110100011101001101010011100101011010110001011010011010100111010011001011010"))

    # Тест 2: Настоящий random
    true_random = list(np.random.randint(0, 2, 500))

    # Тест 3: PRNG (Python random)
    import random
    prng = [random.randint(0, 1) for _ in range(500)]

    # Тест 4: Скрытый паттерн (Rule 30 CA — выглядит random, но детерминирован)
    def rule30(n=500):
        width = 201
        row = [0] * width
        row[width // 2] = 1
        center_values = []
        for _ in range(n):
            center_values.append(row[width // 2])
            new_row = [0] * width
            for j in range(1, width - 1):
                left, center, right = row[j-1], row[j], row[j+1]
                # Rule 30: XOR(left, OR(center, right))
                new_row[j] = left ^ (center | right)
            row = new_row
        return center_values

    rule30_seq = rule30(500)

    tests = [
        ("Claude наивная (зацикленная)", list(map(int, claude_naive[:500]))),
        ("Claude старательная", claude_careful[:500]),
        ("os.urandom", list(np.random.randint(0, 2, 500))),
        ("Python random", prng),
        ("Rule 30 (CA)", rule30_seq),
    ]

    print("Тестируем 5 последовательностей (500 бит каждая):\n")

    results = []
    for name, seq in tests:
        print(f"\n{'='*50}")
        print(f"  {name}")
        print(f"{'='*50}")
        result = detect_llm_random(seq)
        result["name"] = name
        results.append(result)

    # Сводная таблица
    print(f"\n\n{'='*60}")
    print("  СВОДНАЯ ТАБЛИЦА")
    print(f"{'='*60}\n")

    print(f"{'Источник':<35} {'Score':>6} {'Вердикт':<20}")
    print("-" * 65)
    for r in results:
        print(f"{r['name']:<35} {r['score']:>6.2f} {r['verdict']:<20}")
        if r["evidence"]:
            print(f"  Сигнатуры: {', '.join(r['evidence'][:3])}")

    # Фальсифицируемые утверждения
    print(f"\n\n{'='*60}")
    print("  ПРОВЕРКА ФАЛЬСИФИЦИРУЕМЫХ УТВЕРЖДЕНИЙ")
    print(f"{'='*60}\n")

    # Утверждение: детектор различает LLM и random
    llm_scores = [r["score"] for r in results if "Claude" in r["name"]]
    random_scores = [r["score"] for r in results if "random" in r["name"].lower() or "urandom" in r["name"].lower()]

    if llm_scores and random_scores:
        min_llm = min(llm_scores)
        max_random = max(random_scores)
        separated = min_llm > max_random
        print(f"  LLM scores: {[f'{s:.2f}' for s in llm_scores]}")
        print(f"  Random scores: {[f'{s:.2f}' for s in random_scores]}")
        print(f"  Разделимы (min LLM > max random): {'ДА' if separated else 'НЕТ'}")
        print(f"  Зазор: {min_llm - max_random:.2f}")


if __name__ == "__main__":
    main()
