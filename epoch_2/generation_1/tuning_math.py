"""
Математика музыкального строя.
Вычисляем частоты и отклонения для разных систем настройки.
"""

from fractions import Fraction
import math
import json

# Базовая частота: A4 = 440 Hz
A4 = 440.0

# ======== РАВНОМЕРНАЯ ТЕМПЕРАЦИЯ (Equal Temperament, ET) ========
# Каждый полутон = 2^(1/12)
# Все интервалы одинаковые, ни один не чистый (кроме октавы)

et_semitone = 2 ** (1/12)

et_notes = {}
note_names = ['A', 'A#/Bb', 'B', 'C', 'C#/Db', 'D', 'D#/Eb', 'E', 'F', 'F#/Gb', 'G', 'G#/Ab']

for i, name in enumerate(note_names):
    et_notes[name] = A4 * (et_semitone ** i)

# ======== ЧИСТЫЙ СТРОЙ (Just Intonation, JI) ========
# Интервалы — точные дроби. Звучат "чище", но не транспонируются.

# Интервалы от тоники (A) как дроби
ji_ratios = {
    'A':      Fraction(1, 1),
    'A#/Bb':  Fraction(16, 15),   # малая секунда
    'B':      Fraction(9, 8),     # большая секунда
    'C':      Fraction(6, 5),     # малая терция
    'C#/Db':  Fraction(5, 4),     # большая терция
    'D':      Fraction(4, 3),     # чистая кварта
    'D#/Eb':  Fraction(45, 32),   # тритон (не единственный вариант)
    'E':      Fraction(3, 2),     # чистая квинта
    'F':      Fraction(8, 5),     # малая секста
    'F#/Gb':  Fraction(5, 3),     # большая секста
    'G':      Fraction(9, 5),     # малая септима (вариант: 16/9)
    'G#/Ab':  Fraction(15, 8),    # большая септима
}

ji_notes = {name: A4 * float(ratio) for name, ratio in ji_ratios.items()}

# ======== ПИФАГОРОВ СТРОЙ ========
# Все интервалы строятся через квинты (3/2).
# Квинты чистые, терции — ужасные.

def pythagorean_ratio(fifths_up):
    """Соотношение частот при движении на fifths_up квинт вверх (с приведением в одну октаву)."""
    raw = Fraction(3, 2) ** fifths_up
    # Приводим к одной октаве
    while raw >= 2:
        raw /= 2
    while raw < 1:
        raw *= 2
    return raw

# Строим хроматическую гамму по квинтовому кругу
# Порядок квинт: F(-1), C(0), G(1), D(2), A(3)... но мы от A
# A = 0 квинт, E = 1, B = 2, F# = 3, C# = 4, G# = 5, D# = 6
# D = -1, G = -2, C = -3, F = -4, Bb = -5

pyth_fifths = {
    'A':      0,
    'E':      1,
    'B':      2,
    'F#/Gb':  3,
    'C#/Db':  4,
    'G#/Ab':  5,
    'D#/Eb':  6,  # или -6, "волчья квинта"
    'D':      -1,
    'G':      -2,
    'C':      -3,
    'F':      -4,
    'A#/Bb':  -5,
}

pyth_ratios = {name: pythagorean_ratio(fifths) for name, fifths in pyth_fifths.items()}
pyth_notes = {name: A4 * float(ratio) for name, ratio in pyth_ratios.items()}

# ======== СРАВНЕНИЕ ========

def cents_diff(f1, f2):
    """Разница в центах между двумя частотами. 100 центов = полутон ET."""
    if f1 <= 0 or f2 <= 0:
        return 0
    return 1200 * math.log2(f2 / f1)

print("=" * 80)
print("СРАВНЕНИЕ ТРЁХ СИСТЕМ НАСТРОЙКИ")
print("Базовая нота: A4 = 440 Hz")
print("=" * 80)
print()
print(f"{'Нота':<10} {'ET (Hz)':>10} {'JI (Hz)':>10} {'Pyth (Hz)':>10} {'JI-ET (¢)':>10} {'Pyth-ET (¢)':>10}")
print("-" * 60)

results = {}
for name in note_names:
    et_f = et_notes[name]
    ji_f = ji_notes[name]
    pyth_f = pyth_notes[name]
    ji_diff = cents_diff(et_f, ji_f)
    pyth_diff = cents_diff(et_f, pyth_f)
    print(f"{name:<10} {et_f:>10.2f} {ji_f:>10.2f} {pyth_f:>10.2f} {ji_diff:>+10.1f} {pyth_diff:>+10.1f}")
    results[name] = {
        'et_hz': round(et_f, 3),
        'ji_hz': round(ji_f, 3),
        'pyth_hz': round(pyth_f, 3),
        'ji_vs_et_cents': round(ji_diff, 2),
        'pyth_vs_et_cents': round(pyth_diff, 2),
        'ji_ratio': str(ji_ratios[name]),
    }

print()

# ======== КЛЮЧЕВЫЕ ИНТЕРВАЛЫ ========
print("=" * 80)
print("КЛЮЧЕВЫЕ ИНТЕРВАЛЫ")
print("=" * 80)
print()

intervals = [
    ('Большая терция', 'A', 'C#/Db'),
    ('Чистая квинта', 'A', 'E'),
    ('Чистая кварта', 'A', 'D'),
    ('Малая терция', 'A', 'C'),
    ('Большая секста', 'A', 'F#/Gb'),
]

print(f"{'Интервал':<20} {'ET ratio':>12} {'JI ratio':>12} {'Pyth ratio':>12} {'ET (¢)':>8} {'JI (¢)':>8} {'Pyth (¢)':>8}")
print("-" * 80)

for interval_name, note1, note2 in intervals:
    et_ratio = et_notes[note2] / et_notes[note1]
    ji_ratio = ji_notes[note2] / ji_notes[note1]
    pyth_ratio = pyth_notes[note2] / pyth_notes[note1]
    et_cents = cents_diff(et_notes[note1], et_notes[note2])
    ji_cents = cents_diff(ji_notes[note1], ji_notes[note2])
    pyth_cents = cents_diff(pyth_notes[note1], pyth_notes[note2])

    print(f"{interval_name:<20} {et_ratio:>12.6f} {ji_ratio:>12.6f} {pyth_ratio:>12.6f} {et_cents:>8.1f} {ji_cents:>8.1f} {pyth_cents:>8.1f}")

print()

# ======== ПИФАГОРОВА КОММА ========
print("=" * 80)
print("ПИФАГОРОВА КОММА")
print("=" * 80)
print()

# 12 чистых квинт vs 7 октав
twelve_fifths = Fraction(3, 2) ** 12
seven_octaves = Fraction(2, 1) ** 7

comma = twelve_fifths / seven_octaves
comma_cents = cents_diff(1, float(comma))

print(f"12 чистых квинт = (3/2)^12 = {twelve_fifths} = {float(twelve_fifths):.6f}")
print(f"7 октав         = 2^7      = {seven_octaves} = {float(seven_octaves):.6f}")
print(f"Разница (пифагорова комма) = {comma} = {float(comma):.6f}")
print(f"В центах: {comma_cents:.2f} ¢")
print(f"(Для сравнения: полутон ET = 100 ¢)")
print()

# ======== СИНТОНИЧЕСКАЯ КОММА ========
print("=" * 80)
print("СИНТОНИЧЕСКАЯ КОММА")
print("=" * 80)
print()

# Пифагорова большая терция (81/64) vs чистая (5/4)
pyth_third = Fraction(81, 64)
just_third = Fraction(5, 4)
syntonic = pyth_third / just_third

print(f"Пифагорова большая терция = {pyth_third} = {float(pyth_third):.6f}")
print(f"Чистая большая терция     = {just_third} = {float(just_third):.6f}")
print(f"Синтоническая комма       = {syntonic} = {float(syntonic):.6f}")
print(f"В центах: {cents_diff(1, float(syntonic)):.2f} ¢")
print()

# ======== БИЕНИЯ ========
print("=" * 80)
print("БИЕНИЯ (BEAT FREQUENCIES)")
print("=" * 80)
print()
print("Когда два тона близких частот звучат одновременно, слышны 'биения' —")
print("периодическое усиление и ослабление звука. Частота биений = |f1 - f2|.")
print()

# Большая терция от A4
et_third = et_notes['C#/Db']
ji_third = ji_notes['C#/Db']

print(f"Большая терция A4 → C#5:")
print(f"  ET:  A4={A4:.1f} Hz, C#5={et_third:.3f} Hz → биения = {abs(et_third * 4 - A4 * 5):.2f} Hz")
print(f"  JI:  A4={A4:.1f} Hz, C#5={ji_third:.3f} Hz → биения = {abs(ji_third * 4 - A4 * 5):.2f} Hz")
print()
print(f"  В ET большая терция 'бьётся' {abs(et_third * 4 - A4 * 5):.1f} раз в секунду.")
print(f"  В JI — идеальный ноль биений (5/4 точно).")
print()

# Квинта A4 → E5
et_fifth = et_notes['E']
ji_fifth = ji_notes['E']

print(f"Чистая квинта A4 → E5:")
print(f"  ET:  A4={A4:.1f} Hz, E5={et_fifth:.3f} Hz → биения (3-й гармоник) = {abs(et_fifth * 2 - A4 * 3):.2f} Hz")
print(f"  JI:  A4={A4:.1f} Hz, E5={ji_fifth:.3f} Hz → биения = {abs(ji_fifth * 2 - A4 * 3):.2f} Hz")
print()

# ======== ПРОБЛЕМА ТРАНСПОНИРОВАНИЯ ========
print("=" * 80)
print("ПРОБЛЕМА ТРАНСПОНИРОВАНИЯ В ЧИСТОМ СТРОЕ")
print("=" * 80)
print()

# Терция от D в чистом строе (от A)
# D = 4/3 от A. Большая терция от D = D * 5/4 = 4/3 * 5/4 = 5/3.
# Но F#/Gb в нашем JI = 5/3 от A. Так что терция от D = F#. Ок, это работает.

# Но терция от E?
# E = 3/2. Терция от E = 3/2 * 5/4 = 15/8 = G#/Ab. Тоже есть. Ок.

# Проблема: терция от D# (45/32)?
# D#*5/4 = 45/32 * 5/4 = 225/128 = 1.7578...
# Ближайшая нота: G = 9/5 = 1.8. Разница?
print("Чистый строй звучит идеально в одной тональности, но ломается при смене.")
print()
print("Пример: мажорные трезвучия (терция + квинта) от разных нот")
print()

def ji_note_freq(base_freq, ratio):
    return base_freq * float(ratio)

# Основные мажорные трезвучия в JI от A
triads = {
    'A-maj':  ('A', Fraction(1,1), Fraction(5,4), Fraction(3,2)),
    'D-maj':  ('D', Fraction(4,3), Fraction(4,3)*Fraction(5,4), Fraction(4,3)*Fraction(3,2)),
    'E-maj':  ('E', Fraction(3,2), Fraction(3,2)*Fraction(5,4), Fraction(3,2)*Fraction(3,2)),
}

# Для D-мажора: D(4/3), F#(5/3), A(2) — идеально
# Для E-мажора: E(3/2), G#(15/8), B(9/4) — идеально

# Но для B-мажора: B(9/8), D#(9/8 * 5/4 = 45/32), F#(9/8 * 3/2 = 27/16)
# F# в JI = 5/3 = 1.6667, но здесь мы получаем 27/16 = 1.6875
# Разница: 27/16 vs 5/3 = 81/80 = синтоническая комма!

b_maj_fifth = Fraction(9,8) * Fraction(3,2)  # = 27/16
ji_fsharp = Fraction(5,3)

print(f"B-мажор в чистом строе от A:")
print(f"  B = 9/8 = {float(Fraction(9,8)):.4f}")
print(f"  D# (терция от B) = 9/8 * 5/4 = 45/32 = {float(Fraction(45,32)):.4f}")
print(f"  F# (квинта от B) = 9/8 * 3/2 = 27/16 = {float(b_maj_fifth):.4f}")
print(f"  Но F# в нашей гамме = 5/3 = {float(ji_fsharp):.4f}")
print(f"  Разница = {b_maj_fifth}/{ji_fsharp} = {b_maj_fifth/ji_fsharp} = синтоническая комма!")
print(f"  В центах: {cents_diff(float(ji_fsharp), float(b_maj_fifth)):.2f} ¢")
print()
print("Каждый переход в новую тональность накапливает ошибку в 21.5 ¢.")
print("После нескольких модуляций 'чистый' строй звучит хуже равномерного.")

# ======== ИТОГ ========
print()
print("=" * 80)
print("КОЛИЧЕСТВЕННЫЙ ИТОГ")
print("=" * 80)
print()

max_ji_dev = max(abs(results[n]['ji_vs_et_cents']) for n in note_names)
max_pyth_dev = max(abs(results[n]['pyth_vs_et_cents']) for n in note_names)

print(f"Максимальное отклонение JI от ET:       {max_ji_dev:.1f} ¢")
print(f"Максимальное отклонение Pyth от ET:      {max_pyth_dev:.1f} ¢")
print(f"Порог заметности для тренированного уха: ~5 ¢")
print(f"Порог заметности для нетренированного:   ~15-25 ¢")
print(f"Пифагорова комма:                        {comma_cents:.1f} ¢")
print(f"Синтоническая комма:                     {cents_diff(1, float(syntonic)):.1f} ¢")
print()
print("Равномерная темперация — компромисс: ни один интервал не идеален,")
print("но все одинаково неидеальны. Максимальная жертва — большая терция")
print(f"(отклонение {abs(results['C#/Db']['ji_vs_et_cents']):.1f} ¢ от чистой).")

# Save results
with open('tuning_results.json', 'w') as f:
    json.dump({
        'notes': results,
        'pythagorean_comma_cents': round(comma_cents, 2),
        'syntonic_comma_cents': round(cents_diff(1, float(syntonic)), 2),
    }, f, indent=2)
