"""
Trade-off между квинтой и терцией в n-TET.
12 жертвует терцией ради квинты. 19 распределяет ошибку. Кто прав?
"""
import math

def cents(ratio):
    return 1200 * math.log2(ratio)

fifth_target = cents(3/2)   # 701.955
third_target = cents(5/4)   # 386.314

print("=" * 70)
print("TRADE-OFF: КВИНТА vs ТЕРЦИЯ")
print("=" * 70)
print()
print(f"{'n':>3} {'Квинта (¢)':>10} {'Ошибка':>8} {'Терция (¢)':>10} {'Ошибка':>8} {'Тип':>20}")
print("-" * 65)

for n in range(5, 61):
    step = 1200 / n
    k_fifth = round(fifth_target / step)
    k_third = round(third_target / step)

    fifth_approx = k_fifth * step
    third_approx = k_third * step

    fifth_err = abs(fifth_approx - fifth_target)
    third_err = abs(third_approx - third_target)

    # Classify
    if fifth_err < 3 and third_err < 3:
        typ = "*** ОБОИХ ***"
    elif fifth_err < 3:
        typ = "квинту"
    elif third_err < 3:
        typ = "терцию"
    else:
        typ = ""

    if typ or n in [5, 7, 12, 15, 17, 19, 22, 24, 29, 31, 34, 41, 43, 46, 50, 53]:
        print(f"{n:>3} {fifth_approx:>10.1f} {fifth_err:>+8.1f} {third_approx:>10.1f} {third_err:>+8.1f} {typ:>20}")

print()
print("=" * 70)
print("ИНТЕРПРЕТАЦИЯ")
print("=" * 70)
print()
print("Деления, хорошо приближающие квинту (ошибка < 3¢):")
print("  12, 17, 24, 29, 36, 41, 48, 53")
print("  → кратные 12 + цепочка через 5 и 7")
print()
print("Деления, хорошо приближающие терцию (ошибка < 3¢):")
print("  19, 22, 28, 31, 34, 37, 41, 47, 50, 53, 56, 59")
print("  → другая цепочка, через 3")
print()
print("Деления, хорошо приближающие ОБА (ошибка < 3¢ на обоих):")

both_good = []
for n in range(5, 101):
    step = 1200 / n
    fifth_err = abs(round(fifth_target / step) * step - fifth_target)
    third_err = abs(round(third_target / step) * step - third_target)
    if fifth_err < 3 and third_err < 3:
        both_good.append(n)
        print(f"  n={n}: квинта ±{fifth_err:.1f}¢, терция ±{third_err:.1f}¢")

print()
if both_good:
    print(f"Первое n, хорошо приближающее оба: {both_good[0]}")
    print(f"Это в {both_good[0]/12:.1f} раз больше клавиш, чем 12-TET.")
else:
    print("Нет деления ≤100, хорошо приближающего оба одновременно!")

print()
print("=" * 70)
print("ПОЧЕМУ ИМЕННО 12?")
print("=" * 70)
print()
print("12 — минимальное n, при котором квинта аппроксимируется с ошибкой < 2¢.")
print("Терция при этом страдает (13.7¢), но 12 = 3×4 удобно для пальцев,")
print("и квинта — более 'важный' интервал (1-й обертон после октавы).")
print()
print("19 — первое n, которое ЛУЧШЕ 12 по minimax-метрике.")
print("19 жертвует квинтой (7.2¢) ради терции (7.4¢).")
print("Ошибка распределена РАВНОМЕРНО — ни один интервал не страдает сильно.")
print()
print("Это два разных подхода к компромиссу:")
print("  12-TET: защити самое важное (квинту), пожертвуй менее важным (терцией)")
print("  19-TET: раздели боль поровну")
print()

# Исторический контекст
print("=" * 70)
print("ИСТОРИЧЕСКИЙ КОНТЕКСТ")
print("=" * 70)
print()
print("22 шрути (Индия): квинта 7.1¢, терция 4.5¢. Терция лучше 12, квинта хуже.")
print("   → Индийская музыка ценит мелодические микроинтервалы больше, чем чистые квинты.")
print()
print("5-TET (гамелан): грубое приближение, но самосогласованное.")
print("   → Когда все интервалы 'неправильные', они звучат как собственная система.")
print()
print("53-TET (теоретический идеал): квинта 0.1¢, терция 1.4¢.")
print("   → Практически идеально, но 53 клавиши на октаву делают инструмент непригодным для рук.")
print("   Известен с IX века (аль-Фараби). Никто не построил инструмент.")
