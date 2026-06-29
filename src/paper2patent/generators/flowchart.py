"""Generate patent-style method flowcharts using graphviz."""

from __future__ import annotations

import os
from pathlib import Path

from paper2patent.ir import PaperAnalysis


class FlowchartGenerator:
    """Generate a patent method flowchart from method steps."""

    def __init__(self, output_dir: str = "./diagrams/"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, analysis: PaperAnalysis) -> str | None:
        """Generate a flowchart from PaperAnalysis.method_steps.

        Returns path to generated PDF, or None if no steps available.
        """
        if not analysis.method_steps:
            return None

        try:
            import graphviz
        except ImportError:
            return None

        # Find graphviz binary
        try:
            dot = graphviz.Digraph(
                "MethodFlowchart",
                format="pdf",
                engine="dot",
            )
        except Exception:
            # graphviz not installed at system level
            return None

        # Styling for patent figures
        dot.attr(
            rankdir="TB",
            fontname="Helvetica",
            fontsize="10",
            dpi="300",
            nodesep="0.4",
            ranksep="0.6",
        )

        # Node style
        dot.attr(
            "node",
            shape="box",
            style="rounded,filled",
            fillcolor="#FFFFFF",
            fontname="Helvetica",
            fontsize="9",
            margin="0.15,0.1",
        )

        # Start node
        dot.node("start", "开始", shape="ellipse", style="filled", fillcolor="#F0F0F0")

        prev_node = "start"

        for i, step in enumerate(analysis.method_steps):
            node_id = f"step_{step.reference_num}"

            # Build label: step description + reference number
            desc = step.description
            if len(desc) > 60:
                # Wrap long descriptions
                desc_lines = self._wrap_text(desc, 20)
                label = f"{desc_lines}\n({step.reference_num})"
            else:
                label = f"{desc}\n({step.reference_num})"

            # Use diamond for conditional/branch steps
            if any(kw in desc for kw in ("判断", "确定", "选择", "比较", "如果", "是否", "if", "select", "compare", "determine")):
                dot.node(node_id, label, shape="diamond", style="filled", fillcolor="#FFF8E1")
            else:
                dot.node(node_id, label)

            dot.edge(prev_node, node_id)

            # Check if this step could have multiple outcomes (generates branches)
            if any(kw in desc for kw in ("判断", "是否", "如果", "if", "whether")):
                yes_id = f"step_{step.reference_num}_yes"
                dot.node(yes_id, "是", shape="point", width="0.1")
                no_node = f"step_{step.reference_num}_no"
                dot.node(no_node, "否", shape="point", width="0.1")
                dot.edge(node_id, yes_id, "是")
                dot.edge(node_id, no_node, "否", style="dashed")

            prev_node = node_id

        # End node
        dot.node("end", "结束", shape="ellipse", style="filled", fillcolor="#F0F0F0")
        dot.edge(prev_node, "end")

        # Render
        output_base = str(self.output_dir / "flow_method")
        try:
            dot.render(output_base, cleanup=True)
            pdf_path = f"{output_base}.pdf"
            if os.path.exists(pdf_path):
                return pdf_path
            # Try PNG fallback
            png_path = f"{output_base}.png"
            if os.path.exists(png_path):
                return png_path
        except Exception:
            pass

        return None

    def _wrap_text(self, text: str, chars_per_line: int = 20) -> str:
        """Wrap Chinese/English text to specified width."""
        lines = []
        current_line = ""
        current_len = 0

        for char in text:
            char_width = 2 if '一' <= char <= '鿿' else 1
            if current_len + char_width > chars_per_line:
                lines.append(current_line)
                current_line = char
                current_len = char_width
            else:
                current_line += char
                current_len += char_width

        if current_line:
            lines.append(current_line)

        return "\n".join(lines)
