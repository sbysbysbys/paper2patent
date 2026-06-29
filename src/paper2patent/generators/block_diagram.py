"""Generate patent-style system block diagrams using matplotlib."""

from __future__ import annotations

from pathlib import Path

from paper2patent.ir import PaperAnalysis


class BlockDiagramGenerator:
    """Generate a system architecture block diagram from system components."""

    def __init__(self, output_dir: str = "./diagrams/"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, analysis: PaperAnalysis) -> str | None:
        """Generate a block diagram from PaperAnalysis.system_components.

        Returns path to generated PDF/PNG, or None if no components.
        """
        if not analysis.system_components:
            return None

        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
        except ImportError:
            return None

        components = analysis.system_components

        # Layout calculation
        n = len(components)
        if n <= 3:
            cols = n
            rows = 1
        elif n <= 6:
            cols = 3
            rows = (n + 2) // 3
        else:
            cols = 4
            rows = (n + 3) // 4

        fig_width = max(8, cols * 3.5)
        fig_height = max(4, rows * 2.5)

        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        ax.set_xlim(0, cols + 1)
        ax.set_ylim(0, rows + 1)
        ax.axis("off")
        ax.set_aspect("equal")

        block_w = 0.9
        block_h = 0.55

        patches = []
        for i, comp in enumerate(components):
            col = i % cols + 1
            row = rows - (i // cols)

            x = col - block_w / 2
            y = row - block_h / 2

            rect = FancyBboxPatch(
                (x, y), block_w, block_h,
                boxstyle="round,pad=0.05",
                facecolor="#F5F5F5",
                edgecolor="black",
                linewidth=1.2,
            )
            ax.add_patch(rect)

            # Component name + reference number
            label = f"{comp.name}\n({comp.reference_num})"
            ax.text(
                col, row, label,
                ha="center", va="center",
                fontsize=8,
                fontfamily="sans-serif",
            )

            patches.append((i, col, row, comp))

        # Draw connections between components
        for i, col, row, comp in patches:
            for conn_idx in comp.connections:
                if conn_idx < len(components) and conn_idx != i:
                    target = patches[conn_idx]
                    t_col, t_row = target[1], target[2]

                    # Determine arrow direction
                    if row == t_row and col < t_col:
                        # Left-to-right
                        arrow = FancyArrowPatch(
                            (col + block_w / 2, row),
                            (t_col - block_w / 2, t_row),
                            arrowstyle="->",
                            mutation_scale=12,
                            linewidth=0.8,
                            color="black",
                        )
                    elif row > t_row:
                        # Bottom-to-top
                        arrow = FancyArrowPatch(
                            (col, row + block_h / 2),
                            (t_col, t_row - block_h / 2),
                            arrowstyle="->",
                            mutation_scale=12,
                            linewidth=0.8,
                            color="black",
                        )
                    else:
                        # Top-to-bottom
                        arrow = FancyArrowPatch(
                            (col, row - block_h / 2),
                            (t_col, t_row + block_h / 2),
                            arrowstyle="->",
                            mutation_scale=12,
                            linewidth=0.8,
                            color="black",
                        )
                    ax.add_patch(arrow)

        # Title
        ax.set_title("系统结构框图", fontsize=12, fontfamily="sans-serif", pad=10)

        plt.tight_layout()

        # Save as PDF (vector) + PNG fallback
        pdf_path = str(self.output_dir / "block_system.pdf")
        png_path = str(self.output_dir / "block_system.png")
        try:
            plt.savefig(pdf_path, dpi=300, bbox_inches="tight")
            plt.savefig(png_path, dpi=300, bbox_inches="tight")
        finally:
            plt.close()

        return pdf_path if Path(pdf_path).exists() else png_path
