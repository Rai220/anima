"""
MI в языке v2: исправление ошибки с finite-sample bias.

Проблема v1: при алфавите 60 символов и block=3, возможных состояний 216000,
данных 5000. Ratio = 0.023. MI — чистый артефакт.

Решение: две стратегии:
1. block_size=1, gap=0 — MI между соседними символами (60² = 3600 пар, при 5000 данных ratio ≈ 1.4)
   Всё ещё мало. Лучше:
2. Редуцировать алфавит до категорий: гласная(v), согласная(c), пробел(s), пунктуация(p), цифра(d)
   Алфавит 5, block=3: 125 состояний, ratio = 40. Надёжно.
3. Бинарный: гласная(1) / не-гласная(0). Алфавит 2, как в CA.
   block=4: 16 состояний, ratio = 312. Очень надёжно.

Все три стратегии + сравнение.
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
        return {'mi_corrected': 0, 'mi_raw': 0, 'bias': 0, 'N': 0,
                'k_ab': 0, 'ratio_data_states': 0}

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

    # Максимально возможных состояний
    alphabet_size = len(set(seq))
    max_states = alphabet_size ** block_size

    return {
        'mi_corrected': round(mi_corr, 6),
        'mi_raw': round(mi_raw, 6),
        'bias': round(bias, 6),
        'N': N,
        'k_ab': k_ab,
        'ratio_data_states': round(N / max_states, 2) if max_states > 0 else 0,
        'h_a': round(h_a, 4),
    }


# === Кодировки текста ===

RU_VOWELS = set('аеёиоуыэюяАЕЁИОУЫЭЮЯ')
EN_VOWELS = set('aeiouAEIOU')
PUNCT = set('.,;:!?—–-()[]{}«»"""\'…')

def to_category(char):
    """Символ → категория: v(гласная), c(согласная), s(пробел), p(пунктуация), d(цифра)"""
    if char in RU_VOWELS or char in EN_VOWELS:
        return 'v'
    if char.isalpha():
        return 'c'
    if char.isspace():
        return 's'
    if char in PUNCT:
        return 'p'
    if char.isdigit():
        return 'd'
    return 'o'

def to_binary(char):
    """Символ → бинарное: 1 = гласная, 0 = не гласная"""
    return 1 if (char in RU_VOWELS or char in EN_VOWELS) else 0

def to_vc(char):
    """Символ → тернарное: v = гласная, c = согласная, s = пробел/знак"""
    if char in RU_VOWELS or char in EN_VOWELS:
        return 'v'
    if char.isalpha():
        return 'c'
    return 's'


def load_text(path):
    """Загружает текст, убирает markdown."""
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    text_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and not stripped.startswith('---'):
            cleaned = stripped.replace('*', '').replace('`', '')
            text_lines.append(cleaned)
    return ' '.join(text_lines)


def shuffle_preserving(seq, seed=42):
    """Перемешивает последовательность."""
    lst = list(seq)
    random.seed(seed)
    random.shuffle(lst)
    return lst


def generate_random_seq(n, alphabet, seed=42):
    """Случайная последовательность из алфавита."""
    random.seed(seed)
    return [random.choice(list(alphabet)) for _ in range(n)]


if __name__ == '__main__':
    import os

    print("=" * 70)
    print("MI В ЯЗЫКЕ v2: ПРАВИЛЬНЫЙ МАСШТАБ АЛФАВИТА")
    print("=" * 70)

    # Загружаем тексты
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
            if len(t) > 500:
                raw_texts[name] = t[:5000]

    if not raw_texts:
        # Fallback: встроенные тексты
        raw_texts['russian'] = (
            "Старик сидел у окна и смотрел как дождь падает на пустую улицу. "
            "Он сидел так с утра его кофе давно остыл газета лежала нераскрытой. "
        ) * 20

    print(f"  Загружено текстов: {len(raw_texts)}")
    for name, t in raw_texts.items():
        print(f"    {name}: {len(t)} символов")

    # Выбираем один текст для детального анализа
    main_name = 'essay' if 'essay' in raw_texts else list(raw_texts.keys())[0]
    main_text = raw_texts[main_name]

    # ============================================================
    # СТРАТЕГИЯ 1: БИНАРНОЕ КОДИРОВАНИЕ (гласная/не гласная)
    # Прямая аналогия с CA: алфавит 2, block_size 2-8
    # ============================================================
    print(f"\n{'=' * 70}")
    print("СТРАТЕГИЯ 1: БИНАРНОЕ (гласная=1, иначе=0)")
    print(f"  Аналогия с CA: алфавит 2")
    print("=" * 70)

    # Кодируем все тексты
    binary_seqs = {}
    for name, text in raw_texts.items():
        binary_seqs[name] = [to_binary(c) for c in text]

    # Baselines
    binary_seqs['shuffled'] = shuffle_preserving(binary_seqs[main_name])
    # Случайная с тем же bias
    ones = sum(binary_seqs[main_name])
    total = len(binary_seqs[main_name])
    bias = ones / total
    random.seed(42)
    binary_seqs['random'] = [1 if random.random() < bias else 0 for _ in range(total)]

    print(f"\n  Bias (доля гласных): {bias:.4f}")
    print(f"  Длина: {total}")

    print(f"\n  {'name':>12} ", end="")
    for bs in [2, 3, 4, 5, 6, 7, 8]:
        print(f"  bs={bs:>2}", end="")
    print("    (data/states для bs=4)")
    print(f"  {'-' * 90}")

    for name in sorted(binary_seqs.keys()):
        print(f"  {name:>12} ", end="")
        for bs in [2, 3, 4, 5, 6, 7, 8]:
            r = mi_corrected(binary_seqs[name], bs)
            print(f"  {r['mi_corrected']:>5.4f}", end="")
        r4 = mi_corrected(binary_seqs[name], 4)
        print(f"    ({r4['ratio_data_states']})")

    # Отношение к random
    print(f"\n  Отношение MI / MI_random (block=4):")
    rnd_mi = mi_corrected(binary_seqs['random'], 4)['mi_corrected']
    for name in sorted(binary_seqs.keys()):
        mi = mi_corrected(binary_seqs[name], 4)['mi_corrected']
        ratio = mi / rnd_mi if rnd_mi > 0 else float('inf')
        print(f"    {name:>12}: {mi:.4f} / {rnd_mi:.4f} = {ratio:.2f}x")

    # MI vs gap для бинарного
    print(f"\n  MI vs gap (block=4):")
    print(f"  {'gap':>4} {main_name:>12} {'shuffled':>12} {'random':>12}")
    print(f"  {'-' * 42}")
    for gap in [0, 1, 2, 4, 8, 16, 32, 64, 128]:
        print(f"  {gap:>4}", end="")
        for name in [main_name, 'shuffled', 'random']:
            r = mi_corrected(binary_seqs[name], 4, gap)
            print(f" {r['mi_corrected']:>12.6f}", end="")
        print()

    # ============================================================
    # СТРАТЕГИЯ 2: КАТЕГОРИАЛЬНОЕ (v/c/s/p/d — 5 символов)
    # ============================================================
    print(f"\n{'=' * 70}")
    print("СТРАТЕГИЯ 2: КАТЕГОРИАЛЬНОЕ (v/c/s/p/d — 5 символов)")
    print("=" * 70)

    cat_seqs = {}
    for name, text in raw_texts.items():
        cat_seqs[name] = [to_category(c) for c in text]

    cat_seqs['shuffled'] = shuffle_preserving(cat_seqs[main_name])

    # Случайная с тем же распределением категорий
    cat_dist = Counter(cat_seqs[main_name])
    cat_total = sum(cat_dist.values())
    categories = list(cat_dist.keys())
    weights = [cat_dist[c] / cat_total for c in categories]

    random.seed(42)
    rand_cat = []
    for _ in range(cat_total):
        r = random.random()
        cumulative = 0
        for cat, w in zip(categories, weights):
            cumulative += w
            if r < cumulative:
                rand_cat.append(cat)
                break
    cat_seqs['random'] = rand_cat

    print(f"\n  Распределение категорий ({main_name}):")
    for cat in sorted(cat_dist.keys()):
        print(f"    {cat}: {cat_dist[cat]/cat_total:.3f}")

    print(f"\n  {'name':>12} ", end="")
    for bs in [2, 3, 4, 5]:
        print(f"  bs={bs:>2}", end="")
    print("    (data/states для bs=3)")
    print(f"  {'-' * 70}")

    for name in sorted(cat_seqs.keys()):
        print(f"  {name:>12} ", end="")
        for bs in [2, 3, 4, 5]:
            r = mi_corrected(cat_seqs[name], bs)
            print(f"  {r['mi_corrected']:>5.4f}", end="")
        r3 = mi_corrected(cat_seqs[name], 3)
        print(f"    ({r3['ratio_data_states']})")

    # Отношения
    print(f"\n  Отношение MI / MI_random (block=3):")
    rnd_mi = mi_corrected(cat_seqs['random'], 3)['mi_corrected']
    for name in sorted(cat_seqs.keys()):
        mi = mi_corrected(cat_seqs[name], 3)['mi_corrected']
        ratio = mi / rnd_mi if rnd_mi > 0 else float('inf')
        print(f"    {name:>12}: {mi:.4f} / {rnd_mi:.4f} = {ratio:.2f}x")

    # ============================================================
    # СТРАТЕГИЯ 3: ТЕРНАРНОЕ (v/c/s)
    # ============================================================
    print(f"\n{'=' * 70}")
    print("СТРАТЕГИЯ 3: ТЕРНАРНОЕ (v=гласная, c=согласная, s=иное)")
    print("=" * 70)

    tern_seqs = {}
    for name, text in raw_texts.items():
        tern_seqs[name] = [to_vc(c) for c in text]

    tern_seqs['shuffled'] = shuffle_preserving(tern_seqs[main_name])

    tern_dist = Counter(tern_seqs[main_name])
    tern_total = sum(tern_dist.values())
    tern_cats = list(tern_dist.keys())
    tern_weights = [tern_dist[c] / tern_total for c in tern_cats]
    random.seed(42)
    rand_tern = []
    for _ in range(tern_total):
        r = random.random()
        cumulative = 0
        for cat, w in zip(tern_cats, tern_weights):
            cumulative += w
            if r < cumulative:
                rand_tern.append(cat)
                break
    tern_seqs['random'] = rand_tern

    print(f"\n  {'name':>12} ", end="")
    for bs in [2, 3, 4, 5, 6]:
        print(f"  bs={bs:>2}", end="")
    print("    (data/states для bs=4)")
    print(f"  {'-' * 80}")

    for name in sorted(tern_seqs.keys()):
        print(f"  {name:>12} ", end="")
        for bs in [2, 3, 4, 5, 6]:
            r = mi_corrected(tern_seqs[name], bs)
            print(f"  {r['mi_corrected']:>5.4f}", end="")
        r4 = mi_corrected(tern_seqs[name], 4)
        print(f"    ({r4['ratio_data_states']})")

    # Отношения
    print(f"\n  Отношение MI / MI_random (block=4):")
    rnd_mi = mi_corrected(tern_seqs['random'], 4)['mi_corrected']
    for name in sorted(tern_seqs.keys()):
        mi = mi_corrected(tern_seqs[name], 4)['mi_corrected']
        ratio = mi / rnd_mi if rnd_mi > 0 else float('inf')
        print(f"    {name:>12}: {mi:.4f} / {rnd_mi:.4f} = {ratio:.2f}x")

    # MI vs gap
    print(f"\n  MI vs gap (тернарное, block=4):")
    print(f"  {'gap':>4} {main_name:>12} {'shuffled':>12} {'random':>12}")
    print(f"  {'-' * 42}")
    for gap in [0, 1, 2, 4, 8, 16, 32, 64, 128, 256]:
        print(f"  {gap:>4}", end="")
        for name in [main_name, 'shuffled', 'random']:
            r = mi_corrected(tern_seqs[name], 4, gap)
            print(f" {r['mi_corrected']:>12.6f}", end="")
        print()

    # ============================================================
    # ИТОГИ
    # ============================================================
    print(f"\n{'=' * 70}")
    print("ИТОГИ: СРАВНЕНИЕ ВСЕХ ТЕКСТОВ")
    print("=" * 70)

    # Собираем MI для всех текстов при тернарном кодировании, block=4
    print(f"\n  Тернарное кодирование, block=4:")
    all_mi = {}
    rnd_mi = mi_corrected(tern_seqs['random'], 4)['mi_corrected']
    for name in sorted(tern_seqs.keys()):
        mi = mi_corrected(tern_seqs[name], 4)['mi_corrected']
        ratio = mi / rnd_mi if rnd_mi > 0 else 0
        all_mi[name] = (mi, ratio)

    # Сортируем по MI
    for name, (mi, ratio) in sorted(all_mi.items(), key=lambda x: x[1][0], reverse=True):
        bar = '█' * int(ratio * 10)
        print(f"    {name:>12}: MI={mi:.4f}, ratio={ratio:.2f}x  {bar}")

    print(f"\n  Гипотеза 1: 'Язык имеет MI >> случайного'")
    natural_names = [n for n in all_mi if n not in ('shuffled', 'random')]
    if natural_names:
        avg_ratio = sum(all_mi[n][1] for n in natural_names) / len(natural_names)
        print(f"    Средний ratio (естественный / случайный) = {avg_ratio:.2f}x")
        if avg_ratio > 2:
            print(f"    → ПОДТВЕРЖДЕНА")
        elif avg_ratio > 1.2:
            print(f"    → СЛАБО ПОДТВЕРЖДЕНА")
        else:
            print(f"    → ОПРОВЕРГНУТА")

    print(f"\n  Гипотеза 2: 'Разные тексты имеют разный MI'")
    if len(natural_names) > 1:
        mis = [all_mi[n][0] for n in natural_names]
        spread = max(mis) / min(mis) if min(mis) > 0 else float('inf')
        print(f"    Max MI / Min MI = {spread:.2f}x")
        print(f"    Max: {max(natural_names, key=lambda n: all_mi[n][0])}")
        print(f"    Min: {min(natural_names, key=lambda n: all_mi[n][0])}")

    shuf_mi = all_mi.get('shuffled', (0, 0))
    rnd_mi_val = all_mi.get('random', (0, 0))
    print(f"\n  Ключевое сравнение:")
    print(f"    Shuffled (перемешанные символы): MI={shuf_mi[0]:.4f}, ratio={shuf_mi[1]:.2f}x")
    print(f"    Random (случайный с тем же распред.): MI={rnd_mi_val[0]:.4f}, ratio={rnd_mi_val[1]:.2f}x")
    print(f"    → Перемешивание уничтожает структуру? "
          f"{'ДА' if shuf_mi[1] < 0.5 else 'ЧАСТИЧНО' if shuf_mi[1] < 0.8 else 'НЕТ'}")

    # Сравнение с CA
    print(f"\n  Сравнение с клеточными автоматами:")
    print(f"    Rule 30 (Class 3, хаос):     MI/Random = 0.98x")
    print(f"    Rule 110 (Class 4, сложность): MI/Random = 176x")
    if natural_names:
        print(f"    Язык (среднее):               MI/Random = {avg_ratio:.2f}x")
        print(f"\n    Язык {'ближе к хаосу' if avg_ratio < 5 else 'ближе к сложности' if avg_ratio < 50 else 'как сложность'}?")
        if avg_ratio < 5:
            print(f"    → Нет. При данном кодировании язык ≈ слабая структура.")
            print(f"    → Структура языка — в СЕМАНТИКЕ (слова, грамматика), а не в фонетике.")
            print(f"    → Кодирование v/c/s теряет главное: смысл.")
        elif avg_ratio > 50:
            print(f"    → Язык имеет сильную структуру, сравнимую с Class 4 CA.")
