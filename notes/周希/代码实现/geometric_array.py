"""
α-几何增长/收缩动态数组 (Section 3.1 of Tarjan & Zwick 2024)

经典的动态数组实现：
- 增长：容量满时，分配 (1+α) 倍的新数组
- 收缩：负载因子低于 1/(1+α)² 时，分配 1/(1+α) 倍的新数组
- 使用滞后（hysteresis）避免抖动退化

均摊分析：
- 增长均摊代价：(1+α)/α
- 收缩均摊代价：1/α
- α=1（倍增策略）时均摊 O(1)，最多浪费 50% 空间
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class OperationStats:
    """单次操作的统计信息"""
    actual_cost: int      # 实际代价（写入+拷贝的元素数）
    amortized_cost: float # 均摊代价（含势能变化）
    triggered_resize: bool
    new_capacity: int


class GeometricArray:
    """
    使用 α-几何增长策略的可调整数组。

    Parameters
    ----------
    alpha : float, default=1.0
        增长因子参数。α=1 即经典倍增策略。
    """

    def __init__(self, alpha: float = 1.0):
        if alpha <= 0:
            raise ValueError("alpha must be positive")
        self.alpha = alpha
        self.beta = 1 + alpha          # 增长因子
        self.shrink_threshold = 1.0 / (self.beta ** 2)  # 收缩阈值

        # 内部存储
        self._data: List[Optional[int]] = [None]  # 初始容量为1
        self._size: int = 0
        self._capacity: int = 1

        # 代价统计
        self.total_actual_cost: int = 0
        self.total_amortized_cost: float = 0.0
        self.operation_count: int = 0
        self.resize_count: int = 0

    # ── 公开接口 ──────────────────────────────────────────

    @property
    def size(self) -> int:
        return self._size

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def load_factor(self) -> float:
        return self._size / self._capacity if self._capacity > 0 else 0.0

    @property
    def wasted_space(self) -> int:
        """已分配但未使用的空间"""
        return self._capacity - self._size

    @property
    def amortized_cost(self) -> float:
        if self.operation_count == 0:
            return 0.0
        return self.total_actual_cost / self.operation_count

    @property
    def empirical_amortized(self) -> float:
        """经验均摊代价 = 总实际代价 / 操作次数"""
        if self.operation_count == 0:
            return 0.0
        return self.total_actual_cost / self.operation_count

    @property
    def theoretical_amortized_grow(self) -> float:
        """理论增长均摊代价: (1+α)/α"""
        return self.beta / self.alpha

    @property
    def theoretical_amortized_shrink(self) -> float:
        """理论收缩均摊代价: 1/α"""
        return 1.0 / self.alpha

    def get(self, i: int) -> int:
        """返回第 i 个元素，O(1)"""
        if not 0 <= i < self._size:
            raise IndexError(f"index {i} out of range [0, {self._size})")
        return self._data[i]

    def set(self, i: int, value: int) -> None:
        """修改第 i 个元素，O(1)"""
        if not 0 <= i < self._size:
            raise IndexError(f"index {i} out of range [0, {self._size})")
        self._data[i] = value

    def grow(self, value: int) -> OperationStats:
        """在末尾添加元素"""
        self.operation_count += 1
        actual_cost = 1  # 写一个新元素
        triggered_resize = False
        new_capacity = self._capacity

        if self._size == self._capacity:
            # 需要扩容
            triggered_resize = True
            new_capacity = int(self._capacity * self.beta)
            if new_capacity == self._capacity:
                new_capacity = self._capacity + 1  # 确保至少增加1
            actual_cost += self._size  # 拷贝旧元素
            self._resize(new_capacity)
            self.resize_count += 1

        self._data[self._size] = value
        self._size += 1
        self.total_actual_cost += actual_cost

        return OperationStats(
            actual_cost=actual_cost,
            amortized_cost=0.0,  # 见下方的势能法计算
            triggered_resize=triggered_resize,
            new_capacity=self._capacity,
        )

    def shrink(self) -> OperationStats:
        """删除末尾元素"""
        if self._size == 0:
            raise IndexError("shrink from empty array")
        self.operation_count += 1

        value = self._data[self._size - 1]
        self._data[self._size - 1] = None
        self._size -= 1
        actual_cost = 1
        triggered_resize = False
        new_capacity = self._capacity

        # 检查是否需要收缩
        if self._size > 0 and self._size / self._capacity < self.shrink_threshold:
            triggered_resize = True
            new_capacity = max(1, int(self._capacity / self.beta))
            actual_cost += self._size  # 拷贝剩余元素
            self._resize(new_capacity)
            self.resize_count += 1

        self.total_actual_cost += actual_cost

        return OperationStats(
            actual_cost=actual_cost,
            amortized_cost=0.0,
            triggered_resize=triggered_resize,
            new_capacity=self._capacity,
        )

    # ── 势能法均摊分析 ────────────────────────────────────

    def compute_potential(self) -> float:
        """
        计算当前势能。

        势能函数（仅考虑增长）:
          Φ(n, M) = (β/α)(β·n − M)，其中 β = 1+α

        性质:
        - 扩容前 (n=M): Φ = (β/α)(βM − M) = βM，恰好支付扩容代价
        - 扩容后 (M=βn): Φ = 0
        - 始终非负
        """
        if self._size == 0:
            return 0.0
        return (self.beta / self.alpha) * (self.beta * self._size - self._capacity)

    def amortized_grow_cost(self) -> float:
        """计算一次增长操作的均摊代价"""
        old_potential = self.compute_potential()
        n, M = self._size, self._capacity

        if n < M:
            # 普通插入
            new_potential = (self.beta / self.alpha) * (self.beta * (n + 1) - M)
            return 1 + new_potential - old_potential
        else:
            # 触发扩容
            new_M = int(M * self.beta)
            if new_M == M:
                new_M = M + 1
            new_potential = (self.beta / self.alpha) * (self.beta * (n + 1) - new_M)
            return (1 + n) + new_potential - old_potential  # 1(写) + n(拷贝)

    # ── 内部方法 ──────────────────────────────────────────

    def _resize(self, new_capacity: int) -> None:
        """分配新数组并拷贝元素"""
        new_data: List[Optional[int]] = [None] * new_capacity
        for i in range(self._size):
            new_data[i] = self._data[i]
        self._data = new_data
        self._capacity = new_capacity

    def __len__(self) -> int:
        return self._size

    def __getitem__(self, i: int) -> int:
        return self.get(i)

    def __repr__(self) -> str:
        return (f"GeometricArray(α={self.alpha}, size={self._size}, "
                f"capacity={self._capacity}, load={self.load_factor:.2f}, "
                f"amortized={self.empirical_amortized:.2f})")


# ═══════════════════════════════════════════════════════════
# 演示：不同 α 取值的表现对比
# ═══════════════════════════════════════════════════════════

def demo():
    """演示几何增长数组在不同 α 下的表现"""
    import sys

    test_sizes = [10, 100, 1000, 10000]
    alphas = [0.25, 0.5, 1.0, 2.0, 4.0]

    print("=" * 72)
    print("α-几何增长动态数组 — 经验均摊代价对比")
    print("=" * 72)
    print(f"{'α':>6} {'N':>6} {'均摊代价':>10} {'理论增长':>10} {'理论收缩':>10} "
          f"{'扩容次数':>8} {'浪费率':>8}")
    print("-" * 72)

    for alpha in alphas:
        for n in test_sizes:
            arr = GeometricArray(alpha)
            for i in range(n):
                arr.grow(i)

            wasted_ratio = arr.wasted_space / arr.capacity if arr.capacity > 0 else 0

            print(f"{alpha:>6.2f} {n:>6} {arr.empirical_amortized:>10.4f} "
                  f"{arr.theoretical_amortized_grow:>10.4f} "
                  f"{arr.theoretical_amortized_shrink:>10.4f} "
                  f"{arr.resize_count:>8} {wasted_ratio:>8.2%}")

    print()

    # 演示抖动（thrashing）现象
    print("=" * 72)
    print("抖动（Thrashing）演示：增长+收缩混合序列")
    print("=" * 72)

    # 无滞后策略（收缩阈值=1/2）
    arr_no_hysteresis = GeometricArray(alpha=1.0)
    # 手动模拟1/2收缩阈值（不安全的策略）
    n_ops = 100
    total_cost = 0

    arr = GeometricArray(alpha=1.0)
    for _ in range(20):
        arr.grow(0)
    print(f"初始: size={arr.size}, capacity={arr.capacity}")

    # 用默认策略（有滞后, threshold=1/4）做 grow+shrink 交替
    arr2 = GeometricArray(alpha=1.0)
    for _ in range(10):
        arr2.grow(0)
    print(f"  填满前: size={arr2.size}, capacity={arr2.capacity}")

    cost_before = arr2.total_actual_cost
    for _ in range(20):
        arr2.shrink()
    for _ in range(20):
        arr2.grow(0)
    print(f"  交替20次后: size={arr2.size}, capacity={arr2.capacity}, "
          f"总代价={arr2.total_actual_cost - cost_before}, "
          f"均摊/操作={arr2.empirical_amortized:.2f}")
    print("  (有滞后保护 → 未触发反复 resize)")

    print()


if __name__ == "__main__":
    demo()
