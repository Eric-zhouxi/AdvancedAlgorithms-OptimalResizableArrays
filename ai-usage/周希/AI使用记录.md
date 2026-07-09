# 周希 — AI 使用记录

> 记录每次使用 AI 辅助的目的和完整对话内容。

---

### 2026-07-07 第1次使用

**目的**：浏览课程网页，获取大作业要求，下载 Optimal Resizable Arrays 论文，生成大作业大纲

**AI 工具**：Claude Code (claude.ai)

**完整记录**：

> **我**：浏览网页 https://tcs.nju.edu.cn/wiki/index.php?title=%E9%AB%98%E7%BA%A7%E7%AE%97%E6%B3%95_(Spring_2026)/%E5%A4%A7%E4%BD%9C%E4%B8%9A ，我们小组三个人，想要选6.Optimal resizable arrays，请帮我把这个论文保存到 E:\大二下\高级算法\大作业，同时给我一份我们需要怎么做的大纲
>
> **AI**：通过 WebSearch 搜索到两篇相关论文：
> - Brodnik, Carlsson, Demaine, Munro, Sedgewick — *Resizable Arrays in Optimal Time and Space* (WADS 1999)，从 Waterloo CS TR 下载
> - Tarjan & Zwick — *Optimal Resizable Arrays* (SICOMP 2024)，从 arXiv 下载
>
> 两份 PDF 均保存至 `E:\大二下\高级算法\大作业\references\`。
>
> AI 生成了一份完整的大作业大纲，包括：工具准备、论文理解阶段分工、Review 撰写框架（引言→相关研究→核心技术→实现细节→正确性证明→总结→分工说明→AI使用记录）、时间规划、关键提醒。大纲保存为 `大作业大纲.md`。

**产出文件**：
- `references/Resizable_Arrays_in_Optimal_Time_and_Space_Brodnik_et_al_1999.pdf`
- `references/Optimal_Resizable_Arrays_Tarjan_Zwick_2024.pdf`
- `大作业大纲.md`

---

### 2026-07-07 第2次使用

**目的**：在 GitHub 上创建项目仓库，搭建版本历史记录平台

**AI 工具**：Claude Code (claude.ai)

**完整记录**：

> **我**：我们想在GitHub上记录过程，帮我创建并把网址和仓库地址发给我
>
> **AI**：在本地初始化 git 仓库，创建 README.md 和 .gitignore，进行首次提交。发现 gh CLI 未登录，引导我通过浏览器完成 GitHub 设备认证（验证码 46E6-3B19）。登录成功后，创建公开仓库 `AdvancedAlgorithms-OptimalResizableArrays` 并推送。
>
> 仓库地址：https://github.com/Eric-zhouxi/AdvancedAlgorithms-OptimalResizableArrays

**产出**：GitHub 仓库创建完成，项目框架上传。

---

### 2026-07-07 第3次使用

**目的**：翻译两篇论文的关键章节为中文，帮助团队理解

**AI 工具**：Claude Code (claude.ai)

**完整记录**：

> **我**：帮我把那两篇论文翻译
>
> **AI**：尝试用 PyMuPDF 和 PyPDF2 提取 PDF 文本。Tarjan & Zwick (2024) 论文文本提取成功（75343字符），Brodnik et al. (1999) 论文因字体编码问题文本提取失败（乱码）。
>
> AI 翻译了 Tarjan & Zwick 论文的全部关键章节（摘要、引言、形式化定义、前人工作、下界、r=3实现、一般实现、数据结构变换、增长游戏、下界证明、总结），保存为 `notes/Tarjan_Zwick_2024_中英对照.md`。
>
> 对于 Brodnik 论文，AI 基于论文摘要、Tarjan & Zwick (2024) 中对该工作的详细描述以及学术共识，整理翻译了关键内容（两种变体、空间分析、时间复杂度、最优性证明、技术亮点、后续发展），保存为 `notes/Brodnik_et_al_1999_中英对照.md`。
>
> ⚠️ AI 提醒：Brodnik 论文翻译需对照原文核实。

**产出文件**：
- `notes/Tarjan_Zwick_2024_中英对照.md`
- `notes/Brodnik_et_al_1999_中英对照.md`

---

### 2026-07-09 第4次使用

**目的**：搭建项目目录结构，为每人创建笔记和AI使用记录文件夹

**AI 工具**：Claude Code (claude.ai)

**完整记录**：

> **我**：请根据要求新建ai使用反馈文件夹并在notes下和ai使用反馈下新建我们三个人各自的文件夹，我们的名字为周希、李宇轩、吴贤文
>
> **AI**：创建了 `notes/周希/`、`notes/李宇轩/`、`notes/吴贤文/`、`ai-usage/周希/`、`ai-usage/李宇轩/`、`ai-usage/吴贤文/` 共6个目录，每个目录下放置了模板文件（README.md 和 AI使用记录.md）。同时更新了项目 README.md，填写了真实姓名、完善了项目结构说明和过程记录对应关系表。

**产出**：完整的项目目录结构，每人独立的笔记和AI使用记录空间。

---

