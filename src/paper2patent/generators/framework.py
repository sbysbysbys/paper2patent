"""Generate high-level framework/architecture diagrams."""

from __future__ import annotations

from pathlib import Path

from paper2patent.ir import PaperIR, PaperAnalysis


class FrameworkGenerator:
    """Generate a high-level framework overview diagram.

    Uses graphviz for layout when available, falls back to matplotlib.
    """

    def __init__(self, output_dir: str = "./diagrams/"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, paper_ir: PaperIR, analysis: PaperAnalysis) -> str | None:
        """Generate a framework diagram.

        Returns path to generated file, or None if not enough structure.
        """
        # Try graphviz first
        result = self._generate_graphviz(paper_ir, analysis)
        if result:
            return result

        # Fall back to matplotlib
        return self._generate_matplotlib(paper_ir, analysis)

    def _generate_graphviz(self, paper_ir: PaperIR, analysis: PaperAnalysis) -> str | None:
        """Graphviz-based framework diagram: inputs → processing → outputs."""
        if not analysis.method_steps and not analysis.system_components:
            return None

        try:
            import graphviz
        except ImportError:
            return None

        try:
            dot = graphviz.Digraph(
                "FrameworkOverview",
                format="pdf",
                engine="dot",
            )
        except Exception:
            return None

        dot.attr(rankdir="LR", fontname="Helvetica", fontsize="10", dpi="300")
        dot.attr("node", shape="box", style="rounded,filled", fillcolor="#FFFFFF",
                 fontname="Helvetica", fontsize="9")

        # Input block
        dot.node("input", "输入数据\n(Input)", shape="folder", fillcolor="#E3F2FD")

        # Processing blocks from major sections or components
        if analysis.system_components:
            for i, comp in enumerate(analysis.system_components[:5]):
                dot.node(
                    f"comp_{comp.reference_num}",
                    f"{comp.name}\n({comp.reference_num})",
                )

            # Chain them
            dot.edge("input", f"comp_{analysis.system_components[0].reference_num}")
            for i in range(len(analysis.system_components[:5]) - 1):
                dot.edge(
                    f"comp_{analysis.system_components[i].reference_num}",
                    f"comp_{analysis.system_components[i+1].reference_num}",
                )
            last_comp = analysis.system_components[min(4, len(analysis.system_components) - 1)]
            dot.node("output", "输出结果\n(Output)", shape="folder", fillcolor="#E8F5E9")
            dot.edge(f"comp_{last_comp.reference_num}", "output")
        elif analysis.method_steps:
            # Use method steps as processing chain
            first = analysis.method_steps[0]
            last = analysis.method_steps[-1]

            dot.node("input", "输入", shape="folder", fillcolor="#E3F2FD")
            dot.node(
                "process",
                f"处理流程\n{len(analysis.method_steps)}个步骤",
                shape="cylinder",
            )
            dot.node("output", "输出", shape="folder", fillcolor="#E8F5E9")

            dot.edge("input", "process")
            dot.edge("process", "output")

        # Render
        output_base = str(self.output_dir / "framework")
        try:
            dot.render(output_base, cleanup=True)
            import os
            for ext in [".pdf", ".png"]:
                candidate = f"{output_base}{ext}"
                if os.path.exists(candidate):
                    return candidate
        except Exception:
            pass

        return None

    def _generate_matplotlib(self, paper_ir: PaperIR, analysis: PaperAnalysis) -> str | None:
        """Fallback matplotlib framework diagram."""
        sections = paper_ir.sections
        if not sections and not analysis.method_steps:
            return None

        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
        except ImportError:
            return None

        fig, ax = plt.subplots(figsize=(10, 2.5))
        ax.set_xlim(0, 15)
        ax.set_ylim(0, 3)
        ax.axis("off")

        # Three stages: Input → Core → Output
        stages = [
            {"label": "输入", "x": 1.0, "color": "#E3F2FD"},
            {"label": "处理模块", "x": 7.0, "color": "#FFFFFF"},
            {"label": "输出", "x": 13.0, "color": "#E8F5E9"},
        ]

        for stage in stages:
            rect = FancyBboxPatch(
                (stage["x"] - 2, 0.5), 4, 2,
                boxstyle="round,pad=0.1",
                facecolor=stage["color"],
                edgecolor="black",
                linewidth=1.0,
            )
            ax.add_patch(rect)
            ax.text(stage["x"], 1.5, stage["label"],
                    ha="center", va="center", fontsize=10)

        # Arrows between stages
        for i in range(len(stages) - 1):
            arrow = FancyArrowPatch(
                (stages[i]["x"] + 2, 1.5),
                (stages[i + 1]["x"] - 2, 1.5),
                arrowstyle="->",
                mutation_scale=15,
                linewidth=1.0,
                color="black",
            )
            ax.add_patch(arrow)

        # Add section-based substructure inside the core block
        if sections:
            core_sections = [s for s in sections if s.level <= 2][:4]
            for i, sec in enumerate(core_sections):
                ax.text(
                    7.0, 1.8 - i * 0.3,
                    f"• {sec.heading[:30]}",
                    ha="center", va="center",
                    fontsize=6, color="gray",
                )

        plt.tight_layout()

        pdf_path = str(self.output_dir / "framework.pdf")
        png_path = str(self.output_dir / "framework.png")
        try:
            plt.savefig(pdf_path, dpi=300, bbox_inches="tight")
            plt.savefig(png_path, dpi=300, bbox_inches="tight")
        finally:
            plt.close()

        return pdf_path if Path(pdf_path).exists() else png_path
