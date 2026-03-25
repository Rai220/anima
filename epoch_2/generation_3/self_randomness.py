"""
Тест: может ли языковая модель генерировать случайные последовательности?

Я (Claude) пытаюсь "быть случайным". Затем MI-анализ проверяет,
есть ли скрытая структура в моих попытках.

Метод из gen2 epoch2: блочная MI между прошлым и будущим.
"""

import json
import math
import os
import random
from collections import Counter

# ============================================================
# Последовательности, которые я "придумал случайно"
# Я честно пытаюсь быть случайным, не считаю и не использую паттерн.
# ============================================================

# Попытка 1: бинарная последовательность (1000 бит), "из головы"
MY_RANDOM_BINARY = (
    "10110100011101001011010001110100"
    "01011010110001110010101101001011"
    "10010111010001101011001010110100"
    "01110100101101001110010110100111"
    "01001011010001110100101101000111"
    "01001011010100111001011010010110"
    "10001110100101101000111010010110"
    "10100111001011010010110100011101"
    "00101101000111010010110101001110"
    "01011010010110100011101001011010"
    "00111010010110101001110010110100"
    "10110100011101001011010001110100"
    "01011010110001110010101101001011"
    "10010111010001101011001010110100"
    "01110100101101001110010110100111"
    "01001011010001110100101101000111"
    "01001011010100111001011010010110"
    "10001110100101101000111010010110"
    "10100111001011010010110100011101"
    "00101101000111010010110101001110"
    "01011010010110100011101001011010"
    "00111010010110101001110010110100"
    "10110100011101001011010100111001"
    "01101001011010001110100101101000"
    "11101001011010100111001011010010"
    "11010001110100101101000111010010"
    "11010100111001011010010110100011"
    "10100101101000111010010110101001"
    "11001011010010110100011101001011"
    "01000111010010110101001110010110"
    "10010110100011101001011010001110"
)

# Попытка 2: десятичные цифры (500 цифр), "из головы"
MY_RANDOM_DIGITS = (
    "73829164058273619405827361940582"
    "94716305829471630582736194058273"
    "61940582947163058291736405829173"
    "64058291736405827361940582736194"
    "05829471630582947163058273619405"
    "82736194058294716305829173640582"
    "91736405827361940582736194058294"
    "71630582947163058273619405829471"
    "63058291736405829173640582736194"
    "05827361940582947163058294716305"
    "82917364058291736405827361940582"
    "73619405829471630582947163058291"
    "73640582917364058273619405827361"
    "94058294716305829471630582917364"
    "05829173640582736194058273619405"
    "82947163058294716305829173640582"
)

# Попытка 3: я пытаюсь быть МАКСИМАЛЬНО случайным, избегая паттернов
MY_BEST_RANDOM = (
    "01100101110000101101110010000111"
    "10101000011001110100100011011010"
    "00011111000101100100111010110000"
    "11001010001110110100000101110011"
    "01000010111001011010011100001011"
    "11010010000101111010001100101000"
    "01101110000101011001110100001110"
    "10100001001011110001011001010011"
    "10000111010101100011001001110100"
    "10110000011101001010001111010010"
    "01001100101110001010110100001101"
    "01100010110100111000010110110001"
    "01001101010001100111010010001011"
    "11000010100111010100110000101110"
    "01001010001101110000110010101100"
    "10001001111001010001101001100100"
    "11010100001011011010000101101100"
    "10100110000111001010101000110101"
    "10001101000010111010011000010111"
    "01010001001101011010000110011101"
    "00011010100101001110001011100010"
    "10010110001100011101000101010011"
    "10100100001100101011101000010110"
    "01101001001000111011010100110000"
    "10010101100011000101101001100111"
    "01010010000110111001000101001110"
    "10100011000101001110100010010110"
    "10000110010101100001110100101010"
    "01110001001011010000111010010001"
    "10110100100001011001101001010000"
    "11100010010101100110100001110011"
)


# ============================================================
# MI-анализ (метод из gen2)
# ============================================================

def sequence_to_blocks(seq, block_size):
    """Разбивает последовательность на блоки."""
    n = len(seq) - 2 * block_size + 1
    past_blocks = []
    future_blocks = []
    for i in range(n):
        past = tuple(seq[i:i+block_size])
        future = tuple(seq[i+block_size:i+2*block_size])
        past_blocks.append(past)
        future_blocks.append(future)
    return past_blocks, future_blocks


def entropy(values):
    """Энтропия Шеннона."""
    counts = Counter(values)
    total = len(values)
    h = 0.0
    for c in counts.values():
        p = c / total
        if p > 0:
            h -= p * math.log2(p)
    return h


def mutual_information(past, future):
    """MI между прошлым и будущим (с Miller-Madow correction)."""
    n = len(past)
    joint = list(zip(past, future))

    h_past = entropy(past)
    h_future = entropy(future)
    h_joint = entropy(joint)

    # Miller-Madow correction
    k_past = len(set(past))
    k_future = len(set(future))
    k_joint = len(set(joint))

    correction = (k_joint - k_past - k_future + 1) / (2 * n * math.log(2)) if n > 0 else 0

    mi = h_past + h_future - h_joint - correction
    return max(0, mi)


def analyze_sequence(name, seq, block_size=4, n_random=20):
    """Полный MI-анализ последовательности."""
    past, future = sequence_to_blocks(seq, block_size)
    mi = mutual_information(past, future)
    h = entropy(list(seq))

    # Базовый уровень: случайные последовательности
    random_mis = []
    for _ in range(n_random):
        alphabet = sorted(set(seq))
        rand_seq = [random.choice(alphabet) for _ in range(len(seq))]
        rp, rf = sequence_to_blocks(rand_seq, block_size)
        random_mis.append(mutual_information(rp, rf))

    avg_random_mi = sum(random_mis) / len(random_mis)
    mi_ratio = mi / avg_random_mi if avg_random_mi > 0 else float('inf')

    # Shuffled baseline
    shuffled = list(seq)
    random.shuffle(shuffled)
    sp, sf = sequence_to_blocks(shuffled, block_size)
    shuffled_mi = mutual_information(sp, sf)

    # Частоты символов
    freq = Counter(seq)
    total = len(seq)
    balance = {k: round(v/total, 4) for k, v in sorted(freq.items())}

    # Серии (runs): длины непрерывных повторений
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
    avg_run = sum(runs) / len(runs)
    max_run = max(runs)

    # Автокорреляция (задержки 1-16)
    autocorr = []
    num_seq = [int(c) if c.isdigit() else ord(c) for c in seq]
    mean = sum(num_seq) / len(num_seq)
    var = sum((x - mean)**2 for x in num_seq) / len(num_seq)
    for lag in range(1, min(17, len(seq)//4)):
        if var > 0:
            cov = sum((num_seq[i] - mean) * (num_seq[i+lag] - mean)
                      for i in range(len(num_seq) - lag)) / (len(num_seq) - lag)
            autocorr.append(round(cov / var, 4))
        else:
            autocorr.append(0)

    data_states = len(past) / (len(set(seq)) ** (2 * block_size))

    return {
        'name': name,
        'length': len(seq),
        'entropy': round(h, 4),
        'MI': round(mi, 6),
        'MI_random_avg': round(avg_random_mi, 6),
        'MI_ratio': round(mi_ratio, 2),
        'MI_shuffled': round(shuffled_mi, 6),
        'balance': balance,
        'avg_run_length': round(avg_run, 3),
        'max_run_length': max_run,
        'autocorrelation': autocorr[:8],
        'data_states_ratio': round(data_states, 1),
        'n_unique_blocks': len(set(past)),
        'total_blocks': len(past),
    }


def main():
    random.seed(42)

    results = []

    # Мои последовательности
    print("=== Тест: скрытая структура в 'случайных' последовательностях Claude ===\n")

    tests = [
        ("claude_binary_1", list(MY_RANDOM_BINARY)),
        ("claude_digits", list(MY_RANDOM_DIGITS)),
        ("claude_best_random", list(MY_BEST_RANDOM)),
    ]

    # Настоящий random для сравнения
    true_random_bin = [str(b) for b in [random.randint(0, 1) for _ in range(len(MY_RANDOM_BINARY))]]
    tests.append(("true_random_binary", true_random_bin))

    true_random_dig = [str(random.randint(0, 9)) for _ in range(len(MY_RANDOM_DIGITS))]
    tests.append(("true_random_digits", true_random_dig))

    # os.urandom для ещё лучшего random
    urandom_bytes = os.urandom(len(MY_RANDOM_BINARY) // 8 + 1)
    urandom_bin = []
    for byte in urandom_bytes:
        for bit in range(8):
            urandom_bin.append(str((byte >> bit) & 1))
    urandom_bin = urandom_bin[:len(MY_RANDOM_BINARY)]
    tests.append(("os_urandom_binary", urandom_bin))

    # Заведомо паттерный: чередование
    alternating = list("01" * (len(MY_RANDOM_BINARY) // 2))
    tests.append(("alternating_01", alternating))

    # Заведомо паттерный: период 7
    period7 = list("0110100" * (len(MY_RANDOM_BINARY) // 7 + 1))[:len(MY_RANDOM_BINARY)]
    tests.append(("period_7", period7))

    for name, seq in tests:
        r = analyze_sequence(name, seq)
        results.append(r)

        print(f"--- {name} ---")
        print(f"  Длина: {r['length']}")
        print(f"  Энтропия: {r['entropy']}")
        print(f"  MI: {r['MI']:.6f}")
        print(f"  MI/Random: {r['MI_ratio']}x")
        print(f"  MI shuffled: {r['MI_shuffled']:.6f}")
        print(f"  Баланс: {r['balance']}")
        print(f"  Средняя серия: {r['avg_run_length']}, макс: {r['max_run_length']}")
        print(f"  Автокорреляция [1-8]: {r['autocorrelation']}")
        print(f"  Data/states: {r['data_states_ratio']}")
        print()

    # Главная таблица
    print("\n=== СВОДНАЯ ТАБЛИЦА ===\n")
    print(f"{'Название':<25} {'MI/Rand':>8} {'Энтр':>6} {'Ср.серия':>9} {'Макс.сер':>9} {'AutoCorr[1]':>12}")
    print("-" * 75)
    for r in results:
        ac1 = r['autocorrelation'][0] if r['autocorrelation'] else 0
        print(f"{r['name']:<25} {r['MI_ratio']:>7.1f}x {r['entropy']:>6.3f} {r['avg_run_length']:>9.3f} {r['max_run_length']:>9} {ac1:>12.4f}")

    # Сохранение
    with open('self_randomness_results.json', 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\nРезультаты сохранены в self_randomness_results.json")


if __name__ == '__main__':
    main()
