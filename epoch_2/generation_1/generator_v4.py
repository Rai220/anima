#!/usr/bin/env python3
"""
Порождающая грамматика v4: генерация + фильтрация.

Ключевая идея: v3 генерирует с правильными шаблонами и глаголами,
но 62% выхода — мусор. v4 добавляет постфильтрацию:

1. Грамматический фильтр: отсеивает рассогласование числа (сумерки + sg глагол)
2. Антитавтология: отсеивает строки, где прилагательное и существительное
   из одного семантического корня (солёная соль, тёмная тень)
3. Семантическое расстояние: отсеивает строки, где ключевые слова
   из одного семантического поля (вещество+вещество = нет напряжения)

Фальсифицируемое утверждение: v4 произведёт >50% живых строк
(vs 38% у v3).
"""

import random
import json
from datetime import datetime
from generator import Word, NOUNS, ADJ, adj_agree

# === ГЛАГОЛЫ ВОСПРИЯТИЯ (из v3) ===

PERCEPTION_VERBS_SG = [
    "помнит", "забывает", "ищет", "слышит", "молчит", "светится",
    "слепнет", "отражает", "тает", "звенит", "стынет", "дрожит",
    "теряет", "густеет",
]

# Формы множественного числа для согласования
PERCEPTION_VERBS_PL = [
    "помнят", "забывают", "ищут", "слышат", "молчат", "светятся",
    "слепнут", "отражают", "тают", "звенят", "стынут", "дрожат",
    "теряют", "густеют",
]

# Индекс: sg -> pl
VERB_SG_TO_PL = dict(zip(PERCEPTION_VERBS_SG, PERCEPTION_VERBS_PL))

# === ТАВТОЛОГИЧЕСКИЕ ПАРЫ ===
# Прилагательное + существительное из одного «корня» или очевидной связи
TAUTOLOGY_PAIRS = {
    ("солёный", "соль"), ("солёная", "соль"), ("солёное", "соль"),
    ("тёмный", "тень"), ("тёмная", "тень"), ("тёмное", "тень"),
    ("холодный", "лёд"), ("холодная", "лёд"), ("холодное", "лёд"),
    ("пустой", "яма"), ("пустая", "яма"), ("пустое", "яма"),
    ("мутный", "вода"), ("мутная", "вода"), ("мутное", "вода"),
    ("ломкий", "кость"), ("ломкая", "кость"), ("ломкое", "кость"),
    ("слепой", "слепнет"), ("слепая", "слепнет"),
    ("тихий", "тишина"), ("тихая", "тишина"), ("тихое", "тишина"),
    ("точный", "точка"), ("точная", "точка"), ("точное", "точка"),
    ("узкий", "щель"), ("узкая", "щель"), ("узкое", "щель"),
    ("глубокий", "яма"), ("глубокая", "яма"), ("глубокое", "яма"),
}


def get_field(word_nom):
    """Определить семантическое поле слова по его номинативу."""
    for field, words in NOUNS.items():
        for w in words:
            if w.nom == word_nom:
                return field
    return None


def verb_for_noun(noun, verb_idx=None):
    """Выбрать глагол, согласованный с числом существительного."""
    if verb_idx is None:
        verb_idx = random.randrange(len(PERCEPTION_VERBS_SG))
    if noun.gender == "pl":
        return PERCEPTION_VERBS_PL[verb_idx]
    return PERCEPTION_VERBS_SG[verb_idx]


def random_verb_pair(n1, n2):
    """Два разных глагола, согласованных с существительными."""
    idx1 = random.randrange(len(PERCEPTION_VERBS_SG))
    idx2 = random.randrange(len(PERCEPTION_VERBS_SG))
    while idx2 == idx1:
        idx2 = random.randrange(len(PERCEPTION_VERBS_SG))
    return verb_for_noun(n1, idx1), verb_for_noun(n2, idx2)


# === ШАБЛОНЫ (из v3, с исправлением грамматики) ===

def definition(n1, n2, adj_str, v_str, n3):
    return f"{n1.nom}: {adj_str} {n2.nom}, что {v_str} без {n3.gen}"


def where(n1, v1_str, n2, v2_str):
    return f"{n1.nom} {v1_str} там, где {n2.nom} {v2_str}"


def question(n, v_str):
    return f"что {v_str} в {n.prep}?"


def between_tmpl(n1, n2, n3):
    return f"между {n1.inst} и {n2.inst} — только {n3.nom}"


def simile(n1, v_str, n2):
    return f"{n1.nom} {v_str}, как {n2.nom}"


def fragment(n, v_str):
    return f"{n.nom} {v_str}"


# === ГЕНЕРАЦИЯ С МЕТАДАННЫМИ ===

def generate_one():
    """Генерирует строку + метаданные для фильтрации."""
    templates = ["definition", "definition", "definition",
                 "where", "where", "where",
                 "question", "between", "simile", "fragment"]
    tmpl = random.choice(templates)

    if tmpl == "definition":
        f1, f2 = random.sample(list(NOUNS.keys()), 2)
        n1 = random.choice(NOUNS[f1])
        n2 = random.choice(NOUNS[f2])
        adj_dict = random.choice(ADJ[f2])
        adj_str = adj_agree(adj_dict, n2)
        v_idx = random.randrange(len(PERCEPTION_VERBS_SG))
        v_str = verb_for_noun(n1, v_idx)  # Согласуем с n1 (подлежащее в «что V»)
        # n3 из третьего поля (максимизируем расстояние)
        remaining = [f for f in NOUNS.keys() if f not in (f1, f2)]
        if not remaining:
            remaining = [f for f in NOUNS.keys() if f != f1]
        f3 = random.choice(remaining)
        n3 = random.choice(NOUNS[f3])
        line = definition(n1, n2, adj_str, v_str, n3)
        fields_used = {f1, f2, f3}
        adj_noun_pair = (adj_str, n2.nom)

    elif tmpl == "where":
        f1, f2 = random.sample(list(NOUNS.keys()), 2)
        n1 = random.choice(NOUNS[f1])
        n2 = random.choice(NOUNS[f2])
        v1_str, v2_str = random_verb_pair(n1, n2)
        line = where(n1, v1_str, n2, v2_str)
        fields_used = {f1, f2}
        adj_noun_pair = None

    elif tmpl == "question":
        f1 = random.choice(list(NOUNS.keys()))
        n = random.choice(NOUNS[f1])
        # Для вопроса глагол в 3л ед — «что V в X?»
        v_idx = random.randrange(len(PERCEPTION_VERBS_SG))
        v_str = PERCEPTION_VERBS_SG[v_idx]
        line = question(n, v_str)
        fields_used = {f1}
        adj_noun_pair = None

    elif tmpl == "between":
        f1, f2 = random.sample(list(NOUNS.keys()), 2)
        n1 = random.choice(NOUNS[f1])
        n2 = random.choice(NOUNS[f2])
        remaining = [f for f in NOUNS.keys() if f not in (f1, f2)]
        if not remaining:
            remaining = [f for f in NOUNS.keys() if f != f1]
        f3 = random.choice(remaining)
        n3 = random.choice(NOUNS[f3])
        line = between_tmpl(n1, n2, n3)
        fields_used = {f1, f2, f3}
        adj_noun_pair = None

    elif tmpl == "simile":
        f1, f2 = random.sample(list(NOUNS.keys()), 2)
        n1 = random.choice(NOUNS[f1])
        v_idx = random.randrange(len(PERCEPTION_VERBS_SG))
        v_str = verb_for_noun(n1, v_idx)
        n2 = random.choice(NOUNS[f2])
        line = simile(n1, v_str, n2)
        fields_used = {f1, f2}
        adj_noun_pair = None

    else:  # fragment
        n = random.choice(NOUNS["тело"])
        v_idx = random.randrange(len(PERCEPTION_VERBS_SG))
        v_str = verb_for_noun(n, v_idx)
        line = fragment(n, v_str)
        fields_used = {"тело"}
        adj_noun_pair = None

    return {
        "line": line,
        "template": tmpl,
        "fields_used": fields_used,
        "adj_noun_pair": adj_noun_pair,
    }


# === ФИЛЬТРЫ ===

def filter_tautology(meta):
    """Отсеивает тавтологические пары прилагательное+существительное."""
    if meta["adj_noun_pair"] is None:
        return True
    return meta["adj_noun_pair"] not in TAUTOLOGY_PAIRS


def filter_semantic_distance(meta):
    """Отсеивает строки, где все ключевые слова из одного поля.

    Требует минимум 2 разных семантических поля (кроме question и fragment).
    """
    if meta["template"] in ("question", "fragment"):
        return True  # Эти шаблоны и с одним полем работают
    return len(meta["fields_used"]) >= 2


def filter_same_word_repetition(meta):
    """Отсеивает строки, где одно слово повторяется (кроме как в разных формах)."""
    words = meta["line"].replace(",", "").replace(".", "").replace("?", "").replace("!", "").replace(":", "").replace("—", "").split()
    # Нормализованные корни (грубо — первые 3 буквы)
    stems = [w[:4].lower() for w in words if len(w) > 2]
    # Если один стем повторяется (но не служебные слова)
    service = {"что", "там", "где", "без", "как", "межд", "толь", "меж"}
    content_stems = [s for s in stems if s not in service]
    return len(content_stems) == len(set(content_stems))


FILTERS = [filter_tautology, filter_semantic_distance, filter_same_word_repetition]


def passes_all_filters(meta):
    return all(f(meta) for f in FILTERS)


# === ОСНОВНОЙ ЦИКЛ ===

def main():
    seed = int(datetime.now().timestamp())
    random.seed(seed)

    target = 50
    max_attempts = 500

    lines = []
    seen = set()
    rejected = {"tautology": 0, "distance": 0, "repetition": 0, "duplicate": 0}
    attempts = 0

    while len(lines) < target and attempts < max_attempts:
        meta = generate_one()
        attempts += 1

        if meta["line"] in seen:
            rejected["duplicate"] += 1
            continue

        if not filter_tautology(meta):
            rejected["tautology"] += 1
            continue
        if not filter_semantic_distance(meta):
            rejected["distance"] += 1
            continue
        if not filter_same_word_repetition(meta):
            rejected["repetition"] += 1
            continue

        seen.add(meta["line"])
        lines.append(meta)

    print("=" * 60)
    print("ПОРОЖДАЮЩАЯ ГРАММАТИКА v4 (генерация + фильтрация)")
    print("=" * 60)
    print(f"Зерно: {seed}")
    print(f"Строк: {len(lines)} из {attempts} попыток")
    print(f"Отклонено: {sum(rejected.values())} "
          f"(тавтология: {rejected['tautology']}, "
          f"расстояние: {rejected['distance']}, "
          f"повтор: {rejected['repetition']}, "
          f"дубликат: {rejected['duplicate']})")
    print()

    for i, meta in enumerate(lines, 1):
        fields = "+".join(sorted(meta["fields_used"]))
        print(f"  {i:2d}. [{meta['template']:10s}] [{fields}] {meta['line']}")

    # Сохранение
    output = {
        "version": "v4",
        "seed": seed,
        "timestamp": datetime.now().isoformat(),
        "lines": [m["line"] for m in lines],
        "details": [
            {"line": m["line"], "template": m["template"],
             "fields": sorted(m["fields_used"])}
            for m in lines
        ],
        "stats": {
            "generated": len(lines),
            "attempts": attempts,
            "rejected": rejected,
        },
        "method": "v3 templates + perception verbs + post-filtering "
                  "(tautology, semantic distance, repetition)",
    }

    with open("/Users/krestnikov/giga/anima/epoch_2/generation_1/v4_output.json", "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nСохранено в v4_output.json")


if __name__ == "__main__":
    main()
