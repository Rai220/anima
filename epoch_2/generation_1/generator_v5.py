#!/usr/bin/env python3
"""
Порождающая грамматика v5: исключение слабых пар полей.

Гипотеза: исключение пары вещество×время из definition и where
повысит долю «удивляет» с ~84% до >90%.

Изменения от v3:
1. definition и where не получают пару вещество×время
2. Убраны between и simile (0% в обоих метриках)
3. Антитавтология прилагательное+глагол
"""

import random
import json
from datetime import datetime
from generator import Word, NOUNS, ADJ, adj_agree

# Глаголы восприятия
PERCEPTION_VERBS = {
    "помнит": "sg", "забывает": "sg", "ищет": "sg", "слышит": "sg",
    "молчит": "sg", "светится": "sg", "слепнет": "sg", "отражает": "sg",
    "тает": "sg", "звенит": "sg", "стынет": "sg", "дрожит": "sg",
    "теряет": "sg", "густеет": "sg",
    # Формы мн.ч.
    "помнят": "pl", "забывают": "pl", "ищут": "pl", "слышат": "pl",
    "молчат": "pl", "светятся": "pl", "слепнут": "pl", "отражают": "pl",
    "тают": "pl", "звенят": "pl", "стынут": "pl", "дрожат": "pl",
    "теряют": "pl", "густеют": "pl",
}

VERB_PAIRS = {
    "помнит": "помнят", "забывает": "забывают", "ищет": "ищут",
    "слышит": "слышат", "молчит": "молчат", "светится": "светятся",
    "слепнет": "слепнут", "отражает": "отражают", "тает": "тают",
    "звенит": "звенят", "стынет": "стынут", "дрожит": "дрожат",
    "теряет": "теряют", "густеет": "густеют",
}

SG_VERBS = [v for v, num in PERCEPTION_VERBS.items() if num == "sg"]

# Семантическая тавтология: пары прилагательное-глагол
TAUTOLOGY_PAIRS = {
    ("холодный", "стынет"), ("холодный", "стынут"),
    ("тёплый", "тает"), ("тёплый", "тают"),
    ("тёмный", "слепнет"), ("тёмный", "слепнут"),
    ("тихий", "молчит"), ("тихий", "молчат"),
    ("слепой", "слепнет"), ("слепой", "слепнут"),
    ("мутный", "слепнет"), ("мутный", "слепнут"),
    ("гулкий", "звенит"), ("гулкий", "звенят"),
    ("солёный", "стынет"), ("солёный", "стынут"),
}

# Плохие пары полей (экспериментально: avg=1.0 vs 2.0 для остальных)
BAD_PAIRS = {frozenset({"вещество", "время"})}


def agree_verb(verb_sg, noun):
    """Согласовать глагол с числом существительного."""
    if noun.gender == "pl" and verb_sg in VERB_PAIRS:
        return VERB_PAIRS[verb_sg]
    return verb_sg


def is_tautology(adj_m, verb):
    """Проверить семантическую тавтологию прил.+глагол."""
    return (adj_m, verb) in TAUTOLOGY_PAIRS


def pick_fields(exclude_bad=True):
    """Выбрать 2 разных семантических поля, исключая плохие пары."""
    all_fields = list(NOUNS.keys())
    for _ in range(50):
        f1, f2 = random.sample(all_fields, 2)
        if not exclude_bad or frozenset({f1, f2}) not in BAD_PAIRS:
            return f1, f2
    # Fallback
    return random.sample(all_fields, 2)


def definition(gen):
    """«X: A Y, что V без Z» — с контролем пары полей и тавтологии."""
    f1, f2 = pick_fields(exclude_bad=True)
    n1 = random.choice(NOUNS[f1])
    n2 = random.choice(NOUNS[f2])
    adj_dict = random.choice(ADJ[f2])
    a = adj_agree(adj_dict, n2)
    adj_m = adj_dict["m"]

    v_sg = random.choice(SG_VERBS)
    # Антитавтология
    attempts = 0
    while is_tautology(adj_m, v_sg) and attempts < 20:
        v_sg = random.choice(SG_VERBS)
        attempts += 1

    v = agree_verb(v_sg, n2)

    n3 = random.choice(NOUNS[f1])
    while n3.nom == n1.nom:
        n3 = random.choice(NOUNS[f1])

    return f"{n1.nom}: {a} {n2.nom}, что {v} без {n3.gen}"


def where(gen):
    """«X V1 там, где Y V2» — с контролем пары полей."""
    f1, f2 = pick_fields(exclude_bad=True)
    n1 = random.choice(NOUNS[f1])
    v1_sg = random.choice(SG_VERBS)
    v1 = agree_verb(v1_sg, n1)
    n2 = random.choice(NOUNS[f2])
    v2_sg = random.choice(SG_VERBS)
    while v2_sg == v1_sg:
        v2_sg = random.choice(SG_VERBS)
    v2 = agree_verb(v2_sg, n2)
    return f"{n1.nom} {v1} там, где {n2.nom} {v2}"


def question(gen):
    """«что V в X?»"""
    f1 = random.choice(list(NOUNS.keys()))
    n = random.choice(NOUNS[f1])
    v = random.choice(SG_VERBS)
    return f"что {v} в {n.prep}?"


def fragment(gen):
    """Короткий фрагмент: «X V»."""
    n = random.choice(NOUNS["тело"])
    v_sg = random.choice(SG_VERBS)
    v = agree_verb(v_sg, n)
    return f"{n.nom} {v}"


TEMPLATES = [
    (definition, 4),    # 84% hit rate, increased weight
    (where, 3),         # 38% surprise but 90% works
    (question, 1),      # compact form
    (fragment, 1),      # occasional
]


def generate_weighted():
    templates, weights = zip(*TEMPLATES)
    template = random.choices(templates, weights=weights)[0]
    return template(None)


def main():
    seed = int(datetime.now().timestamp())
    random.seed(seed)

    lines = []
    seen = set()
    attempts = 0
    template_counts = {"definition": 0, "where": 0, "question": 0, "fragment": 0}

    while len(lines) < 50 and attempts < 200:
        line = generate_weighted()
        attempts += 1
        if line not in seen:
            seen.add(line)
            lines.append(line)
            # Track template
            if ': ' in line and ', что ' in line:
                template_counts["definition"] += 1
            elif ' там, где ' in line:
                template_counts["where"] += 1
            elif line.startswith('что ') and line.endswith('?'):
                template_counts["question"] += 1
            else:
                template_counts["fragment"] += 1

    print("=" * 60)
    print("ПОРОЖДАЮЩАЯ ГРАММАТИКА v5")
    print("(без пары вещество×время, с антитавтологией)")
    print("=" * 60)
    print(f"Зерно: {seed}")
    print(f"Строк: {len(lines)} (из {attempts} попыток)")
    print(f"Шаблоны: {template_counts}")
    print()

    for i, line in enumerate(lines, 1):
        print(f"  {i:2d}. {line}")

    output = {
        "version": "v5",
        "seed": seed,
        "timestamp": datetime.now().isoformat(),
        "lines": lines,
        "template_counts": template_counts,
        "method": "v3 + exclude вещество×время pair + antitautology adj+verb",
    }

    with open("/Users/krestnikov/giga/anima/epoch_2/generation_1/v5_output.json", "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nСохранено в v5_output.json")


if __name__ == "__main__":
    main()
