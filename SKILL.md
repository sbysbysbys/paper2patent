---
name: paper2patent
description: Convert academic papers (LaTeX source or PDF) into Chinese invention patent .docx format. Use when the user asks to convert a paper to patent, generate patent claims from a paper, create patent diagrams, or draft a patent application from research.
version: 1.0.0
author: paper2patent
license: MIT
tags: [patent, paper, latex, pdf, docx, CNIPA, intellectual-property, academic-writing]
dependencies: [python-docx, PyMuPDF, latex2json, pylatexenc, graphviz, matplotlib, Pillow, rich, click, pydantic]
---

# Paper-to-Patent Skill

Convert academic papers (LaTeX source folder or PDF) into a formatted Chinese invention patent (`.docx`).

## Pipeline

```
Input (paper) → Parse → Analyze → Patent Structure → Claims → Figures → Diagrams → Format → Validate → .docx
```

## Quick Start

### CLI usage

```bash
# From PDF
paper2patent paper.pdf -o output/

# From LaTeX folder
paper2patent latex_project/ -o output/

# Dry-run (only intermediate JSON/md, no docx)
paper2patent paper.pdf --dry-run

# With reference patent for style
paper2patent paper.pdf -r reference_patent.docx

# Skip diagram generation (faster, manual diagrams later)
paper2patent paper.pdf --no-diagrams
```

### Python API

```python
from paper2patent.pipeline import PaperToPatentPipeline

pipeline = PaperToPatentPipeline(
    output_dir="./output/",
    patent_type="cn",
    verbose=True,
)
output = pipeline.run("paper.pdf")
print(f"Patent saved to: {output}")
```

## What It Does

### Input
- **PDF**: Academic paper PDF (text-based or scanned)
- **LaTeX**: `.tex` main file or project folder

### Output
- **`.docx`**: Formatted CN invention patent (摘要 + 权利要求书 + 说明书 + 附图)
- **`intermediate/`**: PaperIR, PaperAnalysis, claims.md, patent_structure.md
- **`figures/`**: Extracted paper figures
- **`diagrams/`**: Generated flowcharts and block diagrams

### Patent Sections Generated
1. 说明书摘要 (Abstract)
2. 权利要求书 (Claims) — independent + dependent
3. 说明书:
   - 【技术领域】(Technical Field)
   - 【背景技术】(Background)
   - 【发明内容】(Summary — problem + solution + beneficial effects)
   - 【附图说明】(Brief Description of Drawings)
   - 【具体实施方式】(Detailed Description / Embodiments)
4. 说明书附图 (Drawings)

### Diagrams Generated
- **Method flowchart** (graphviz) — steps with reference numerals
- **System block diagram** (matplotlib) — components + connections
- **Framework diagram** — high-level architecture

## Prerequisites

```bash
# Python deps
pip install paper2patent

# System deps
brew install graphviz  # macOS
apt install graphviz   # Linux
```

## Configuration

### Reference Patent Styles

Provide a reference `.docx` patent to extract formatting:
```bash
paper2patent paper.pdf -r my_lab_patent_template.docx
```

The system extracts: font family/size, paragraph spacing, margins, heading styles and merges them with CNIPA defaults.

### LLM Backend

The paper analysis step (Step 2) uses Claude by default. Override with:
```bash
paper2patent paper.pdf --llm claude   # default
paper2patent paper.pdf --llm openai   # requires OPENAI_API_KEY
```

## Validation

The pipeline automatically validates:
- Claims single-sentence rule
- Dependent claim reference legality (no 多引多)
- Abstract < 300 characters (CN requirement)
- All 5 mandatory 【】 sections present
- Figure reference numeral cross-check

Report saved to `output/intermediate/validation_report.txt`.

## Notes

- LLM is only used in Step 2 (semantic analysis). Steps 3-9 are rule/template-based for deterministic output.
- All intermediate outputs are saved for manual review and adjustment.
- For scanned PDFs, install optional OCR deps: `pip install paper2patent[ocr]`
