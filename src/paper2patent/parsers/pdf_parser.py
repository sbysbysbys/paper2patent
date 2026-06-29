"""Parse PDF files into PaperIR using PyMuPDF + pymupdf4llm."""

from __future__ import annotations

import os
import re
from pathlib import Path

import fitz  # PyMuPDF

from paper2patent.parsers.base import BaseParser
from paper2patent.ir import PaperIR, Section, Figure, Table, Equation


class PDFParser(BaseParser):
    """Parse an academic PDF into PaperIR.

    Uses pymupdf4llm for structured extraction (headings, figures, tables, reading order).
    Falls back to raw PyMuPDF text extraction when pymupdf4llm is unavailable.
    """

    def parse(self, input_path: str) -> PaperIR:
        input_path = os.path.abspath(input_path)

        # Check if it's a scanned PDF (needs OCR)
        if self._is_scanned(input_path):
            if self.verbose:
                print("[yellow]Detected scanned PDF. Install paddleocr for better results.[/yellow]")
            return self._parse_with_ocr(input_path)

        # Try pymupdf4llm first
        try:
            return self._parse_with_pymupdf4llm(input_path)
        except ImportError:
            if self.verbose:
                print("[dim]pymupdf4llm not available, using PyMuPDF raw extraction[/dim]")
            return self._parse_raw(input_path)

    # ------------------------------------------------------------------
    # pymupdf4llm path (preferred)
    # ------------------------------------------------------------------

    def _parse_with_pymupdf4llm(self, input_path: str) -> PaperIR:
        import pymupdf4llm

        # Convert to markdown with image extraction
        md_text = pymupdf4llm.to_markdown(
            input_path,
            write_images=True,
            image_path=str(Path(input_path).parent / "extracted_images"),
            dpi=300,
        )

        ir = PaperIR(
            source_format="pdf",
            source_path=input_path,
        )

        # Parse the markdown output to extract structure
        ir.sections = self._parse_md_sections(md_text)
        ir.figures = self._find_extracted_figures(input_path)
        ir.full_text = md_text
        ir.language = self._detect_language(md_text)

        # Extract title from first heading
        if ir.sections:
            ir.title = ir.sections[0].heading
            # Check if the first section is actually the paper title
            if not ir.title or len(ir.title) < 5:
                ir.title = self._guess_title_from_pdf(input_path)

        # Extract abstract
        ir.abstract = self._extract_abstract_from_md(md_text)

        return ir

    def _parse_md_sections(self, md_text: str) -> list[Section]:
        """Extract heading-structured sections from pymupdf4llm markdown output."""
        sections = []
        current_heading = ""
        current_level = 1
        current_content: list[str] = []

        for line in md_text.split("\n"):
            heading_match = re.match(r"^(#{1,6})\s+(.+)", line)
            if heading_match:
                # Save previous section
                if current_heading or current_content:
                    sections.append(Section(
                        heading=current_heading,
                        content="\n".join(current_content).strip(),
                        level=current_level,
                    ))
                current_heading = heading_match.group(2).strip()
                current_level = len(heading_match.group(1))
                current_content = []
            else:
                current_content.append(line)

        # Don't forget the last section
        if current_heading or current_content:
            sections.append(Section(
                heading=current_heading,
                content="\n".join(current_content).strip(),
                level=current_level,
            ))

        return sections

    def _extract_abstract_from_md(self, md_text: str) -> str:
        """Find abstract paragraph in pymupdf4llm output."""
        for line in md_text.split("\n"):
            line_lower = line.strip().lower()
            if line_lower.startswith("abstract") or line_lower.startswith("abstract—") or line_lower.startswith("abstract."):
                return line.strip()[8:].strip("—. \t")
        return ""

    def _guess_title_from_pdf(self, input_path: str) -> str:
        """Fallback: extract largest-font text from first page as title."""
        doc = fitz.open(input_path)
        page = doc[0]
        blocks = page.get_text("dict")["blocks"]
        doc.close()

        max_size = 0
        title_text = ""
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        if span["size"] > max_size and len(span["text"].strip()) > 5:
                            max_size = span["size"]
                            title_text = span["text"].strip()
        return title_text

    def _find_extracted_figures(self, input_path: str) -> list[Figure]:
        """Find images extracted by pymupdf4llm."""
        figures = []
        img_dir = Path(input_path).parent / "extracted_images"
        if img_dir.exists():
            for i, img_file in enumerate(sorted(img_dir.glob("*"))):
                if img_file.suffix.lower() in (".png", ".jpg", ".jpeg"):
                    figures.append(Figure(
                        index=i + 1,
                        image_path=str(img_file),
                    ))
        return figures

    # ------------------------------------------------------------------
    # Raw PyMuPDF path (fallback)
    # ------------------------------------------------------------------

    def _parse_raw(self, input_path: str) -> PaperIR:
        doc = fitz.open(input_path)

        all_text_parts = []
        figures = []
        equations = []

        for page_num, page in enumerate(doc):
            # Text
            text = page.get_text()
            all_text_parts.append(text)

            # Images
            for img_index, img in enumerate(page.get_images(full=True)):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                ext = base_image["ext"]

                img_filename = f"page{page_num+1}_img{img_index+1}.{ext}"
                img_path = str(Path(input_path).parent / "extracted_images" / img_filename)
                os.makedirs(os.path.dirname(img_path), exist_ok=True)
                with open(img_path, "wb") as f:
                    f.write(image_bytes)

                figures.append(Figure(
                    index=len(figures) + 1,
                    image_path=img_path,
                    page_number=page_num + 1,
                ))

            # Vector graphics (cluster_drawings)
            try:
                clusters = page.cluster_drawings()
                for cluster_idx, rect in enumerate(clusters):
                    pix = page.get_pixmap(clip=rect, dpi=300)
                    vec_path = str(Path(input_path).parent / "extracted_images" /
                                   f"page{page_num+1}_vector{cluster_idx+1}.png")
                    os.makedirs(os.path.dirname(vec_path), exist_ok=True)
                    pix.save(vec_path)
                    figures.append(Figure(
                        index=len(figures) + 1,
                        image_path=vec_path,
                        page_number=page_num + 1,
                        bbox=(rect.x0, rect.y0, rect.x1, rect.y1),
                        is_vector=True,
                    ))
            except Exception:
                pass  # cluster_drawings may fail on some PDFs

        doc.close()

        full_text = "\n\n".join(all_text_parts)

        ir = PaperIR(
            source_format="pdf",
            source_path=input_path,
            full_text=full_text,
            figures=figures,
            language=self._detect_language(full_text),
        )

        # Sections from raw text (heuristic)
        ir.sections = self._parse_raw_sections(full_text)

        # Title from first large text
        ir.title = self._guess_title_from_pdf(input_path)

        return ir

    def _parse_raw_sections(self, text: str) -> list[Section]:
        """Crude section splitting by double newlines + keyword detection."""
        sections = []
        # Try to detect common section patterns
        section_patterns = [
            r'(?:\d+[\.\s]+)?(?:Introduction|Related Work|Method|Experiment|Conclusion|Results|Discussion|Background|Approach|Model|Architecture|Implementation|Evaluation)(?:\s|:|—|–)',
        ]
        for pattern in section_patterns:
            splits = re.split(pattern, text, flags=re.IGNORECASE)
            if len(splits) > 1:
                headings = re.findall(pattern, text, flags=re.IGNORECASE)
                for i, (heading, content) in enumerate(zip(headings, splits[1:])):
                    sections.append(Section(
                        heading=heading.strip(),
                        content=content.strip()[:3000],  # limit content length
                        level=1,
                    ))
                break

        if not sections:
            # Just split by blank lines into chunks
            chunks = text.split("\n\n")
            for i, chunk in enumerate(chunks[:10]):
                cleaned = chunk.strip()
                if len(cleaned) > 50:
                    sections.append(Section(
                        heading="",
                        content=cleaned,
                        level=1,
                    ))

        return sections

    # ------------------------------------------------------------------
    # OCR path
    # ------------------------------------------------------------------

    def _parse_with_ocr(self, input_path: str) -> PaperIR:
        """Handle scanned PDF with OCR (requires paddleocr)."""
        try:
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(lang="ch")
        except ImportError:
            if self.verbose:
                print("[red]paddleocr not installed. Install with: pip install paddleocr paddlepaddle[/red]")
            # Fall back to raw extraction (may produce empty results)
            return self._parse_raw(input_path)

        doc = fitz.open(input_path)
        all_text_parts = []
        figures = []

        for page_num, page in enumerate(doc):
            # Render page as image
            pix = page.get_pixmap(dpi=300)
            img_path = f"/tmp/paper2patent_page_{page_num}.png"
            pix.save(img_path)

            # OCR
            result = ocr.ocr(img_path)
            if result and result[0]:
                page_text = "\n".join(line[1][0] for line in result[0])
                all_text_parts.append(page_text)

            # Clean up temp image
            try:
                os.remove(img_path)
            except OSError:
                pass

        doc.close()

        full_text = "\n\n".join(all_text_parts)

        return PaperIR(
            source_format="pdf",
            source_path=input_path,
            full_text=full_text,
            figures=figures,
            language=self._detect_language(full_text),
        )

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _is_scanned(self, input_path: str) -> bool:
        """Determine if a PDF is scanned (image-based)."""
        doc = fitz.open(input_path)
        # Check first 3 pages
        total_chars = 0
        for i in range(min(3, len(doc))):
            total_chars += len(doc[i].get_text().strip())
        doc.close()
        return total_chars < 100  # Very few extractable chars → scanned

    def _detect_language(self, text: str) -> str:
        sample = text[:2000]
        cjk_count = sum(1 for c in sample if '一' <= c <= '鿿')
        if cjk_count > 50:
            return "zh"
        elif cjk_count > 10:
            return "mixed"
        return "en"
