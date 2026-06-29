"""Annotate figures with patent reference numerals."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


class FigureAnnotator:
    """Add reference numeral annotations to patent figures."""

    def __init__(self, font_size: int = 14, line_width: int = 2):
        self.font_size = font_size
        self.line_width = line_width
        # Try to find a suitable font
        self.font = self._get_font()

    def _get_font(self):
        """Find a usable font for annotations."""
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",  # macOS
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            "C:\\Windows\\Fonts\\arial.ttf",  # Windows
        ]
        for fp in font_paths:
            if Path(fp).exists():
                try:
                    return ImageFont.truetype(fp, self.font_size)
                except Exception:
                    pass
        return ImageFont.load_default()

    def annotate(
        self,
        image_path: str,
        annotations: list[dict],
        output_path: str,
    ) -> str:
        """Add reference numeral annotations to an image.

        Args:
            image_path: Source image to annotate
            annotations: List of {"num": 10, "x": 100, "y": 200, "label": "组件A"}
            output_path: Where to save annotated image

        Returns:
            Path to annotated image
        """
        img = Image.open(image_path).convert("RGB")
        draw = ImageDraw.Draw(img)

        for ann in annotations:
            x, y = ann["x"], ann["y"]
            num = ann["num"]

            # Draw leader line (short line from label to point)
            label_x = x + 20
            label_y = y - 10
            draw.line(
                [(x, y), (label_x, label_y)],
                fill="black",
                width=self.line_width,
            )

            # Draw reference numeral
            text = str(num)
            bbox = draw.textbbox((label_x, label_y - self.font_size), text, font=self.font)
            # White background for readability
            draw.rectangle(
                [bbox[0] - 2, bbox[1] - 2, bbox[2] + 2, bbox[3] + 2],
                fill="white",
                outline="black",
            )
            draw.text((label_x, label_y - self.font_size), text, fill="black", font=self.font)

        img.save(output_path, dpi=(300, 300))
        return output_path

    def add_reference_numbers_grid(
        self,
        image_path: str,
        components: list[dict],
        output_path: str,
    ) -> str:
        """Auto-position reference numbers for system components.

        Components are arranged in a grid pattern.
        Each component: {"name": str, "num": int, "col": int, "row": int}
        """
        img = Image.open(image_path).convert("RGB")
        w, h = img.size
        draw = ImageDraw.Draw(img)

        # Calculate grid positions
        if components:
            n_cols = max(c.get("col", 1) for c in components)
            n_rows = max(c.get("row", 1) for c in components)
            cell_w = w / (n_cols + 1)
            cell_h = h / (n_rows + 1)

            for comp in components:
                col = comp.get("col", 1)
                row = comp.get("row", 1)

                # Position marker in the center of each cell
                cx = int(cell_w * col)
                cy = int(cell_h * row)

                # Put reference number inside component
                text = str(comp["num"])
                draw.text((cx, cy - 20), f"({text})", fill="black", font=self.font)

        img.save(output_path, dpi=(300, 300))
        return output_path
