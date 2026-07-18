"""
通用 r 参数化可调整数组 (Sections 5–7 of Tarjan & Zwick 2024)

基于冗余基数 B 计数器的层次化块结构。

核心思想：
  - 对给定 r ≥ 2，维护参数 B，N^(1/r) ≤ B < 4N^(1/r)
  - 元素存储在大小分别为 B, B², B³, ..., B^(r-1) 的块中
  - 这是 r-1 级层次结构，模拟冗余基数 B 计数器
  - 每级最多 2B 个满块（冗余表示），保证均摊 O(r)

代价分析：
  - 存储额外空间: O(N^(1/r))
  - 增长/收缩均摊时间: O(r)
  - 访问: O(1)

实现方式：扁平存储 + 块元数据 + 代价跟踪
  - 实际元素存于 Python 列表（保证 O(1) 访问）
  - 块结构通过整数计数器跟踪
  - 合并/拆分代价精确记录
"""

import math
from typing import List, Tuple


class GeneralRArray:
    """
    通用 r 参数化可调整数组。

    Parameters
    ----------
    r : int
        trade-off 参数（r ≥ 2）。
        r=2 等价于 HAT，r=3 等价于 Section 5 的简单实现。
    """

    def __init__(self, r: int = 2):
        if r < 2:
            raise ValueError("r must be at least 2")
        self.r: int = r
        self.B: int = 2  # 块大小参数

        # 扁平元素存储
        self._elements: List[int] = []
        self._size: int = 0

        # 块结构元数据
        # 部分填充块（第0层最后一个块）中的元素数: 0 ≤ partial < B
        self._partial: int = 0
        # f[i] = 第 i 层满块的数量: 0 ≤ f[i] < 2B
        # 第 i 层的每个块有 B^(i+1) 个元素
        self._f: List[int] = [0] * (r - 1)

        # 代价统计
        self.total_copy_cost: int = 0   # 总拷贝代价
        self.operation_count: int = 0   # 操作次数
        self.merge_count: int = 0       # 合并次数
        self.split_count: int = 0       # 拆分次数
        self.rebuild_count: int = 0     # 重建次数

        # 详细代价日志（可选，用于调试）
        self._cost_log: List[str] = []

    # ── 公开属性 ──────────────────────────────────────────

    @property
    def size(self) -> int:
        return self._size

    @property
    def r(self) -> int:
        return self._r

    @r.setter
    def r(self, value: int):
        self._r = value

    @property
    def num_levels(self) -> int:
        """有效层数 = r-1"""
        return self._r - 1

    @property
    def extra_space_estimate(self) -> int:
        """
        估计的额外空间。
        实际使用: 每层最多 2B 个块的指针 + 块内浪费
        上界: 2B(r-1) + 1 个块
        """
        total_blocks = 1  # 部分块
        for fi in self._f:
            total_blocks += fi
        # 块内浪费：仅部分块可能有浪费
        wasted = self.B - self._partial if self._partial > 0 else 0
        return total_blocks + wasted

    @property
    def empirical_amortized(self) -> float:
        if self.operation_count == 0:
            return 0.0
        return self.total_copy_cost / self.operation_count

    @property
    def theoretical_amortized(self) -> float:
        """理论上界: O(r)"""
        return float(self._r)

    @property
    def B_bound(self) -> Tuple[float, float]:
        """理论 B 范围: [N^(1/r), 4N^(1/r))"""
        if self._size == 0:
            return (0, 0)
        n_root = self._size ** (1.0 / self._r)
        return (n_root, 4 * n_root)

    @property
    def total_elements_from_metadata(self) -> int:
        """
        从块元数据反算总元素数，应等于 self._size。
        用于验证内部一致性。
        """
        total = self._partial
        for i, fi in enumerate(self._f):
            total += fi * (self.B ** (i + 1))
        return total

    # ── 核心操作 ──────────────────────────────────────────

    def get(self, i: int) -> int:
        """O(1) 访问第 i 个元素（使用扁平存储）"""
        if not 0 <= i < self._size:
            raise IndexError(f"index {i} out of range [0, {self._size})")
        return self._elements[i]

    def set(self, i: int, value: int) -> None:
        """O(1) 修改第 i 个元素"""
        if not 0 <= i < self._size:
            raise IndexError(f"index {i} out of range [0, {self._size})")
        self._elements[i] = value

    def grow(self, value: int) -> None:
        """
        在末尾添加元素。

        均摊代价: O(r)。
        最坏情况触发级联合并，但均摊到每次操作为 O(r)。
        """
        self.operation_count += 1

        # 检查是否需要重建（N = B^r 时 B 加倍）
        if self._size == self.B ** self._r:
            self._rebuild(2 * self.B)

        # 情况1: 部分块有空位 → 直接放入
        if self._partial < self.B:
            self._elements.append(value)
            self._size += 1
            self._partial += 1
            self.total_copy_cost += 1  # 写一个元素
            return

        # 情况2: 部分块刚好填满 → 变为满块
        self._elements.append(value)
        self._size += 1
        self.total_copy_cost += 1

        # 原来的部分块现在满了，计入 f[0]
        self._f[0] += 1
        # 新元素形成新的部分块
        self._partial = 1

        # 情况3: 检查级联合并（carry propagation）
        self._cascade_merge(0)

    def shrink(self) -> int:
        """
        删除末尾元素。

        均摊代价: O(r)。
        """
        if self._size == 0:
            raise IndexError("shrink from empty array")
        self.operation_count += 1

        # 检查是否需要收缩 B
        if self._size == (self.B // 2) ** self._r and self.B > 2:
            self._rebuild(max(self.B // 2, 2))

        value = self._elements.pop()
        self._size -= 1

        # 情况1: 部分块有元素 → 直接删除
        if self._partial > 0:
            self._partial -= 1
            self.total_copy_cost += 1
            return value

        # 情况2: 部分块为空 → 借用满块
        self.total_copy_cost += 1

        # 先尝试从 f[0] 借用
        if self._f[0] > 0:
            self._f[0] -= 1
            self._partial = self.B - 1
            return value

        # 情况3: f[0] 也为空 → 级联拆分（borrow propagation）
        self._cascade_split(0)
        self._partial = self.B - 1
        return value

    # ── 级联合并 (Carry) ──────────────────────────────────

    def _cascade_merge(self, level: int) -> None:
        """
        从 level 开始向上执行级联合并。

        规则：当 f[level] = 2B 时，
              合并 B 个 level 块为 1 个 level+1 块。
              代价 = B × B^(level+1) = B^(level+2)。

        这模拟了冗余基数 B 计数器的进位操作。
        """
        while level < self.num_levels and self._f[level] >= 2 * self.B:
            block_size = self.B ** (level + 1)    # 当前层每块大小
            merge_cost = self.B * block_size       # B 个块 × 每块大小
            self.total_copy_cost += merge_cost
            self.merge_count += 1

            self._f[level] -= self.B  # 移除 B 个当前层满块

            if level + 1 < self.num_levels:
                self._f[level + 1] += 1  # 在上一层新增 1 个满块
            # 如果 level+1 == num_levels（即 r-1），则 f[r-1] 不存在。
            # 这不会发生，因为我们会在 N=B^r 时提前重建。

            level += 1

    # ── 级联拆分 (Borrow) ─────────────────────────────────

    def _cascade_split(self, level: int) -> None:
        """
        从 level 开始向上执行级联拆分。

        规则：当 f[level] = 0 时，向上一级借用 1 个块，
              拆分为 B 个当前层块。
              代价 = B^(level+2)（拆分一个上级块）。

        这模拟了冗余基数 B 计数器的借位操作。
        """
        # 找到第一个有满块的层级
        src_level = level
        while src_level < self.num_levels and self._f[src_level] == 0:
            src_level += 1

        if src_level >= self.num_levels:
            # 所有层都没有满块，只剩部分块中的元素
            # 此时 N ≤ partial < B，且所有元素都在扁平存储中
            # 不应到达这里（因为调用方已确保有元素）
            return

        # 从 src_level 拆分一个块
        block_size = self.B ** (src_level + 1)
        split_cost = block_size  # 拷贝被拆分的块
        self.total_copy_cost += split_cost
        self.split_count += 1

        self._f[src_level] -= 1

        # 填充中间层：每层获得 B-1 个满块
        for l in range(src_level - 1, level, -1):
            self._f[l] += self.B - 1

        # 目标层获得 B-1 个满块（第 B 个块变成新的部分块）
        if level < self.num_levels:
            self._f[level] += self.B - 1

    # ── 重建 (Rebuild) ────────────────────────────────────

    def _rebuild(self, new_B: int) -> None:
        """
        用新的 B 重建整个结构。

        触发条件：
        - 增长时 N = B^r → B' = 2B
        - 收缩时 N = (B/2)^r → B' = B/2

        代价 = N（拷贝所有元素）。
        均摊 O(1)：几何级数保证总重建代价为 O(N)。
        """
        old_elements = self._elements[:]  # 保存旧元素
        old_size = self._size

        self.B = new_B
        self._elements = []
        self._size = 0
        self._partial = 0
        self._f = [0] * self.num_levels

        self.total_copy_cost += old_size  # 重建的拷贝代价
        self.rebuild_count += 1

        # 重新插入所有元素（不计入 operation_count）
        for x in old_elements:
            self._insert_rebuild(x)

    def _insert_rebuild(self, value: int) -> None:
        """重建期间的内部插入（不计额外代价和操作数）"""
        if self._partial < self.B:
            self._elements.append(value)
            self._size += 1
            self._partial += 1
            return

        self._elements.append(value)
        self._size += 1
        self._f[0] += 1
        self._partial = 1
        self._cascade_merge_rebuild(0)

    def _cascade_merge_rebuild(self, level: int) -> None:
        """重建期间的级联合并（不计代价）"""
        while level < self.num_levels and self._f[level] >= 2 * self.B:
            self._f[level] -= self.B
            if level + 1 < self.num_levels:
                self._f[level + 1] += 1
            level += 1

    # ── 验证 ──────────────────────────────────────────────

    def verify(self) -> bool:
        """
        验证内部一致性：
        1. 从元数据计算的总元素数等于 _size
        2. 部分块满足 0 ≤ partial < B
        3. 每层满块满足 0 ≤ f[i] < 2B
        """
        # 检查1
        if self.total_elements_from_metadata != self._size:
            return False
        # 检查2: partial 在 [0, B] 范围内
        # (partial == B 表示最后一块恰好填满，下次增长时触发进位)
        if not (0 <= self._partial <= self.B):
            return False
        # 检查3
        for fi in self._f:
            if fi < 0 or fi >= 2 * self.B:
                return False
        return True

    # ── 辅助 ──────────────────────────────────────────────

    def _level_block_size(self, level: int) -> int:
        """第 level 层每个块的大小 = B^(level+1)"""
        return self.B ** (level + 1)

    def describe(self) -> str:
        """返回当前结构的文本描述"""
        parts = [f"N={self._size}, B={self.B}, r={self._r}"]
        parts.append(f"partial={self._partial}/{self.B}")
        for i, fi in enumerate(self._f):
            sz = self._level_block_size(i)
            parts.append(f"  level {i}: {fi} blocks × {sz} = {fi * sz} elements")
        parts.append(f"amortized={self.empirical_amortized:.4f}")
        return "\n".join(parts)

    def __len__(self) -> int:
        return self._size

    def __getitem__(self, i: int) -> int:
        return self.get(i)

    def __repr__(self) -> str:
        return (f"GeneralRArray(r={self._r}, N={self._size}, B={self.B}, "
                f"amortized={self.empirical_amortized:.2f})")


# ═══════════════════════════════════════════════════════════
# r=3 特例 (Section 5)：大块+小块结构
# ═══════════════════════════════════════════════════════════

class R3Array(GeneralRArray):
    """
    r=3 特例 (Section 5 of Tarjan & Zwick 2024)。

    两层的简化结构：
    - 大块（size=B²）：总是满的，约 N/B² 个
    - 小块（size=B）：最多 2B 个，最后一个小块可能部分填充
    - 两个索引块（大块索引 + 小块索引）

    增长：通常在小块末尾添加
          2B 个小块满时 → 合并为 1 个大块
          无小块时 → 拆分大块为 B 个小块
    """

    def __init__(self):
        super().__init__(r=3)

    @property
    def large_blocks(self) -> int:
        """大块（size=B²）的数量"""
        return self._f[1] if len(self._f) > 1 else 0

    @property
    def small_blocks(self) -> int:
        """小块（size=B）的数量"""
        return self._f[0]


# ═══════════════════════════════════════════════════════════
# 演示与实验
# ═══════════════════════════════════════════════════════════

def demo_single(r: int, n: int = 5000) -> GeneralRArray:
    """对指定的 r 运行演示"""
    arr = GeneralRArray(r)
    milestones = set()
    step = max(1, n // 10)
    for i in range(0, n + 1, step):
        milestones.add(i)
    milestones.add(n)

    for i in range(n):
        arr.grow(i)
        if arr.size in milestones:
            lo, hi = arr.B_bound
            print(f"  N={arr.size:>6}: B={arr.B:>4} ∈ [{int(lo)},{int(hi)}), "
                  f"partial={arr._partial:>3}, f={arr._f}, "
                  f"cost={arr.total_copy_cost:>8}, amortized={arr.empirical_amortized:>8.4f}")

    print(f"  验证: {arr.verify()}, 合并={arr.merge_count}, "
          f"拆分={arr.split_count}, 重建={arr.rebuild_count}")
    return arr


def demo():
    """演示不同 r 值下的行为"""
    print("=" * 72)
    print("通用 r 参数化可调整数组 — 代价分析")
    print("=" * 72)

    for r in [2, 3, 4, 5]:
        print(f"\n{'─' * 60}")
        print(f"r = {r} (层数 = {r-1})")
        print(f"{'─' * 60}")
        arr = demo_single(r, n=2000)

        # 理论分析
        print(f"  理论均摊上界: O({r})")

    # 对比不同 r 的均摊代价
    print(f"\n{'=' * 72}")
    print("不同 r 的经验均摊代价对比 (N=5000)")
    print(f"{'=' * 72}")
    print(f"{'r':>4} {'B':>6} {'合并':>6} {'拆分':>6} {'重建':>4} {'均摊':>10}")
    print("-" * 48)

    for r in range(2, 11):
        arr = GeneralRArray(r)
        for i in range(5000):
            arr.grow(i)
        print(f"{r:>4} {arr.B:>6} {arr.merge_count:>6} {arr.split_count:>6} "
              f"{arr.rebuild_count:>4} {arr.empirical_amortized:>10.4f}")

    print()


if __name__ == "__main__":
    demo()
