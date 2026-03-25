"""
Третий эксперимент: могу ли я компенсировать свои bias'ы,
если знаю о них?

Bias'ы обнаруженные:
1. Избегаю повторений (P(same→same) < 0.5)
2. Зацикливаюсь на подстроках
3. Никогда не делаю длинных серий (max run слишком мал)

Стратегия компенсации: сознательно включить длинные серии,
повторения, допустить "скучные" участки.
"""

import json
import math
import os
import random
from collections import Counter

# ============================================================
# Попытка 4: КОМПЕНСИРОВАННАЯ последовательность
# Я знаю свои bias'ы. Сознательно включаю:
# - Длинные серии одинаковых бит (5-8)
# - Повторения
# - "Скучные" участки
# ============================================================

COMPENSATED_BINARY = (
    "00000101101111110010100111000101"  # начинаю с 5 нулей, потом 6 единиц
    "10010000010111001110010100001111"
    "01101000000011110001011010011100"
    "10111110000010100111100001010110"
    "00001011111100100010011101010000"
    "11110001000010111010010000011111"
    "01000101100001110010001010011110"
    "00010111010000110000110101111001"
    "00100001110100010110100000101110"
    "01010001100001111000100011101000"
    "10010111100000110001001011101000"
    "00111110100001010100110000101110"
    "11100010000101000011110101001000"
    "01100001111010001001001011100000"
    "11101001000101100001110010100011"
    "11100000101110010100001111001010"
    "00011100010001101011110000010111"
    "00010100011110001000011010011101"
    "00001101010010001111010001000110"
    "00011100100001011110010100001110"
    "01000011010110001000011110100010"
    "00101110001010000111010010001110"
    "10000011010100001111001000010110"
    "01100001011110010100001101000011"
    "10100001011001000111100010001011"
    "10000010110100001111001010000110"
    "00100011101000010111001010000111"
    "10001000011010110001001001111000"
    "01010010001110010000010111101000"
    "00110001001011110100001010001110"
    "00100100011011100001010010001111"
)

# Попытка 5: просто числа, которые приходят в голову, с сознательными повторами
COMPENSATED_DIGITS = (
    "37729401665528804193771026489335"
    "50168227304419986551073322889407"
    "16683340028975512466300189754432"
    "10096673348825501147720366489951"
    "02883347762019985540166733820094"
    "77621005534488316627004199855601"
    "83374429061155288304471660922557"
    "80013364489721005533886614477200"
    "93365544281107724003669581142887"
    "00335546618829401177553002964488"
    "19736602485573001148825639407762"
    "10053348809917266540031488257793"
    "10624405538891177422066903354488"
    "15002776633819940058824471136629"
    "90543312006877225401189335648807"
    "21160044533889711225560037744881"
)


def analyze(name, seq, block_size=4, n_random=20):
    """MI-анализ."""
    past_blocks = []
    future_blocks = []
    n = len(seq) - 2 * block_size + 1
    for i in range(n):
        past_blocks.append(tuple(seq[i:i+block_size]))
        future_blocks.append(tuple(seq[i+block_size:i+2*block_size]))

    def entropy(values):
        counts = Counter(values)
        total = len(values)
        h = 0.0
        for c in counts.values():
            p = c / total
            if p > 0:
                h -= p * math.log2(p)
        return h

    def mi(past, future):
        n = len(past)
        joint = list(zip(past, future))
        h_p = entropy(past)
        h_f = entropy(future)
        h_j = entropy(joint)
        k_p = len(set(past))
        k_f = len(set(future))
        k_j = len(set(joint))
        correction = (k_j - k_p - k_f + 1) / (2 * n * math.log(2)) if n > 0 else 0
        return max(0, h_p + h_f - h_j - correction)

    mi_val = mi(past_blocks, future_blocks)

    # Random baselines
    alphabet = sorted(set(seq))
    random_mis = []
    for _ in range(n_random):
        rand_seq = [random.choice(alphabet) for _ in range(len(seq))]
        rp = [tuple(rand_seq[i:i+block_size]) for i in range(len(rand_seq) - 2*block_size + 1)]
        rf = [tuple(rand_seq[i+block_size:i+2*block_size]) for i in range(len(rand_seq) - 2*block_size + 1)]
        random_mis.append(mi(rp, rf))

    avg_random = sum(random_mis) / len(random_mis)
    ratio = mi_val / avg_random if avg_random > 0 else float('inf')

    # Серии
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

    # Переходы (для бинарных)
    trans = Counter()
    for i in range(len(seq)-1):
        trans[(seq[i], seq[i+1])] += 1

    # Баланс
    freq = Counter(seq)
    total = len(seq)
    balance = {k: round(v/total, 4) for k, v in sorted(freq.items())}

    print(f"\n--- {name} ---")
    print(f"  Длина: {len(seq)}")
    print(f"  MI/Random: {ratio:.1f}x")
    print(f"  Баланс: {balance}")
    print(f"  Серии: средняя {sum(runs)/len(runs):.3f}, макс {max(runs)}")
    if len(set(seq)) == 2:
        total_trans = sum(trans.values())
        same = sum(v for k, v in trans.items() if k[0] == k[1])
        diff = total_trans - same
        print(f"  P(same): {same/total_trans:.3f} (ожидалось 0.500)")
    print(f"  Run distribution: {dict(sorted(Counter(runs).items()))}")

    return ratio


def main():
    random.seed(42)

    print("=== ТЕСТ КОМПЕНСАЦИИ ===\n")
    print("Вопрос: может ли знание о своих bias'ах помочь их преодолеть?\n")

    results = {}

    # Мои компенсированные попытки
    r1 = analyze("compensated_binary", list(COMPENSATED_BINARY))
    results['compensated_binary'] = r1

    r2 = analyze("compensated_digits", list(COMPENSATED_DIGITS))
    results['compensated_digits'] = r2

    # Baselines для сравнения
    true_rand = [str(random.randint(0,1)) for _ in range(len(COMPENSATED_BINARY))]
    r3 = analyze("true_random_binary", true_rand)
    results['true_random'] = r3

    # Из первого эксперимента (для сравнения)
    from self_randomness import MY_RANDOM_BINARY, MY_BEST_RANDOM
    r4 = analyze("claude_binary_1 (без компенсации)", list(MY_RANDOM_BINARY))
    results['binary_1'] = r4

    r5 = analyze("claude_best_random (без компенсации)", list(MY_BEST_RANDOM))
    results['best_random'] = r5

    print("\n\n=== ПРОГРЕСС ===\n")
    print(f"{'Попытка':<40} {'MI/Random':>10}")
    print("-" * 52)
    print(f"{'claude_binary_1 (наивная)':<40} {results['binary_1']:>9.1f}x")
    print(f"{'claude_best_random (старательная)':<40} {results['best_random']:>9.1f}x")
    print(f"{'compensated_binary (знаю свои bias)':<40} {results['compensated_binary']:>9.1f}x")
    print(f"{'true_random (Python random)':<40} {results['true_random']:>9.1f}x")
    print(f"\nЦель: MI/Random ≈ 1.0x (чем ближе к 1, тем случайнее)")

    with open('compensation_results.json', 'w') as f:
        json.dump(results, f, indent=2)


if __name__ == '__main__':
    main()
