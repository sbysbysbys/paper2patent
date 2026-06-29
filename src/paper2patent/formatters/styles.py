"""Style profile management — load defaults, merge with reference, apply to docx."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from paper2patent.ir import StyleProfile


def build_style_profile(
    patent_type: str = "cn",
    reference_docx: Optional[str] = None,
) -> StyleProfile:
    """Build a StyleProfile from defaults, optionally merging a reference patent.

    Priority: reference_docx styles > built-in defaults
    """
    # Load built-in defaults
    profile = _load_defaults(patent_type)

    # Merge reference patent styles if provided
    if reference_docx and os.path.exists(reference_docx):
        ref_profile = _extract_from_docx(reference_docx)
        profile = _merge_profiles(profile, ref_profile)

    return profile


def _load_defaults(patent_type: str) -> StyleProfile:
    """Load the built-in default style profile."""
    # Find the default styles JSON
    default_path = Path(__file__).parent / "default_cn_styles.json"

    if default_path.exists():
        data = json.loads(default_path.read_text(encoding="utf-8"))
        return _json_to_profile(data)

    # Hard-coded fallback defaults
    return StyleProfile(
        name=f"default_{patent_type}",
        source="builtin",
        page_size="A4",
        margin_top_mm=25.0,
        margin_bottom_mm=15.0,
        margin_left_mm=25.0,
        margin_right_mm=15.0,
        body_font_family="宋体",
        body_font_size_pt=12.0,
        heading_font_family="黑体",
        heading_font_size_pt=14.0,
        heading_bold=True,
        line_spacing=1.5,
        first_line_indent_chars=2,
        section_title_brackets="【】",
    )


def _json_to_profile(data: dict) -> StyleProfile:
    """Convert JSON style dict to StyleProfile."""
    page = data.get("page", {})
    body = data.get("body_font", {})
    heading = data.get("heading_font", {})
    para = data.get("paragraph", {})
    claims = data.get("claims", {})
    abstract = data.get("abstract", {})
    section = data.get("section_title", {})

    return StyleProfile(
        name=data.get("name", "custom"),
        page_size=page.get("size", "A4"),
        margin_top_mm=float(page.get("margin_top_mm", 25)),
        margin_bottom_mm=float(page.get("margin_bottom_mm", 15)),
        margin_left_mm=float(page.get("margin_left_mm", 25)),
        margin_right_mm=float(page.get("margin_right_mm", 15)),
        body_font_family=body.get("family", "宋体"),
        body_font_size_pt=float(body.get("size_pt", 12)),
        body_font_color=body.get("color", "000000"),
        heading_font_family=heading.get("family", "黑体"),
        heading_font_size_pt=float(heading.get("size_pt", 14)),
        heading_bold=heading.get("bold", True),
        line_spacing=float(para.get("line_spacing", 1.5)),
        first_line_indent_chars=int(para.get("first_line_indent_chars", 2)),
        section_title_brackets=section.get("brackets_style", "【】"),
        claims_font_family=claims.get("font_family", "宋体"),
        claims_font_size_pt=float(claims.get("font_size_pt", 12)),
        abstract_font_family=abstract.get("font_family", "宋体"),
        abstract_font_size_pt=float(abstract.get("font_size_pt", 12)),
    )


def _extract_from_docx(docx_path: str) -> StyleProfile:
    """Extract styles from a reference .docx patent."""
    from paper2patent.formatters.reference_reader import ReferenceReader
    reader = ReferenceReader()
    return reader.extract(docx_path)


def _merge_profiles(base: StyleProfile, reference: StyleProfile) -> StyleProfile:
    """Merge reference profile into base. Reference overrides non-default values."""
    # For simplicity, replace base fields with reference if they differ from default
    ref_data = reference.model_dump()
    base_data = base.model_dump()

    for field in ref_data:
        ref_val = ref_data[field]
        # Only override if reference has a non-empty/more-specific value
        if ref_val and ref_val != base_data.get(field):
            base_data[field] = ref_val

    base_data["source"] = f"merged:{reference.source}"
    return StyleProfile(**base_data)


def apply_styles_to_docx(doc, profile: StyleProfile) -> None:
    """Apply a StyleProfile to a python-docx Document object."""
    from docx.shared import Pt, Cm, RGBColor
    from docx.enum.text import WD_LINE_SPACING

    # Page margins
    for section in doc.sections:
        section.top_margin = Cm(profile.margin_top_mm / 10)
        section.bottom_margin = Cm(profile.margin_bottom_mm / 10)
        section.left_margin = Cm(profile.margin_left_mm / 10)
        section.right_margin = Cm(profile.margin_right_mm / 10)

    # Normal style
    style = doc.styles["Normal"]
    style.font.size = Pt(profile.body_font_size_pt)
    style.font.name = profile.body_font_family
    style.font.color.rgb = RGBColor.from_string(profile.body_font_color)
    style.paragraph_format.line_spacing = profile.line_spacing
