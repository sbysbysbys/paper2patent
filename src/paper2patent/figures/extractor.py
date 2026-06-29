"""Figure extraction and cropping from PDF/LaTeX sources."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import fitz  # PyMuPDF

from paper2patent.ir import PaperIR


class FigureExtractor:
    """Extract figures from a paper, crop from PDF, and prepare for patent output."""

    def __init__(self, output_dir: str = "./figures/"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract(self, paper_ir: PaperIR) -> list[dict]:
        """Extract all figures and return patent-ready figure info list."""
        figures_info = []

        if paper_ir.source_format == "pdf":
            figures_info = self._extract_from_pdf(paper_ir)
        elif paper_ir.source_format == "latex":
            figures_info = self._extract_from_latex(paper_ir)
        else:
            # Just copy any existing figure paths
            figures_info = self._copy_existing(paper_ir)

        # Rename sequentially for patent
        return self._renumber(figures_info)

    # ------------------------------------------------------------------
    # PDF extraction
    # ------------------------------------------------------------------

    def _extract_from_pdf(self, paper_ir: PaperIR) -> list[dict]:
        """Extract figures from source PDF with intelligent cropping."""
        figures_info = []

        try:
            doc = fitz.open(paper_ir.source_path)

            for page_num, page in enumerate(doc):
                # Method 1: Extract embedded raster images
                for img_info in page.get_images(full=True):
                    xref = img_info[0]
                    try:
                        base_image = doc.extract_image(xref)
                        ext = base_image["ext"]
                        img_bytes = base_image["image"]

                        out_name = f"extracted_p{page_num+1}_i{xref}.{ext}"
                        out_path = self.output_dir / out_name
                        with open(out_path, "wb") as f:
                            f.write(img_bytes)

                        figures_info.append({
                            "original_path": str(out_path),
                            "caption": f"图 来自第{page_num + 1}页",
                            "page": page_num + 1,
                            "source": "embedded_raster",
                        })
                    except Exception:
                        continue

                # Method 2: Extract vector graphics via cluster_drawings
                try:
                    clusters = page.cluster_drawings()
                    for ci, rect in enumerate(clusters):
                        # Only extract reasonably-sized clusters (not full-page)
                        area = abs(rect.width * rect.height)
                        page_area = abs(page.rect.width * page.rect.height)
                        if area < page_area * 0.9 and area > page_area * 0.02:
                            pix = page.get_pixmap(clip=rect, dpi=300)
                            out_name = f"clustered_p{page_num+1}_c{ci+1}.png"
                            out_path = self.output_dir / out_name
                            pix.save(str(out_path))

                            # Try to find nearby caption text
                            caption = self._find_caption_nearby(page, rect)

                            figures_info.append({
                                "original_path": str(out_path),
                                "caption": caption or f"图 来自第{page_num + 1}页",
                                "page": page_num + 1,
                                "source": "clustered_vector",
                            })
                except Exception:
                    pass

            doc.close()
        except Exception as e:
            # If PyMuPDF fails, fall back to existing figures in PaperIR
            for fig in paper_ir.figures:
                if fig.image_path and os.path.exists(fig.image_path):
                    figures_info.append({
                        "original_path": fig.image_path,
                        "caption": fig.caption,
                        "page": fig.page_number,
                        "source": "paper_ir",
                    })

        return figures_info

    def _find_caption_nearby(self, page, rect) -> str | None:
        """Search for 'Figure X' / 'Fig. X' text below a figure cluster."""
        # Expand search area below the figure
        caption_area = fitz.Rect(
            rect.x0 - 20,
            rect.y1,
            rect.x1 + 20,
            min(rect.y1 + 80, page.rect.y1),
        )
        text = page.get_text("text", clip=caption_area)
        if text.strip():
            lines = text.strip().split("\n")
            for line in lines[:3]:
                line = line.strip()
                if any(kw in line.lower() for kw in ("fig", "figure", "图", "表")):
                    return line
        return None

    # ------------------------------------------------------------------
    # LaTeX extraction
    # ------------------------------------------------------------------

    def _extract_from_latex(self, paper_ir: PaperIR) -> list[dict]:
        """Copy figure files from LaTeX project."""
        figures_info = []

        for fig in paper_ir.figures:
            if fig.image_path and os.path.exists(fig.image_path):
                # Copy to output directory
                src = Path(fig.image_path)
                dst = self.output_dir / f"latex_{src.name}"
                shutil.copy2(src, dst)

                figures_info.append({
                    "original_path": str(dst),
                    "caption": fig.caption,
                    "source": "latex",
                })

        return figures_info

    # ------------------------------------------------------------------
    # Copy existing
    # ------------------------------------------------------------------

    def _copy_existing(self, paper_ir: PaperIR) -> list[dict]:
        """Just use figures already in PaperIR."""
        figures_info = []
        for fig in paper_ir.figures:
            if fig.image_path:
                figures_info.append({
                    "original_path": fig.image_path,
                    "caption": fig.caption,
                    "source": "paper_ir",
                })
        return figures_info

    # ------------------------------------------------------------------
    # Renumbering
    # ------------------------------------------------------------------

    def _renumber(self, figures_info: list[dict]) -> list[dict]:
        """Rename figure files to patent-standard numbered format."""
        result = []
        for i, info in enumerate(figures_info, 1):
            src = Path(info["original_path"])

            # Determine format
            new_ext = ".png"
            # Convert to PNG for consistency
            if src.suffix.lower() in (".jpg", ".jpeg", ".bmp", ".tiff", ".tif"):
                from PIL import Image
                img = Image.open(src)
                new_name = f"fig{i}.png"
                new_path = self.output_dir / new_name
                img.save(str(new_path), "PNG")
            elif src.suffix.lower() == ".pdf":
                # Convert PDF page to PNG
                try:
                    doc = fitz.open(str(src))
                    page = doc[0]
                    pix = page.get_pixmap(dpi=300)
                    new_name = f"fig{i}.png"
                    new_path = self.output_dir / new_name
                    pix.save(str(new_path))
                    doc.close()
                except Exception:
                    # Just copy as-is
                    new_name = f"fig{i}{src.suffix.lower()}"
                    new_path = self.output_dir / new_name
                    shutil.copy2(src, new_path)
            else:
                new_name = f"fig{i}{src.suffix.lower()}"
                new_path = self.output_dir / new_name
                shutil.copy2(src, new_path)

            result.append({
                "path": str(new_path),
                "caption": f"图{i} 是{info.get('caption', '本发明实施例的示意图')}",
                "original_path": str(src),
                "index": i,
            })

        return result

    # ------------------------------------------------------------------
    # Crop figures with captions from PDF
    # ------------------------------------------------------------------

    def crop_figure_with_caption(
        self, pdf_path: str, figure_bbox: tuple, caption_bbox: tuple, output_path: str
    ) -> str:
        """Crop a figure plus its caption as a single image from PDF.

        Args:
            pdf_path: Source PDF path
            figure_bbox: (x0, y0, x1, y1) of the figure
            caption_bbox: (x0, y0, x1, y1) of the caption
            output_path: Where to save the cropped image
        """
        doc = fitz.open(pdf_path)
        page = doc[0]  # assume figure on first page (can be parameterized)

        # Union of figure and caption bounding boxes
        combined = fitz.Rect(
            min(figure_bbox[0], caption_bbox[0]),
            min(figure_bbox[1], caption_bbox[1]),
            max(figure_bbox[2], caption_bbox[2]),
            max(figure_bbox[3], caption_bbox[3]),
        )

        # Add small padding
        padding = 10
        combined = fitz.Rect(
            combined.x0 - padding,
            combined.y0 - padding,
            combined.x1 + padding,
            combined.y1 + padding,
        )

        pix = page.get_pixmap(clip=combined, dpi=300)
        pix.save(output_path)
        doc.close()

        return output_path

    # ------------------------------------------------------------------
    # Black & White conversion
    # ------------------------------------------------------------------

    def convert_to_bw(self, image_path: str) -> str:
        """Convert a single image to patent-ready black-and-white.

        - Grayscale conversion
        - Contrast enhancement
        - 300 DPI output
        """
        from PIL import Image, ImageEnhance

        img = Image.open(image_path)
        # Convert to grayscale
        bw = img.convert("L")
        # Boost contrast for clear line reproduction
        enhancer = ImageEnhance.Contrast(bw)
        bw = enhancer.enhance(1.4)
        # Save
        out_path = image_path  # overwrite
        bw.save(out_path, dpi=(300, 300))
        return out_path

    def convert_all_to_bw(self, figure_dir: str) -> list[str]:
        """Convert all figures in a directory to black-and-white."""
        converted = []
        fig_dir = Path(figure_dir)
        for img_file in sorted(fig_dir.glob("*")):
            if img_file.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"):
                try:
                    self.convert_to_bw(str(img_file))
                    converted.append(str(img_file))
                except Exception:
                    pass
        return converted
