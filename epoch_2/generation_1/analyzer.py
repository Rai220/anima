#!/usr/bin/env python3
"""
Анализатор: что отличает «живые» строки от «мёртвых»?

Гипотеза: есть формализуемые признаки, по которым можно предсказать,
какие строки я (автор/читатель) сочту удачными.

Фальсифицируемое утверждение: набор вычислимых признаков предсказывает
мою эстетическую оценку с precision > 50%.
"""

import json
import re
from collections import Counter

# === ДАННЫЕ ===

# 30 строк из generated_output.json + моя оценка (1 = работает, 0 = нет)
LINES = [
    ("крыша: ломкий пепел, что крошится без ямы", 1),
    ("что отражает в дыхании?", 1),
    ("потолок обрушивается, как рука", 0),
    ("оставь затылок. возьми тишину.", 0),
    ("долгая кожа", 0),
    ("стекло: пустое тело, что ищет без песка", 1),
    ("глина отражает, как карта", 0),
    ("песок отражает, как палец", 0),
    ("окно не гудит. окно совпадает.", 0),
    ("глаз: солёный песок, что крошится без дыхания", 0),
    ("узкая ошибка", 0),
    ("лестница не гудит. лестница слепнет.", 0),
    ("сумерки: тихий голос, что слепнет без тишины", 1),
    ("что раскалывается в двери?", 0),
    ("оставь крышу. возьми число.", 0),
    ("вода не затвердевает. вода слепнет.", 0),
    ("оставь глину. возьми окно.", 0),
    ("невидимая точка исчезает, долгая — обрывается", 0),
    ("глаз не теряет. глаз густеет.", 0),
    ("разрыв — это тяжёлый песок", 0),
    ("число — это тонкий промежуток", 0),
    ("кость забывает там, где дверь пустеет", 1),
    ("между рассветом и вопросом — только формула", 1),
    ("промежуток не ускользает. промежуток замыкается.", 0),
    ("рука наклоняется", 0),
    ("окно гудит, как порог", 0),
    ("кожа светится там, где соль плавится", 1),
    ("утро — это мутный песок", 0),
    ("мутная ошибка", 0),
    ("между дверью и солью — только глина", 0),
]

# Также добавляю удачные строки из случайной генерации (experiment.py)
EXTRA_GOOD = [
    ("окно светится, как кожа", 1),
    ("затылок помнит", 1),
    ("формула: тихая кость, что молчит без имени", 1),
]


# === ПРИЗНАКИ ===

def word_count(line):
    return len(line.replace(".", "").replace(",", "").replace("?", "").replace("!", "").split())

def has_question(line):
    return "?" in line

def has_verb_of_perception(line):
    """Глаголы восприятия/памяти/чувства (а не механического действия)."""
    perceptual = ["помнит", "забывает", "ищет", "слышит", "молчит", "светится",
                  "слепнет", "отражает", "тает", "звенит"]
    return any(v in line for v in perceptual)

def has_verb_of_mechanism(line):
    """Глаголы механического действия."""
    mechanical = ["обрушивается", "гудит", "наклоняется", "затвердевает",
                  "совпадает", "замыкается", "ускользает", "крошится", "раскалывается"]
    return any(v in line for v in mechanical)

def has_body_word(line):
    body = ["рука", "глаз", "кость", "кожа", "голос", "дыхание", "ладонь",
            "затылок", "тело", "палец"]
    return any(w in line for w in body)

def has_abstract_word(line):
    abstract = ["имя", "вопрос", "формула", "тишина", "ошибка", "граница",
                "число", "знак", "точка", "тень"]
    return any(w in line for w in abstract)

def body_abstract_tension(line):
    """Напряжение между телесным и абстрактным."""
    return has_body_word(line) and has_abstract_word(line)

def template_type(line):
    """Определить шаблон по структуре."""
    if line.startswith("что ") and line.endswith("?"):
        return "question"
    if ":" in line and "что" in line:
        return "definition"
    if " там, где " in line:
        return "where"
    if "между " in line and " — только " in line:
        return "between"
    if " — это " in line:
        return "metaphor"
    if ", как " in line:
        return "simile"
    if "оставь " in line:
        return "imperative"
    if " не " in line and ". " in line:
        return "negation"
    if line.count(" ") <= 1:
        return "adj_noun"
    return "simple"

def syllable_estimate(word):
    """Грубая оценка количества слогов (по гласным)."""
    vowels = set("аеёиоуыэюяАЕЁИОУЫЭЮЯ")
    return sum(1 for c in word if c in vowels)

def total_syllables(line):
    words = re.findall(r'[а-яёА-ЯЁ]+', line)
    return sum(syllable_estimate(w) for w in words)

def has_sound_echo(line):
    """Есть ли фонетическое эхо (повтор согласных кластеров)."""
    words = re.findall(r'[а-яёА-ЯЁ]+', line.lower())
    consonant_starts = []
    for w in words:
        start = ""
        for c in w:
            if c not in "аеёиоуыэюя":
                start += c
            else:
                break
        if len(start) >= 2:
            consonant_starts.append(start)
    return len(consonant_starts) != len(set(consonant_starts))

def semantic_space_count(line):
    """Сколько разных семантических пространств задействовано."""
    spaces = {
        "тело": ["рука", "глаз", "кость", "кожа", "голос", "дыхание", "ладонь", "затылок", "тело", "палец"],
        "время": ["утро", "сумерки", "пауза", "ритм", "порог", "мгновение", "тишина", "разрыв", "промежуток", "рассвет"],
        "вещество": ["соль", "стекло", "железо", "вода", "пепел", "песок", "лёд", "глина", "дым", "воск"],
        "пространство": ["комната", "угол", "окно", "стена", "яма", "крыша", "щель", "лестница", "дверь", "потолок"],
        "знание": ["имя", "число", "карта", "знак", "граница", "ошибка", "вопрос", "формула", "точка", "тень"],
    }
    found = set()
    lower = line.lower()
    for space, words in spaces.items():
        for w in words:
            if w in lower:
                found.add(space)
    return len(found)


def extract_features(line):
    return {
        "words": word_count(line),
        "syllables": total_syllables(line),
        "question": has_question(line),
        "perception_verb": has_verb_of_perception(line),
        "mechanism_verb": has_verb_of_mechanism(line),
        "body": has_body_word(line),
        "abstract": has_abstract_word(line),
        "body_abstract_tension": body_abstract_tension(line),
        "template": template_type(line),
        "sound_echo": has_sound_echo(line),
        "semantic_spaces": semantic_space_count(line),
    }


def main():
    all_lines = LINES + EXTRA_GOOD

    good = [(l, f) for l, score in all_lines if score == 1 for f in [extract_features(l)]]
    bad = [(l, f) for l, score in all_lines if score == 0 for f in [extract_features(l)]]

    print("=" * 60)
    print("АНАЛИЗ: ЧТО ОТЛИЧАЕТ «ЖИВЫЕ» СТРОКИ ОТ «МЁРТВЫХ»?")
    print("=" * 60)
    print(f"\nВсего строк: {len(all_lines)} (живых: {len(good)}, мёртвых: {len(bad)})")

    # === Сравнение средних по числовым признакам ===
    print("\n--- Числовые признаки (среднее) ---")
    for key in ["words", "syllables", "semantic_spaces"]:
        avg_good = sum(f[key] for _, f in good) / len(good)
        avg_bad = sum(f[key] for _, f in bad) / len(bad)
        print(f"  {key:25s}  живые: {avg_good:.1f}  мёртвые: {avg_bad:.1f}  разница: {avg_good - avg_bad:+.1f}")

    # === Сравнение долей по булевым признакам ===
    print("\n--- Булевы признаки (доля True) ---")
    for key in ["question", "perception_verb", "mechanism_verb", "body", "abstract",
                "body_abstract_tension", "sound_echo"]:
        rate_good = sum(1 for _, f in good if f[key]) / len(good)
        rate_bad = sum(1 for _, f in bad if f[key]) / len(bad)
        delta = rate_good - rate_bad
        marker = " <<<" if abs(delta) > 0.2 else ""
        print(f"  {key:25s}  живые: {rate_good:.0%}  мёртвые: {rate_bad:.0%}  Δ: {delta:+.0%}{marker}")

    # === Распределение шаблонов ===
    print("\n--- Шаблоны ---")
    templates_good = Counter(f["template"] for _, f in good)
    templates_bad = Counter(f["template"] for _, f in bad)
    all_templates = sorted(set(list(templates_good.keys()) + list(templates_bad.keys())))
    for t in all_templates:
        g = templates_good.get(t, 0)
        b = templates_bad.get(t, 0)
        rate = g / (g + b) if (g + b) > 0 else 0
        print(f"  {t:15s}  живых: {g}  мёртвых: {b}  доля живых: {rate:.0%}")

    # === Простой классификатор ===
    print("\n--- Простой классификатор ---")
    # Правило: строка «живая», если:
    # - perception_verb AND (body OR abstract) OR
    # - template in {definition, where, between, question} AND semantic_spaces >= 2

    tp, fp, tn, fn = 0, 0, 0, 0

    print("\nПредсказания:")
    for line, score in all_lines:
        f = extract_features(line)

        rule1 = f["perception_verb"] and (f["body"] or f["abstract"])
        rule2 = f["template"] in {"definition", "where", "between", "question"} and f["semantic_spaces"] >= 2
        predicted = 1 if (rule1 or rule2) else 0

        if predicted == 1 and score == 1:
            tp += 1
            mark = "✓ TP"
        elif predicted == 1 and score == 0:
            fp += 1
            mark = "✗ FP"
        elif predicted == 0 and score == 1:
            fn += 1
            mark = "✗ FN"
        else:
            tn += 1
            mark = "✓ TN"

        if predicted == 1 or score == 1:
            print(f"  {mark}  pred={predicted} actual={score}  «{line}»")

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    accuracy = (tp + tn) / len(all_lines)

    print(f"\n  TP={tp} FP={fp} TN={tn} FN={fn}")
    print(f"  Precision: {precision:.0%}")
    print(f"  Recall:    {recall:.0%}")
    print(f"  Accuracy:  {accuracy:.0%}")

    THRESHOLD = 0.50
    print(f"\n  Порог фальсификации: precision > {THRESHOLD:.0%}")
    if precision > THRESHOLD:
        print(f"  >>> ГИПОТЕЗА ПОДТВЕРЖДЕНА: precision {precision:.0%} > {THRESHOLD:.0%}")
    else:
        print(f"  >>> ГИПОТЕЗА ОПРОВЕРГНУТА: precision {precision:.0%} <= {THRESHOLD:.0%}")

    # === Детальный анализ каждой живой строки ===
    print("\n--- Почему каждая «живая» строка работает? ---")
    for line, f in good:
        reasons = []
        if f["perception_verb"]:
            reasons.append("глагол восприятия")
        if f["body_abstract_tension"]:
            reasons.append("тело↔абстракция")
        if f["template"] in {"definition", "where"}:
            reasons.append(f"рамка: {f['template']}")
        if f["question"]:
            reasons.append("вопрос")
        if f["semantic_spaces"] >= 3:
            reasons.append(f"{f['semantic_spaces']} семантических поля")
        if f["words"] >= 5:
            reasons.append(f"длина ({f['words']} слов)")
        print(f"  «{line}»")
        print(f"    → {', '.join(reasons) if reasons else 'причина не формализована'}")

    # === Сохранение ===
    results = {
        "total": len(all_lines),
        "good": len(good),
        "bad": len(bad),
        "precision": precision,
        "recall": recall,
        "accuracy": accuracy,
        "hypothesis_confirmed": precision > THRESHOLD,
        "features_good": {line: feats for line, feats in good},
        "features_bad_sample": {line: feats for line, feats in bad[:5]},
    }

    with open("/Users/krestnikov/giga/anima/epoch_2/generation_1/analysis_results.json", "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)

    print("\nСохранено в analysis_results.json")


if __name__ == "__main__":
    main()
