"""
HAT（Hashed Array Tree）数据结构 (Section 3.2, Sitarski 1996)

Tarjan & Zwick (2024) 中 r=2 的特例。

结构：
  顶层索引块 I（大小 B，存指针）
      ↓
  ┌──────┬──────┬──────┬──────┬──────┐
  │块0   │块1   │块2   │...   │块m-1 │  ← 数据块，每个大小 B
  └──────┴──────┴──────┴──────┴──────┘

空间分析：N + 3B + 2
  - N: 元素本身
  - B: 顶层索引块
  - B: 当前正在填充的数据块（可能未满）
  - B: 备用空数据块（支持 O(1) 最坏情况增长）
  - +2: size 和 B 两个元数据

性质：
  - B 为 2 的幂，√N ≤ B < 4√N
  - N = B² 时重建（B 加倍），均摊 O(1)
  - 访问 O(1)：第 i 个元素 → 第 ⌊i/B⌋ 个数据块的第 (i mod B) 个位置
"""

from typing import List, Optional, Tuple


class HAT:
    """
    Hashed Array Tree — 两级可调整数组。

    第 i 个元素位于: data_blocks[i // B][i % B]
    """

    def __init__(self):
        # B: 块大小，2的幂
        self.B: int = 2
        # 顶层索引块：指向各数据块的指针
        self.index: List[List[Optional[int]]] = []
        # 数据块列表
        self.data_blocks: List[List[Optional[int]]] = []
        # 备用空块（预分配，用于 O(1) 最坏情况增长）
        self.spare_block: Optional[List[Optional[int]]] = None

        self._size: int = 0

        # 代价统计
        self.total_copy_cost: int = 0
        self.operation_count: int = 0

        # 初始化：一个空数据块 + 备用块
        self._init_blocks()

        # 初始化索引块
        self.index = [self.data_blocks[0]]

    def _init_blocks(self) -> None:
        """初始化数据块和备用块"""
        self.data_blocks = [[None] * self.B]
        self.spare_block = [None] * self.B

    # ── 公开接口 ──────────────────────────────────────────

    @property
    def size(self) -> int:
        return self._size

    @property
    def num_blocks(self) -> int:
        """当前数据块总数（含部分填充块）"""
        return (self._size + self.B - 1) // self.B if self._size > 0 else 1

    @property
    def extra_space(self) -> int:
        """
        超出 N 的额外空间。
        公式：3B + 2（近似）
        实际：索引块 (B) + 未满数据块的浪费 (B) + 备用块 (B) + 元数据
        """
        index_overhead = len(self.index)  # 索引条目数
        wasted_in_blocks = sum(
            self.B - sum(1 for x in blk if x is not None)
            for blk in self.data_blocks
        )
        spare_overhead = self.B if self.spare_block else 0
        return index_overhead + wasted_in_blocks + spare_overhead + 2

    @property
    def empirical_amortized(self) -> float:
        if self.operation_count == 0:
            return 0.0
        return self.total_copy_cost / self.operation_count

    @property
    def theoretical_B_bound(self) -> Tuple[float, float]:
        """理论上的 B 范围: [√N, 4√N)"""
        import math
        sqrt_n = math.sqrt(self._size) if self._size > 0 else 0
        return (sqrt_n, 4 * sqrt_n)

    def get(self, i: int) -> int:
        """O(1) 访问第 i 个元素"""
        if not 0 <= i < self._size:
            raise IndexError(f"index {i} out of range [0, {self._size})")
        block_idx = i // self.B
        offset = i % self.B
        return self.data_blocks[block_idx][offset]

    def set(self, i: int, value: int) -> None:
        """O(1) 修改第 i 个元素"""
        if not 0 <= i < self._size:
            raise IndexError(f"index {i} out of range [0, {self._size})")
        block_idx = i // self.B
        offset = i % self.B
        self.data_blocks[block_idx][offset] = value

    def grow(self, value: int) -> None:
        """在末尾添加元素，均摊 O(1)"""
        self.operation_count += 1
        self.total_copy_cost += 1  # 写入新元素

        if self._size == self.B * self.B:
            # N = B²：触发重建，B 加倍
            self._rebuild(self.B * 2)

        # 找到当前最后一个块
        last_block_idx = self._size // self.B
        offset = self._size % self.B

        if last_block_idx >= len(self.data_blocks):
            # 需要新块：使用备用块
            if self.spare_block is None:
                self.spare_block = [None] * self.B
            new_block = self.spare_block
            new_block[0] = value
            self.data_blocks.append(new_block)
            self.index.append(new_block)
            self.spare_block = [None] * self.B  # 分配新备用块
            self.total_copy_cost += self.B  # 清零备用块
        else:
            self.data_blocks[last_block_idx][offset] = value

        self._size += 1

    def shrink(self) -> int:
        """删除末尾元素，均摊 O(1)"""
        if self._size == 0:
            raise IndexError("shrink from empty array")
        self.operation_count += 1

        last_block_idx = (self._size - 1) // self.B
        offset = (self._size - 1) % self.B
        value = self.data_blocks[last_block_idx][offset]
        self.data_blocks[last_block_idx][offset] = None
        self._size -= 1
        self.total_copy_cost += 1

        # 如果最后一个块变空，释放它
        if offset == 0 and last_block_idx > 0:
            empty_block = self.data_blocks.pop()
            self.index.pop()
            # 如果备用块不存在，保留这个空块作为备用
            if self.spare_block is None:
                self.spare_block = empty_block

        # 检查是否需要收缩 B
        if self._size > 0 and self._size <= (self.B // 2) ** 2 and self.B > 2:
            self._rebuild(self.B // 2)

        return value

    # ── 内部方法 ──────────────────────────────────────────

    def _rebuild(self, new_B: int) -> None:
        """以新的 B 重建整个结构。拷贝所有元素，代价 = N。"""
        old_size = self._size
        old_elements = [self.get(i) for i in range(self._size)]

        self.B = new_B
        self._size = 0
        self.total_copy_cost += old_size  # 拷贝代价

        # 重新初始化
        self._init_blocks()
        self.index = [self.data_blocks[0]]

        # 重新插入所有元素（不计额外代价）
        for x in old_elements:
            last_block_idx = self._size // self.B
            offset = self._size % self.B
            if last_block_idx >= len(self.data_blocks):
                if self.spare_block is None:
                    self.spare_block = [None] * self.B
                new_block = self.spare_block
                self.data_blocks.append(new_block)
                self.index.append(new_block)
                self.spare_block = [None] * self.B
            self.data_blocks[last_block_idx][offset] = x
            self._size += 1

    def __len__(self) -> int:
        return self._size

    def __getitem__(self, i: int) -> int:
        return self.get(i)

    def __repr__(self) -> str:
        sqrt_n = int(self._size ** 0.5) if self._size > 0 else 0
        return (f"HAT(size={self._size}, B={self.B}, "
                f"blocks={len(self.data_blocks)}, "
                f"√N={sqrt_n}, B∈[{sqrt_n}, {4*sqrt_n}), "
                f"extra≈{self.extra_space}, "
                f"amortized={self.empirical_amortized:.2f})")


# ═══════════════════════════════════════════════════════════
# 演示
# ═══════════════════════════════════════════════════════════

def demo():
    """演示 HAT 的工作过程"""
    print("=" * 72)
    print("HAT (Hashed Array Tree) — r=2 特例")
    print("=" * 72)

    hat = HAT()
    milestones = [2, 4, 8, 16, 32, 64, 100, 200, 500, 1000]

    print(f"{'N':>6} {'B':>4} {'块数':>5} {'额外空间':>8} {'√N':>5} "
          f"{'B范围':>12} {'均摊':>8}")
    print("-" * 72)

    for target in milestones:
        while hat.size < target:
            hat.grow(hat.size)
        lo, hi = hat.theoretical_B_bound
        print(f"{hat.size:>6} {hat.B:>4} {len(hat.data_blocks):>5} "
              f"{hat.extra_space:>8} {int(hat.size**0.5):>5} "
              f"[{int(lo)},{int(hi)}) {hat.empirical_amortized:>8.4f}")

    print()

    # 验证访问正确性
    print("验证前10个元素:", [hat[i] for i in range(10)])
    print(f"总拷贝代价: {hat.total_copy_cost}")
    print(f"经验均摊: {hat.empirical_amortized:.4f}")
    print(f"理论均摊: O(1)")
    print()


if __name__ == "__main__":
    demo()
