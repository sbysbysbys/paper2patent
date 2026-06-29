# 📄 paper2patent (论文转专利)

**将学术论文（LaTeX / PDF）自动转换为中国发明专利 .docx 格式**

[![Tests](https://github.com/paper2patent/paper2patent/actions/workflows/test.yml/badge.svg)](https://github.com/paper2patent/paper2patent/actions/workflows/test.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> 中文 | [English](README.md)

## 功能介绍

输入一篇学术论文（PDF 或 LaTeX 源码），自动生成一份格式化的**中国发明专利** `.docx` 文件。包含：

- 自动生成的权利要求书（独立权利要求 + 从属权利要求）
- 按 CNIPA 规范格式化的五书结构
- 论文原图提取 + 程序化流程图/框图生成
- 可选的参考专利格式学习

```
输入: paper.pdf      →      输出: 专利说明书_xxx.docx
                              ├── 说明书摘要
                              ├── 权利要求书
                              ├── 说明书
                              │   ├── 【技术领域】
                              │   ├── 【背景技术】
                              │   ├── 【发明内容】
                              │   ├── 【附图说明】
                              │   └── 【具体实施方式】
                              └── 说明书附图
```

## 9 步流水线

| 步骤 | 功能 | 工具 | 产出 |
|------|------|------|------|
| 1. 解析 | 解析 LaTeX/PDF 输入 | `latex2json` / `PyMuPDF` + `pymupdf4llm` | `PaperIR` |
| 2. 分析 | LLM 辅助提取方法步骤、系统组件、创新点 | Claude / OpenAI API | `PaperAnalysis` |
| 3. 结构生成 | 论文章节 → 专利【】章节 | 规则+模板 | `PatentIR` sections |
| 4. 权利要求 | 生成独立权利要求 + 从属权利要求 | 规则引擎 | Claims |
| 5. 图片提取 | 从 PDF 提取+裁剪图片 | `PyMuPDF` | `figures/` |
| 6. 图表生成 | 流程图( graphviz ) + 框图( matplotlib ) | graphviz + matplotlib | `diagrams/` |
| 7. 样式配置 | 内置 CNIPA 默认 + 可选参考专利覆盖 | `python-docx` | `StyleProfile` |
| 8. 格式化 | 组装输出 .docx | `python-docx` | `.docx` |
| 9. 校验 | 权利要求、章节、交叉引用检查 | 规则引擎 | Report |

## 快速开始

### 安装

```bash
# 从源码安装
git clone https://github.com/paper2patent/paper2patent.git
cd paper2patent
pip install -e .

# 系统依赖
brew install graphviz        # macOS
sudo apt install graphviz    # Linux
```

### 命令行

```bash
# 基本转换
paper2patent paper.pdf -o output/

# 从 LaTeX 项目
paper2patent latex_project/ -o output/

# 仅生成中间文件（不写 docx）
paper2patent paper.pdf --dry-run

# 使用参考专利提取样式
paper2patent paper.pdf -r 模板专利.docx

# 跳过图表生成
paper2patent paper.pdf --no-diagrams

# 详细日志
paper2patent paper.pdf -v
```

### Python API

```python
from paper2patent.pipeline import PaperToPatentPipeline

pipeline = PaperToPatentPipeline(
    output_dir="./output/",
    patent_type="cn",
    reference_docx="模板.docx",  # 可选
    verbose=True,
)
output = pipeline.run("paper.pdf")
print(f"专利保存到: {output}")
```

### Claude Code Skill

```bash
# 复制到 Claude Code skills 目录
cp SKILL.md ~/.claude/skills/paper2patent/SKILL.md

# 在 Claude Code 中调用:
# "/paper2patent paper.pdf"
```

## 功能特性

- ✅ **PDF 输入** — 支持文本型 + 扫描件（OCR 需 PaddleOCR）
- ✅ **LaTeX 输入** — 完整项目文件夹，自动解析 `\input`/`\include`
- ✅ **权利要求生成** — 独立权利要求（方法+装置）+ 从属权利要求（参数、变体）
- ✅ **图片提取** — 嵌入式位图 + 矢量图，智能裁剪
- ✅ **流程图生成** — graphviz 方法流程图，带引用号标注
- ✅ **框图生成** — matplotlib 系统架构框图
- ✅ **CNIPA 格式** — 页边距、字体、行距、章节标题均符合规范
- ✅ **参考专利学习** — 从现有 .docx 专利提取样式
- ✅ **自动校验** — 权利要求单句检查、多引多检查、交叉引用检查
- ✅ **Dry-run 模式** — 预览中间 JSON/markdown 再决定是否生成 docx

## 输出目录结构

```
patent_output/
├── 专利_title.docx           # 最终格式化的专利文件
├── intermediate/
│   ├── paper_ir.json         # 解析后的论文结构
│   ├── paper_analysis.json   # LLM 分析结果
│   ├── patent_structure.md   # 专利章节草稿
│   ├── claims.md             # 权利要求草稿
│   └── validation_report.txt # 校验报告
├── figures/
│   ├── fig1.png              # 提取的论文原图
│   └── fig2.png
└── diagrams/
    ├── flow_method.pdf       # 方法流程图
    ├── block_system.pdf      # 系统结构框图
    └── framework.pdf         # 整体框架图
```

## 依赖

| 类别 | 包 | 用途 |
|------|-----|------|
| **核心** | `python-docx`, `click`, `pydantic` | .docx 写入、CLI、数据模型 |
| **PDF** | `PyMuPDF`, `pymupdf4llm` | PDF 解析、图片提取 |
| **LaTeX** | `latex2json`, `pylatexenc` | LaTeX → 结构化 JSON、公式转文本 |
| **图表** | `graphviz`, `matplotlib`, `Pillow` | 流程图、框图、图片处理 |
| **UI** | `rich` | 终端美化输出 |
| **可选** | `paddleocr` (OCR), `docling` (语义PDF), `anthropic`/`openai` (LLM) | |

## 中国专利格式规范

本工具遵循以下 CNIPA 格式要求：

| 规范项 | 设置 |
|--------|------|
| 纸张 | A4 (210mm × 297mm) |
| 页边距 | 上 25mm、下 15mm、左 25mm、右 15mm |
| 正文字体 | 宋体 12pt |
| 标题字体 | 黑体 14pt 加粗 |
| 行距 | 1.5 倍 |
| 首行缩进 | 2 字符 |
| 章节标题 | 【技术领域】【背景技术】【发明内容】【附图说明】【具体实施方式】 |
| 摘要字数 | ≤ 300 字 |
| 权利要求 | 每项单句（仅句末一个。） |
| 引用规则 | 禁止多引多 |

## 路线图

- [ ] 美国专利 (USPTO) 格式支持
- [ ] LaTeX 专利模板输出
- [ ] 交互式权利要求编辑器
- [ ] 多语言专利翻译
- [ ] 更多参考专利样式自动检测
- [ ] Web 界面

## 许可证

MIT — 详见 [LICENSE](LICENSE)。

## 贡献

欢迎提交 Issue 和 Pull Request！
