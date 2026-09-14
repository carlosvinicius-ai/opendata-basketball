"""Chart generator for static visualization assets in the presentation layer.

Generates radar plots, percentile distributions, and renders them to PNG files
or Base64 data URIs for inline embedding in standalone HTML5 reports.
Respects Clean Architecture: does NOT import directly from domain.
"""

import base64
import io
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


class ChartsGenerator:
    """Produces static charts and figures for reports."""

    def __init__(self, output_dir: str = "reports/assets") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def fig_to_base64(self, fig: plt.Figure) -> str:
        """Convert a matplotlib Figure to a base64 encoded PNG data URI string."""
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=130, facecolor=fig.get_facecolor(), edgecolor="none")
        buf.seek(0)
        img_b64 = base64.b64encode(buf.read()).decode("utf-8")
        plt.close(fig)
        return f"data:image/png;base64,{img_b64}"

    def generate_positional_radar(
        self,
        position_averages: dict[str, dict[str, float]],
        save_png: bool = True,
        filename: str = "position_radar.png",
    ) -> str:
        """Generate a polar radar chart comparing BAV and SCI averages by player position.

        Args:
            position_averages: Mapping like {'PG': {'bav': 0.8, 'sci': 0.2}, ...}
            save_png: Whether to save the image to disk.
            filename: Name of the output image.

        Returns:
            Base64 data URI string of the chart.
        """
        positions = list(position_averages.keys())
        if not positions:
            positions = ["PG", "SG", "SF", "PF", "C"]
            position_averages = {p: {"bav": 0.0, "sci": 0.0} for p in positions}

        n_categories = len(positions)
        angles = np.linspace(0, 2 * np.pi, n_categories, endpoint=False).tolist()
        angles += angles[:1]

        bav_vals = [position_averages.get(p, {}).get("bav", 0.0) for p in positions]
        bav_vals += bav_vals[:1]

        sci_vals = [position_averages.get(p, {}).get("sci", 0.0) for p in positions]
        sci_vals += sci_vals[:1]

        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={"polar": True})
        fig.patch.set_facecolor("#18181b")
        ax.set_facecolor("#18181b")

        ax.plot(angles, bav_vals, color="#38bdf8", linewidth=2.0, label="On-Ball (BAV)")
        ax.fill(angles, bav_vals, color="#38bdf8", alpha=0.25)

        ax.plot(angles, sci_vals, color="#a855f7", linewidth=2.0, label="Off-Ball (SCI)")
        ax.fill(angles, sci_vals, color="#a855f7", alpha=0.25)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(positions, color="#e4e4e7", fontsize=11, fontweight="bold")
        ax.tick_params(colors="#a1a1aa", pad=10)
        ax.grid(color="#3f3f46", linestyle="--", linewidth=0.8)

        ax.legend(
            loc="upper right",
            bbox_to_anchor=(1.25, 1.15),
            facecolor="#27272a",
            edgecolor="#3f3f46",
            labelcolor="#f4f4f5",
        )
        ax.set_title("Positional Archetypes: BAV vs SCI", color="#f4f4f5", fontsize=13, fontweight="bold", pad=20)

        if save_png:
            out_path = self.output_dir / filename
            fig.savefig(out_path, format="png", bbox_inches="tight", dpi=130, facecolor=fig.get_facecolor())

        return self.fig_to_base64(fig)

    def generate_percentile_dotplot(
        self,
        player_records: list[dict[str, Any]],
        top_n: int = 15,
        save_png: bool = True,
        filename: str = "percentile_distribution.png",
    ) -> str:
        """Generate a horizontal dot plot showing Top N players across FSPV percentiles."""
        top_players = sorted(player_records, key=lambda r: float(r.get("fspv_score", 0.0)), reverse=True)[:top_n]
        top_players.reverse()

        names = [p.get("player_name", f"Player #{p.get('player_id')}") for p in top_players]
        fspv_scores = [float(p.get("fspv_score", 0.0)) for p in top_players]
        bav_scores = [float(p.get("bav_score", 0.0)) for p in top_players]
        sci_scores = [float(p.get("sci_score", 0.0)) for p in top_players]

        fig, ax = plt.subplots(figsize=(8, 6))
        fig.patch.set_facecolor("#18181b")
        ax.set_facecolor("#18181b")

        y_positions = np.arange(len(names))

        ax.hlines(y=y_positions, xmin=np.minimum(bav_scores, sci_scores), xmax=np.maximum(bav_scores, sci_scores), color="#52525b", linewidth=1.5, alpha=0.7)
        ax.scatter(bav_scores, y_positions, color="#38bdf8", s=60, label="BAV z-score", zorder=3)
        ax.scatter(sci_scores, y_positions, color="#a855f7", s=60, label="SCI z-score", zorder=3)
        ax.scatter(fspv_scores, y_positions, color="#22c55e", s=100, marker="D", label="FSPV (Combined)", zorder=4)

        ax.set_yticks(y_positions)
        ax.set_yticklabels(names, color="#e4e4e7", fontsize=10)
        ax.tick_params(colors="#a1a1aa")
        ax.grid(color="#27272a", linestyle=":", linewidth=0.8, axis="x")

        for spine in ax.spines.values():
            spine.set_color("#3f3f46")

        ax.set_xlabel("Standardized Z-Score", color="#a1a1aa", fontsize=10, labelpad=8)
        ax.set_title(f"Top {top_n} Full Spectrum Player Value Breakdown", color="#f4f4f5", fontsize=12, fontweight="bold", pad=12)
        ax.legend(facecolor="#27272a", edgecolor="#3f3f46", labelcolor="#f4f4f5", loc="lower right")

        if save_png:
            out_path = self.output_dir / filename
            fig.savefig(out_path, format="png", bbox_inches="tight", dpi=130, facecolor=fig.get_facecolor())

        return self.fig_to_base64(fig)
