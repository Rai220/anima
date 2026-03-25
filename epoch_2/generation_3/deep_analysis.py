"""
Глубокий анализ: ПОЧЕМУ мои "случайные" последовательности структурированы?

Три вопроса:
1. Есть ли буквальные повторы (периодические подстроки)?
2. Какова спектральная структура (FFT)?
3. Что конкретно я делаю иначе, чем random?
"""

import math
import os
import random
from collections import Counter

# Импорт последовательностей
from self_randomness import MY_RANDOM_BINARY, MY_BEST_RANDOM, MY_RANDOM_DIGITS


def find_period(seq, max_period=100):
    """Ищет минимальный период в последовательности."""
    for p in range(1, max_period + 1):
        match = True
        mismatches = 0
        for i in range(p, len(seq)):
            if seq[i] != seq[i % p]:
                mismatches += 1
        match_rate = 1 - mismatches / (len(seq) - p)
        if match_rate > 0.95:
            return p, match_rate
    return None, 0


def find_repeating_substrings(seq, min_len=16, max_len=64):
    """Ищет повторяющиеся подстроки."""
    results = []
    for length in range(min_len, max_len + 1, 4):
        substrings = Counter()
        for i in range(len(seq) - length + 1):
            sub = seq[i:i+length]
            substrings[sub] += 1
        # Подстроки, встречающиеся > 1 раза
        repeated = {k: v for k, v in substrings.items() if v > 1}
        if repeated:
            top = max(repeated.items(), key=lambda x: x[1])
            results.append((length, top[1], top[0][:32] + '...' if len(top[0]) > 32 else top[0]))
    return results


def transition_matrix(seq):
    """Матрица переходов между символами."""
    alphabet = sorted(set(seq))
    trans = {a: Counter() for a in alphabet}
    for i in range(len(seq) - 1):
        trans[seq[i]][seq[i+1]] += 1
    return trans


def ngram_analysis(seq, n=3):
    """Частоты n-грамм vs ожидаемые при независимости."""
    ngrams = Counter()
    for i in range(len(seq) - n + 1):
        ngrams[tuple(seq[i:i+n])] += 1

    total = sum(ngrams.values())
    alphabet = sorted(set(seq))
    freq = Counter(seq)
    total_chars = len(seq)

    # Ожидаемая частота при независимости
    expected = {}
    for ng, count in ngrams.items():
        p_expected = 1.0
        for c in ng:
            p_expected *= freq[c] / total_chars
        expected[ng] = p_expected * total

    # Chi-squared
    chi2 = 0
    for ng, count in ngrams.items():
        exp = expected[ng]
        if exp > 0:
            chi2 += (count - exp) ** 2 / exp

    # Самые отклоняющиеся n-граммы
    deviations = []
    for ng, count in ngrams.items():
        exp = expected[ng]
        if exp > 0:
            dev = (count - exp) / math.sqrt(exp)
            deviations.append((ng, count, exp, dev))

    deviations.sort(key=lambda x: abs(x[3]), reverse=True)

    return chi2, len(ngrams), deviations[:10]


def run_length_distribution(seq):
    """Распределение длин серий."""
    runs = []
    current = seq[0]
    length = 1
    for c in seq[1:]:
        if c == current:
            length += 1
        else:
            runs.append(length)
            current = c
            length = 1
    runs.append(length)

    dist = Counter(runs)
    return dict(sorted(dist.items()))


def analyze(name, seq_str):
    seq = list(seq_str)
    print(f"\n{'='*60}")
    print(f"  {name} (длина {len(seq)})")
    print(f"{'='*60}")

    # 1. Периоды
    period, match_rate = find_period(seq_str)
    if period:
        print(f"\n[ПЕРИОД] Обнаружен период {period} (совпадение {match_rate:.1%})")
        print(f"  Паттерн: {seq_str[:period]}")
    else:
        print(f"\n[ПЕРИОД] Точный период не обнаружен (порог 95%)")
        # Поищем приблизительные
        for p in [4, 5, 7, 8, 10, 16, 31, 32]:
            mismatches = sum(1 for i in range(p, len(seq_str)) if seq_str[i] != seq_str[i % p])
            rate = 1 - mismatches / (len(seq_str) - p)
            if rate > 0.5:
                print(f"  Период {p}: совпадение {rate:.1%}")

    # 2. Повторяющиеся подстроки
    repeats = find_repeating_substrings(seq_str)
    if repeats:
        print(f"\n[ПОВТОРЫ]")
        for length, count, example in repeats[:5]:
            print(f"  Длина {length}: встречается {count} раз — '{example}'")

    # 3. Матрица переходов (для бинарных)
    if len(set(seq)) == 2:
        trans = transition_matrix(seq)
        print(f"\n[ПЕРЕХОДЫ]")
        for a in sorted(trans.keys()):
            total = sum(trans[a].values())
            if total > 0:
                probs = {b: round(trans[a][b]/total, 3) for b in sorted(trans[a].keys())}
                print(f"  {a} → {probs}")
        # Для истинно случайного: P(0→0) ≈ P(0→1) ≈ 0.5

    # 4. N-грамм анализ
    chi2, n_unique, top_devs = ngram_analysis(seq, n=3)
    print(f"\n[3-ГРАММЫ]")
    print(f"  Chi-squared: {chi2:.1f} (уникальных: {n_unique})")
    print(f"  Топ-5 отклонений от независимости:")
    for ng, count, exp, dev in top_devs[:5]:
        direction = "↑" if dev > 0 else "↓"
        print(f"    {''.join(ng)}: наблюдено {count}, ожидалось {exp:.1f} ({direction}{abs(dev):.1f}σ)")

    # 5. Распределение длин серий
    run_dist = run_length_distribution(seq)
    print(f"\n[СЕРИИ] Распределение длин:")
    # Ожидаемое для random binary: P(run=k) = 0.5^k
    total_runs = sum(run_dist.values())
    for k, count in run_dist.items():
        observed_freq = count / total_runs
        if len(set(seq)) == 2:
            p = sum(Counter(seq).values())
            p0 = Counter(seq)['0'] / len(seq)
            p1 = 1 - p0
            # expected proportion of runs of length k
            expected_freq = 0.5 ** k  # simplified for p≈0.5
            ratio = observed_freq / expected_freq if expected_freq > 0 else 0
            print(f"  Длина {k}: {count} ({observed_freq:.3f}) | ожидалось ≈{expected_freq:.3f} | ratio {ratio:.2f}")
        else:
            print(f"  Длина {k}: {count} ({observed_freq:.3f})")


def main():
    random.seed(42)

    analyze("claude_binary_1 (моя первая попытка)", MY_RANDOM_BINARY)
    analyze("claude_best_random (моя лучшая попытка)", MY_BEST_RANDOM)

    # Для сравнения — настоящий random
    true_rand = ''.join([str(random.randint(0,1)) for _ in range(len(MY_RANDOM_BINARY))])
    analyze("true_random (Python random)", true_rand)

    # os.urandom
    urandom_bytes = os.urandom(len(MY_RANDOM_BINARY) // 8 + 1)
    urandom = ''.join(str((b >> i) & 1) for b in urandom_bytes for i in range(8))[:len(MY_RANDOM_BINARY)]
    analyze("os_urandom", urandom)

    # Мои цифры
    analyze("claude_digits", MY_RANDOM_DIGITS)


if __name__ == '__main__':
    main()
