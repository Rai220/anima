"""
Эксперимент: можно ли обнаружить "ремесленное знание" в математике алгоритмически?

Гауэрс утверждает, что комбинаторика организована вокруг "общих принципов" —
расплывчатых, но мощных эвристик. Примеры:
  1. Вероятностный метод (выбери случайно и считай)
  2. Концентрация меры (функция от многих слабых переменных ~ константа)
  3. Фурье-анализ (для подсчёта решений — смотри на коэффициенты)
  4. Регулярность (большие графы ~ несколько квазислучайных кусков)

Вопрос: если закодировать набор доказательств как последовательности шагов,
обнаружится ли кластерная структура, соответствующая этим принципам?

Подход:
- Представим 30 знаменитых комбинаторных результатов
- Для каждого закодируем ключевые техники (ручная разметка, честная)
- Проверим: образуют ли техники кластеры? Есть ли иерархия?
- Сравним с предсказаниями Гауэрса
"""

import json
from collections import Counter

# Каждое доказательство = (название, [список техник])
# Техники из канона:
#   prob = вероятностный метод
#   count = подсчёт (включая двойной подсчёт)
#   pigeon = принцип Дирихле
#   fourier = гармонический анализ
#   regularity = лемма регулярности или её варианты
#   concentration = концентрация меры
#   algebraic = алгебраический метод (полиномы, линейная алгебра)
#   topological = топологические методы
#   greedy = жадный алгоритм / индуктивное построение
#   extremal = рассмотри экстремальный пример
#   random_graph = свойства случайных графов G(n,p)
#   deletion = вероятностный метод + удаление плохих элементов
#   lovasz_local = локальная лемма Ловаса
#   entropy = энтропийный метод
#   container = метод контейнеров
#   density_increment = приращение плотности (аргумент Рота)
#   energy_increment = приращение энергии
#   flag_algebra = алгебра флагов
#   dependent_random = случайный выбор с зависимостями

PROOFS = [
    ("Эрдёш: R(k) ≥ 2^{k/2}", ["prob", "count"]),
    ("Эрдёш-Секереш: R(k) ≤ C(2k,k)", ["pigeon", "greedy"]),
    ("Турана теорема: ex(n, K_r)", ["extremal", "count"]),
    ("Кёнига теорема: паросочетания в двудольных", ["greedy", "algebraic"]),
    ("Рамсей: конечная теорема", ["pigeon", "greedy"]),
    ("Шпернера теорема: антицепи в 2^[n]", ["count", "algebraic"]),
    ("Дилуорса теорема: разбиение на цепи", ["pigeon", "extremal"]),
    ("Хинчин: порог для свойств случайных графов", ["prob", "random_graph", "count"]),
    ("Ловас: хроматическое число vs обхват", ["prob", "deletion"]),
    ("Спенсер: шесть стандартных отклонений", ["prob", "concentration"]),
    ("Бек: дискрепансия гиперграфов", ["prob", "concentration"]),
    ("Семереди: лемма регулярности", ["regularity", "count", "extremal"]),
    ("Семереди: арифметические прогрессии", ["regularity", "count"]),
    ("Рот: прогрессии длины 3", ["fourier", "density_increment"]),
    ("Гауэрс: количественный Семереди", ["fourier", "count", "regularity"]),
    ("Грин-Тао: простые содержат арифм. прогрессии", ["fourier", "regularity", "prob"]),
    ("Дворецки: почти евклидовы сечения", ["concentration", "prob"]),
    ("Кашин: ортогональное разложение", ["prob", "concentration", "random_graph"]),
    ("Болобаш-Томасон: псевдослучайные графы", ["random_graph", "algebraic", "count"]),
    ("Франкл-Уилсон: пересечения множеств", ["algebraic", "count"]),
    ("Алон-Тарси: раскраски списками", ["algebraic"]),
    ("Алон: комбинаторный Нуллштеллензатц", ["algebraic", "count"]),
    ("Ловас локальная лемма", ["prob", "lovasz_local"]),
    ("Мозер-Тардош: конструктивная локальная лемма", ["prob", "lovasz_local", "greedy"]),
    ("Фюреди-Комлош: Turán для K_{3,3}", ["prob", "algebraic", "count"]),
    ("Балог-Семереди-Гауэрс", ["count", "random_graph", "regularity"]),
    ("Кван: порог для совершенного паросочетания", ["prob", "random_graph", "entropy"]),
    ("Кели-Ромеро-Самос: R(k) ≤ (4-ε)^k", ["prob", "random_graph", "concentration", "regularity"]),
    ("Саксл-Шелп: числа Рамсея для деревьев", ["greedy", "extremal"]),
    ("Хейлз-Джуэтт: комбинаторная теорема", ["density_increment", "regularity"]),
]


def analyze():
    # 1. Частоты техник
    all_techniques = []
    for name, techs in PROOFS:
        all_techniques.extend(techs)

    freq = Counter(all_techniques)
    print("=== Частоты техник ===")
    for tech, count in freq.most_common():
        bar = "█" * count
        print(f"  {tech:25s} {count:2d} {bar}")

    print(f"\nВсего доказательств: {len(PROOFS)}")
    print(f"Уникальных техник: {len(freq)}")
    print(f"Среднее техник на доказательство: {sum(len(t) for _, t in PROOFS) / len(PROOFS):.1f}")

    # 2. Матрица совстречаемости (co-occurrence)
    techniques = sorted(freq.keys(), key=lambda t: -freq[t])
    n = len(techniques)
    tech_idx = {t: i for i, t in enumerate(techniques)}

    cooccur = [[0] * n for _ in range(n)]
    for name, techs in PROOFS:
        for i, t1 in enumerate(techs):
            for t2 in techs[i+1:]:
                a, b = tech_idx[t1], tech_idx[t2]
                cooccur[a][b] += 1
                cooccur[b][a] += 1

    print("\n=== Сильнейшие пары техник (совстречаемость ≥ 3) ===")
    pairs = []
    for i in range(n):
        for j in range(i+1, n):
            if cooccur[i][j] >= 3:
                pairs.append((cooccur[i][j], techniques[i], techniques[j]))

    pairs.sort(reverse=True)
    for count, t1, t2 in pairs:
        print(f"  {t1} + {t2}: {count}")

    # 3. Кластеры: какие техники "живут вместе"?
    # Простой подход: для каждой техники, вектор совстречаемости
    # Затем корреляция между векторами
    print("\n=== Кластеры техник (по Жаккару) ===")

    # Для каждой техники — множество доказательств, где она используется
    tech_proofs = {t: set() for t in techniques}
    for i, (name, techs) in enumerate(PROOFS):
        for t in techs:
            tech_proofs[t].add(i)

    # Жаккар для пар техник
    jaccard_pairs = []
    for i in range(n):
        for j in range(i+1, n):
            t1, t2 = techniques[i], techniques[j]
            s1, s2 = tech_proofs[t1], tech_proofs[t2]
            if len(s1 | s2) > 0:
                jacc = len(s1 & s2) / len(s1 | s2)
                if jacc > 0.2:
                    jaccard_pairs.append((jacc, t1, t2))

    jaccard_pairs.sort(reverse=True)
    for jacc, t1, t2 in jaccard_pairs[:15]:
        print(f"  {t1:25s} ~ {t2:25s} J={jacc:.2f}")

    # 4. Проверка гипотезы Гауэрса: образуют ли техники
    # "семейства", соответствующие его принципам?
    print("\n=== Проверка кластеров Гауэрса ===")

    gowers_clusters = {
        "Вероятностный метод": {"prob", "deletion", "lovasz_local", "dependent_random", "random_graph"},
        "Концентрация меры": {"concentration", "entropy"},
        "Фурье-анализ": {"fourier", "density_increment", "energy_increment"},
        "Регулярность": {"regularity"},
        "Алгебраический метод": {"algebraic"},
    }

    for cluster_name, cluster_techs in gowers_clusters.items():
        # Сколько доказательств попадают в этот кластер?
        cluster_proofs = set()
        for t in cluster_techs:
            if t in tech_proofs:
                cluster_proofs |= tech_proofs[t]

        # Средняя плотность внутри кластера
        internal_links = 0
        total_possible = 0
        active_techs = [t for t in cluster_techs if t in tech_proofs]
        for i, t1 in enumerate(active_techs):
            for t2 in active_techs[i+1:]:
                s1, s2 = tech_proofs[t1], tech_proofs[t2]
                if len(s1 | s2) > 0:
                    internal_links += len(s1 & s2) / len(s1 | s2)
                    total_possible += 1

        avg_jaccard = internal_links / total_possible if total_possible > 0 else 0

        # Средняя плотность с техниками вне кластера
        external_links = 0
        ext_total = 0
        outside_techs = [t for t in techniques if t not in cluster_techs]
        for t1 in active_techs:
            for t2 in outside_techs:
                s1, s2 = tech_proofs[t1], tech_proofs[t2]
                if len(s1 | s2) > 0:
                    external_links += len(s1 & s2) / len(s1 | s2)
                    ext_total += 1

        avg_external = external_links / ext_total if ext_total > 0 else 0

        ratio = avg_jaccard / avg_external if avg_external > 0 else float('inf')

        print(f"  {cluster_name}:")
        print(f"    Доказательств: {len(cluster_proofs)}/{len(PROOFS)}")
        print(f"    Внутренний Жаккар: {avg_jaccard:.3f}")
        print(f"    Внешний Жаккар:   {avg_external:.3f}")
        print(f"    Соотношение:      {ratio:.2f}x")

    # 5. Главный вопрос: двумерна ли карта техник?
    # Есть ли оси "теория—задачи" и "дискретное—непрерывное"?
    print("\n=== Главный вопрос: сколько измерений у карты техник? ===")

    # PCA-подобный анализ: SVD матрицы совстречаемости
    # Простая реализация через степенной метод
    import math

    # Нормализуем матрицу совстречаемости
    max_val = max(cooccur[i][j] for i in range(n) for j in range(n)) or 1
    norm_matrix = [[cooccur[i][j] / max_val for j in range(n)] for i in range(n)]

    def matrix_multiply(A, v):
        n = len(A)
        return [sum(A[i][j] * v[j] for j in range(n)) for i in range(n)]

    def normalize(v):
        norm = math.sqrt(sum(x*x for x in v))
        if norm == 0:
            return v, 0
        return [x/norm for x in v], norm

    def power_iteration(A, num_iter=100):
        n = len(A)
        v = [1.0/math.sqrt(n)] * n
        eigenvalue = 0
        for _ in range(num_iter):
            Av = matrix_multiply(A, v)
            v, eigenvalue = normalize(Av)
        return v, eigenvalue

    def deflate(A, v, eigenvalue):
        n = len(A)
        return [[A[i][j] - eigenvalue * v[i] * v[j] for j in range(n)] for i in range(n)]

    eigenvalues = []
    A = [row[:] for row in norm_matrix]
    for k in range(min(5, n)):
        v, ev = power_iteration(A)
        eigenvalues.append(ev)
        A = deflate(A, v, ev)

    total_var = sum(eigenvalues)
    print(f"  Собственные значения: {', '.join(f'{ev:.3f}' for ev in eigenvalues)}")
    if total_var > 0:
        cumulative = 0
        for i, ev in enumerate(eigenvalues):
            cumulative += ev
            pct = 100 * cumulative / total_var
            print(f"  {i+1} измерени{'е' if i==0 else 'я' if i<4 else 'й'}: {pct:.1f}% дисперсии")

    return freq, pairs, jaccard_pairs


if __name__ == "__main__":
    freq, pairs, jaccard_pairs = analyze()

    print("\n" + "="*60)
    print("ВЫВОДЫ")
    print("="*60)

    print("""
1. ЧАСТОТЫ. Самые частые техники — это ремесленное ядро комбинаторики.
   Если 'prob' и 'count' лидируют — Гауэрс прав, что вероятностный метод
   и подсчёт — главные принципы.

2. ПАРЫ. Сильные совстречаемости показывают, какие техники "живут вместе".
   Если prob+count сильнее prob+fourier — есть реальная кластерная структура.

3. КЛАСТЕРЫ ГАУЭРСА. Если внутренний Жаккар >> внешнего для каждого
   кластера — принципы Гауэрса реальны (техники внутри одного семейства
   чаще используются вместе, чем с чужими).

4. РАЗМЕРНОСТЬ. Если 2 измерения покрывают >80% дисперсии —
   карта техник по существу двумерна, и можно искать оси.
   Если нет — пространство техник сложнее, чем "две культуры".
""")
