"""
Фазовый переход в понимании: свойство проблемы или метода?

Эксперимент: полином степени d, различные методы восстановления,
различное количество обучающих точек k. Как точность зависит от k?

Гипотеза из предыдущей работы: при k = d+1 происходит резкий переход.
Но это было для точной интерполяции Лагранжа на конечном поле.

Вопрос: что происходит с приближёнными методами (регрессия, нейросеть)?
Переход остаётся резким или размывается?
"""

import numpy as np
import json
from itertools import product

np.random.seed(42)


def generate_polynomial(degree, coeff_range=(-3, 3)):
    """Случайный полином степени d."""
    coeffs = np.random.uniform(coeff_range[0], coeff_range[1], degree + 1)
    return coeffs


def evaluate_poly(coeffs, x):
    """Вычислить полином."""
    return sum(c * x**i for i, c in enumerate(coeffs))


def generate_data(coeffs, n_points, x_range=(-2, 2), noise_std=0.0):
    """Сгенерировать данные: x -> p(x) + шум."""
    x = np.random.uniform(x_range[0], x_range[1], n_points)
    y = np.array([evaluate_poly(coeffs, xi) for xi in x])
    if noise_std > 0:
        y += np.random.normal(0, noise_std, n_points)
    return x, y


def test_accuracy(predictor, coeffs, n_test=200, x_range=(-2, 2)):
    """Точность на тестовых данных."""
    x_test = np.linspace(x_range[0], x_range[1], n_test)
    y_true = np.array([evaluate_poly(coeffs, xi) for xi in x_test])
    y_pred = predictor(x_test)

    # R² как метрика
    ss_res = np.sum((y_true - y_pred)**2)
    ss_tot = np.sum((y_true - np.mean(y_true))**2)
    if ss_tot < 1e-12:
        return 1.0 if ss_res < 1e-10 else 0.0
    r2 = 1 - ss_res / ss_tot
    return max(r2, 0.0)  # обрезаем отрицательные


# === Методы восстановления ===

def lagrange_interpolator(x_train, y_train, degree=None):
    """Точная интерполяция (numpy polyfit с degree = len-1)."""
    d = len(x_train) - 1
    try:
        coeffs = np.polyfit(x_train, y_train, d)
        return lambda x: np.polyval(coeffs, x)
    except:
        return lambda x: np.zeros_like(x)


def polynomial_regression(x_train, y_train, degree):
    """Полиномиальная регрессия фиксированной степени d."""
    try:
        coeffs = np.polyfit(x_train, y_train, degree)
        return lambda x: np.polyval(coeffs, x)
    except:
        return lambda x: np.zeros_like(x)


def ridge_regression(x_train, y_train, degree, alpha=0.01):
    """Гребневая регрессия степени d."""
    X = np.vander(x_train, degree + 1)
    try:
        I = np.eye(degree + 1)
        coeffs = np.linalg.solve(X.T @ X + alpha * I, X.T @ y_train)
        return lambda x: np.vander(x, degree + 1) @ coeffs
    except:
        return lambda x: np.zeros_like(x)


def simple_neural_net(x_train, y_train, hidden=20, epochs=2000, lr=0.01):
    """Однослойная нейросеть (реализация на numpy)."""
    x = x_train.reshape(-1, 1)
    y = y_train.reshape(-1, 1)

    # Нормализация
    x_mean, x_std = x.mean(), x.std() + 1e-8
    y_mean, y_std = y.mean(), y.std() + 1e-8
    x_norm = (x - x_mean) / x_std
    y_norm = (y - y_mean) / y_std

    # Инициализация (He)
    W1 = np.random.randn(1, hidden) * np.sqrt(2.0 / 1)
    b1 = np.zeros((1, hidden))
    W2 = np.random.randn(hidden, 1) * np.sqrt(2.0 / hidden)
    b2 = np.zeros((1, 1))

    for epoch in range(epochs):
        # Forward
        z1 = x_norm @ W1 + b1
        a1 = np.tanh(z1)
        z2 = a1 @ W2 + b2

        # Loss
        loss = np.mean((z2 - y_norm)**2)

        # Backward
        dz2 = 2 * (z2 - y_norm) / len(x)
        dW2 = a1.T @ dz2
        db2 = dz2.sum(axis=0, keepdims=True)
        da1 = dz2 @ W2.T
        dz1 = da1 * (1 - a1**2)
        dW1 = x_norm.T @ dz1
        db1 = dz1.sum(axis=0, keepdims=True)

        W2 -= lr * dW2
        b2 -= lr * db2
        W1 -= lr * dW1
        b1 -= lr * db1

    def predict(x_new):
        x_n = (x_new.reshape(-1, 1) - x_mean) / x_std
        a = np.tanh(x_n @ W1 + b1)
        return (a @ W2 + b2).flatten() * y_std + y_mean

    return predict


# === Эксперимент ===

def run_experiment():
    results = []

    degrees = [2, 3, 5, 8]
    k_multipliers = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 5.0]
    noise_levels = [0.0, 0.1, 0.5]
    n_trials = 10

    total = len(degrees) * len(k_multipliers) * len(noise_levels) * n_trials
    done = 0

    for degree in degrees:
        for noise in noise_levels:
            for k_mult in k_multipliers:
                k = max(2, int(round((degree + 1) * k_mult)))

                for trial in range(n_trials):
                    coeffs = generate_polynomial(degree)
                    x_train, y_train = generate_data(coeffs, k, noise_std=noise)

                    # Метод 1: Полиномиальная регрессия точной степени
                    if k > degree:
                        pred = polynomial_regression(x_train, y_train, degree)
                        acc_polyfit = test_accuracy(pred, coeffs)
                    else:
                        # Недоопределённая система — используем что есть
                        pred = polynomial_regression(x_train, y_train, k - 1)
                        acc_polyfit = test_accuracy(pred, coeffs)

                    # Метод 2: Гребневая регрессия
                    reg_degree = min(degree, k - 1)
                    pred = ridge_regression(x_train, y_train, reg_degree)
                    acc_ridge = test_accuracy(pred, coeffs)

                    # Метод 3: Нейросеть
                    pred = simple_neural_net(x_train, y_train, hidden=20, epochs=1500, lr=0.01)
                    acc_nn = test_accuracy(pred, coeffs)

                    # Метод 4: Точная интерполяция (Лагранж)
                    pred = lagrange_interpolator(x_train, y_train)
                    acc_lagrange = test_accuracy(pred, coeffs)

                    results.append({
                        'degree': degree,
                        'k': k,
                        'k_ratio': k / (degree + 1),
                        'noise': noise,
                        'trial': trial,
                        'polyfit': round(acc_polyfit, 4),
                        'ridge': round(acc_ridge, 4),
                        'neural_net': round(acc_nn, 4),
                        'lagrange': round(acc_lagrange, 4),
                    })

                    done += 1
                    if done % 50 == 0:
                        print(f"  {done}/{total} done")

    return results


def analyze(results):
    """Агрегировать и извлечь паттерн."""
    analysis = {}

    for r in results:
        key = (r['degree'], r['k_ratio'], r['noise'])
        if key not in analysis:
            analysis[key] = {'polyfit': [], 'ridge': [], 'neural_net': [], 'lagrange': []}
        for method in ['polyfit', 'ridge', 'neural_net', 'lagrange']:
            analysis[key][method].append(r[method])

    summary = []
    for (deg, kr, noise), accs in sorted(analysis.items()):
        entry = {
            'degree': deg,
            'k_ratio': round(kr, 2),
            'noise': noise,
        }
        for method in ['polyfit', 'ridge', 'neural_net', 'lagrange']:
            vals = accs[method]
            entry[f'{method}_mean'] = round(np.mean(vals), 4)
            entry[f'{method}_std'] = round(np.std(vals), 4)
        summary.append(entry)

    return summary


def compute_transition_sharpness(summary):
    """
    Вычислить резкость перехода для каждого метода.
    Резкость = максимальное изменение accuracy на единицу k_ratio.
    """
    transitions = {}

    for noise in [0.0, 0.1, 0.5]:
        for degree in [2, 3, 5, 8]:
            entries = [s for s in summary if s['degree'] == degree and s['noise'] == noise]
            entries.sort(key=lambda x: x['k_ratio'])

            for method in ['polyfit', 'ridge', 'neural_net', 'lagrange']:
                key = f'{method}_mean'
                max_jump = 0
                jump_location = 0
                for i in range(1, len(entries)):
                    delta_acc = entries[i][key] - entries[i-1][key]
                    delta_k = entries[i]['k_ratio'] - entries[i-1]['k_ratio']
                    if delta_k > 0:
                        slope = delta_acc / delta_k
                        if slope > max_jump:
                            max_jump = slope
                            jump_location = entries[i]['k_ratio']

                t_key = (degree, noise, method)
                transitions[t_key] = {
                    'max_slope': round(max_jump, 4),
                    'jump_at_k_ratio': round(jump_location, 2)
                }

    return transitions


if __name__ == '__main__':
    print("=== Фазовый переход в понимании ===")
    print("Степени полиномов:", [2, 3, 5, 8])
    print("Методы: polyfit, ridge, neural_net, lagrange")
    print()

    results = run_experiment()

    with open('phase_transition_raw.json', 'w') as f:
        json.dump(results, f, indent=2)

    summary = analyze(results)
    transitions = compute_transition_sharpness(summary)

    # Вывод ключевых результатов
    print("\n=== РЕЗУЛЬТАТЫ ===\n")

    for noise in [0.0, 0.1, 0.5]:
        print(f"\n--- Шум = {noise} ---")
        print(f"{'deg':>4} {'k/d+1':>6} | {'polyfit':>8} {'ridge':>8} {'nn':>8} {'lagrange':>8}")
        print("-" * 55)
        for s in summary:
            if s['noise'] == noise:
                print(f"{s['degree']:>4} {s['k_ratio']:>6.2f} | "
                      f"{s['polyfit_mean']:>8.4f} {s['ridge_mean']:>8.4f} "
                      f"{s['neural_net_mean']:>8.4f} {s['lagrange_mean']:>8.4f}")

    print("\n\n=== РЕЗКОСТЬ ПЕРЕХОДА ===")
    print(f"{'deg':>4} {'noise':>5} {'method':>10} | {'max_slope':>10} {'at k_ratio':>10}")
    print("-" * 50)
    for (deg, noise, method), t in sorted(transitions.items()):
        if t['max_slope'] > 0.1:
            print(f"{deg:>4} {noise:>5.1f} {method:>10} | {t['max_slope']:>10.4f} {t['jump_at_k_ratio']:>10.2f}")

    # Сохранить
    output = {
        'summary': summary,
        'transitions': {f"{k[0]}_{k[1]}_{k[2]}": v for k, v in transitions.items()},
    }
    with open('phase_transition_results.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("\n\nРезультаты сохранены в phase_transition_results.json")
