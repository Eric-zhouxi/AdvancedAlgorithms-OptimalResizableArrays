# 代码实现：Optimal Resizable Arrays

> 基于 Tarjan & Zwick (2024) *"Optimal Resizable Arrays"* 论文的 Python 实现。
> 通过模拟块管理逻辑和代价跟踪，验证论文中的均摊分析结论。

---

## 文件说明

| 文件 | 内容 | 对应论文 |
|---|---|---|
| `geometric_array.py` | α-几何增长/收缩动态数组 | Section 3.1 |
| `hat.py` | HAT 数据结构（r=2 特例） | Section 3.2 |
| `general_r_array.py` | 通用 r 参数化可调整数组 | Section 5–7 |
| `growth_game.py` | 增长游戏的模拟与最优代价计算 | Section 8 |
| `demo.py` | 演示脚本：运行实验、对比分析 | — |

## 运行方式

```bash
cd notes/周希/代码实现

# 运行演示（对比所有实现）
python demo.py

# 单独运行某个模块
python geometric_array.py
python hat.py
python general_r_array.py
python growth_game.py
```

## 核心设计思路

所有实现采用 **扁平存储 + 块元数据** 的架构：

- **实际元素**存储在一个 Python 列表中，保证 O(1) 随机访问
- **块管理逻辑**通过整数计数器跟踪每层有多少个"满块"、部分填充块有多少元素
- **代价跟踪**记录合并/拆分操作中"需要拷贝的元素数量"，用于验证均摊分析

这种设计让我们可以在不影响功能正确性的前提下，精确测量操作代价，并验证论文中的上界（O(r) 均摊）和下界（Ω(r) 均摊，通过增长游戏）。

## 关键概念速查

| 符号 | 含义 |
|---|---|
| r | trade-off 参数（r ≥ 2），决定数据结构的层数 |
| B | 块大小参数，满足 B = Θ(N^(1/r)) |
| s(N) | 稳定状态下存储 N 个元素的额外空间 |
| t(N) | 增长操作期间临时需要的额外空间 |
| fᵢ | 第 i 层满块的数量（0 ≤ fᵢ < 2B） |
| partial | 第 0 层部分填充块中的元素数 |
