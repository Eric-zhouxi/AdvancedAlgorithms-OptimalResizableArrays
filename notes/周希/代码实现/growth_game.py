"""
增长游戏（Growth Game）模拟与精确解 (Section 8 of Tarjan & Zwick 2024)

增长游戏是将可调整数组的增长操作抽象为纯组合游戏的模型。

游戏定义（(N, k)-增长游戏）:
  - k 个子数组 A₁, A₂, ..., A_k
  - 约束：非空子数组必须是前缀；除 A₁ 外所有非空子数组必须满
  - 目标：以最小总代价插入 N 个元素

操作:
  1. 有空位 → 直接放入 (代价 1)
  2. 有空子数组 → 分配新子数组 (代价 1)
  3. 所有 k 个子数组满 → 选择 i，合并 A₁..A_i (代价 1+Σaⱼ)

定理 8.6 (精确公式):
  当 binom(n+k-1, k) ≤ N < binom(n+k, k) 时:
    C_{N,k} = (N+1)n − binom(n+k, k+1)
    A_{N,k} ≥ (k/(k+1))(n−1) ≥ (1/2)(n−1)
"""

import math
import sys
from functools import lru_cache
from typing import Tuple


# ═══════════════════════════════════════════════════════════
# 二项式系数
# ═══════════════════════════════════════════════════════════

@lru_cache(maxsize=None)
def binom(n: int, k: int) -> int:
    """二项式系数 C(n, k)"""
    if k < 0 or k > n:
        return 0
    if k == 0 or k == n:
        return 1
    # 使用较小的 k 以加速计算
    k = min(k, n - k)
    result = 1
    for i in range(k):
        result = result * (n - i) // (i + 1)
    return result


# ═══════════════════════════════════════════════════════════
# 定理 8.6: 精确公式
# ═══════════════════════════════════════════════════════════

def growth_game_optimal_cost(N: int, k: int) -> int:
    """
    使用定理 8.6 的精确公式计算 (N, k)-增长游戏的最小总代价。

    Parameters
    ----------
    N : int
        要插入的元素总数
    k : int
        子数组数量

    Returns
    -------
    C_{N,k} : int
        最优（最小）总代价
    """
    if N <= 0:
        return 0

    # 找到 n 使得 binom(n+k-1, k) ≤ N < binom(n+k, k)
    n = find_n_for_N(N, k)

    # 定理 8.6: C_{N,k} = (N+1)n − binom(n+k, k+1)
    cost = (N + 1) * n - binom(n + k, k + 1)
    return cost


def growth_game_amortized_lower_bound(N: int, k: int) -> float:
    """
    定理 8.6 的均摊代价下界。

    A_{N,k} ≥ (k/(k+1))(n−1) ≥ (1/2)(n−1)
    """
    if N <= 0:
        return 0.0
    n = find_n_for_N(N, k)
    return (k / (k + 1)) * (n - 1)


def find_n_for_N(N: int, k: int) -> int:
    """
    找到 n 使得 binom(n+k-1, k) ≤ N < binom(n+k, k)。

    组合意义：n 是使得 k 个子数组的总"容量"至少为 N+1 的最小值。
    从 n=0 开始搜索以保证对所有 (N, k) 组合都正确。
    """
    if N <= 0:
        return 0
    n = 0
    while binom(n + k, k) <= N:
        n += 1
        if n > 100000:  # 安全上限
            break
    return n


# ═══════════════════════════════════════════════════════════
# 动态规划: 暴力计算最优代价（小规模验证）
# ═══════════════════════════════════════════════════════════

class GrowthGameDP:
    """
    用动态规划精确计算 (N, k, ℓ)-增长游戏的最优代价。

    状态: (a₁, ..., a_k) 子数组的元素数
    ℓ: A₁ 允许的空位数上限（ℓ=0 对应标准增长游戏）

    注意：状态数随 N 和 k 指数增长，仅适用于小规模验证。
    """

    def __init__(self, N: int, k: int, ell: int = 0):
        self.N = N
        self.k = k
        self.ell = ell
        self._memo = {}

    def solve(self) -> int:
        """返回最小总代价"""
        initial_state = tuple([0] * self.k)
        return self._dp(0, initial_state)

    def _dp(self, inserted: int, state: Tuple[int, ...]) -> int:
        if inserted == self.N:
            return 0

        key = (inserted, state)
        if key in self._memo:
            return self._memo[key]

        # 找到第一个非满子数组
        a = list(state)
        best = float('inf')

        # 找到第一个有空位的子数组索引
        free_idx = -1
        for i in range(self.k):
            if i == 0:
                if a[i] < a[i + 1] + self.ell if i + 1 < self.k and a[i + 1] > 0 else True:
                    # A₁ 可以有 ℓ 个额外空位
                    free_idx = i
                    break
            elif a[i] > 0 and a[i] < a[i - 1]:
                free_idx = i
                break
            elif a[i] == 0:
                free_idx = i
                break

        # 操作1/2: 直接放入
        if free_idx >= 0:
            new_state = list(state)
            new_state[free_idx] += 1
            # 确保前缀性质
            new_state = self._normalize(tuple(new_state))
            cost = 1 + self._dp(inserted + 1, tuple(new_state))
            best = min(best, cost)

        # 操作3: 合并（所有子数组满时）
        all_full = all(
            a[i] > 0 for i in range(self.k)
        )
        if all_full or free_idx < 0:
            for i in range(1, self.k + 1):
                merged_sum = sum(a[:i])
                new_state = [merged_sum + 1] + list(a[i:]) + [0]
                new_state = new_state[:self.k]
                new_state = self._normalize(tuple(new_state))
                cost = 1 + merged_sum + self._dp(inserted + 1, tuple(new_state))
                best = min(best, cost)

        self._memo[key] = best
        return best

    def _normalize(self, state: Tuple[int, ...]) -> Tuple[int, ...]:
        """确保除A₁外所有非空子数组满，且非空前缀"""
        a = list(state)
        # 简单的标准化：将空子数组移到末尾
        # (完整实现需要确保约束满足)
        return tuple(a)


# ═══════════════════════════════════════════════════════════
# 模拟: 使用论文中的最优策略
# ═══════════════════════════════════════════════════════════

class GrowthGameSimulator:
    """
    按照论文描述的"最优策略"模拟增长游戏。

    最优策略的核心原则:
    - 尽可能让最后的子数组有最多的空位
    - 合并时选择最小的 i 使得合并后代价最优
    - 目标是最小化总拷贝代价
    """

    def __init__(self, k: int, ell: int = 0):
        self.k = k
        self.ell = ell
        # 子数组元素数
        self.a = [0] * k
        self.total_cost = 0
        self.N = 0

    def insert(self) -> None:
        """插入一个元素，使用贪心最优策略"""
        self.N += 1

        # 找第一个有空位的子数组
        free_idx = self._find_free()

        if free_idx >= 0:
            self.a[free_idx] += 1
            self.total_cost += 1  # 写入代价
        else:
            # 所有子数组满：需要合并
            # 选择最优的 i（最小化代价的策略：合并尽可能少的块）
            best_i = self._choose_merge()
            merged_sum = sum(self.a[:best_i])
            # 合并
            self.a[0] = merged_sum + 1  # 合并后的块 + 新元素
            for j in range(1, best_i):
                self.a[j] = self.a[j + best_i - 1] if j + best_i - 1 < len(self.a) else 0
            self.a[best_i - 1] = 0
            self.total_cost += 1 + merged_sum  # 合并代价 + 写入

    def _find_free(self) -> int:
        """找第一个有空位的子数组"""
        for i in range(self.k):
            if self.a[i] == 0:
                return i
            if i == 0 and self.a[0] < self.a[1] + self.ell if self.k > 1 and self.a[1] > 0 else True:
                return i
        return -1

    def _choose_merge(self) -> int:
        """选择合并的子数组数量（贪心：最小化代价）"""
        # 贪心策略：合并最少的子数组
        return 1 if self.k >= 1 else self.k

    @property
    def amortized_cost(self) -> float:
        if self.N == 0:
            return 0.0
        return self.total_cost / self.N


# ═══════════════════════════════════════════════════════════
# 推论 8.13: 最优最终状态
# ═══════════════════════════════════════════════════════════

def optimal_final_state_cost(N: int, k: int) -> int:
    """
    当 N = binom(n+k, k) − 1 时的精确代价（推论 8.13）。

    C_{N,k} = (kn/(k+1))(N+1)
    """
    if N <= 0:
        return 0
    n = find_n_for_N(N, k)
    # 验证是否恰为最优最终状态
    if N == binom(n + k, k) - 1:
        return (k * n * (N + 1)) // (k + 1)
    return growth_game_optimal_cost(N, k)


# ═══════════════════════════════════════════════════════════
# 下界到 Ω(r) 的连接 (Section 9)
# ═══════════════════════════════════════════════════════════

def amortized_lower_bound_via_growth_game(N: int, r: int) -> float:
    """
    使用增长游戏的下界推导均摊代价下界 Ω(r)。

    连接逻辑（论文 Section 9）:
    1. 若数据结构使用 N + O(N^(1/r)) 空间，则块数 k = Θ(r·N^(1/r))
    2. 代入增长游戏的均摊下界 A_{N,k} ≥ (k/(k+1))(n−1)
    3. n ≈ k!^(1/k) · N^(1/k)，替换 k ≈ r·N^(1/r)，得 A ≥ Ω(r)
    """
    # k ≈ r · N^(1/r)
    k = max(1, int(r * (N ** (1.0 / r))))
    return growth_game_amortized_lower_bound(N, k)


# ═══════════════════════════════════════════════════════════
# 演示
# ═══════════════════════════════════════════════════════════

def demo():
    """演示增长游戏的精确公式与下界"""
    print("=" * 72)
    print("增长游戏（Growth Game）— 定理 8.6 精确公式与下界")
    print("=" * 72)

    # 小规模示例
    print("\n小规模示例 (k=2):")
    print(f"{'N':>6} {'n':>4} {'binomial范围':>25} {'C(N,k)':>10} {'A(N,k)下界':>12}")
    print("-" * 65)

    for N in [1, 2, 3, 5, 8, 10, 15, 20, 30, 50, 100]:
        k = 2
        n = find_n_for_N(N, k)
        lo = binom(n + k - 1, k)
        hi = binom(n + k, k)
        cost = growth_game_optimal_cost(N, k)
        amortized = growth_game_amortized_lower_bound(N, k)
        print(f"{N:>6} {n:>4} [{lo}, {hi})     {cost:>10} {amortized:>12.4f}")

    # 不同 k 的对比
    print(f"\n{'─' * 72}")
    print("不同 k 值的均摊代价下界 (N=1000):")
    print(f"{'k':>6} {'n':>6} {'C(N,k)':>12} {'A(N,k)下界':>14} {'(1/2)(n-1)':>12}")
    print("-" * 56)

    N = 1000
    for k in [1, 2, 3, 5, 10, 20]:
        n = find_n_for_N(N, k)
        cost = growth_game_optimal_cost(N, k)
        amortized = growth_game_amortized_lower_bound(N, k)
        half_n = 0.5 * (n - 1)
        print(f"{k:>6} {n:>6} {cost:>12} {amortized:>14.4f} {half_n:>12.4f}")

    # 连接 Section 9: 下界 Ω(r)
    print(f"\n{'─' * 72}")
    print("从增长游戏到 Ω(r) 均摊下界 (Section 9):")
    print(f"{'r':>4} {'N':>8} {'k≈rN^(1/r)':>14} {'A(N,k)下界':>14}")
    print("-" * 48)

    for r in [2, 3, 4, 5]:
        for N in [100, 10000, 1000000]:
            lower = amortized_lower_bound_via_growth_game(N, r)
            k = max(1, int(r * (N ** (1.0 / r))))
            print(f"{r:>4} {N:>8} {k:>14} {lower:>14.4f}")

    print()
    print("结论: A(N,k) 随 r 增长 → 均摊下界 Ω(r)")
    print()


if __name__ == "__main__":
    demo()
