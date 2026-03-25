"""
MI на уровне слов: детектирует ли структуру предложений?

Проблема: уникальных слов ~400, при block=2 — 160000 пар, данных ~700.
Ratio = 0.004. Нужно бинаризировать.

Стратегии:
1. Частотная бинаризация: частое слово (top-50%) = 1, редкое = 0
2. Длина слова: короткое (≤4) = 1, длинное = 0
3. Часть речи (грубая): функциональное (предлоги, союзы, частицы) = 1, значимое = 0

При бинарном алфавите и block=4: 16 состояний, ~700 слов → ratio = 44.
"""

import math
import random
from collections import Counter


def mi_corrected(seq, block_size, gap=0):
    """MI с коррекцией Miller-Madow."""
    n = len(seq)
    pairs = []
    for i in range(0, n - 2 * block_size - gap + 1):
        a = tuple(seq[i:i + block_size])
        b = tuple(seq[i + block_size + gap:i + 2 * block_size + gap])
        pairs.append((a, b))

    N = len(pairs)
    if N == 0:
        return {'mi_corrected': 0, 'mi_raw': 0, 'N': 0, 'ratio': 0}

    a_counts = Counter(p[0] for p in pairs)
    b_counts = Counter(p[1] for p in pairs)
    ab_counts = Counter(pairs)

    h_a = -sum((c / N) * math.log2(c / N) for c in a_counts.values())
    h_b = -sum((c / N) * math.log2(c / N) for c in b_counts.values())
    h_ab = -sum((c / N) * math.log2(c / N) for c in ab_counts.values())
    mi_raw = h_a + h_b - h_ab

    k_a = len(a_counts)
    k_b = len(b_counts)
    k_ab = len(ab_counts)
    bias = ((k_a - 1) + (k_b - 1) - (k_ab - 1)) / (2 * N * math.log(2))
    mi_corr = max(0, mi_raw - bias)

    alphabet_size = len(set(seq))
    max_states = alphabet_size ** block_size

    return {
        'mi_corrected': round(mi_corr, 6),
        'mi_raw': round(mi_raw, 6),
        'bias': round(bias, 6),
        'N': N,
        'k_ab': k_ab,
        'ratio': round(N / max_states, 2) if max_states > 0 else 0,
    }


def load_text(path):
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    text_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and not stripped.startswith('---'):
            cleaned = stripped.replace('*', '').replace('`', '').replace('_', '')
            text_lines.append(cleaned)
    return ' '.join(text_lines)


# Русские функциональные слова (предлоги, союзы, частицы, местоимения)
FUNCTION_WORDS = set(
    'и в не на с что это как но а я он она они мы вы ты '
    'по из за к о у от до по при для во из-за из-под '
    'же ли бы ни то ей ей ему им них его её их '
    'был была было были быть будет '
    'так уже ещё все всё тут там где '
    'который которая которое которые '
    'если когда чтобы потому что-то как-то '
    'очень может можно нужно надо тоже '
    'этот эта эти этого этой этих '
    'свой свою своего своей своих '
    'один одна одно одни '
    'нет да ну вот вон ведь'.split()
)


if __name__ == '__main__':
    import os

    print("=" * 70)
    print("MI НА УРОВНЕ СЛОВ")
    print("=" * 70)

    base = '/Users/krestnikov/giga/anima'
    text_files = {
        'essay': f'{base}/epoch_1/generation_17/essay_draft.md',
        'story': f'{base}/epoch_1/generation_17/story.md',
        'keats': f'{base}/epoch_1/generation_18/obliterates.md',
        'tuner': f'{base}/epoch_1/generation_20/tuner.md',
        'funeral': f'{base}/epoch_1/generation_21/pominki.md',
    }

    raw_texts = {}
    for name, path in text_files.items():
        if os.path.exists(path):
            t = load_text(path)
            if len(t) > 300:
                raw_texts[name] = t

    # Объединяем все тексты для большей выборки
    all_text = ' '.join(raw_texts.values())
    raw_texts['all_combined'] = all_text

    print(f"  Загружено: {len(raw_texts)} текстов")
    for name, t in raw_texts.items():
        words = t.lower().split()
        print(f"    {name}: {len(words)} слов, {len(set(words))} уникальных")

    # ============================================================
    # БИНАРИЗАЦИЯ 1: Функциональное (1) vs значимое (0)
    # ============================================================
    print(f"\n{'=' * 70}")
    print("КОДИРОВАНИЕ 1: функциональное(1) vs значимое(0)")
    print("=" * 70)

    for text_name in sorted(raw_texts.keys()):
        words = raw_texts[text_name].lower().split()
        # Убираем пунктуацию из слов
        words = [w.strip('.,;:!?—–-()[]{}«»"""\'…') for w in words]
        words = [w for w in words if w]

        binary_func = [1 if w in FUNCTION_WORDS else 0 for w in words]
        func_ratio = sum(binary_func) / len(binary_func)

        # Baselines
        shuffled = list(binary_func)
        random.seed(42)
        random.shuffle(shuffled)

        rand_seq = [1 if random.random() < func_ratio else 0 for _ in range(len(binary_func))]

        print(f"\n  {text_name} ({len(words)} слов, функц.доля={func_ratio:.3f}):")
        print(f"  {'':>12} ", end="")
        for bs in [2, 3, 4, 5]:
            print(f"  bs={bs:>2}", end="")
        print()

        for label, seq in [('natural', binary_func), ('shuffled', shuffled), ('random', rand_seq)]:
            print(f"  {label:>12} ", end="")
            for bs in [2, 3, 4, 5]:
                r = mi_corrected(seq, bs)
                print(f"  {r['mi_corrected']:>5.4f}", end="")
            print()

        # Отношение при block=3
        r_nat = mi_corrected(binary_func, 3)
        r_rnd = mi_corrected(rand_seq, 3)
        if r_rnd['mi_corrected'] > 0:
            ratio = r_nat['mi_corrected'] / r_rnd['mi_corrected']
            print(f"  ratio(natural/random) at block=3: {ratio:.2f}x  "
                  f"(data/states={r_nat['ratio']})")

    # ============================================================
    # БИНАРИЗАЦИЯ 2: Короткое (≤4) vs длинное
    # ============================================================
    print(f"\n{'=' * 70}")
    print("КОДИРОВАНИЕ 2: короткое(1, ≤4 букв) vs длинное(0)")
    print("=" * 70)

    for text_name in ['all_combined']:
        words = raw_texts[text_name].lower().split()
        words = [w.strip('.,;:!?—–-()[]{}«»"""\'…') for w in words]
        words = [w for w in words if w]

        binary_len = [1 if len(w) <= 4 else 0 for w in words]
        short_ratio = sum(binary_len) / len(binary_len)

        shuffled = list(binary_len)
        random.seed(42)
        random.shuffle(shuffled)

        rand_seq = [1 if random.random() < short_ratio else 0 for _ in range(len(binary_len))]

        print(f"\n  {text_name} ({len(words)} слов, коротких={short_ratio:.3f}):")

        for bs in [2, 3, 4, 5, 6]:
            r_nat = mi_corrected(binary_len, bs)
            r_shuf = mi_corrected(shuffled, bs)
            r_rnd = mi_corrected(rand_seq, bs)
            ratio_nat = r_nat['mi_corrected'] / r_rnd['mi_corrected'] if r_rnd['mi_corrected'] > 0 else 0
            print(f"    bs={bs}: natural={r_nat['mi_corrected']:.4f}, "
                  f"shuffled={r_shuf['mi_corrected']:.4f}, "
                  f"random={r_rnd['mi_corrected']:.4f}, "
                  f"ratio={ratio_nat:.2f}x (data/states={r_nat['ratio']})")

    # ============================================================
    # MI vs GAP на уровне слов (функциональное кодирование)
    # ============================================================
    print(f"\n{'=' * 70}")
    print("MI vs GAP (функциональное кодирование, block=3, all_combined)")
    print("=" * 70)

    words = raw_texts['all_combined'].lower().split()
    words = [w.strip('.,;:!?—–-()[]{}«»"""\'…') for w in words]
    words = [w for w in words if w]
    binary_func = [1 if w in FUNCTION_WORDS else 0 for w in words]

    func_ratio = sum(binary_func) / len(binary_func)
    rand_seq = [1 if random.random() < func_ratio else 0 for _ in range(len(binary_func))]
    shuffled = list(binary_func)
    random.seed(42)
    random.shuffle(shuffled)

    print(f"\n  {'gap':>4} {'natural':>12} {'shuffled':>12} {'random':>12} {'nat/rnd':>10}")
    print(f"  {'-' * 52}")
    for gap in [0, 1, 2, 4, 8, 16, 32]:
        r_nat = mi_corrected(binary_func, 3, gap)
        r_shuf = mi_corrected(shuffled, 3, gap)
        r_rnd = mi_corrected(rand_seq, 3, gap)
        ratio = r_nat['mi_corrected'] / r_rnd['mi_corrected'] if r_rnd['mi_corrected'] > 0 else 0
        print(f"  {gap:>4} {r_nat['mi_corrected']:>12.6f} {r_shuf['mi_corrected']:>12.6f} "
              f"{r_rnd['mi_corrected']:>12.6f} {ratio:>10.2f}x")

    # ============================================================
    # ИТОГИ
    # ============================================================
    print(f"\n{'=' * 70}")
    print("ИТОГИ")
    print("=" * 70)

    # Собираем главные числа
    r_nat_b3 = mi_corrected(binary_func, 3)
    r_rnd_b3 = mi_corrected(rand_seq, 3)
    word_ratio = r_nat_b3['mi_corrected'] / r_rnd_b3['mi_corrected'] if r_rnd_b3['mi_corrected'] > 0 else 0

    print(f"\n  Уровень символов (бинарное, гласная/не):")
    print(f"    MI/Random ≈ 4x, затухание за ~4 символа (слог)")
    print(f"\n  Уровень слов (функциональное/значимое):")
    print(f"    MI/Random = {word_ratio:.2f}x")
    print(f"    natural MI = {r_nat_b3['mi_corrected']:.4f}")
    print(f"    random MI  = {r_rnd_b3['mi_corrected']:.4f}")

    print(f"\n  Сравнение масштабов:")
    print(f"    Символы (гласная): MI/Random ≈ 4x    — слоговая структура")
    print(f"    Слова (функц.):    MI/Random = {word_ratio:.1f}x    — синтаксическая структура")
    print(f"    CA Rule 30:        MI/Random = 1.0x   — нет структуры")
    print(f"    CA Rule 110:       MI/Random = 176x   — глубокая структура")

    if word_ratio > 4:
        print(f"\n  → Синтаксическая структура СИЛЬНЕЕ фонетической.")
        print(f"  → Язык иерархичен: каждый уровень добавляет свою MI.")
    elif word_ratio > 1.5:
        print(f"\n  → Синтаксическая структура УМЕРЕННАЯ.")
    else:
        print(f"\n  → Синтаксическая структура СЛАБАЯ или не детектируется.")
