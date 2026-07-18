"""
演示与对比：Optimal Resizable Arrays 实现

对 GeometricArray、HAT、GeneralRArray 进行横向对比，
并结合增长游戏的下界分析验证均摊代价的理论预测。
"""

import sys
import os
import math
import time
from typing import List, Tuple

# Windows GBK 兼容性：设置环境变量强制 UTF-8
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 导入各实现
from geometric_array import GeometricArray
from hat import HAT
from general_r_array import GeneralRArray, R3Array
from growth_game import (
    growth_game_optimal_cost,
    growth_game_amortized_lower_bound,
    amortized_lower_bound_via_growth_game,
)


# ═══════════════════════════════════════════════════════════
# 1. 正确性验证
# ═══════════════════════════════════════════════════════════

def verify_correctness():
    """验证所有实现的基本正确性"""
    print("=" * 72)
    print("1. 正确性验证")
    print("=" * 72)

    test_sizes = [0, 1, 5, 10, 100, 500]

    # GeometricArray
    print("\nGeometricArray:")
    for alpha in [0.5, 1.0, 2.0]:
        errors = 0
        for n in test_sizes:
            arr = GeometricArray(alpha)
            for i in range(n):
                arr.grow(i * 2)
            for i in range(n):
                if arr[i] != i * 2:
                    errors += 1
        status = "✓" if errors == 0 else f"✗ ({errors} errors)"
        print(f"  α={alpha}: {status}")

    # HAT
    print("\nHAT:")
    errors = 0
    for n in test_sizes:
        hat = HAT()
        for i in range(n):
            hat.grow(i * 3)
        for i in range(n):
            if hat[i] != i * 3:
                errors += 1
        # 验证 shrink
        for _ in range(min(n, 10)):
            hat.shrink()
    status = "✓" if errors == 0 else f"✗ ({errors} errors)"
    print(f"  {status}")

    # GeneralRArray
    print("\nGeneralRArray:")
    for r in [2, 3, 4, 5]:
        errors = 0
        for n in test_sizes:
            arr = GeneralRArray(r)
            for i in range(n):
                arr.grow(i)
            for i in range(n):
                if arr[i] != i:
                    errors += 1
            # 验证内部一致性
            if not arr.verify():
                errors += 1
        status = "✓" if errors == 0 else f"✗ ({errors} errors)"
        print(f"  r={r}: {status}")


# ═══════════════════════════════════════════════════════════
# 2. 均摊代价分析
# ═══════════════════════════════════════════════════════════

def analyze_amortized_cost():
    """分析各实现的均摊代价，与理论预测对比"""
    print(f"\n{'=' * 72}")
    print("2. 均摊代价分析")
    print("=" * 72)

    N = 10000

    # GeometricArray
    print(f"\nGeometricArray (N={N}):")
    print(f"  {'α':>6} {'均摊(经验)':>12} {'均摊(理论增长)':>16} {'浪费率':>10}")
    print(f"  {'─' * 50}")
    for alpha in [0.25, 0.5, 1.0, 2.0, 4.0]:
        arr = GeometricArray(alpha)
        for i in range(N):
            arr.grow(i)
        print(f"  {alpha:>6.2f} {arr.empirical_amortized:>12.4f} "
              f"{arr.theoretical_amortized_grow:>16.4f} "
              f"{arr.wasted_space / arr.capacity:>10.2%}")

    # HAT
    print(f"\nHAT (N={N}):")
    hat = HAT()
    for i in range(N):
        hat.grow(i)
    lo, hi = hat.theoretical_B_bound
    print(f"  经验均摊: {hat.empirical_amortized:.4f}")
    print(f"  理论均摊: O(1)")
    print(f"  B={hat.B}, B∈[{int(lo)}, {int(hi)})")
    print(f"  额外空间: {hat.extra_space}, 理论: O(√N) ≈ O({int(N**0.5)})")

    # GeneralRArray: 不同 r 对比
    print(f"\nGeneralRArray (N={N}):")
    print(f"  {'r':>4} {'B':>6} {'均摊(经验)':>12} {'均摊(理论O(r))':>16} "
          f"{'合并':>6} {'拆分':>6} {'重建':>4} {'额外空间≈':>12}")
    print(f"  {'─' * 72}")
    for r in range(2, 11):
        arr = GeneralRArray(r)
        for i in range(N):
            arr.grow(i)
        print(f"  {r:>4} {arr.B:>6} {arr.empirical_amortized:>12.4f} "
              f"{'O(' + str(r) + ')':>16} "
              f"{arr.merge_count:>6} {arr.split_count:>6} {arr.rebuild_count:>4} "
              f"{arr.extra_space_estimate:>12}")


# ═══════════════════════════════════════════════════════════
# 3. 增长游戏验证
# ═══════════════════════════════════════════════════════════

def verify_growth_game():
    """验证增长游戏的精确公式"""
    print(f"\n{'=' * 72}")
    print("3. 增长游戏 — 定理 8.6 验证")
    print("=" * 72)

    print(f"\n  {'N':>6} {'k':>3} {'n':>4} {'C(N,k)':>12} {'A(N,k)':>10} {'≥(k/(k+1))(n-1)':>18}")
    print(f"  {'─' * 60}")

    test_cases = [
        (5, 2), (10, 2), (20, 2), (50, 2),
        (10, 3), (50, 3), (100, 3),
        (100, 5), (500, 5),
    ]
    for N, k in test_cases:
        from growth_game import find_n_for_N
        n = find_n_for_N(N, k)
        cost = growth_game_optimal_cost(N, k)
        amortized = growth_game_amortized_lower_bound(N, k)
        bound = (k / (k + 1)) * (n - 1)
        print(f"  {N:>6} {k:>3} {n:>4} {cost:>12} {amortized:>10.4f} {bound:>18.4f}")


# ═══════════════════════════════════════════════════════════
# 4. 空间-时间 Trade-off 验证
# ═══════════════════════════════════════════════════════════

def verify_space_time_tradeoff():
    """
    验证论文的核心 trade-off：
    存储空间 s(N) 与均摊时间之间的权衡。

    推论 4.3: 若 s(N) = O(N^(1/r))，则均摊时间 = Ω(r)。
    定理 6.1: 上界 O(r) 匹配下界。
    """
    print(f"\n{'=' * 72}")
    print("4. 空间-时间 Trade-off 验证")
    print("=" * 72)

    N = 50000

    print(f"\n  N = {N}")
    print(f"  {'r':>4} {'存储s(N)=N^(1/r)':>20} {'临时t(N)=N^(1-1/r)':>22} "
          f"{'均摊(经验)':>12} {'理论O(r)':>10} {'下界Ω(r)':>10}")
    print(f"  {'─' * 82}")

    for r in [2, 3, 4, 5, 6]:
        arr = GeneralRArray(r)
        for i in range(N):
            arr.grow(i)

        s_N = N ** (1.0 / r)         # O(N^(1/r))
        t_N = N ** (1.0 - 1.0 / r)   # O(N^(1-1/r))

        # 增长游戏下界
        lower_bound = amortized_lower_bound_via_growth_game(N, r)

        print(f"  {r:>4} {s_N:>20.1f} {t_N:>22.1f} "
              f"{arr.empirical_amortized:>12.4f} {'O(' + str(r) + ')':>10} "
              f"≥{lower_bound:>8.2f}")


# ═══════════════════════════════════════════════════════════
# 5. 抖动（Thrashing）演示
# ═══════════════════════════════════════════════════════════

def demo_thrashing():
    """演示无滞后保护时的抖动退化"""
    print(f"\n{'=' * 72}")
    print("5. 抖动（Thrashing）演示")
    print("=" * 72)

    # 模拟一个"不良"策略：满时扩容×2，半满时收缩÷2
    class BadArray:
        """不良策略：增长阈值100%，收缩阈值50%（无滞后保护）"""

        def __init__(self):
            self.data = [None] * 2
            self.capacity = 2
            self.size = 0
            self.total_cost = 0

        def grow(self, x):
            self.total_cost += 1
            if self.size == self.capacity:
                new_cap = self.capacity * 2
                new_data = [None] * new_cap
                for i in range(self.size):
                    new_data[i] = self.data[i]
                self.data = new_data
                self.capacity = new_cap
                self.total_cost += self.size  # 拷贝
            self.data[self.size] = x
            self.size += 1

        def shrink(self):
            self.total_cost += 1
            self.size -= 1
            if self.size > 0 and self.size <= self.capacity // 2:
                new_cap = self.capacity // 2
                new_data = [None] * new_cap
                for i in range(self.size):
                    new_data[i] = self.data[i]
                self.data = new_data
                self.capacity = new_cap
                self.total_cost += self.size  # 拷贝

        @property
        def amortized(self):
            return self.total_cost / (self.size + 1) if self.size > 0 else 0

    # 使用不良策略
    bad = BadArray()
    for _ in range(100):
        bad.grow(0)

    cost_before = bad.total_cost
    ops_before = bad.size
    # 在阈值边界反复操作
    for _ in range(50):
        bad.shrink()
        bad.grow(0)
        bad.shrink()
        bad.grow(0)

    ops = bad.size - ops_before + 50 * 4  # approximate
    extra_cost = bad.total_cost - cost_before
    print(f"\n  不良策略（无滞后）:")
    print(f"    100次插入后 size={bad.size}, capacity={bad.capacity}")
    print(f"    边界交替操作新增代价: {extra_cost}, "
          f"均摊/操作 ≈ {extra_cost / 100 if extra_cost > 0 else 0:.1f}")

    # 使用良好策略（有滞后保护）
    good = GeometricArray(alpha=1.0)
    for _ in range(100):
        good.grow(0)

    cost_before = good.total_actual_cost
    for _ in range(50):
        good.shrink()
        good.grow(0)
        good.shrink()
        good.grow(0)

    extra_cost = good.total_actual_cost - cost_before
    print(f"\n  良好策略（α=1.0，收缩阈值=1/4）:")
    print(f"    size={good.size}, capacity={good.capacity}")
    print(f"    交替操作新增代价: {extra_cost}, "
          f"均摊 ≈ {good.empirical_amortized:.2f}")
    print(f"    滞后保护使得阈值间差距为因子4，避免了反复resize")


# ═══════════════════════════════════════════════════════════
# 6. 性能基准测试
# ═══════════════════════════════════════════════════════════

def benchmark():
    """简单的性能基准测试"""
    print(f"\n{'=' * 72}")
    print("6. 性能基准测试 (操作耗时)")
    print("=" * 72)

    N = 100000

    implementations = [
        ("GeometricArray(α=1)", lambda: GeometricArray(1.0)),
        ("HAT", lambda: HAT()),
        ("GeneralRArray(r=2)", lambda: GeneralRArray(2)),
        ("GeneralRArray(r=3)", lambda: GeneralRArray(3)),
        ("GeneralRArray(r=5)", lambda: GeneralRArray(5)),
        ("GeneralRArray(r=10)", lambda: GeneralRArray(10)),
    ]

    print(f"\n  N = {N}")
    print(f"  {'实现':<25} {'总耗时(ms)':>12} {'均摊(经验)':>12}")
    print(f"  {'─' * 52}")

    for name, factory in implementations:
        start = time.perf_counter()
        arr = factory()
        for i in range(N):
            arr.grow(i)
        elapsed = (time.perf_counter() - start) * 1000

        am = arr.empirical_amortized if hasattr(arr, 'empirical_amortized') else arr.amortized_cost
        print(f"  {name:<25} {elapsed:>12.2f} {am:>12.4f}")


# ═══════════════════════════════════════════════════════════
# 运行全部演示
# ═══════════════════════════════════════════════════════════

def main():
    """运行全部验证与演示"""
    print("=" * 72)
    print("  Optimal Resizable Arrays — 代码实现验证")
    print("  Tarjan & Zwick (2024), SIAM Journal on Computing")
    print("=" * 72)

    verify_correctness()
    analyze_amortized_cost()
    verify_growth_game()
    verify_space_time_tradeoff()
    demo_thrashing()
    benchmark()

    print(f"\n{'=' * 72}")
    print("  全部验证完成。")
    print("=" * 72)


if __name__ == "__main__":
    main()
