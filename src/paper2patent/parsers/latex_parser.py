"""Parse LaTeX source files into PaperIR."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

from paper2patent.parsers.base import BaseParser
from paper2patent.ir import PaperIR, Section, Figure, Table, Equation, Citation


class LaTeXParser(BaseParser):
    """Parse a LaTeX project folder (or single .tex file) into PaperIR.

    Uses latex2json for structure extraction and pylatexenc for math → text.
    """

    def parse(self, input_path: str) -> PaperIR:
        input_path = os.path.abspath(input_path)
        project_dir = self._resolve_project_dir(input_path)

        # Use latex2json if available
        try:
            from latex2json import LaTeXConverter
            converter = LaTeXConverter()
            doc = converter.convert(input_path)
            return self._from_latex2json(doc, input_path, project_dir)
        except ImportError:
            if self.verbose:
                print("[dim]latex2json not available, using regex-based fallback[/dim]")

        # Fallback: regex-based parsing
        return self._parse_manual(input_path, project_dir)

    # ------------------------------------------------------------------
    # latex2json path
    # ------------------------------------------------------------------

    def _from_latex2json(self, doc: dict, input_path: str, project_dir: str) -> PaperIR:
        ir = PaperIR(
            source_format="latex",
            source_path=input_path,
            language="en",  # will be detected
        )

        # Title
        ir.title = doc.get("title", "")

        # Authors
        authors = doc.get("authors", [])
        if isinstance(authors, list):
            ir.authors = [a.get("name", str(a)) if isinstance(a, dict) else str(a) for a in authors]

        # Abstract
        ir.abstract = doc.get("abstract", "")

        # Sections
        for sec in doc.get("sections", []):
            ir.sections.append(Section(
                heading=sec.get("heading", ""),
                content=sec.get("content", ""),
                level=sec.get("level", 1),
                parent_heading=sec.get("parent"),
            ))

        # Figures
        for i, fig in enumerate(doc.get("figures", [])):
            ir.figures.append(Figure(
                index=i + 1,
                image_path=fig.get("path", ""),
                caption=fig.get("caption", ""),
            ))

        # Tables
        for i, tab in enumerate(doc.get("tables", [])):
            ir.tables.append(Table(
                index=i + 1,
                caption=tab.get("caption", ""),
                headers=tab.get("headers", []),
                rows=tab.get("rows", []),
            ))

        # Equations
        for i, eq in enumerate(doc.get("equations", [])):
            latex = eq.get("latex", "")
            ir.equations.append(Equation(
                index=i + 1,
                latex=latex,
                unicode_text=self._latex_math_to_unicode(latex),
                context=eq.get("context", ""),
            ))

        # Citations from bibliography
        for bib in doc.get("bibliography", []):
            ir.citations.append(Citation(
                key=bib.get("key", ""),
                title=bib.get("title", ""),
                authors=bib.get("authors", ""),
                year=bib.get("year", 0),
                venue=bib.get("journal", "") or bib.get("booktitle", ""),
                raw_bibtex=bib.get("raw", ""),
            ))

        # Full text
        ir.full_text = self._build_full_text(ir)

        # Detect language
        ir.language = self._detect_language(ir.full_text)

        return ir

    def _latex_math_to_unicode(self, latex: str) -> str:
        """Convert LaTeX math to Unicode text using pylatexenc."""
        if not latex:
            return ""
        try:
            from pylatexenc.latex2text import LatexNodes2Text
            l2t = LatexNodes2Text()
            return l2t.latex_to_text(latex)
        except ImportError:
            return latex

    # ------------------------------------------------------------------
    # Manual regex fallback
    # ------------------------------------------------------------------

    def _parse_manual(self, input_path: str, project_dir: str) -> PaperIR:
        """Regex-based fallback parser when latex2json is unavailable."""
        # Read the main tex file
        with open(input_path, "r", encoding="utf-8", errors="replace") as f:
            tex_content = f.read()

        # Resolve \input and \include
        tex_content = self._resolve_inputs(tex_content, project_dir)

        ir = PaperIR(
            source_format="latex",
            source_path=input_path,
            language=self._detect_language(tex_content),
        )

        # Extract title
        ir.title = self._extract_title(tex_content)

        # Extract authors
        ir.authors = self._extract_authors(tex_content)

        # Extract abstract
        ir.abstract = self._extract_abstract(tex_content)

        # Extract sections
        ir.sections = self._extract_sections(tex_content)

        # Extract figures
        ir.figures = self._extract_figures(tex_content, project_dir)

        # Extract tables
        ir.tables = self._extract_tables(tex_content)

        # Extract equations
        ir.equations = self._extract_equations(tex_content)

        # Extract bibliography
        ir.citations = self._extract_bibliography(tex_content, project_dir)

        # Full text
        ir.full_text = self._build_full_text(ir)

        return ir

    def _resolve_project_dir(self, input_path: str) -> str:
        p = Path(input_path)
        return str(p.parent) if p.is_file() else input_path

    def _resolve_inputs(self, tex: str, project_dir: str) -> str:
        """Resolve \\input{...} and \\include{...} commands."""
        def _replace(match):
            fname = match.group(1).strip()
            if not fname.endswith(".tex"):
                fname += ".tex"
            fpath = os.path.join(project_dir, fname)
            if os.path.exists(fpath):
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    return f.read()
            return match.group(0)

        tex = re.sub(r'\\input\{([^}]+)\}', _replace, tex)
        tex = re.sub(r'\\include\{([^}]+)\}', _replace, tex)
        return tex

    def _extract_title(self, tex: str) -> str:
        m = re.search(r'\\title\{((?:[^{}]|\{[^{}]*\})*)\}', tex, re.DOTALL)
        if m:
            title = m.group(1).strip()
            # Strip LaTeX commands
            title = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', title)
            return title
        return ""

    def _extract_authors(self, tex: str) -> list[str]:
        authors = []
        for m in re.finditer(r'\\author\{((?:[^{}]|\{[^{}]*\})*)\}', tex, re.DOTALL):
            author_text = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', m.group(1))
            # Split by \and or commas
            parts = re.split(r'\\and|,', author_text)
            for p in parts:
                p = re.sub(r'\s+', ' ', p).strip()
                if p:
                    authors.append(p)
        return authors

    def _extract_abstract(self, tex: str) -> str:
        # Try \begin{abstract}...\end{abstract}
        m = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', tex, re.DOTALL)
        if m:
            return re.sub(r'\s+', ' ', m.group(1)).strip()
        return ""

    def _extract_sections(self, tex: str) -> list[Section]:
        """Extract section hierarchy from LaTeX."""
        sections = []
        # Remove comments
        tex_clean = re.sub(r'(?<!\\)%.*$', '', tex, flags=re.MULTILINE)

        # Match \section, \subsection, \subsubsection
        pattern = r'\\(section|subsection|subsubsection)\{((?:[^{}]|\{[^{}]*\})*)\}'
        matches = list(re.finditer(pattern, tex_clean))

        for i, m in enumerate(matches):
            cmd = m.group(1)
            heading = m.group(2).strip()

            # Determine level
            if cmd == "section":
                level = 1
            elif cmd == "subsection":
                level = 2
            else:
                level = 3

            # Extract content until next heading or end
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(tex_clean)
            content = tex_clean[start:end].strip()
            # Clean LaTeX commands from content
            content = self._clean_latex(content)

            sections.append(Section(
                heading=heading,
                content=content,
                level=level,
            ))

        return sections

    def _extract_figures(self, tex: str, project_dir: str) -> list[Figure]:
        figures = []
        pattern = r'\\begin\{figure\*?\}(.*?)\\end\{figure\*?\}'
        for i, m in enumerate(re.finditer(pattern, tex, re.DOTALL)):
            body = m.group(1)
            # Extract \includegraphics
            img_m = re.search(r'\\includegraphics(?:\[.*?\])?\{([^}]+)\}', body)
            image_path = img_m.group(1) if img_m else ""
            if image_path and not os.path.isabs(image_path):
                # Try to locate the image file
                candidates = [
                    os.path.join(project_dir, image_path),
                    os.path.join(project_dir, "figures", os.path.basename(image_path)),
                    os.path.join(project_dir, "figs", os.path.basename(image_path)),
                    os.path.join(project_dir, "images", os.path.basename(image_path)),
                ]
                for c in candidates:
                    if os.path.exists(c):
                        image_path = c
                        break

            # Extract \caption
            cap_m = re.search(r'\\caption\{((?:[^{}]|\{[^{}]*\})*)\}', body, re.DOTALL)
            caption = cap_m.group(1).strip() if cap_m else ""

            figures.append(Figure(
                index=i + 1,
                image_path=image_path,
                caption=caption,
            ))

        return figures

    def _extract_tables(self, tex: str) -> list[Table]:
        tables = []
        pattern = r'\\begin\{table\*?\}(.*?)\\end\{table\*?\}'
        for i, m in enumerate(re.finditer(pattern, tex, re.DOTALL)):
            body = m.group(1)
            cap_m = re.search(r'\\caption\{((?:[^{}]|\{[^{}]*\})*)\}', body, re.DOTALL)
            caption = cap_m.group(1).strip() if cap_m else ""

            # Try to extract tabular content
            tab_m = re.search(r'\\begin\{tabular\}(.*?)\\end\{tabular\}', body, re.DOTALL)
            if tab_m:
                tab_content = tab_m.group(1)
                rows = []
                for row_line in tab_content.split(r"\\"):
                    cells = re.split(r'&', row_line)
                    cells = [re.sub(r'\\(?:textbf|textit|texttt)\{([^}]*)\}', r'\1', c).strip()
                             for c in cells]
                    rows.append(cells)
                headers = rows[0] if rows else []
                data_rows = rows[1:] if len(rows) > 1 else []
            else:
                headers, data_rows = [], []

            tables.append(Table(
                index=i + 1,
                caption=caption,
                headers=headers,
                rows=data_rows,
            ))

        return tables

    def _extract_equations(self, tex: str) -> list[Equation]:
        equations = []
        patterns = [
            r'\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}',
            r'\\begin\{align\*?\}(.*?)\\end\{align\*?\}',
        ]
        idx = 0
        for pattern in patterns:
            for m in re.finditer(pattern, tex, re.DOTALL):
                idx += 1
                latex_eq = m.group(1).strip()
                equations.append(Equation(
                    index=idx,
                    latex=latex_eq,
                    unicode_text=self._latex_math_to_unicode(latex_eq),
                ))
        return equations

    def _extract_bibliography(self, tex: str, project_dir: str) -> list[Citation]:
        citations = []
        # Try to find .bib file
        bib_m = re.search(r'\\bibliography\{([^}]+)\}', tex)
        if bib_m:
            bib_path = os.path.join(project_dir, bib_m.group(1).strip() + ".bib")
            if os.path.exists(bib_path):
                citations = self._parse_bibtex(bib_path)
        return citations

    def _parse_bibtex(self, bib_path: str) -> list[Citation]:
        citations = []
        try:
            with open(bib_path, "r", encoding="utf-8", errors="replace") as f:
                bib_content = f.read()

            pattern = r'@\w+\{([^,]+),\s*(.*?)\}\s*\n\}'
            for m in re.finditer(pattern, bib_content, re.DOTALL):
                key = m.group(1).strip()
                fields = m.group(2)
                title = self._bib_field(fields, "title")
                authors = self._bib_field(fields, "author")
                year_str = self._bib_field(fields, "year")
                year = int(year_str) if year_str.isdigit() else 0
                venue = self._bib_field(fields, "journal") or self._bib_field(fields, "booktitle") or ""

                citations.append(Citation(
                    key=key,
                    title=title,
                    authors=authors,
                    year=year,
                    venue=venue,
                    raw_bibtex=m.group(0),
                ))
        except Exception:
            pass  # BibTeX parsing is best-effort

        return citations

    def _bib_field(self, text: str, field: str) -> str:
        pattern = field + r'\s*=\s*["{\{]?(.*?)["}\}]?\s*,'
        m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if m:
            return m.group(1).strip()
        return ""

    def _clean_latex(self, text: str) -> str:
        """Strip common LaTeX commands from text for clean reading."""
        # Remove \cite{...}
        text = re.sub(r'\\cite[a-z]*\{[^}]*\}', '', text)
        # Remove \ref{...}
        text = re.sub(r'\\ref\{[^}]*\}', '', text)
        # Remove \label{...}
        text = re.sub(r'\\label\{[^}]*\}', '', text)
        # Simplify common commands
        text = re.sub(r'\\texttt\{([^}]*)\}', r'\1', text)
        text = re.sub(r'\\textit\{([^}]*)\}', r'*\1*', text)
        text = re.sub(r'\\textbf\{([^}]*)\}', r'**\1**', text)
        text = re.sub(r'\\emph\{([^}]*)\}', r'*\1*', text)
        # Remove remaining simple commands
        text = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', text)
        text = re.sub(r'\\[a-zA-Z]+', '', text)
        # Collapse whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        return text.strip()

    def _build_full_text(self, ir: PaperIR) -> str:
        parts = []
        if ir.title:
            parts.append(ir.title)
        if ir.abstract:
            parts.append(ir.abstract)
        for sec in ir.sections:
            if sec.heading:
                parts.append(f"{'#' * sec.level} {sec.heading}")
            if sec.content:
                parts.append(sec.content)
        return "\n\n".join(parts)

    def _detect_language(self, text: str) -> str:
        """Heuristic: count CJK characters in the first 2000 chars."""
        sample = text[:2000]
        cjk_count = sum(1 for c in sample if '一' <= c <= '鿿')
        if cjk_count > 50:
            return "zh"
        elif cjk_count > 10:
            return "mixed"
        return "en"
