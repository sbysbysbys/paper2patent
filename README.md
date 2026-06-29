# 📄 paper2patent

**Convert academic papers (LaTeX / PDF) → Chinese invention patent (.docx)**

[![Tests](https://github.com/paper2patent/paper2patent/actions/workflows/test.yml/badge.svg)](https://github.com/paper2patent/paper2patent/actions/workflows/test.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> **English** | [中文](README_zh.md)

## What It Does

Takes an academic paper (PDF or LaTeX source) and produces a formatted **Chinese invention patent** `.docx` file — with generated claims, structured descriptions, extracted & generated diagrams, all following CNIPA formatting standards.

```
Input: paper.pdf      →      Output: 专利说明书_xxx.docx
                              ├── 说明书摘要 (Abstract)
                              ├── 权利要求书 (Claims)
                              ├── 说明书 (Description)
                              │   ├── 【技术领域】
                              │   ├── 【背景技术】
                              │   ├── 【发明内容】
                              │   ├── 【附图说明】
                              │   └── 【具体实施方式】
                              └── 说明书附图 (Figures)
```

## 9-Step Pipeline

| Step | Description | Output |
|------|-------------|--------|
| 1. Parse | LaTeX → `latex2json` / PDF → `PyMuPDF` + `pymupdf4llm` | `PaperIR` |
| 2. Analyze | LLM-assisted extraction of method steps, components, novelty | `PaperAnalysis` |
| 3. Structure | Map paper sections → CN patent 【】sections | `PatentIR` |
| 4. Claims | Generate independent + dependent claims | Claims list |
| 5. Figures | Extract + crop figures from PDF/LaTeX | `figures/` |
| 6. Diagrams | `graphviz` flowcharts + `matplotlib` block diagrams | `diagrams/` |
| 7. Styles | Build CNIPA profile (defaults + optional reference .docx) | `StyleProfile` |
| 8. Format | Assemble `.docx` with precise formatting | `.docx` |
| 9. Validate | Check claims, sections, cross-references | Report |

## Quick Start

### Installation

```bash
# From source
git clone https://github.com/paper2patent/paper2patent.git
cd paper2patent
pip install -e .

# System dependencies
brew install graphviz        # macOS
sudo apt install graphviz    # Linux
```

### CLI

```bash
# Basic conversion
paper2patent paper.pdf -o output/

# From LaTeX project
paper2patent latex_project/ -o output/

# Dry-run (intermediate files only, no .docx)
paper2patent paper.pdf --dry-run

# With reference patent for style extraction
paper2patent paper.pdf -r template_patent.docx

# Skip diagram generation
paper2patent paper.pdf --no-diagrams

# Verbose logging
paper2patent paper.pdf -v
```

### Python API

```python
from paper2patent.pipeline import PaperToPatentPipeline

pipeline = PaperToPatentPipeline(
    output_dir="./output/",
    patent_type="cn",
    reference_docx="template_patent.docx",  # optional
    verbose=True,
)
output = pipeline.run("paper.pdf")
print(f"Patent saved to: {output}")
```

### Claude Code Skill

```bash
# Copy to Claude Code skills
cp SKILL.md ~/.claude/skills/paper2patent/SKILL.md

# Then in Claude Code:
# "/paper2patent paper.pdf"
```

## Features

- ✅ **PDF input** — text-based + scanned (OCR via PaddleOCR)
- ✅ **LaTeX input** — full project folder with `\input`/`\include` resolution
- ✅ **Claims generation** — independent (method + system) + dependent (parameters, alternatives)
- ✅ **Figure extraction** — embedded raster + vector graphics with intelligent cropping
- ✅ **Flowchart generation** — `graphviz` method flowcharts with reference numerals
- ✅ **Block diagram generation** — `matplotlib` system architecture diagrams
- ✅ **CNIPA formatting** — margins, fonts, line spacing, section headings all compliant
- ✅ **Reference patent styles** — extract formatting from existing `.docx` patents
- ✅ **Validation** — claims single-sentence check, multi-dependency check, cross-reference check
- ✅ **Dry-run mode** — preview intermediate JSON/markdown without writing `.docx`

## Output Structure

```
patent_output/
├── 专利_title.docx           # Final formatted patent
├── intermediate/
│   ├── paper_ir.json         # Parsed paper structure
│   ├── paper_analysis.json   # LLM analysis
│   ├── patent_structure.md   # Draft patent sections
│   ├── claims.md             # Draft claims
│   └── validation_report.txt # Validation results
├── figures/
│   ├── fig1.png              # Extracted paper figures
│   └── fig2.png
└── diagrams/
    ├── flow_method.pdf       # Method flowchart
    ├── block_system.pdf      # System block diagram
    └── framework.pdf         # Framework overview
```

## Dependencies

| Category | Package | Purpose |
|----------|---------|---------|
| **Core** | `python-docx`, `click`, `pydantic` | .docx writing, CLI, data models |
| **PDF** | `PyMuPDF`, `pymupdf4llm` | PDF parsing, image extraction |
| **LaTeX** | `latex2json`, `pylatexenc` | LaTeX → structured JSON, math → text |
| **Diagrams** | `graphviz`, `matplotlib`, `Pillow` | Flowcharts, block diagrams, images |
| **UI** | `rich` | Terminal output |
| **Optional** | `paddleocr` (OCR), `docling` (semantic PDF), `anthropic`/`openai` (LLM) | |

## Roadmap

- [ ] US patent (USPTO) format support
- [ ] LaTeX patent template output
- [ ] Interactive claim editor
- [ ] Multi-language patent translation
- [ ] Style profile: more reference patent auto-detection patterns
- [ ] Web UI

## License

MIT — see [LICENSE](LICENSE).

## Contributing

Contributions welcome! Open an issue or PR on GitHub.
