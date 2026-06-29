# 📄 paper2patent

**一键将学术论文（LaTeX / PDF）转成可直接提交的中国发明专利 .docx**

[![Tests](https://github.com/sbysbysbys/paper2patent/actions/workflows/test.yml/badge.svg)](https://github.com/sbysbysbys/paper2patent/actions/workflows/test.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> 中文 | [English](README.md)

---

## 🎯 为什么选 paper2patent？

市面上能把论文"翻译"成专利的工具屈指可数，而 paper2patent 不止是翻译——**它是目前最完整的论文→专利自动化流水线**。

### 🏆 四大核心优势

| 优势 | 说明 |
|------|------|
| **📊 能生图** | 自动生成方法流程图 (graphviz)、系统架构框图 (matplotlib)、整体框架图 — 带专利引用号标注，直接可用 |
| **🖼️ 能提取图** | 从 PDF 论文中提取嵌入位图 **和** 矢量图，智能裁剪 figure + caption，300 DPI 高保真输出，一键转黑白 |
| **🧠 专家级撰写** | 内置 **Patent Writing Expert** — 分析 **300+** 篇真实中国发明专利提炼的知识库，覆盖 **21 个技术领域** |
| **📐 格式即交付** | CNIPA 标准格式一步到位：A4/宋体/黑体/1.5倍行距/首行缩进/【】章节标题，打开就能提交 |

### 🔬 300+ 专利知识库，21 领域全覆盖

不仅懂 AI——我们的 Patent Expert 分析了以下全部领域的真实专利：

| 计算机视觉 | NLP | 神经网络架构 | 强化学习 | 网络安全 | 多模态 |
|:--:|:--:|:--:|:--:|:--:|:--:|
| 时序预测 | 边缘计算 | 大语言模型 | Transformer | 药物发现 | **化学/催化** |
| **生物/基因编辑** | **半导体/芯片** | **新能源/电池** | **机械/传动** | **医疗器械** | **5G/通信** |
| **材料/涂层** | **工业机器人** | **环保/水处理** | | | |

> 不会因为你做 CV 就只会写 CV 专利——跨领域通用撰写能力是 paper2patent 的核心壁垒。

---

## 🚀 一条命令，九步到位

```bash
paper2patent paper.pdf -o output/
```

```
Input: paper.pdf  ──→  Output: 专利说明书_xxx.docx
                           ├── 说明书摘要
                           ├── 权利要求书
                           │   ├── 独立权利要求（方法 + 装置 + 电子设备 + 存储介质）
                           │   └── 从属权利要求（参数、变体、细化限定）
                           ├── 说明书
                           │   ├── 【技术领域】
                           │   ├── 【背景技术】
                           │   ├── 【发明内容】
                           │   ├── 【附图说明】
                           │   └── 【具体实施方式】
                           ├── 说明书附图（原论文图 + 生成的流程图/框图）
                           └── 校验报告
```

| Step | 做什么 | 怎么做的 |
|:----:|--------|----------|
| 1 | **解析输入** | LaTeX → `latex2json` / PDF → `PyMuPDF` + `pymupdf4llm`（扫描件 OCR 回退） |
| 2 | **分析论文** | LLM 驱动的语义分析，提取方法步骤、系统组件、创新点、参数范围 |
| 3 | **生成专利结构** | 论文 IMRD → 专利五书【】章节映射，背景技术只写局限性 |
| 4 | **生成权利要求** | Expert 模板 + 规则引擎：独立（4类）+ 从属，自动避多引多 |
| 5 | **提取论文原图** | PyMuPDF 位图+矢量图双提取，智能裁剪，300 DPI，可选黑白转换 |
| 6 | **生成流程图/框图** | graphviz 方法流程图 + matplotlib 系统框图 + 框架图，全带引用号 |
| 7 | **样式配置** | 内置 CNIPA 默认 + 可选 `-r 参考专利.docx` 自动学习样式 |
| 8 | **格式化输出** | python-docx 精确控制：页边距、字体、行距、缩进、分页 |
| 9 | **自动校验** | 单句检查、多引多检查、禁用词检测、摘要字数、交叉引用 |

---

## 📦 安装

```bash
git clone https://github.com/sbysbysbys/paper2patent.git
cd paper2patent
pip install -e .

# 系统依赖（流程图生成）
brew install graphviz        # macOS
sudo apt install graphviz    # Linux
```

## 🖥️ 使用

```bash
# 基础转换
paper2patent paper.pdf -o output/

# LaTeX 项目
paper2patent latex_project/ -o output/

# 附图全部转黑白（CNIPA 要求）
paper2patent paper.pdf --bw-figures

# 先看格式预览再转
paper2patent paper.pdf --show-format

# 参考已有专利的样式
paper2patent paper.pdf -r 模板专利.docx

# 预览中间产物，不生成 docx
paper2patent paper.pdf --dry-run
```

Python API：

```python
from paper2patent.pipeline import PaperToPatentPipeline

pipeline = PaperToPatentPipeline(
    output_dir="./output/",
    patent_type="cn",
    reference_docx="模板.docx",  # 可选：学习已有专利样式
    bw_figures=True,             # 黑白图
    verbose=True,
)
output = pipeline.run("paper.pdf")
```

Claude Code Skill：

```bash
cp SKILL.md ~/.claude/skills/paper2patent/SKILL.md
# 然后在 Claude Code 中直接 /paper2patent paper.pdf
```

---

## 🧠 Patent Writing Expert

paper2patent 不只是模板填充。它内置了一个**专利撰写专家系统**，知识来源于对 300+ 件真实中国发明专利（覆盖 21 个技术领域）的系统分析。

**Expert 自动渗透到流水线每个环节：**

- **分析阶段** → LLM 先读 Expert 的六大撰写原则，再分析论文
- **权利要求** → 用专家模板生成，自动过滤"等等/约/最好是"等禁用词
- **说明书章节** → 技术领域、摘要、结语均使用真实专利高频惯用句式
- **校验阶段** → 按 Expert checklist 逐项检查（单句/多引多/术语一致/交叉引用）

**Expert API 可独立调用：**

```python
from paper2patent.converter.expert_mode import (
    get_claim_template,        # 获取权利要求模板
    get_section_guide,         # 获取章节结构指南
    get_writing_checklist,     # 获取撰写检查清单
    EXPERT_SYSTEM_PROMPT,      # 获取专家系统 Prompt（可直接喂 LLM）
)
```

---

## 🎨 图表能力详解

### 论文原图提取

```
PDF 论文 ──→ PyMuPDF 双通道提取 ──→ 智能裁剪 ──→ 统一编号 fig1.png ...
              ├── 嵌入位图：原始分辨率无损提取
              └── 矢量图 cluster_drawings()：300 DPI 高保真渲染
              └── Caption 自动匹配（Fig/Figure/图 关键词检测）
              └── 可选：灰度化 + 对比度 1.4x → 专利级黑白线图
```

### 程序化图表生成

- **方法流程图** (graphviz)：从方法步骤自动生成，菱形判断节点 + 引用号 `(110)(120)...`
- **系统架构框图** (matplotlib)：FancyBboxPatch 组件块 + FancyArrowPatch 连接线 + 引用号标注
- **整体框架图**：Input → Processing → Output 三层结构，自动推断数据流

---

## ✅ 输出校验

转换完成自动生成校验报告，逐项检查：

- [x] 权利要求是否单句（仅句末一个 。）
- [x] 是否包含 `其特征在于` 分隔
- [x] 是否避免多引多
- [x] 摘要是否 < 300 字
- [x] 五个必选章节是否齐全
- [x] 附图引用号是否在说明书中全部出现
- [x] 是否包含禁用词（等等/约/最好是…）
- [x] 术语是否前后一致

---

## 📂 输出目录

```
patent_output/
├── 专利_title.docx              # 最终格式化的专利文件
├── 专利格式预览.docx             # （--show-format）格式说明文档
├── intermediate/                 # 每一步中间产物，可手动调整
│   ├── paper_ir.json
│   ├── paper_analysis.json
│   ├── patent_structure.md
│   ├── claims.md
│   └── validation_report.txt
├── figures/                      # 论文原图
│   ├── fig1.png
│   └── fig2.png
└── diagrams/                     # 程序化生成的图
    ├── flow_method.pdf           # 方法流程图
    ├── block_system.pdf          # 系统架构框图
    └── framework.pdf             # 整体框架图
```

---

## 🗺️ 路线图

- [ ] 美国专利 (USPTO) 格式支持
- [ ] LaTeX 专利模板输出
- [ ] 交互式权利要求编辑器
- [ ] 多语言专利翻译
- [ ] Web 界面

---

## 📜 许可证

MIT — 详见 [LICENSE](LICENSE)。
