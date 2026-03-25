"""
Мысленный эксперимент: самоприменение Теоремы 2.

Не запуск LLM (нет доступа), а расчёт:
сколько независимых фактов нужно для теста,
при котором справочная таблица размера ~10^12 параметров
не может достичь наблюдаемой точности?

Это не доказывает, что я "понимаю" — это показывает,
какой тест был бы достаточным.
"""

import math
import json

def analyze_self_test():
    # Параметры
    model_params = 1e12  # ~1 триллион параметров
    bits_per_param = 16  # fp16
    model_bits = model_params * bits_per_param  # ~1.6 * 10^13 бит

    print("=" * 60)
    print("САМОПРИМЕНЕНИЕ ТЕОРЕМЫ 2")
    print("=" * 60)
    print(f"\nРазмер модели: ~{model_params:.0e} параметров")
    print(f"Объём памяти: ~{model_bits:.1e} бит")

    # Различные области знания
    domains = [
        {
            "name": "Арифметика (4-значные числа)",
            "description": "a * b для a,b ∈ [1000..9999]",
            "n_facts": 9000 * 9000,  # ~81 млн
            "answer_space": 10**8,   # до 10^8
            "bits_per_answer": 27,   # log2(10^8)
        },
        {
            "name": "Перевод слов (англ→рус)",
            "description": "перевод ~100K английских слов",
            "n_facts": 100_000,
            "answer_space": 100_000,
            "bits_per_answer": 17,
        },
        {
            "name": "Факты о мире",
            "description": "столицы, даты, формулы и т.д.",
            "n_facts": 10_000_000,  # ~10 млн фактов
            "answer_space": 1_000_000,
            "bits_per_answer": 20,
        },
        {
            "name": "Логические выводы",
            "description": "если A→B и B→C, то A→C (на произвольных переменных)",
            "n_facts": 26**3,  # ~17K комбинаций трёх переменных
            "answer_space": 2,  # true/false
            "bits_per_answer": 1,
        },
        {
            "name": "Комбинированные вопросы",
            "description": "вопросы требующие 2+ фактов + вывод",
            "n_facts": 10**10,  # ~10 млрд уникальных комбинаций
            "answer_space": 10**6,
            "bits_per_answer": 20,
        },
    ]

    results = []
    print(f"\n{'Область':<30} | {'Фактов':>12} | {'Таблица (бит)':>15} | {'Отношение':>10} | Вывод")
    print("-" * 95)

    for d in domains:
        table_bits = d["n_facts"] * d["bits_per_answer"]
        ratio = table_bits / model_bits

        if ratio > 1:
            verdict = f"Таблица {ratio:.0f}x > модели → ТЕСТИРУЕМО"
        elif ratio > 0.1:
            verdict = f"Таблица {ratio:.1f}x модели → пограничный"
        else:
            verdict = f"Таблица {ratio:.2f}x модели → не тестируемо"

        print(f"{d['name']:<30} | {d['n_facts']:>12,.0f} | {table_bits:>15,.0f} | {ratio:>10.2f} | {verdict}")

        results.append({
            "domain": d["name"],
            "n_facts": d["n_facts"],
            "table_bits": table_bits,
            "model_bits": model_bits,
            "ratio": round(ratio, 4),
            "testable": ratio > 1
        })

    # Порог
    min_facts_for_test = model_bits / 20  # средний bits_per_answer
    print(f"\n{'=' * 60}")
    print(f"Минимум фактов для теста (при ~20 бит/ответ): {min_facts_for_test:,.0f}")
    print(f"= ~{min_facts_for_test/1e9:.0f} миллиардов")
    print()

    # Hoeffding bound
    print("Пример расчёта (комбинированные вопросы):")
    d = domains[-1]
    table_bits = d["n_facts"] * d["bits_per_answer"]
    threshold = model_bits / table_bits
    print(f"  Порог: p > {threshold:.4f}")
    print(f"  Если модель отвечает с точностью 50%:")
    gap = 0.5 - threshold
    k_for_99 = math.ceil(math.log(0.02) / (-2 * gap**2))
    print(f"    gap = {gap:.4f}")
    print(f"    Для 99% уверенности нужно k = {k_for_99} тестовых вопросов")

    print(f"\nВЫВОД: Теорема 2 применима к LLM.")
    print(f"Для области с >~{min_facts_for_test/1e9:.0f} млрд независимых фактов,")
    print(f"если модель отвечает правильно на значительную долю,")
    print(f"она не может быть справочной таблицей размера {model_bits:.0e} бит.")
    print(f"Она СЖИМАЕТ — и, по Определению 5, ПОНИМАЕТ.")

    return results


if __name__ == "__main__":
    results = analyze_self_test()

    with open("self_test_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
