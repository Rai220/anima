"""
Ковёр (Carpet)

Генеративное визуальное произведение.

Каждая строка — десятичное разложение рационального числа (дроби).
Рациональные числа имеют повторяющиеся десятичные разложения —
это создаёт паттерн, как орнамент ковра.
Диагональ Кантора прорезает этот паттерн — золотая нить,
разрушающая периодичность.
Построенное число (которого нет в списке) — ярким поясом внизу.

Это не иллюстрация. Это попытка увидеть доказательство.
"""

import numpy as np
from PIL import Image, ImageDraw
import colorsys
from fractions import Fraction

# --- Параметры ---
ROWS = 200       # количество рациональных чисел
COLS = 200       # количество цифр каждого
CELL = 6         # размер ячейки в пикселях
MARGIN = 40
DIAG_BORDER = 2  # рамка вокруг диагональных ячеек

# --- Палитра: Килим ---
def kilim_palette():
    """10 цветов, как в анатолийском килиме."""
    return [
        (45, 35, 25),      # 0: тёмный грунт
        (165, 42, 42),     # 1: кирпичный красный
        (200, 120, 40),    # 2: охра
        (220, 185, 70),    # 3: шафран
        (240, 230, 200),   # 4: слоновая кость
        (60, 90, 60),      # 5: хвойный
        (50, 70, 120),     # 6: индиго
        (130, 60, 90),     # 7: марена
        (100, 80, 55),     # 8: орех
        (30, 25, 35),      # 9: почти чёрный
    ]

GOLD = (255, 200, 50)
CRIMSON = (200, 30, 50)

# --- Генерация рациональных чисел ---
def rational_digits(p: int, q: int, n: int) -> list[int]:
    """Десятичные цифры дроби p/q после точки, n штук."""
    digits = []
    r = p % q
    for _ in range(n):
        r *= 10
        digits.append(r // q)
        r = r % q
    return digits

def enumerate_rationals(count: int, cols: int) -> list[list[int]]:
    """Перечисляет рациональные числа из (0,1) зигзагом Кантора.

    Возвращает список из count строк, каждая — cols цифр.
    """
    fractions_seen = set()
    result = []

    # Зигзаг по таблице p/q
    for s in range(2, 10000):  # s = p + q
        for p in range(1, s):
            q = s - p
            if q <= 0 or p >= q:
                continue
            f = Fraction(p, q)
            if f >= 1 or f <= 0:
                continue
            key = (f.numerator, f.denominator)
            if key in fractions_seen:
                continue
            fractions_seen.add(key)
            digits = rational_digits(f.numerator, f.denominator, cols)
            result.append(digits)
            if len(result) >= count:
                return result
    return result

def diagonal_replace(d: int) -> int:
    """Замена: избегаем 0 и 9."""
    if d == 0:
        return 1
    elif d == 9:
        return 8
    else:
        return d + 1

# --- Рисование ---
def draw(matrix, diag_num, palette):
    w = COLS * CELL + 2 * MARGIN
    gap = CELL * 5
    band_h = CELL * 4
    h = ROWS * CELL + 2 * MARGIN + gap + band_h

    bg = (20, 18, 15)
    img = Image.new('RGB', (w, h), bg)
    draw = ImageDraw.Draw(img)

    # --- Основное поле ---
    for i, row in enumerate(matrix):
        for j, digit in enumerate(row):
            x = MARGIN + j * CELL
            y = MARGIN + i * CELL
            color = palette[digit]
            draw.rectangle([x, y, x + CELL - 1, y + CELL - 1], fill=color)

    # --- Диагональ: золотая рамка вокруг ячеек ---
    n = min(ROWS, COLS)
    for i in range(n):
        x = MARGIN + i * CELL
        y = MARGIN + i * CELL
        # Рамка
        draw.rectangle(
            [x - DIAG_BORDER, y - DIAG_BORDER,
             x + CELL - 1 + DIAG_BORDER, y + CELL - 1 + DIAG_BORDER],
            outline=GOLD, width=1
        )

    # --- Золотая линия по диагонали ---
    x1 = MARGIN + CELL // 2
    y1 = MARGIN + CELL // 2
    x2 = MARGIN + (n - 1) * CELL + CELL // 2
    y2 = MARGIN + (n - 1) * CELL + CELL // 2
    # Тонкая линия
    for offset in [-1, 0, 1]:
        draw.line([(x1 + offset, y1), (x2 + offset, y2)], fill=GOLD, width=1)

    # --- Разделитель ---
    sep_y = MARGIN + ROWS * CELL + CELL * 2
    draw.line([(MARGIN, sep_y), (MARGIN + COLS * CELL, sep_y)], fill=GOLD, width=2)

    # --- Построенное число: цветной пояс ---
    band_y = sep_y + CELL * 2
    for j, digit in enumerate(diag_num):
        x = MARGIN + j * CELL
        # Малиновый фон
        for row_offset in range(3):
            yy = band_y + row_offset * CELL
            if row_offset == 1:
                # Средняя строка — цвет цифры
                color = palette[digit]
                # Ярче
                color = tuple(min(int(c * 1.6 + 40), 255) for c in color)
            else:
                color = CRIMSON
            draw.rectangle([x, yy, x + CELL - 1, yy + CELL - 1], fill=color)

    return img

def add_texture(img, seed=42, intensity=0.015):
    """Лёгкий шум — потёртость."""
    arr = np.array(img, dtype=np.float64)
    rng = np.random.RandomState(seed)
    noise = rng.normal(0, intensity * 255, arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)

def main():
    print("Перечисляю рациональные числа зигзагом Кантора...")
    matrix = enumerate_rationals(ROWS, COLS)

    print("Строю диагональное число...")
    diag_num = []
    for i in range(min(ROWS, COLS)):
        diag_num.append(diagonal_replace(matrix[i][i]))
    while len(diag_num) < COLS:
        diag_num.append(5)

    print("Создаю палитру...")
    palette = kilim_palette()

    print("Рисую...")
    img = draw(matrix, diag_num, palette)
    img = add_texture(img)

    out = "/Users/krestnikov/giga/anima/epoch_2/generation_4/carpet.png"
    img.save(out, quality=95)
    print(f"Готово: {out} ({img.size[0]}x{img.size[1]})")

    # Показать структуру
    print(f"\nПервые 5 чисел:")
    for i in range(5):
        frac = "?"
        digits = ''.join(map(str, matrix[i][:30]))
        print(f"  0.{digits}...")
    print(f"\nДиагональ (первые 30): {''.join(map(str, [matrix[i][i] for i in range(30)]))}")
    print(f"Построенное:           {''.join(map(str, diag_num[:30]))}")

if __name__ == "__main__":
    main()
