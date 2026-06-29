"""PaperIR — Unified intermediate representation of an academic paper.

All parsers (LaTeX, PDF) produce this structure so downstream
steps are format-agnostic.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# PaperIR
# ---------------------------------------------------------------------------

class Section(BaseModel):
    heading: str = ""
    content: str = ""
    level: int = 1  # 1 = top-level section, 2 = subsection, ...
    parent_heading: Optional[str] = None


class Figure(BaseModel):
    index: int = 0
    image_path: str = ""  # path to extracted image file
    caption: str = ""
    page_number: int = 0
    bbox: tuple[float, float, float, float] = (0, 0, 0, 0)  # x0, y0, x1, y1 in page coords
    is_vector: bool = False


class Table(BaseModel):
    index: int = 0
    caption: str = ""
    headers: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)
    page_number: int = 0


class Equation(BaseModel):
    index: int = 0
    latex: str = ""
    unicode_text: str = ""
    context: str = ""  # surrounding paragraph text


class Citation(BaseModel):
    key: str = ""
    title: str = ""
    authors: str = ""
    year: int = 0
    venue: str = ""
    raw_bibtex: str = ""


class PaperIR(BaseModel):
    """Unified intermediate representation of an academic paper."""

    title: str = ""
    authors: list[str] = Field(default_factory=list)
    abstract: str = ""
    keywords: list[str] = Field(default_factory=list)

    sections: list[Section] = Field(default_factory=list)
    figures: list[Figure] = Field(default_factory=list)
    tables: list[Table] = Field(default_factory=list)
    equations: list[Equation] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)

    # Metadata
    source_format: str = ""  # "latex" or "pdf"
    source_path: str = ""
    paper_type: str = ""  # "method" / "system" / "both" / "unknown"
    language: str = ""    # "zh" / "en" / "mixed"

    # Raw full text for LLM consumption
    full_text: str = ""


# ---------------------------------------------------------------------------
# PaperAnalysis (Step 2 output)
# ---------------------------------------------------------------------------

class MethodStep(BaseModel):
    index: int = 0
    description: str = ""     # Chinese description of what this step does
    actor: str = ""           # which component performs it
    input_data: str = ""
    output_data: str = ""
    reference_num: int = 0    # patent reference numeral (110, 120, ...)


class SystemComponent(BaseModel):
    index: int = 0
    name: str = ""            # Chinese name
    function: str = ""        # what it does
    inputs: str = ""
    outputs: str = ""
    connections: list[int] = Field(default_factory=list)  # indices of connected components
    reference_num: int = 0    # patent reference numeral (10, 20, ...)


class NoveltyPoint(BaseModel):
    description: str = ""
    claim_target: str = ""    # which claim this maps to


class PaperAnalysis(BaseModel):
    """LLM-assisted structured analysis of a paper."""

    # Domain / classification
    technical_field: str = ""  # CN 【技术领域】candidate, 1-2 sentences
    technical_problem: str = ""  # what problem the paper solves

    # Core inventive content
    method_steps: list[MethodStep] = Field(default_factory=list)
    system_components: list[SystemComponent] = Field(default_factory=list)

    # Novelty
    novelty_points: list[NoveltyPoint] = Field(default_factory=list)

    # Parameters
    key_parameters: list[dict] = Field(default_factory=list)
    # e.g. [{"name": "学习率", "value": "0.001-0.01", "context": "优化器超参数"}]

    # Variations
    alternatives: list[str] = Field(default_factory=list)

    # Paper type
    is_method_invention: bool = False
    is_system_invention: bool = False


# ---------------------------------------------------------------------------
# PatentIR (Step 3-4 output)
# ---------------------------------------------------------------------------

class PatentClaim(BaseModel):
    number: int = 0
    claim_type: str = ""  # "independent" or "dependent"
    category: str = ""    # "method" or "system"
    text: str = ""
    depends_on: list[int] = Field(default_factory=list)  # claim numbers this depends on
    reference_nums: list[int] = Field(default_factory=list)  # reference numerals used


class PatentSection(BaseModel):
    heading: str = ""   # e.g. "【技术领域】", "【背景技术】", ...
    content: str = ""   # markdown content


class PatentIR(BaseModel):
    """Structured patent document ready for formatting."""

    title: str = ""
    patent_type: str = "cn"

    # Abstract (max 300 chars for CN invention)
    abstract: str = ""
    abstract_figure_path: str = ""

    # Claims
    claims: list[PatentClaim] = Field(default_factory=list)

    # Description sections
    sections: list[PatentSection] = Field(default_factory=list)

    # Figures
    figures: list[dict] = Field(default_factory=list)
    # [{"path": "figures/fig1.png", "caption": "图1是...", "ref_nums": [10, 20]}]

    # Generated diagrams
    diagrams: list[dict] = Field(default_factory=list)
    # [{"path": "diagrams/flow_method.pdf", "caption": "图X是...方法流程图"}]


# ---------------------------------------------------------------------------
# StyleProfile (Step 7 output)
# ---------------------------------------------------------------------------

class StyleProfile(BaseModel):
    """Patent document formatting profile."""

    name: str = "default_cn"
    source: str = "builtin"  # "builtin" or "reference:<path>"

    # Page
    page_size: str = "A4"  # "A4" or "Letter"
    margin_top_mm: float = 25.0
    margin_bottom_mm: float = 15.0
    margin_left_mm: float = 25.0
    margin_right_mm: float = 15.0

    # Font
    body_font_family: str = "宋体"
    body_font_size_pt: float = 12.0
    body_font_color: str = "000000"

    # Heading
    heading_font_family: str = "黑体"
    heading_font_size_pt: float = 14.0
    heading_bold: bool = True

    # Paragraph
    line_spacing: float = 1.5
    first_line_indent_chars: int = 2

    # Section title prefix style
    section_title_brackets: str = "【】"  # CN uses 【】

    # Claims
    claims_font_family: str = "宋体"
    claims_font_size_pt: float = 12.0

    # Abstract
    abstract_font_family: str = "宋体"
    abstract_font_size_pt: float = 12.0
