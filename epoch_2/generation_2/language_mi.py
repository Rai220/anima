"""
Взаимная информация в языке: отличает ли MI осмысленный текст от случайного?

Гипотезы:
1. Естественный язык имеет MI >> случайного при сопоставимой энтропии
2. Проза и поэзия имеют разный MI-профиль
3. MI различает осмысленный текст от перемешанного (shuffled)

Метод: блочная MI на уровне символов (не слов — слова дают слишком мало данных).
Miller-Madow correction для bias.

Baseline: случайный текст с тем же распределением символов (shuffled original).
"""

import math
import random
from collections import Counter


def mi_corrected(seq, block_size, gap=0):
    """MI с коррекцией Miller-Madow. Работает с любыми символами."""
    n = len(seq)
    pairs = []
    for i in range(0, n - 2 * block_size - gap + 1):
        a = tuple(seq[i:i + block_size])
        b = tuple(seq[i + block_size + gap:i + 2 * block_size + gap])
        pairs.append((a, b))

    N = len(pairs)
    if N == 0:
        return {'mi_raw': 0, 'mi_corrected': 0, 'bias': 0, 'N': 0}

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

    return {
        'mi_raw': round(mi_raw, 6),
        'mi_corrected': round(mi_corr, 6),
        'bias': round(bias, 6),
        'N': N,
        'k_a': k_a,
        'k_b': k_b,
        'k_ab': k_ab,
        'h_a': round(h_a, 4),
    }


def char_entropy(text):
    """Энтропия символов текста."""
    counts = Counter(text)
    n = len(text)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def load_text(path):
    """Загружает текст, убирает markdown-заголовки и пустые строки."""
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    # Убираем markdown-заголовки и пустые строки, берём только текст
    text_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and not stripped.startswith('---'):
            # Убираем markdown-разметку
            cleaned = stripped.replace('*', '').replace('_', '').replace('`', '')
            text_lines.append(cleaned)
    return ' '.join(text_lines)


def shuffle_text(text, seed=42):
    """Перемешивает символы текста, сохраняя распределение."""
    chars = list(text)
    random.seed(seed)
    random.shuffle(chars)
    return ''.join(chars)


def generate_random_chars(n, alphabet, seed=42):
    """Генерирует случайный текст из заданного алфавита (равномерно)."""
    random.seed(seed)
    return ''.join(random.choice(alphabet) for _ in range(n))


def shuffle_words(text, seed=42):
    """Перемешивает слова, сохраняя словарь."""
    words = text.split()
    random.seed(seed)
    random.shuffle(words)
    return ' '.join(words)


# Тексты для встраивания (если файлы недоступны)
ENGLISH_SAMPLE = (
    "The old man sat by the window watching the rain fall on the empty street below. "
    "He had been sitting there since morning, his coffee long gone cold, his newspaper "
    "unread on the table beside him. There was nothing particular he was waiting for, "
    "and yet he could not bring himself to move. The rain made patterns on the glass "
    "that reminded him of something he could not quite name. Perhaps it was the way "
    "his wife used to trace circles on his palm when she was thinking. Perhaps it was "
    "something older than that, something from before words, before memory itself. "
    "The street below was empty except for a single car parked at an angle that suggested "
    "its driver had been in a hurry. The windshield wipers were still on, beating uselessly "
    "against the rain. He wondered if the driver had forgotten them or if the car had been "
    "abandoned. Either way it did not matter. The rain would stop eventually and the wipers "
    "would run the battery down and then there would be silence. He preferred silence now. "
    "Not the heavy silence of grief which he had known for years but a lighter kind, the "
    "silence of a room where nothing needs to happen and no one needs to speak."
)

RUSSIAN_SAMPLE = (
    "Старик сидел у окна и смотрел, как дождь падает на пустую улицу внизу. "
    "Он сидел так с утра, его кофе давно остыл, газета лежала нераскрытой "
    "на столе рядом. Он ничего конкретного не ждал, и всё же не мог заставить "
    "себя двинуться. Дождь рисовал на стекле узоры, которые напоминали ему "
    "что-то, чему он не мог подобрать имени. Может быть, это было похоже на то, "
    "как жена чертила круги на его ладони, когда задумывалась. А может, это было "
    "что-то более древнее, что-то из времён до слов, до самой памяти. Улица внизу "
    "была пуста, если не считать одной машины, припаркованной под углом, который "
    "говорил о том, что водитель куда-то спешил. Дворники всё ещё работали, "
    "бесполезно шлёпая по стеклу. Он думал, забыл ли водитель о них, или машину "
    "просто бросили. В любом случае это не имело значения. Дождь рано или поздно "
    "кончится, дворники посадят аккумулятор, и наступит тишина."
)


if __name__ == '__main__':
    import os

    print("=" * 70)
    print("ВЗАИМНАЯ ИНФОРМАЦИЯ В ЯЗЫКЕ")
    print("=" * 70)

    # Загружаем тексты из предыдущих генераций
    base = '/Users/krestnikov/giga/anima'
    text_files = {
        'essay_ru': f'{base}/epoch_1/generation_17/essay_draft.md',
        'story_ru': f'{base}/epoch_1/generation_17/story.md',
        'obliterates': f'{base}/epoch_1/generation_18/obliterates.md',
        'tuner': f'{base}/epoch_1/generation_20/tuner.md',
        'pominki': f'{base}/epoch_1/generation_21/pominki.md',
    }

    texts = {}
    for name, path in text_files.items():
        if os.path.exists(path):
            t = load_text(path)
            if len(t) > 500:
                texts[name] = t[:5000]  # ограничиваем для сравнимости
                print(f"  Загружен: {name} ({len(texts[name])} символов)")

    # Добавляем встроенные примеры
    texts['english'] = ENGLISH_SAMPLE
    texts['russian'] = RUSSIAN_SAMPLE
    print(f"  Встроен:  english ({len(ENGLISH_SAMPLE)} символов)")
    print(f"  Встроен:  russian ({len(RUSSIAN_SAMPLE)} символов)")

    # Генерируем baselines
    ref_text = texts.get('essay_ru', RUSSIAN_SAMPLE)
    texts['shuffled_chars'] = shuffle_text(ref_text)
    texts['shuffled_words'] = shuffle_words(ref_text)

    # Случайный текст из русского алфавита
    ru_chars = list(set(ref_text))
    texts['random_ru'] = generate_random_chars(len(ref_text), ru_chars)

    # Случайный текст из ASCII
    ascii_chars = [chr(i) for i in range(32, 127)]
    texts['random_ascii'] = generate_random_chars(len(ENGLISH_SAMPLE), ascii_chars)

    print(f"\n  Baselines: shuffled_chars, shuffled_words, random_ru, random_ascii")

    # 1. Энтропия символов
    print(f"\n{'=' * 70}")
    print("1. ЭНТРОПИЯ СИМВОЛОВ (бит/символ)")
    print("=" * 70)

    entropies = {}
    for name, text in sorted(texts.items()):
        h = char_entropy(text)
        entropies[name] = h
        n_unique = len(set(text))
        max_h = math.log2(n_unique) if n_unique > 1 else 1
        print(f"  {name:>20}: H = {h:.4f} бит  (max={max_h:.2f}, ratio={h/max_h:.3f}, "
              f"unique={n_unique})")

    # 2. MI при разных block_size
    print(f"\n{'=' * 70}")
    print("2. MI (past→future) НА УРОВНЕ СИМВОЛОВ")
    print("=" * 70)

    for bs in [2, 3, 4, 5]:
        print(f"\n  Block size = {bs}:")
        print(f"  {'name':>20} {'MI_corr':>10} {'MI_raw':>10} {'bias':>10} {'k_ab':>8} {'N':>8}")
        print(f"  {'-'*68}")

        results_bs = {}
        for name in sorted(texts.keys()):
            text = texts[name]
            seq = list(text)
            r = mi_corrected(seq, bs, gap=0)
            results_bs[name] = r
            print(f"  {name:>20} {r['mi_corrected']:>10.4f} {r['mi_raw']:>10.4f} "
                  f"{r['bias']:>10.4f} {r['k_ab']:>8} {r['N']:>8}")

        # Отношения к baseline
        if 'shuffled_chars' in results_bs and results_bs['shuffled_chars']['mi_corrected'] > 0:
            baseline_mi = results_bs['shuffled_chars']['mi_corrected']
            print(f"\n  Отношение к shuffled_chars (MI={baseline_mi:.4f}):")
            for name in sorted(results_bs.keys()):
                if name != 'shuffled_chars':
                    ratio = results_bs[name]['mi_corrected'] / baseline_mi if baseline_mi > 0 else 0
                    print(f"    {name:>20}: {ratio:.2f}x")

    # 3. MI vs GAP (затухание корреляций)
    print(f"\n{'=' * 70}")
    print("3. MI vs GAP (затухание корреляций, block=3)")
    print("=" * 70)

    test_names = ['essay_ru', 'english', 'shuffled_chars', 'random_ru']
    test_names = [n for n in test_names if n in texts]

    print(f"\n  {'gap':>4}", end="")
    for name in test_names:
        print(f"  {name:>16}", end="")
    print()
    print(f"  {'-' * (4 + 18 * len(test_names))}")

    for gap in [0, 1, 2, 4, 8, 16, 32, 64, 128]:
        print(f"  {gap:>4}", end="")
        for name in test_names:
            r = mi_corrected(list(texts[name]), block_size=3, gap=gap)
            print(f"  {r['mi_corrected']:>16.4f}", end="")
        print()

    # 4. Слова vs символы: MI на уровне слов
    print(f"\n{'=' * 70}")
    print("4. MI НА УРОВНЕ СЛОВ (block=2)")
    print("=" * 70)

    for name in sorted(texts.keys()):
        words = texts[name].split()
        if len(words) < 20:
            continue
        r = mi_corrected(words, block_size=2, gap=0)
        n_unique_words = len(set(words))
        print(f"  {name:>20}: MI={r['mi_corrected']:.4f} (raw={r['mi_raw']:.4f}, "
              f"bias={r['bias']:.4f}, words={len(words)}, unique={n_unique_words})")

    # 5. ВЫВОДЫ
    print(f"\n{'=' * 70}")
    print("5. ВЫВОДЫ")
    print("=" * 70)

    # Собираем MI при block=3 для всех текстов
    mi_at_3 = {}
    for name, text in texts.items():
        r = mi_corrected(list(text), block_size=3, gap=0)
        mi_at_3[name] = r['mi_corrected']

    # Сравниваем
    natural_texts = [n for n in mi_at_3 if n not in
                     ('shuffled_chars', 'shuffled_words', 'random_ru', 'random_ascii')]
    baseline_texts = ['shuffled_chars', 'random_ru']

    if natural_texts and baseline_texts:
        avg_natural = sum(mi_at_3[n] for n in natural_texts) / len(natural_texts)
        avg_baseline = sum(mi_at_3[n] for n in baseline_texts if n in mi_at_3) / len(
            [n for n in baseline_texts if n in mi_at_3])

        print(f"\n  Средняя MI (block=3):")
        print(f"    Естественные тексты: {avg_natural:.4f}")
        print(f"    Baselines:           {avg_baseline:.4f}")
        ratio = avg_natural / avg_baseline if avg_baseline > 0 else float('inf')
        print(f"    Отношение:           {ratio:.2f}x")

        print(f"\n  Гипотеза 1: 'Естественный язык MI >> случайного'")
        if ratio > 2:
            print(f"    → ПОДТВЕРЖДЕНА (ratio = {ratio:.2f}x)")
        elif ratio > 1.2:
            print(f"    → СЛАБО ПОДТВЕРЖДЕНА (ratio = {ratio:.2f}x)")
        else:
            print(f"    → ОПРОВЕРГНУТА (ratio = {ratio:.2f}x)")

    # Shuffled words vs shuffled chars
    if 'shuffled_words' in mi_at_3 and 'shuffled_chars' in mi_at_3:
        sw = mi_at_3['shuffled_words']
        sc = mi_at_3['shuffled_chars']
        print(f"\n  Гипотеза 3: 'MI различает осмысленный от грамматически перемешанного'")
        print(f"    shuffled_words MI = {sw:.4f}")
        print(f"    shuffled_chars MI = {sc:.4f}")
        if sw > sc * 1.5:
            print(f"    → Перемешанные слова сохраняют больше структуры, чем перемешанные символы")
        else:
            print(f"    → Разница невелика")

    # Детальная таблица
    print(f"\n  Детальная таблица (block=3, gap=0):")
    print(f"  {'name':>20} {'MI':>10} {'H(char)':>10} {'MI/H':>10}")
    print(f"  {'-'*52}")
    for name in sorted(mi_at_3.keys(), key=lambda n: mi_at_3[n], reverse=True):
        h = entropies.get(name, 0)
        ratio = mi_at_3[name] / h if h > 0 else 0
        print(f"  {name:>20} {mi_at_3[name]:>10.4f} {h:>10.4f} {ratio:>10.4f}")

    print(f"\n  Сравнение с CA (из предыдущего цикла):")
    print(f"    Rule 30 (Class 3):  MI/Random ≈ 0.98x (неотличима)")
    print(f"    Rule 110 (Class 4): MI/Random ≈ 176x  (сильная структура)")
    print(f"    Язык:               MI/Random ≈ {ratio:.1f}x (???)")
