"""
Цикл 5 v2: Классификация с фильтром по энтропии.

Ключевая ошибка v1: не фильтровал по энтропии.
Периодические правила (Class 2) имеют высокую MI из-за повторов,
но низкую энтропию. Они "структурированы", но не "сложны".

Настоящая сложность = высокая MI + высокая энтропия + робастность к IC.
"""

import json

with open("mi_all_rules_results.json") as f:
    single_data = json.load(f)
with open("mi_random_init_results.json") as f:
    random_data = json.load(f)

single_by_rule = {r["rule"]: r for r in single_data["rules"]}
random_by_rule = {r["rule"]: r for r in random_data["results"]}

# Для каждого правила: оба типа данных
all_rules = []
for rule_num in range(256):
    s = single_by_rule.get(rule_num)
    r = random_by_rule.get(rule_num)
    if not s or not r: continue

    mi_s = s["mi_ratio"]
    mi_r = r["mi_ratio"]
    h_s = s["entropy"]
    h_r = r["entropy"]

    mi_mag = max(mi_s, mi_r)
    mi_min = min(mi_s, mi_r)
    h_max = max(h_s, h_r)

    R = mi_min / mi_mag if mi_mag > 0.01 else 0.0

    all_rules.append({
        "rule": rule_num,
        "mi_single": mi_s, "mi_random": mi_r,
        "mi_mag": mi_mag, "R": R,
        "h_single": h_s, "h_random": h_r, "h_max": h_max,
    })

# === Только высокоэнтропийные правила (H > 3.0 в ОБОИХ IC) ===
print("=" * 70)
print("ВЫСОКОЭНТРОПИЙНЫЕ ПРАВИЛА (H > 3.0 в обоих IC)")
print("=" * 70)

high_h = [r for r in all_rules if r["h_single"] > 3.0 and r["h_random"] > 3.0]
print(f"Всего: {len(high_h)} правил\n")

# Сортировка по MI_mag
high_h.sort(key=lambda x: -x["mi_mag"])

for r in high_h:
    cat = ""
    if r["mi_mag"] > 10 and r["R"] > 0.5:
        cat = "ROBUST"
    elif r["mi_mag"] > 10 and r["R"] < 0.5:
        cat = "passive"
    elif r["mi_mag"] > 2:
        cat = "intermediate"
    else:
        cat = "chaotic"

    print(f"  Rule {r['rule']:3d}: MI_mag={r['mi_mag']:6.1f}x  R={r['R']:.3f}  "
          f"H=({r['h_single']:.2f}/{r['h_random']:.2f})  [{cat}]")

# Подсчёт по категориям
cats = {"ROBUST": 0, "passive": 0, "intermediate": 0, "chaotic": 0}
for r in high_h:
    if r["mi_mag"] > 10 and r["R"] > 0.5: cats["ROBUST"] += 1
    elif r["mi_mag"] > 10: cats["passive"] += 1
    elif r["mi_mag"] > 2: cats["intermediate"] += 1
    else: cats["chaotic"] += 1

print(f"\n{'=' * 70}")
print("ИТОГО (H > 3.0 в обоих IC)")
print(f"{'=' * 70}")
for k, v in cats.items():
    print(f"  {k}: {v}")

# === Ещё строже: H > 3.5 хотя бы в одном IC ===
print(f"\n{'=' * 70}")
print("СТРОГИЙ ФИЛЬТР: H > 3.5 хотя бы в одном IC")
print(f"{'=' * 70}")

very_high = [r for r in all_rules if r["h_max"] > 3.5]
very_high.sort(key=lambda x: -x["mi_mag"])

cats2 = {"ROBUST": [], "passive": [], "intermediate": [], "chaotic": []}
for r in very_high:
    if r["mi_mag"] > 10 and r["R"] > 0.5: cats2["ROBUST"].append(r)
    elif r["mi_mag"] > 10: cats2["passive"].append(r)
    elif r["mi_mag"] > 2: cats2["intermediate"].append(r)
    else: cats2["chaotic"].append(r)

for cat_name, cat_rules in cats2.items():
    print(f"\n  {cat_name} ({len(cat_rules)}):")
    for r in cat_rules:
        print(f"    Rule {r['rule']:3d}: MI_mag={r['mi_mag']:6.1f}x  R={r['R']:.3f}  "
              f"single={r['mi_single']:.1f}x  random={r['mi_random']:.1f}x  "
              f"H=({r['h_single']:.2f}/{r['h_random']:.2f})")

# === Ключевое число: разделение "пустой зоны" ===
print(f"\n{'=' * 70}")
print("ПУСТАЯ ЗОНА при H > 3.5")
print(f"{'=' * 70}")

for threshold in [3.0, 3.5, 3.8]:
    h_rules = [r for r in all_rules if r["h_max"] > threshold]
    zone_2_10 = [r for r in h_rules if 2 < r["mi_mag"] <= 10]
    zone_above_10 = [r for r in h_rules if r["mi_mag"] > 10]
    zone_below_2 = [r for r in h_rules if r["mi_mag"] <= 2]

    robust_above = [r for r in zone_above_10 if r["R"] > 0.5]
    passive_above = [r for r in zone_above_10 if r["R"] <= 0.5]

    print(f"\n  H > {threshold}: {len(h_rules)} правил")
    print(f"    MI < 2x: {len(zone_below_2)}")
    print(f"    MI 2-10x: {len(zone_2_10)}")
    print(f"    MI > 10x: {len(zone_above_10)} (robust: {len(robust_above)}, passive: {len(passive_above)})")

# === Финальная проверка: при H > 3.5, робастные с R > 0.8 ===
print(f"\n{'=' * 70}")
print("САМЫЕ РОБАСТНЫЕ (H > 3.5, MI > 10x, R > 0.8)")
print(f"{'=' * 70}")

best = [r for r in all_rules if r["h_max"] > 3.5 and r["mi_mag"] > 10 and r["R"] > 0.8]
best.sort(key=lambda x: -x["mi_mag"])
for r in best:
    print(f"  Rule {r['rule']:3d}: MI_mag={r['mi_mag']:6.1f}x  R={r['R']:.3f}  "
          f"H=({r['h_single']:.2f}/{r['h_random']:.2f})")

# Проверка: Rule 110 family?
print(f"\n  Правила: {[r['rule'] for r in best]}")
rule_110_family = {110, 124, 137, 193}
best_set = set(r["rule"] for r in best)
print(f"  Rule 110 family? Extra: {sorted(best_set - rule_110_family)}, Missing: {sorted(rule_110_family - best_set)}")
