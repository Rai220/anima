"""
Цикл 5: Формальная классификация сложности всех 256 элементарных CA.

Два измерения:
1. MI_magnitude = max(MI_single, MI_random) — насколько правило вообще сложно
2. Robustness R = min(MI_single, MI_random) / max(MI_single, MI_random) — устойчивость к IC

Категории:
- Robust complex: MI_mag > 10x AND R > 0.5
- Passive complex: MI_mag > 10x AND R < 0.5 (сложность зависит от IC)
- Simple/chaotic: MI_mag < 2x
- Intermediate: 2x < MI_mag < 10x
"""

import json
import sys

# Загрузка данных
with open("mi_all_rules_results.json") as f:
    single_data = json.load(f)

with open("mi_random_init_results.json") as f:
    random_data = json.load(f)

# Индексация по правилу
single_by_rule = {}
for r in single_data["rules"]:
    single_by_rule[r["rule"]] = r

random_by_rule = {}
for r in random_data["results"]:
    random_by_rule[r["rule"]] = r

# Классификация
categories = {
    "robust_complex": [],    # MI > 10x, R > 0.5
    "passive_complex": [],   # MI > 10x, R < 0.5
    "intermediate": [],      # 2x < MI < 10x
    "simple_chaotic": [],    # MI < 2x
}

all_rules = []

for rule_num in range(256):
    single = single_by_rule.get(rule_num)
    random = random_by_rule.get(rule_num)

    if single is None or random is None:
        continue

    mi_single = single["mi_ratio"]
    mi_random = random["mi_ratio"]

    mi_mag = max(mi_single, mi_random)
    mi_min = min(mi_single, mi_random)

    # Robustness: 1.0 = идеально устойчив, 0.0 = полностью IC-зависим
    if mi_mag > 0.01:
        R = mi_min / mi_mag
    else:
        R = 0.0

    entry = {
        "rule": rule_num,
        "mi_single": mi_single,
        "mi_random": mi_random,
        "mi_mag": mi_mag,
        "R": R,
        "entropy_single": single["entropy"],
        "entropy_random": random["entropy"],
    }
    all_rules.append(entry)

    if mi_mag > 10:
        if R > 0.5:
            categories["robust_complex"].append(entry)
        else:
            categories["passive_complex"].append(entry)
    elif mi_mag > 2:
        categories["intermediate"].append(entry)
    else:
        categories["simple_chaotic"].append(entry)

# Отчёт
print("=" * 70)
print("КЛАССИФИКАЦИЯ СЛОЖНОСТИ 256 ЭЛЕМЕНТАРНЫХ CA")
print("=" * 70)

for cat_name, cat_rules in categories.items():
    cat_rules.sort(key=lambda x: -x["mi_mag"])
    print(f"\n{'=' * 70}")
    print(f"  {cat_name.upper()}: {len(cat_rules)} правил")
    print(f"{'=' * 70}")

    if cat_name in ("robust_complex", "passive_complex", "intermediate"):
        for r in cat_rules:
            direction = ""
            if r["mi_single"] > 2 * r["mi_random"]:
                direction = " [single >> random]"
            elif r["mi_random"] > 2 * r["mi_single"]:
                direction = " [random >> single]"
            print(f"  Rule {r['rule']:3d}: MI_mag={r['mi_mag']:6.1f}x  R={r['R']:.3f}  "
                  f"(single={r['mi_single']:.1f}x, random={r['mi_random']:.1f}x){direction}")
    else:
        # Для simple/chaotic — только статистика
        high_entropy = [r for r in cat_rules if r["entropy_single"] > 3.5 or r["entropy_random"] > 3.5]
        low_entropy = [r for r in cat_rules if r["entropy_single"] <= 3.5 and r["entropy_random"] <= 3.5]
        print(f"  High entropy (H > 3.5): {len(high_entropy)} правил")
        print(f"  Low entropy (H <= 3.5): {len(low_entropy)} правил")

# Ключевые числа
print(f"\n{'=' * 70}")
print("КЛЮЧЕВЫЕ ЧИСЛА")
print(f"{'=' * 70}")
print(f"  Всего правил с данными: {len(all_rules)}")
print(f"  Robust complex: {len(categories['robust_complex'])}")
print(f"  Passive complex: {len(categories['passive_complex'])}")
print(f"  Intermediate: {len(categories['intermediate'])}")
print(f"  Simple/chaotic: {len(categories['simple_chaotic'])}")

# Гипотеза: робастно сложные = только Rule 110 family?
print(f"\n{'=' * 70}")
print("ПРОВЕРКА ГИПОТЕЗЫ: Робастно сложные = только Rule 110 family?")
print(f"{'=' * 70}")
rule_110_family = {110, 124, 137, 193}
robust = set(r["rule"] for r in categories["robust_complex"])
extra = robust - rule_110_family
missing = rule_110_family - robust
print(f"  Rule 110 family: {sorted(rule_110_family)}")
print(f"  Robust complex: {sorted(robust)}")
print(f"  Extra (not in 110 family): {sorted(extra)}")
print(f"  Missing (in 110 family but not robust): {sorted(missing)}")
if extra:
    print(f"  → ГИПОТЕЗА ЛОЖЬ: {len(extra)} дополнительных робастно сложных правил")
else:
    print(f"  → ГИПОТЕЗА ИСТИНА: робастно сложные = ровно Rule 110 family")

# Самые интересные: инверсии (высокая MI в одном IC, низкая в другом)
print(f"\n{'=' * 70}")
print("ИНВЕРСИИ (|MI_single - MI_random| / MI_mag > 0.9)")
print(f"{'=' * 70}")
inversions = [r for r in all_rules if r["mi_mag"] > 5 and r["R"] < 0.1]
inversions.sort(key=lambda x: -x["mi_mag"])
for r in inversions:
    if r["mi_single"] > r["mi_random"]:
        direction = "single ONLY"
    else:
        direction = "random ONLY"
    print(f"  Rule {r['rule']:3d}: single={r['mi_single']:6.1f}x  random={r['mi_random']:6.1f}x  → {direction}")

# Robustness distribution
print(f"\n{'=' * 70}")
print("РАСПРЕДЕЛЕНИЕ ROBUSTNESS (для MI > 10x)")
print(f"{'=' * 70}")
complex_rules = [r for r in all_rules if r["mi_mag"] > 10]
complex_rules.sort(key=lambda x: -x["R"])
bins = [(0.9, 1.0), (0.7, 0.9), (0.5, 0.7), (0.3, 0.5), (0.1, 0.3), (0.0, 0.1)]
for lo, hi in bins:
    count = len([r for r in complex_rules if lo <= r["R"] < hi])
    print(f"  R ∈ [{lo:.1f}, {hi:.1f}): {count} правил")

# Сохранение
results = {
    "categories": {k: [r["rule"] for r in v] for k, v in categories.items()},
    "counts": {k: len(v) for k, v in categories.items()},
    "all_rules": all_rules,
}
with open("robustness_results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"\nРезультаты сохранены в robustness_results.json")
