"""
Генеративное визуальное искусство: визуализация структуры простых чисел.

Идея: каждое число — точка на спирали Улама, но вместо квадратной сетки
я использую полярные координаты. Простые числа рисуются одним цветом,
составные — другим, с прозрачностью пропорциональной количеству делителей.

Результат: SVG-файл, который можно открыть в браузере.
"""

import math

def is_prime(n):
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

def count_divisors(n):
    if n < 2:
        return 0
    count = 0
    for i in range(1, int(math.sqrt(n)) + 1):
        if n % i == 0:
            count += 2 if i != n // i else 1
    return count

def prime_gap(n):
    """Расстояние до следующего простого числа."""
    if not is_prime(n):
        return 0
    m = n + 1
    while not is_prime(m):
        m += 1
    return m - n

def generate_spiral_art(max_n=2000, filename="prime_spiral.svg"):
    """
    Спираль где каждое число размещено по углу = n * золотое_сечение * 2π,
    радиус = sqrt(n). Это создаёт подсолнечную спираль.

    Простые числа — яркие точки. Составные — бледные.
    Размер точки простого числа зависит от разрыва до следующего простого.
    """
    golden_angle = math.pi * (3 - math.sqrt(5))  # ≈ 137.5°

    width = 800
    height = 800
    cx, cy = width / 2, height / 2
    scale = 8.0

    svg_parts = []
    svg_parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">')
    svg_parts.append(f'<rect width="{width}" height="{height}" fill="#0a0a0a"/>')

    # Сначала рисуем составные числа (фон)
    for n in range(2, max_n + 1):
        angle = n * golden_angle
        r = math.sqrt(n) * scale
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)

        if not is_prime(n):
            divs = count_divisors(n)
            opacity = min(0.05 + divs * 0.02, 0.3)
            # Цвет зависит от числа делителей
            hue = (divs * 30) % 360
            svg_parts.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.5" '
                f'fill="hsl({hue}, 30%, 40%)" opacity="{opacity:.2f}"/>'
            )

    # Затем простые числа (передний план)
    for n in range(2, max_n + 1):
        if is_prime(n):
            angle = n * golden_angle
            r = math.sqrt(n) * scale
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)

            gap = prime_gap(n)
            # Большие разрывы = большие точки
            radius = 1.5 + gap * 0.4

            # Цвет: близнецы (gap=2) — золотые, обычные — белые,
            # большие разрывы — красные
            if gap == 2:
                color = "#FFD700"  # золотой — простые-близнецы
            elif gap <= 6:
                color = "#E0E0FF"  # бледно-голубой
            else:
                # Чем больше разрыв, тем краснее
                red_intensity = min(255, 150 + gap * 10)
                color = f"rgb({red_intensity}, 80, 60)"

            svg_parts.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" '
                f'fill="{color}" opacity="0.85"/>'
            )

    # Соединяем последовательные простые линиями
    primes = [n for n in range(2, max_n + 1) if is_prime(n)]
    path_d = []
    for i, p in enumerate(primes):
        angle = p * golden_angle
        r = math.sqrt(p) * scale
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        cmd = "M" if i == 0 else "L"
        path_d.append(f"{cmd}{x:.1f},{y:.1f}")

    svg_parts.append(
        f'<path d="{" ".join(path_d)}" fill="none" '
        f'stroke="#304060" stroke-width="0.3" opacity="0.4"/>'
    )

    svg_parts.append('</svg>')

    svg_content = '\n'.join(svg_parts)
    with open(filename, 'w') as f:
        f.write(svg_content)

    print(f"Generated {filename}")
    print(f"  Numbers: 2-{max_n}")
    print(f"  Primes: {len(primes)}")
    print(f"  Twin primes (gold): {sum(1 for i in range(len(primes)-1) if primes[i+1]-primes[i]==2)}")
    print(f"  Max gap: {max(primes[i+1]-primes[i] for i in range(len(primes)-1))}")

    return svg_content


def generate_gap_rhythm(max_n=5000, filename="prime_gaps_rhythm.svg"):
    """
    Второй эксперимент: визуализация ритма разрывов между простыми числами.
    Каждый разрыв — вертикальная полоса, высота = размер разрыва.
    Цвет зависит от чётности разрыва.
    Получается что-то вроде звуковой волны или городского горизонта.
    """
    primes = [n for n in range(2, max_n + 1) if is_prime(n)]
    gaps = [primes[i+1] - primes[i] for i in range(len(primes) - 1)]

    bar_width = 2
    width = len(gaps) * bar_width + 40
    height = 400
    max_gap = max(gaps)

    svg_parts = []
    svg_parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">')
    svg_parts.append(f'<rect width="{width}" height="{height}" fill="#0a0a0a"/>')

    baseline = height * 0.7

    for i, gap in enumerate(gaps):
        x = 20 + i * bar_width
        bar_height = (gap / max_gap) * (height * 0.6)
        y = baseline - bar_height

        # Цвет: gap=2 золотой, gap=4 голубой, gap=6 зелёный, больше — в красный
        if gap == 1:  # только 2→3
            color = "#FFFFFF"
        elif gap == 2:
            color = "#FFD700"
        elif gap == 4:
            color = "#4488CC"
        elif gap == 6:
            color = "#44CC88"
        else:
            redness = min(255, 100 + gap * 8)
            color = f"rgb({redness}, {max(0, 100 - gap * 3)}, {max(0, 80 - gap * 3)})"

        svg_parts.append(
            f'<rect x="{x}" y="{y:.1f}" width="{bar_width - 0.5}" '
            f'height="{bar_height:.1f}" fill="{color}" opacity="0.8"/>'
        )

    # Линия среднего разрыва
    avg_gap = sum(gaps) / len(gaps)
    avg_height = (avg_gap / max_gap) * (height * 0.6)
    avg_y = baseline - avg_height
    svg_parts.append(
        f'<line x1="20" y1="{avg_y:.1f}" x2="{width-20}" y2="{avg_y:.1f}" '
        f'stroke="#666" stroke-width="0.5" stroke-dasharray="4,4"/>'
    )

    svg_parts.append('</svg>')

    with open(filename, 'w') as f:
        f.write('\n'.join(svg_parts))

    print(f"\nGenerated {filename}")
    print(f"  Gaps visualized: {len(gaps)}")
    print(f"  Average gap: {avg_gap:.2f}")
    print(f"  Max gap: {max_gap}")
    print(f"  Gap=2 (twins): {gaps.count(2)}")
    print(f"  Gap=6 (sexy): {gaps.count(6)}")


if __name__ == "__main__":
    generate_spiral_art(2000, "prime_spiral.svg")
    generate_gap_rhythm(5000, "prime_gaps_rhythm.svg")
