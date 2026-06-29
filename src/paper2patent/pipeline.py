"""Main orchestration pipeline — wires all 9 steps together."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from paper2patent.ir import PaperIR, PaperAnalysis, PatentIR, StyleProfile
from paper2patent.parsers.base import BaseParser
from paper2patent.parsers.pdf_parser import PDFParser
from paper2patent.parsers.latex_parser import LaTeXParser

console = Console()


class PaperToPatentPipeline:
    """Orchestrates the 9-step paper → patent conversion."""

    def __init__(
        self,
        output_dir: str = "./patent_output/",
        patent_type: str = "cn",
        reference_docx: Optional[str] = None,
        generate_diagrams: bool = True,
        extract_figures: bool = True,
        bw_figures: bool = False,
        show_format: bool = False,
        llm_backend: str = "claude",
        verbose: bool = False,
        dry_run: bool = False,
    ):
        self.output_dir = Path(output_dir)
        self.patent_type = patent_type
        self.reference_docx = reference_docx
        self.generate_diagrams = generate_diagrams
        self.extract_figures = extract_figures
        self.bw_figures = bw_figures
        self.show_format = show_format
        self.llm_backend = llm_backend
        self.verbose = verbose
        self.dry_run = dry_run

        # Intermediate outputs
        self.paper_ir: Optional[PaperIR] = None
        self.paper_analysis: Optional[PaperAnalysis] = None
        self.patent_ir: Optional[PatentIR] = None
        self.style_profile: Optional[StyleProfile] = None

    def run(self, input_path: str, paper_analysis: Optional[PaperAnalysis] = None) -> Path:
        """Execute the full pipeline and return the output path.

        Args:
            input_path: Path to paper (.pdf or .tex)
            paper_analysis: Pre-computed analysis (skips Step 2 LLM call).
                           When None, attempts LLM with rules fallback.
        """
        input_path = os.path.abspath(input_path)
        self._setup_dirs()

        console.rule("[bold blue]Paper → Patent Conversion Pipeline[/bold blue]")
        console.print(f"Input: [cyan]{input_path}[/cyan]")
        console.print(f"Output dir: [cyan]{self.output_dir}[/cyan]")
        console.print(f"Patent type: [cyan]{self.patent_type.upper()}[/cyan]")
        if self.bw_figures:
            console.print(f"Figure mode: [bold]Black & White[/bold] (CNIPA)")
        else:
            console.print(f"Figure mode: [dim]Color (--bw-figures to enforce B&W)[/dim]")
        console.print()

        # --- Format preview (if --show-format) ---
        if self.show_format:
            self.style_profile = self._step7_style_profile()  # build + store
            fmt_path = self._generate_format_preview()
            console.print(f"[green]✓[/green] Format preview saved to: [cyan]{fmt_path}[/cyan]")
            console.print()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            # Step 1: Parse input → PaperIR
            progress.add_task("[1/9] Parsing input...", total=None)
            self.paper_ir = self._step1_parse(input_path)
            self._save_intermediate("paper_ir.json", self.paper_ir.model_dump())
            self._log("[green]✓[/green] Step 1: Input parsed → PaperIR")

            # Step 2: LLM generates ALL patent text content
            # All paths go through LLM — no rules-based text generation
            progress.add_task("[2/9] LLM generating patent content...", total=None)
            try:
                self.patent_ir, self.paper_analysis = self._step2_llm_generate(paper_analysis)
            except Exception as e:
                console.print(f"\n[bold red]LLM generation failed: {e}[/bold red]")
                console.print("[yellow]Set ANTHROPIC_API_KEY or OPENAI_API_KEY.[/yellow]")
                raise SystemExit(1) from e
            self._save_intermediate("patent_from_llm.json", self.patent_ir.model_dump())
            if self.paper_analysis:
                self._save_intermediate("paper_analysis.json", self.paper_analysis.model_dump())
            self._save_intermediate("claims.md", self._claims_to_markdown())
                self._log("[green]✓[/green] Step 2: LLM generated full patent content")

            # Step 5: Extract & process figures
            if self.extract_figures:
                progress.add_task("[5/9] Extracting figures...", total=None)
                self._step5_figures()
                if self.bw_figures:
                    self._convert_figures_bw()
                self._log("[green]✓[/green] Step 5: Figures extracted")
            else:
                self._log("[dim]○[/dim] Step 5: Figures (skipped)")

            # Step 6: Generate diagrams
            if self.generate_diagrams:
                progress.add_task("[6/9] Generating diagrams...", total=None)
                self._step6_diagrams()
                if self.bw_figures:
                    self._convert_diagrams_bw()
                self._log("[green]✓[/green] Step 6: Diagrams generated")
            else:
                self._log("[dim]○[/dim] Step 6: Diagrams (skipped)")

            # Step 7: Build style profile
            progress.add_task("[7/9] Building style profile...", total=None)
            self.style_profile = self._step7_style_profile()
            self._log("[green]✓[/green] Step 7: Style profile ready")

            # Step 8: Format & assemble .docx
            if not self.dry_run:
                progress.add_task("[8/9] Formatting .docx...", total=None)
                output_path = self._step8_format()
                self._log(f"[green]✓[/green] Step 8: .docx written → {output_path}")
            else:
                output_path = self.output_dir / "patent_dry_run.md"
                self._save_intermediate("patent_structure.md", self._patent_to_markdown())
                self._log("[dim]○[/dim] Step 8: Dry-run (skipped .docx)")

            # Step 9: Validate
            progress.add_task("[9/9] Validating...", total=None)
            report = self._step9_validate()
            self._save_intermediate("validation_report.txt", report)
            self._log("[green]✓[/green] Step 9: Validation complete")

        # Summary
        console.rule("[bold blue]Done[/bold blue]")
        self._print_summary(report)

        return output_path

    # ------------------------------------------------------------------
    # Step implementations (filled in as modules are built)
    # ------------------------------------------------------------------

    def _setup_dirs(self) -> None:
        for sub in ["intermediate", "figures", "diagrams"]:
            (self.output_dir / sub).mkdir(parents=True, exist_ok=True)

    def _save_intermediate(self, filename: str, data) -> None:
        path = self.output_dir / "intermediate" / filename
        if isinstance(data, str):
            path.write_text(data, encoding="utf-8")
        else:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _log(self, msg: str) -> None:
        if self.verbose:
            console.print(msg)

    # ------------------------------------------------------------------
    # Step 1
    # ------------------------------------------------------------------

    def _step1_parse(self, input_path: str) -> PaperIR:
        parser = self._get_parser(input_path)
        return parser.parse(input_path)

    def _get_parser(self, input_path: str) -> BaseParser:
        path = Path(input_path)
        if path.suffix == ".pdf":
            return PDFParser(verbose=self.verbose)
        elif path.suffix == ".tex":
            return LaTeXParser(verbose=self.verbose)
        elif path.is_dir():
            # Look for main .tex file
            tex_files = list(path.glob("*.tex"))
            if tex_files:
                return LaTeXParser(verbose=self.verbose)
            pdf_files = list(path.glob("*.pdf"))
            if pdf_files:
                return PDFParser(verbose=self.verbose)
            raise ValueError(f"No .tex or .pdf found in directory: {input_path}")
        else:
            raise ValueError(f"Unsupported input: {input_path}")

    # ------------------------------------------------------------------
    # Step 2 (new): LLM generates full patent content
    # ------------------------------------------------------------------

    def _step2_llm_generate(self, paper_analysis: Optional[PaperAnalysis] = None):
        """Use LLM to generate complete PatentIR in one call.
        If paper_analysis is provided, it's passed to LLM for higher quality.
        Returns (PatentIR, PaperAnalysis) tuple.
        """
        from paper2patent.converter.llm_generator import LLMGenerator

        generator = LLMGenerator(backend=self.llm_backend, verbose=self.verbose)
        return generator.generate(self.paper_ir, paper_analysis)

    # ------------------------------------------------------------------
    # Step 2 (old): LLM-assisted paper analysis only
    # ------------------------------------------------------------------

    def _step2_analyze(self) -> PaperAnalysis:
        from paper2patent.analyzer.paper_analyzer import PaperAnalyzer

        analyzer = PaperAnalyzer(backend=self.llm_backend, verbose=self.verbose)
        return analyzer.analyze(self.paper_ir)

    # ------------------------------------------------------------------
    # Step 3
    # ------------------------------------------------------------------

    def _step3_structure(self) -> PatentIR:
        from paper2patent.converter.section_mapper import SectionMapper

        mapper = SectionMapper(patent_type=self.patent_type)
        return mapper.map(self.paper_ir, self.paper_analysis)

    # ------------------------------------------------------------------
    # Step 4
    # ------------------------------------------------------------------

    def _step4_claims(self) -> None:
        from paper2patent.converter.claims_generator import ClaimsGenerator

        generator = ClaimsGenerator(patent_type=self.patent_type)
        claims = generator.generate(self.paper_ir, self.paper_analysis)
        self.patent_ir.claims = claims

    # ------------------------------------------------------------------
    # Step 5
    # ------------------------------------------------------------------

    def _step5_figures(self) -> None:
        from paper2patent.figures.extractor import FigureExtractor

        extractor = FigureExtractor(output_dir=str(self.output_dir / "figures"))
        figures_info = extractor.extract(self.paper_ir)
        self.patent_ir.figures = figures_info

    # ------------------------------------------------------------------
    # Step 6
    # ------------------------------------------------------------------

    def _step6_diagrams(self) -> None:
        diag_dir = str(self.output_dir / "diagrams")
        diagrams = []

        # Flowchart
        from paper2patent.generators.flowchart import FlowchartGenerator

        fc = FlowchartGenerator(output_dir=diag_dir)
        fc_path = fc.generate(self.paper_analysis)
        if fc_path:
            diagrams.append({
                "path": fc_path,
                "caption": f"图{len(self.patent_ir.figures) + len(diagrams) + 1} 是本发明方法的流程示意图",
                "type": "flowchart",
            })

        # Block diagram
        from paper2patent.generators.block_diagram import BlockDiagramGenerator

        bd = BlockDiagramGenerator(output_dir=diag_dir)
        bd_path = bd.generate(self.paper_analysis)
        if bd_path:
            diagrams.append({
                "path": bd_path,
                "caption": f"图{len(self.patent_ir.figures) + len(diagrams) + 1} 是本发明系统的结构框图",
                "type": "block_diagram",
            })

        # Framework diagram
        from paper2patent.generators.framework import FrameworkGenerator

        fw = FrameworkGenerator(output_dir=diag_dir)
        fw_path = fw.generate(self.paper_ir, self.paper_analysis)
        if fw_path:
            diagrams.append({
                "path": fw_path,
                "caption": f"图{len(self.patent_ir.figures) + len(diagrams) + 1} 是本发明整体框架示意图",
                "type": "framework",
            })

        self.patent_ir.diagrams = diagrams

    # ------------------------------------------------------------------
    # Step 7
    # ------------------------------------------------------------------

    def _step7_style_profile(self) -> StyleProfile:
        from paper2patent.formatters.styles import build_style_profile

        return build_style_profile(
            patent_type=self.patent_type,
            reference_docx=self.reference_docx,
        )

    # ------------------------------------------------------------------
    # Step 8
    # ------------------------------------------------------------------

    def _step8_format(self) -> Path:
        from paper2patent.formatters.cn_docx import CNDocxWriter

        writer = CNDocxWriter(
            output_dir=str(self.output_dir),
            style_profile=self.style_profile,
        )
        return writer.write(self.patent_ir)

    # ------------------------------------------------------------------
    # Step 9
    # ------------------------------------------------------------------

    def _step9_validate(self) -> str:
        from paper2patent.validator.patent_validator import PatentValidator

        validator = PatentValidator(patent_type=self.patent_type)
        return validator.validate(self.patent_ir)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _claims_to_markdown(self) -> str:
        if not self.patent_ir or not self.patent_ir.claims:
            return ""
        lines = ["# 权利要求书", ""]
        for c in self.patent_ir.claims:
            prefix = f"{c.number}."
            if c.depends_on:
                deps = "或".join(str(d) for d in c.depends_on)
                prefix += f" (引用权利要求{deps})"
            lines.append(f"{prefix} {c.text}")
            lines.append("")
        return "\n".join(lines)

    def _patent_to_markdown(self) -> str:
        if not self.patent_ir:
            return ""
        lines = [f"# {self.patent_ir.title}", ""]
        lines.append(f"## 摘要\n\n{self.patent_ir.abstract}\n")
        for section in self.patent_ir.sections:
            lines.append(f"## {section.heading}\n\n{section.content}\n")
        if self.patent_ir.claims:
            lines.append(self._claims_to_markdown())
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # BW figure conversion
    # ------------------------------------------------------------------

    def _convert_figures_bw(self) -> None:
        """Convert extracted paper figures to black-and-white."""
        if not self.patent_ir or not self.patent_ir.figures:
            return
        from PIL import Image

        for fig_info in self.patent_ir.figures:
            path = fig_info.get("path", "")
            if path and os.path.exists(path):
                try:
                    img = Image.open(path).convert("L")  # grayscale
                    # Increase contrast for patent legibility
                    from PIL import ImageEnhance
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(1.3)
                    img.save(path)
                except Exception:
                    pass
        self._log("[dim]  → Figures converted to B&W[/dim]")

    def _convert_diagrams_bw(self) -> None:
        """Generated diagrams are already B&W by default (graphviz/matplotlib).
        Ensure they are in grayscale mode."""
        if not self.patent_ir or not self.patent_ir.diagrams:
            return
        from PIL import Image

        for diag_info in self.patent_ir.diagrams:
            path = diag_info.get("path", "")
            if path and os.path.exists(path):
                try:
                    img = Image.open(path).convert("L")
                    from PIL import ImageEnhance
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(1.2)
                    img.save(path)
                except Exception:
                    pass
        self._log("[dim]  → Diagrams converted to B&W[/dim]")

    # ------------------------------------------------------------------
    # Format preview document
    # ------------------------------------------------------------------

    def _generate_format_preview(self) -> Path:
        """Generate a standalone .docx showing current patent format settings."""
        from paper2patent.formatters.cn_docx import CNDocxWriter

        writer = CNDocxWriter(
            output_dir=str(self.output_dir),
            style_profile=self.style_profile,
        )
        return writer.write_format_preview()

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def _print_summary(self, report: str) -> None:
        table = Table(title="Conversion Summary")
        table.add_column("Item", style="cyan")
        table.add_column("Details", style="green")

        if self.paper_ir:
            table.add_row("Input", self.paper_ir.title or "(untitled)")
            table.add_row("Sections", str(len(self.paper_ir.sections)))
            table.add_row("Figures found", str(len(self.paper_ir.figures)))

        if self.patent_ir:
            table.add_row("Claims generated", str(len(self.patent_ir.claims)))
            table.add_row("Patent sections", str(len(self.patent_ir.sections)))

        if not self.dry_run:
            table.add_row("Output", str(self.output_dir / f"专利说明书_{self.patent_ir.title if self.patent_ir else 'output'}.docx"))

        table.add_row("Intermediate files", str(self.output_dir / "intermediate/"))

        console.print(table)
        if report.strip():
            console.print("\n[bold]Validation:[/bold]")
            console.print(report)
