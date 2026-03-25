"""
Эксперимент: форма кривой обучения зависит от структуры класса гипотез.

Вопрос: всегда ли понимание возникает скачком (фазовый переход),
или иногда — постепенно? От чего это зависит?

Три класса гипотез:
1. Полиномы mod p — "плоская" структура, все коэффициенты равноважны
2. Деревья решений — иерархическая, верхние ветки важнее нижних
3. Пороговые функции — линейные, каждый новый пример чуть улучшает

Предсказание:
- Полиномы: резкий переход (подтверждено ранее, контрольная группа)
- Деревья: ступенчатое улучшение (плато на каждом уровне)
- Линейные: плавное улучшение (примерно линейное)

Измеряем: accuracy на всём пространстве как функцию k (число обучающих примеров).
"""

import json
import random
import itertools
from collections import Counter

random.seed(42)

# ===================== Класс 1: Полиномы mod p =====================

def poly_eval(coeffs, x, p):
    """Вычисляет полином с коэффициентами coeffs в точке x mod p."""
    result = 0
    for i, c in enumerate(coeffs):
        result = (result + c * pow(x, i, p)) % p
    return result

def poly_interpolate(points, p):
    """Интерполяция Лагранжа mod p. Возвращает коэффициенты или None если недостаточно точек."""
    n = len(points)
    if n == 0:
        return None

    # Строим полином степени n-1 через n точек
    xs = [pt[0] for pt in points]
    ys = [pt[1] for pt in points]

    # Проверяем, все ли x различны
    if len(set(xs)) < n:
        return None

    # Лагранжева интерполяция → значения во всех точках 0..p-1
    def lagrange_eval(x_eval):
        result = 0
        for i in range(n):
            num = ys[i]
            for j in range(n):
                if i != j:
                    diff = (xs[i] - xs[j]) % p
                    inv = pow(diff, p - 2, p)  # обратный элемент по Ферма
                    num = (num * ((x_eval - xs[j]) * inv)) % p
            result = (result + num) % p
        return result

    return lagrange_eval

def experiment_polynomial(p, degree, n_trials=30):
    """Кривая обучения для полиномов степени degree mod p."""
    results = {}  # k -> [accuracy, ...]

    for trial in range(n_trials):
        # Случайный полином
        coeffs = [random.randint(0, p-1) for _ in range(degree + 1)]
        all_points = [(x, poly_eval(coeffs, x, p)) for x in range(p)]

        for k in range(1, min(p, degree + 5)):
            sample = random.sample(all_points, k)

            if k <= degree:
                # Недостаточно точек — интерполируем полином степени k-1
                interp = poly_interpolate(sample, p)
                if interp is None:
                    acc = 0.0
                else:
                    correct = sum(1 for x in range(p) if interp(x) == poly_eval(coeffs, x, p))
                    acc = correct / p
            else:
                # Достаточно точек — интерполируем полином степени degree
                # Но берём только degree+1 точек
                sub = sample[:degree + 1]
                interp = poly_interpolate(sub, p)
                if interp is None:
                    acc = 0.0
                else:
                    correct = sum(1 for x in range(p) if interp(x) == poly_eval(coeffs, x, p))
                    acc = correct / p

            results.setdefault(k, []).append(acc)

    return {k: sum(v)/len(v) for k, v in results.items()}


# ===================== Класс 2: Деревья решений =====================

def make_random_tree(n_features, max_depth):
    """Случайное дерево решений на n_features бинарных признаках, глубина <= max_depth."""
    if max_depth == 0:
        return random.choice([0, 1])

    feature = random.randint(0, n_features - 1)
    left = make_random_tree(n_features, max_depth - 1)
    right = make_random_tree(n_features, max_depth - 1)
    return (feature, left, right)

def eval_tree(tree, x):
    """Вычисляет дерево решений на входе x (список бит)."""
    if isinstance(tree, int):
        return tree
    feature, left, right = tree
    if x[feature] == 0:
        return eval_tree(left, x)
    else:
        return eval_tree(right, x)

def learn_tree(examples, n_features, max_depth):
    """Жадное обучение дерева решений (ID3-подобное)."""
    if not examples:
        return random.choice([0, 1])

    labels = [y for _, y in examples]
    if len(set(labels)) == 1:
        return labels[0]

    if max_depth == 0:
        # Голосование большинством
        return Counter(labels).most_common(1)[0][0]

    # Выбираем лучший признак по information gain (упрощённо: максимум |count_0 - count_1|)
    best_feature = None
    best_score = -1

    for f in range(n_features):
        left_labels = [y for x, y in examples if x[f] == 0]
        right_labels = [y for x, y in examples if x[f] == 1]

        if not left_labels or not right_labels:
            continue

        # Gini impurity reduction
        def gini(labels):
            if not labels:
                return 0
            p = sum(labels) / len(labels)
            return 2 * p * (1 - p)

        parent_gini = gini(labels)
        child_gini = (len(left_labels) * gini(left_labels) + len(right_labels) * gini(right_labels)) / len(labels)
        score = parent_gini - child_gini

        if score > best_score:
            best_score = score
            best_feature = f

    if best_feature is None:
        return Counter(labels).most_common(1)[0][0]

    left_examples = [(x, y) for x, y in examples if x[best_feature] == 0]
    right_examples = [(x, y) for x, y in examples if x[best_feature] == 1]

    left_tree = learn_tree(left_examples, n_features, max_depth - 1)
    right_tree = learn_tree(right_examples, n_features, max_depth - 1)

    return (best_feature, left_tree, right_tree)

def experiment_tree(n_features, max_depth, n_trials=30):
    """Кривая обучения для деревьев решений."""
    all_inputs = list(itertools.product([0, 1], repeat=n_features))
    n_inputs = len(all_inputs)
    results = {}

    for trial in range(n_trials):
        tree = make_random_tree(n_features, max_depth)
        all_labeled = [(list(x), eval_tree(tree, list(x))) for x in all_inputs]

        for k in range(1, min(n_inputs, n_features * (2**max_depth) + 5)):
            sample = random.sample(all_labeled, min(k, n_inputs))
            learned = learn_tree(sample, n_features, max_depth)

            correct = sum(1 for x, y in all_labeled if eval_tree(learned, list(x)) == y)
            acc = correct / n_inputs
            results.setdefault(k, []).append(acc)

    return {k: sum(v)/len(v) for k, v in results.items()}


# ===================== Класс 3: Линейные пороговые =====================

def make_random_threshold(n_features):
    """Случайная пороговая функция: f(x) = 1 если sum(w_i * x_i) >= threshold."""
    weights = [random.uniform(-1, 1) for _ in range(n_features)]
    # Порог — медиана взвешенных сумм
    all_inputs = list(itertools.product([0, 1], repeat=n_features))
    sums = sorted(sum(w * x for w, x in zip(weights, inp)) for inp in all_inputs)
    threshold = sums[len(sums) // 2]
    return weights, threshold

def eval_threshold(weights, threshold, x):
    return 1 if sum(w * xi for w, xi in zip(weights, x)) >= threshold else 0

def learn_threshold_simple(examples, n_features, n_iters=100):
    """Простой перцептрон для обучения пороговой функции."""
    weights = [0.0] * n_features
    threshold = 0.0
    lr = 0.1

    for _ in range(n_iters):
        for x, y in examples:
            pred = 1 if sum(w * xi for w, xi in zip(weights, x)) >= threshold else 0
            if pred != y:
                for i in range(n_features):
                    weights[i] += lr * (y - pred) * x[i]
                threshold -= lr * (y - pred)

    return weights, threshold

def experiment_threshold(n_features, n_trials=30):
    """Кривая обучения для пороговых функций."""
    all_inputs = list(itertools.product([0, 1], repeat=n_features))
    n_inputs = len(all_inputs)
    results = {}

    for trial in range(n_trials):
        weights, threshold = make_random_threshold(n_features)
        all_labeled = [(list(x), eval_threshold(weights, threshold, list(x))) for x in all_inputs]

        for k in range(1, min(n_inputs, 3 * n_features + 5)):
            sample = random.sample(all_labeled, min(k, n_inputs))
            w_learned, t_learned = learn_threshold_simple(sample, n_features)

            correct = sum(1 for x, y in all_labeled
                         if (1 if sum(wi * xi for wi, xi in zip(w_learned, list(x))) >= t_learned else 0) == y)
            acc = correct / n_inputs
            results.setdefault(k, []).append(acc)

    return {k: sum(v)/len(v) for k, v in results.items()}


# ===================== Запуск =====================

if __name__ == "__main__":
    print("=== Эксперимент: форма кривых обучения ===\n")

    # Параметры
    p = 17  # простое число для полиномов
    degree = 4
    n_features = 6  # 64 входа
    tree_depth = 3

    print(f"Полиномы: степень {degree}, mod {p}")
    poly_results = experiment_polynomial(p, degree, n_trials=30)
    print("  k -> accuracy:")
    for k in sorted(poly_results.keys()):
        bar = "█" * int(poly_results[k] * 40)
        print(f"  k={k:2d}: {poly_results[k]:.3f} {bar}")

    print(f"\nДеревья решений: {n_features} признаков, глубина {tree_depth}")
    tree_results = experiment_tree(n_features, tree_depth, n_trials=30)
    print("  k -> accuracy:")
    for k in sorted(tree_results.keys()):
        bar = "█" * int(tree_results[k] * 40)
        print(f"  k={k:2d}: {tree_results[k]:.3f} {bar}")

    print(f"\nПороговые функции: {n_features} признаков")
    thresh_results = experiment_threshold(n_features, n_trials=30)
    print("  k -> accuracy:")
    for k in sorted(thresh_results.keys()):
        bar = "█" * int(thresh_results[k] * 40)
        print(f"  k={k:2d}: {thresh_results[k]:.3f} {bar}")

    # Анализ формы кривых
    print("\n=== Анализ формы кривых ===")

    def curve_sharpness(results):
        """Измеряет резкость перехода: максимальный скачок accuracy между соседними k."""
        ks = sorted(results.keys())
        if len(ks) < 2:
            return 0.0
        max_jump = 0
        jump_k = 0
        for i in range(1, len(ks)):
            jump = results[ks[i]] - results[ks[i-1]]
            if jump > max_jump:
                max_jump = jump
                jump_k = ks[i]
        return max_jump, jump_k

    def curve_linearity(results):
        """Измеряет линейность кривой: R² линейной регрессии."""
        ks = sorted(results.keys())
        accs = [results[k] for k in ks]
        n = len(ks)
        if n < 3:
            return 0.0

        x_mean = sum(ks) / n
        y_mean = sum(accs) / n

        ss_xy = sum((ks[i] - x_mean) * (accs[i] - y_mean) for i in range(n))
        ss_xx = sum((ks[i] - x_mean) ** 2 for i in range(n))
        ss_yy = sum((accs[i] - y_mean) ** 2 for i in range(n))

        if ss_xx == 0 or ss_yy == 0:
            return 0.0

        r = ss_xy / (ss_xx * ss_yy) ** 0.5
        return r ** 2

    for name, res in [("Полиномы", poly_results), ("Деревья", tree_results), ("Пороговые", thresh_results)]:
        sharpness, jump_k = curve_sharpness(res)
        linearity = curve_linearity(res)
        print(f"\n{name}:")
        print(f"  Макс. скачок: {sharpness:.3f} при k={jump_k}")
        print(f"  Линейность (R²): {linearity:.3f}")
        if sharpness > 0.3:
            print(f"  → ФАЗОВЫЙ ПЕРЕХОД (резкий скачок)")
        elif linearity > 0.9:
            print(f"  → ПЛАВНОЕ улучшение (линейное)")
        else:
            print(f"  → СТУПЕНЧАТОЕ улучшение")

    # Сохраняем результаты
    all_results = {
        "polynomial": {str(k): v for k, v in poly_results.items()},
        "decision_tree": {str(k): v for k, v in tree_results.items()},
        "threshold": {str(k): v for k, v in thresh_results.items()},
        "params": {
            "p": p, "degree": degree,
            "n_features": n_features, "tree_depth": tree_depth,
            "n_trials": 30
        }
    }

    with open("phase_transition_types_results.json", "w") as f:
        json.dump(all_results, f, indent=2)

    print("\nРезультаты сохранены в phase_transition_types_results.json")
