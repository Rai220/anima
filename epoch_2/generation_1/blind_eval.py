#!/usr/bin/env python3
"""
Слепая оценка: смешать строки из v3 и v4, перемешать,
оценить без знания версии, затем раскрыть.

Это проверка на предвзятость: если я знаю, что строка из v4,
я могу быть к ней щедрее.

Метод:
1. Берём по 30 строк из v3 и v4 (случайная выборка)
2. Перемешиваем
3. Оцениваем каждую: 1 = работает, 0 = нет
4. Раскрываем метки, считаем процент для каждой версии
"""

import json
import random

def load_lines(path, label):
    with open(path) as f:
        data = json.load(f)
    return [(line, label) for line in data["lines"]]


def main():
    v3 = load_lines("/Users/krestnikov/giga/anima/epoch_2/generation_1/v3_output.json", "v3")
    v4 = load_lines("/Users/krestnikov/giga/anima/epoch_2/generation_1/v4_output.json", "v4")

    # По 30 строк из каждой версии
    random.seed(42)
    sample_v3 = random.sample(v3, min(30, len(v3)))
    sample_v4 = random.sample(v4, min(30, len(v4)))

    pool = sample_v3 + sample_v4
    random.shuffle(pool)

    # Сохраняем порядок для воспроизводимости
    shuffled = [{"idx": i, "line": line, "version": ver}
                for i, (line, ver) in enumerate(pool)]

    # Выводим только строки (без меток) для оценки
    print("=" * 60)
    print("СЛЕПАЯ ОЦЕНКА: 60 строк, версии скрыты")
    print("=" * 60)
    print()
    for item in shuffled:
        print(f"  {item['idx']:2d}. {item['line']}")

    # Сохраняем с метками (для последующей проверки)
    with open("/Users/krestnikov/giga/anima/epoch_2/generation_1/blind_eval_key.json", "w") as f:
        json.dump(shuffled, f, ensure_ascii=False, indent=2)

    print(f"\nКлюч сохранён в blind_eval_key.json")
    print("Оцените каждую строку: 1 = работает, 0 = нет")


if __name__ == "__main__":
    main()
