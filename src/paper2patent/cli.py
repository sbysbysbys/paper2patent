"""CLI entry point for paper2patent."""

from __future__ import annotations

import sys
import click

from paper2patent.pipeline import PaperToPatentPipeline


@click.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option(
    "-o", "--output-dir",
    default="./patent_output/",
    type=click.Path(),
    help="Output directory (default: ./patent_output/)",
)
@click.option(
    "-t", "--patent-type",
    type=click.Choice(["cn", "us"]),
    default="cn",
    help="Patent type (default: cn)",
)
@click.option(
    "-r", "--reference",
    type=click.Path(exists=True),
    default=None,
    help="Reference .docx patent for style extraction",
)
@click.option(
    "--no-diagrams",
    is_flag=True,
    help="Skip flowchart/block diagram generation",
)
@click.option(
    "--no-figures",
    is_flag=True,
    help="Skip paper figure extraction",
)
@click.option(
    "--llm",
    type=click.Choice(["claude", "openai"]),
    default="claude",
    help="LLM backend for paper analysis (default: claude)",
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    help="Verbose logging",
)
@click.option(
    "--bw-figures",
    is_flag=True,
    help="Convert all figures to black-and-white (CNIPA requirement)",
)
@click.option(
    "--show-format",
    is_flag=True,
    help="Generate a patent format preview .docx with current style settings",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Only generate intermediate JSON/md, skip .docx writing",
)
def main(
    input_path: str,
    output_dir: str,
    patent_type: str,
    reference: str | None,
    no_diagrams: bool,
    no_figures: bool,
    llm: str,
    verbose: bool,
    dry_run: bool,
    bw_figures: bool,
    show_format: bool,
) -> None:
    """
    Convert an academic paper (LaTeX folder or PDF) to a patent .docx file.

    INPUT_PATH: Path to .tex file, LaTeX project folder, or .pdf file.
    """
    pipeline = PaperToPatentPipeline(
        output_dir=output_dir,
        patent_type=patent_type,
        reference_docx=reference,
        generate_diagrams=not no_diagrams,
        extract_figures=not no_figures,
        bw_figures=bw_figures,
        show_format=show_format,
        llm_backend=llm,
        verbose=verbose,
        dry_run=dry_run,
    )

    try:
        pipeline.run(input_path)
    except Exception as e:
        click.secho(f"\nError: {e}", fg="red", err=True)
        if verbose:
            raise
        sys.exit(1)


if __name__ == "__main__":
    main()
