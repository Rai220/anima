#!/usr/bin/env python3
"""
Порождающая грамматика v3: информированная анализом.

Используем только шаблоны и лексику, которые анализатор определил как
коррелирующие с «живыми» строками:
- шаблоны: definition, where (+ question как бонус)
- глаголы: только восприятия/памяти
- слова тела — предпочтительны

Фальсифицируемое утверждение: v3 произведёт >20% «живых» строк
(vs ~6% у v2, где 10/160).
"""

import random
import json
from datetime import datetime
from generator import Word, NOUNS, ADJ, adj_agree

# Глаголы восприятия/памяти/чувства — те, что коррелируют с «живыми» строками
PERCEPTION_VERBS = [
    "помнит", "забывает", "ищет", "слышит", "молчит", "светится",
    "слепнет", "отражает", "тает", "звенит", "стынет", "дрожит",
    "теряет", "густеет",
]

# Только шаблоны с высокой долей «живых»
def definition(gen):
    """«X: A Y, что V без Z» — 80% живых."""
    f1, f2 = random.sample(list(NOUNS.keys()), 2)
    n1 = random.choice(NOUNS[f1])
    n2 = random.choice(NOUNS[f2])
    adj_dict = random.choice(ADJ[f2])
    a = adj_agree(adj_dict, n2)
    v = random.choice(PERCEPTION_VERBS)
    n3 = random.choice(NOUNS[f1])
    while n3.nom == n1.nom:
        n3 = random.choice(NOUNS[f1])
    return f"{n1.nom}: {a} {n2.nom}, что {v} без {n3.gen}"


def where(gen):
    """«X V1 там, где Y V2» — 100% живых."""
    f1, f2 = random.sample(list(NOUNS.keys()), 2)
    n1 = random.choice(NOUNS[f1])
    v1 = random.choice(PERCEPTION_VERBS)
    n2 = random.choice(NOUNS[f2])
    v2 = random.choice(PERCEPTION_VERBS)
    # Разные глаголы
    while v2 == v1:
        v2 = random.choice(PERCEPTION_VERBS)
    return f"{n1.nom} {v1} там, где {n2.nom} {v2}"


def question(gen):
    """«что V в X?» — 50% живых, но компактная форма."""
    f1 = random.choice(list(NOUNS.keys()))
    n = random.choice(NOUNS[f1])
    v = random.choice(PERCEPTION_VERBS)
    return f"что {v} в {n.prep}?"


def between_abstract(gen):
    """«между X и Y — только Z» с абстрактными/временными словами."""
    # Предпочитаем время+знание (наиболее абстрактная комбинация)
    fields = random.sample(["время", "знание", "вещество"], 2)
    f1, f2 = fields
    n1 = random.choice(NOUNS[f1])
    n2 = random.choice(NOUNS[f2])
    # Третье слово — из другого поля
    f3 = random.choice([f for f in NOUNS.keys() if f not in fields])
    n3 = random.choice(NOUNS[f3])
    return f"между {n1.inst} и {n2.inst} — только {n3.nom}"


def simile_perception(gen):
    """«X V, как Y» но только с глаголами восприятия."""
    f1, f2 = random.sample(list(NOUNS.keys()), 2)
    n1 = random.choice(NOUNS[f1])
    v = random.choice(PERCEPTION_VERBS)
    n2 = random.choice(NOUNS[f2])
    return f"{n1.nom} {v}, как {n2.nom}"


def fragment(gen):
    """Короткий фрагмент: «X V» — как «затылок помнит»."""
    # Предпочитаем тело
    n = random.choice(NOUNS["тело"])
    v = random.choice(PERCEPTION_VERBS)
    return f"{n.nom} {v}"


TEMPLATES = [
    (definition, 3),      # 80% hit rate, weight 3
    (where, 3),           # 100% hit rate, weight 3
    (question, 1),        # 50%, lower weight
    (between_abstract, 1),# 50%
    (simile_perception, 1),# 20% but with perception verbs might improve
    (fragment, 1),        # worked for "затылок помнит"
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
    while len(lines) < 50 and attempts < 200:
        line = generate_weighted()
        attempts += 1
        if line not in seen:
            seen.add(line)
            lines.append(line)

    print("=" * 60)
    print("ПОРОЖДАЮЩАЯ ГРАММАТИКА v3 (информированная анализом)")
    print("=" * 60)
    print(f"Зерно: {seed}")
    print(f"Строк: {len(lines)} (из {attempts} попыток)")
    print()

    for i, line in enumerate(lines, 1):
        print(f"  {i:2d}. {line}")

    output = {
        "version": "v3",
        "seed": seed,
        "timestamp": datetime.now().isoformat(),
        "lines": lines,
        "method": "informed by analyzer.py: perception verbs + definition/where templates",
    }

    with open("/Users/krestnikov/giga/anima/epoch_2/generation_1/v3_output.json", "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nСохранено в v3_output.json")


if __name__ == "__main__":
    main()
