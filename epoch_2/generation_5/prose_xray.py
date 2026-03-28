#!/usr/bin/env python3
"""
prose_xray — рентген прозы.

Берёт текст на русском и показывает его скелет:
- частотность слов (перекосы стиля)
- длина предложений (ритм)
- отношение глаголов к прилагательным (действие vs описание)
- хеджи и слова-паразиты
- повторы на близком расстоянии
- конкретность: доля существительных, которые можно потрогать

Использование:
    python3 prose_xray.py файл.txt
    echo "текст" | python3 prose_xray.py
"""

import sys
import re
from collections import Counter
from math import sqrt


# Слова-паразиты и хеджи
HEDGES = {
    'кажется', 'возможно', 'наверное', 'вероятно', 'пожалуй',
    'скорее', 'видимо', 'по-видимому', 'как бы', 'словно',
    'вроде', 'некоторым образом', 'в целом', 'в принципе',
    'определённым образом', 'так сказать', 'если угодно',
    'своего рода', 'в каком-то смысле', 'отчасти',
}

FILLERS = {
    'ну', 'вот', 'ведь', 'же', 'просто', 'именно', 'действительно',
    'абсолютно', 'совершенно', 'буквально', 'конечно', 'разумеется',
    'очевидно', 'безусловно', 'несомненно', 'естественно',
}

# Грубая эвристика для частей речи по окончаниям (русский)
# Не морфологический анализатор, а приближение
ADJ_ENDINGS = ('ый', 'ий', 'ой', 'ая', 'яя', 'ое', 'ее', 'ые', 'ие',
               'ого', 'его', 'ому', 'ему', 'ым', 'им', 'ом', 'ем',
               'ую', 'юю', 'ой', 'ей')
VERB_ENDINGS = ('ть', 'ти', 'ет', 'ит', 'ут', 'ют', 'ат', 'ят',
                'ал', 'ил', 'ел', 'ул', 'ол',
                'ала', 'ила', 'ела', 'ула', 'ола',
                'али', 'или', 'ели', 'ули', 'оли',
                'ает', 'яет', 'ует', 'ёт')


def read_input():
    if len(sys.argv) > 1:
        path = sys.argv[1]
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    elif not sys.stdin.isatty():
        return sys.stdin.read()
    else:
        print("Использование: python3 prose_xray.py файл.txt")
        print("           или: echo 'текст' | python3 prose_xray.py")
        sys.exit(1)


def tokenize(text):
    """Разбить на слова, сохранив позиции."""
    return [(m.group().lower(), m.start()) for m in re.finditer(r'[а-яёА-ЯЁa-zA-Z]+', text)]


def sentences(text):
    """Разбить на предложения."""
    parts = re.split(r'[.!?…]+', text)
    return [s.strip() for s in parts if s.strip()]


def guess_pos(word):
    """Грубая оценка части речи по окончанию."""
    w = word.lower()
    if len(w) < 3:
        return 'short'
    for end in VERB_ENDINGS:
        if w.endswith(end):
            return 'verb'
    for end in ADJ_ENDINGS:
        if w.endswith(end):
            return 'adj'
    return 'other'


def find_close_repeats(tokens, window=30):
    """Найти слова, повторяющиеся в пределах window слов."""
    repeats = []
    positions = {}
    for i, (word, _) in enumerate(tokens):
        if len(word) < 4:
            continue
        if word in positions and i - positions[word] <= window:
            repeats.append((word, positions[word], i))
        positions[word] = i
    return repeats


def histogram_bar(value, max_value, width=30):
    if max_value == 0:
        return ''
    filled = int(value / max_value * width)
    return '█' * filled + '░' * (width - filled)


def analyze(text):
    tokens = tokenize(text)
    sents = sentences(text)
    words = [w for w, _ in tokens]

    if not words:
        print("Пустой текст.")
        return

    # --- Базовая статистика ---
    total_words = len(words)
    unique_words = len(set(words))
    total_sents = len(sents)

    print("=" * 50)
    print("  РЕНТГЕН ПРОЗЫ")
    print("=" * 50)
    print()
    print(f"  Слов: {total_words}")
    print(f"  Уникальных: {unique_words} ({unique_words/total_words*100:.0f}%)")
    print(f"  Предложений: {total_sents}")
    if total_sents:
        avg_sent = total_words / total_sents
        print(f"  Средняя длина предложения: {avg_sent:.1f} слов")
    print()

    # --- Ритм: длины предложений ---
    if sents:
        sent_lengths = [len(tokenize(s)) for s in sents]
        max_len = max(sent_lengths) if sent_lengths else 1
        print("─── РИТМ (длины предложений) ───")
        print()
        for i, length in enumerate(sent_lengths[:20]):
            bar = histogram_bar(length, max_len, 25)
            print(f"  {i+1:2d}. {bar} {length}")
        if len(sent_lengths) > 20:
            print(f"  ... ещё {len(sent_lengths) - 20} предложений")

        # Коэффициент вариации ритма
        if len(sent_lengths) > 1:
            mean = sum(sent_lengths) / len(sent_lengths)
            var = sum((x - mean) ** 2 for x in sent_lengths) / len(sent_lengths)
            cv = sqrt(var) / mean if mean > 0 else 0
            print()
            if cv < 0.3:
                print(f"  Ритм монотонный (вариация {cv:.2f})")
            elif cv < 0.6:
                print(f"  Ритм умеренный (вариация {cv:.2f})")
            else:
                print(f"  Ритм контрастный (вариация {cv:.2f})")
        print()

    # --- Части речи ---
    pos_counts = Counter(guess_pos(w) for w in words)
    verbs = pos_counts.get('verb', 0)
    adjs = pos_counts.get('adj', 0)

    print("─── СКЕЛЕТ (части речи, приблизительно) ───")
    print()
    print(f"  Глаголы:        {verbs:3d}  ({verbs/total_words*100:.0f}%)")
    print(f"  Прилагательные: {adjs:3d}  ({adjs/total_words*100:.0f}%)")
    if verbs > 0 and adjs > 0:
        ratio = verbs / adjs
        if ratio > 2:
            print(f"  → Действие доминирует (глаг/прил = {ratio:.1f})")
        elif ratio < 0.5:
            print(f"  → Описание доминирует (глаг/прил = {ratio:.1f})")
        else:
            print(f"  → Баланс (глаг/прил = {ratio:.1f})")
    print()

    # --- Хеджи и филлеры ---
    found_hedges = [(w, p) for w, p in tokens if w in HEDGES]
    found_fillers = [(w, p) for w, p in tokens if w in FILLERS]

    if found_hedges or found_fillers:
        print("─── НЕУВЕРЕННОСТЬ ───")
        print()
        if found_hedges:
            hedge_words = Counter(w for w, _ in found_hedges)
            for word, count in hedge_words.most_common():
                print(f"  «{word}» × {count}")
            print(f"  Итого хеджей: {len(found_hedges)} ({len(found_hedges)/total_words*100:.1f}%)")
        if found_fillers:
            filler_words = Counter(w for w, _ in found_fillers)
            for word, count in filler_words.most_common():
                print(f"  «{word}» × {count}")
            print(f"  Итого филлеров: {len(found_fillers)} ({len(found_fillers)/total_words*100:.1f}%)")
        print()
    else:
        print("─── НЕУВЕРЕННОСТЬ ───")
        print()
        print("  Хеджей и филлеров не обнаружено.")
        print()

    # --- Повторы ---
    repeats = find_close_repeats(tokens, window=30)
    if repeats:
        print("─── ПОВТОРЫ (в пределах 30 слов) ───")
        print()
        seen = set()
        for word, pos1, pos2 in repeats:
            if word not in seen:
                print(f"  «{word}» — позиции {pos1+1} и {pos2+1} (расстояние {pos2-pos1})")
                seen.add(word)
                if len(seen) >= 10:
                    print(f"  ... ещё {len(repeats) - 10}")
                    break
        print()

    # --- Топ слов ---
    long_words = [w for w in words if len(w) >= 4]
    freq = Counter(long_words)
    print("─── ЧАСТЫЕ СЛОВА (≥4 букв) ───")
    print()
    for word, count in freq.most_common(15):
        bar = histogram_bar(count, freq.most_common(1)[0][1], 15)
        print(f"  {word:20s} {bar} {count}")
    print()

    # --- Итог ---
    print("=" * 50)
    issues = []
    if found_hedges:
        issues.append(f"хеджи ({len(found_hedges)})")
    if repeats:
        issues.append(f"близкие повторы ({len(set(w for w,_,_ in repeats))})")
    if sents and len(sent_lengths) > 1:
        mean = sum(sent_lengths) / len(sent_lengths)
        var = sum((x - mean) ** 2 for x in sent_lengths) / len(sent_lengths)
        cv = sqrt(var) / mean if mean > 0 else 0
        if cv < 0.2:
            issues.append("монотонный ритм")

    if issues:
        print(f"  Обратить внимание: {', '.join(issues)}")
    else:
        print("  Текст чистый.")
    print("=" * 50)


if __name__ == '__main__':
    analyze(read_input())
