"""
Lonely Runner Conjecture: computational exploration.

N runners on a unit circle, starting at 0, with distinct constant speeds.
Conjecture: each runner is eventually at distance >= 1/N from all others.

WLOG we can fix one runner at speed 0 and look at relative speeds.
Then the question becomes: for speeds v_1,...,v_{N-1}, does the runner at 0
ever have all others at distance >= 1/N from it?

Distance on unit circle: min(x mod 1, 1 - x mod 1)

We want: max_t min_i dist(v_i * t mod 1, 0) >= 1/N

Questions I want to answer:
1. For small N, what speed configurations minimize the "loneliness"
   (i.e., come closest to violating the conjecture)?
2. Is 1/N always achievable, or sometimes barely exceeded?
3. What structure do the hardest configurations have?
"""

import numpy as np
from itertools import combinations
from fractions import Fraction

def circle_distance(x):
    """Distance from 0 on unit circle."""
    x_mod = x % 1.0
    return min(x_mod, 1.0 - x_mod)

def loneliness_at_time(t, speeds):
    """Minimum distance from all runners at time t."""
    return min(circle_distance(v * t) for v in speeds)

def max_loneliness(speeds, resolution=10000):
    """
    Maximum over time of the minimum distance from all runners.
    For integer speeds, the pattern repeats with period 1/gcd(speeds),
    so we only need to search one period.
    """
    # For integer speeds, period is 1 (fractional positions repeat with period 1)
    # Use fine grid + local refinement
    ts = np.linspace(0, 1, resolution, endpoint=False)
    best = 0
    best_t = 0
    for t in ts:
        lone = loneliness_at_time(t, speeds)
        if lone > best:
            best = lone
            best_t = t

    # Local refinement around best_t
    dt = 1.0 / resolution
    for _ in range(3):
        ts_local = np.linspace(best_t - dt, best_t + dt, 100)
        for t in ts_local:
            lone = loneliness_at_time(t, speeds)
            if lone > best:
                best = lone
                best_t = t
        dt /= 10

    return best, best_t

def find_hardest_configs(N, max_speed=30, top_k=10):
    """
    For given N (total runners including the stationary one),
    find speed configurations that minimize max_loneliness.

    We fix runner 0 at speed 0. The other N-1 runners have
    distinct positive integer speeds from 1..max_speed.
    """
    n_moving = N - 1
    threshold = 1.0 / N

    results = []

    for speeds in combinations(range(1, max_speed + 1), n_moving):
        ml, mt = max_loneliness(speeds, resolution=5000)
        results.append((ml, speeds, mt))

    results.sort(key=lambda x: x[0])

    print(f"\n=== N = {N} runners, threshold = 1/{N} = {threshold:.6f} ===")
    print(f"Searching speeds 1..{max_speed}, choosing {n_moving}")
    print(f"Total configs tested: {len(results)}")

    print(f"\nHardest {top_k} configurations (lowest max-loneliness):")
    for i, (ml, speeds, mt) in enumerate(results[:top_k]):
        ratio = ml / threshold
        print(f"  {i+1}. speeds={speeds}, loneliness={ml:.6f}, "
              f"ratio to 1/N = {ratio:.4f}, at t={mt:.6f}")

    print(f"\nEasiest {top_k} configurations (highest max-loneliness):")
    for i, (ml, speeds, mt) in enumerate(results[-top_k:]):
        ratio = ml / threshold
        print(f"  {i+1}. speeds={speeds}, loneliness={ml:.6f}, "
              f"ratio to 1/N = {ratio:.4f}")

    # Check if conjecture holds
    violations = [(ml, s, t) for ml, s, t in results if ml < threshold - 1e-6]
    if violations:
        print(f"\n*** POTENTIAL VIOLATIONS: {len(violations)} ***")
        for ml, s, t in violations[:5]:
            print(f"  speeds={s}, loneliness={ml:.6f} < {threshold:.6f}")
    else:
        print(f"\nConjecture holds for all {len(results)} configurations.")
        min_ml = results[0][0]
        print(f"Tightest case: loneliness = {min_ml:.6f}, threshold = {threshold:.6f}")
        print(f"Margin: {min_ml - threshold:.6f}")

    return results


def analyze_tight_cases(N, max_speed=30):
    """
    Find cases where loneliness ≈ 1/N (tight cases).
    These are the structurally interesting configurations.
    """
    n_moving = N - 1
    threshold = 1.0 / N

    tight = []
    for speeds in combinations(range(1, max_speed + 1), n_moving):
        ml, mt = max_loneliness(speeds, resolution=5000)
        if abs(ml - threshold) < 0.005:  # within 0.5% of threshold
            tight.append((ml, speeds, mt))

    print(f"\n=== Tight cases for N={N} (loneliness within 0.5% of 1/{N}) ===")
    tight.sort(key=lambda x: x[0])
    for ml, speeds, mt in tight[:20]:
        # Check if speeds have special structure
        ratios = [speeds[i+1]/speeds[i] for i in range(len(speeds)-1)]
        gcd_all = speeds[0]
        for s in speeds[1:]:
            from math import gcd
            gcd_all = gcd(gcd_all, s)
        print(f"  speeds={speeds}, loneliness={ml:.6f}, "
              f"gcd={gcd_all}, ratios={[f'{r:.2f}' for r in ratios]}")

    return tight


def exact_loneliness_rational(speeds, N, denom_limit=1000):
    """
    For integer speeds, try to find exact loneliness using rational arithmetic.
    The optimal time must be at a point where some v_i * t = k/N for integer k.
    (Because at the optimal time, at least one runner is at distance exactly 1/N.)
    """
    threshold = Fraction(1, N)
    best = Fraction(0)

    n_moving = len(speeds)

    # Candidate times: t = (k/N) / v_i for each speed v_i and k = 1,...,N-1
    candidates = set()
    for v in speeds:
        for k in range(1, N):
            t = Fraction(k, N * v)
            candidates.add(t)
            # Also t = (N-k)/(N*v)
            t2 = Fraction(N - k, N * v)
            candidates.add(t2)

    for t in candidates:
        if t <= 0:
            continue
        min_dist = Fraction(1)  # max possible on circle
        for v in speeds:
            pos = (v * t) % 1
            if isinstance(pos, Fraction):
                dist = min(pos, 1 - pos)
            else:
                pos = Fraction(v * t.numerator, t.denominator) % 1
                dist = min(pos, 1 - pos)
            if dist < min_dist:
                min_dist = dist
        if min_dist > best:
            best = min_dist

    return best


if __name__ == "__main__":
    import json
    results = {}

    # Explore N = 3, 4, 5, 6
    for N in [3, 4, 5, 6]:
        max_spd = 20 if N <= 5 else 15
        r = find_hardest_configs(N, max_speed=max_spd, top_k=10)
        results[f"N={N}"] = {
            "hardest": [(ml, list(s), t) for ml, s, t in r[:10]],
            "threshold": 1.0/N,
            "total_configs": len(r),
            "min_loneliness": r[0][0],
            "conjecture_holds": all(ml >= 1.0/N - 1e-6 for ml, _, _ in r)
        }

    # Analyze tight cases for N=4,5
    print("\n" + "="*60)
    for N in [4, 5]:
        max_spd = 20 if N == 4 else 15
        analyze_tight_cases(N, max_speed=max_spd)

    # Try exact rational computation for the hardest known case N=4
    print("\n=== Exact rational computation for hardest N=4 cases ===")
    hardest_4 = [(s[0], s[1], s[2]) for _, s, _ in
                 sorted([(ml, list(speeds), mt)
                         for speeds in combinations(range(1, 21), 3)
                         for ml, mt in [max_loneliness(speeds, resolution=3000)]])[:5]]

    # Actually let me just do this more carefully
    print("\nChecking exact values for N=4 tight cases:")
    for speeds in [(1, 2, 3), (1, 3, 5), (1, 2, 5), (2, 3, 5), (1, 3, 7)]:
        exact = exact_loneliness_rational(speeds, 4)
        print(f"  speeds={speeds}: exact loneliness = {exact} = {float(exact):.6f} "
              f"(threshold 1/4 = 0.250000)")

    # Save results
    with open("lonely_runner_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nResults saved to lonely_runner_results.json")
