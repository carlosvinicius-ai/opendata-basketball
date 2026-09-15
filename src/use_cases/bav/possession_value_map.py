"""Possession Value Map (xT Analogue for Basketball).

Maps Ball Action Value (BAV) onto a 2D spatial grid of the offensive half-court,
visualizing where actions generate the highest marginal scoring probability.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
from scipy.ndimage import gaussian_filter


@dataclass(frozen=True)
class CourtGridConfig:
    """Dimensions and resolution for the half-court spatial grid in meters."""

    x_bins: int = 14  # Length of half-court (14m)
    y_bins: int = 15  # Width of court (15m, from -7.5 to +7.5)
    x_min: float = 0.0
    x_max: float = 14.0
    y_min: float = -7.5
    y_max: float = 7.5
    sigma_smooth: float = 1.0


class PossessionValueMap:
    """Generates and analyzes 2D spatial grids of expected possession value."""

    def __init__(self, config: CourtGridConfig | None = None) -> None:
        self.config = config or CourtGridConfig()

    def compute_grid(self, actions_df: pl.DataFrame) -> dict[str, Any]:
        """Compute the 2D possession value grid from scored actions.

        Args:
            actions_df: DataFrame containing 'start_x', 'start_y', and 'bav_value'.

        Returns:
            Dictionary containing:
            - 'grid': 2D numpy array [x_bins, y_bins] with smoothed mean BAV
            - 'counts': 2D numpy array with action sample counts per cell
            - 'hotspots': Top spatial zones with highest positive BAV value
        """
        cfg = self.config
        grid_sum = np.zeros((cfg.x_bins, cfg.y_bins), dtype=np.float64)
        grid_count = np.zeros((cfg.x_bins, cfg.y_bins), dtype=np.int32)

        # Identify coordinate column names
        x_col = "ball_x" if "ball_x" in actions_df.columns else ("start_x" if "start_x" in actions_df.columns else None)
        y_col = "ball_y" if "ball_y" in actions_df.columns else ("start_y" if "start_y" in actions_df.columns else None)

        if not x_col or not y_col or "bav_value" not in actions_df.columns:
            return {
                "grid": grid_sum.tolist(),
                "counts": grid_count.tolist(),
                "hotspots": [],
            }

        # Filter actions with valid coordinates and BAV values
        valid = actions_df.filter(
            pl.col(x_col).is_not_null()
            & pl.col(y_col).is_not_null()
            & pl.col("bav_value").is_not_null()
        )

        if valid.is_empty():
            return {
                "grid": grid_sum.tolist(),
                "counts": grid_count.tolist(),
                "hotspots": [],
            }

        # Convert coordinates to grid indices
        for row in valid.iter_rows(named=True):
            raw_x = float(row[x_col])
            raw_y = float(row[y_col])
            bav = float(row["bav_value"])

            # Map from court feet to meters if magnitude suggests feet (>15m)
            if abs(raw_x) > 15.0 or abs(raw_y) > 8.0:
                raw_x = abs(raw_x) * 0.3048
                raw_y = raw_y * 0.3048
            else:
                raw_x = abs(raw_x)

            # Clamp to grid bounds
            x_norm = np.clip(raw_x, cfg.x_min, cfg.x_max - 1e-4)
            y_norm = np.clip(raw_y, cfg.y_min, cfg.y_max - 1e-4)

            i = int((x_norm - cfg.x_min) / (cfg.x_max - cfg.x_min) * cfg.x_bins)
            j = int((y_norm - cfg.y_min) / (cfg.y_max - cfg.y_min) * cfg.y_bins)

            grid_sum[i, j] += bav
            grid_count[i, j] += 1

        # Mean BAV per cell
        grid_mean = np.zeros_like(grid_sum)
        mask = grid_count > 0
        grid_mean[mask] = grid_sum[mask] / grid_count[mask]

        # Apply Gaussian smoothing over the surface
        smoothed_grid = gaussian_filter(grid_mean, sigma=cfg.sigma_smooth)

        # Identify top 5 hotspots
        hotspots = []
        flat_indices = np.argsort(smoothed_grid.ravel())[::-1][:5]
        for idx in flat_indices:
            r, c = divmod(int(idx), cfg.y_bins)
            hotspots.append({
                "x_bin": r,
                "y_bin": c,
                "x_meters": round(cfg.x_min + (r + 0.5) * (cfg.x_max - cfg.x_min) / cfg.x_bins, 2),
                "y_meters": round(cfg.y_min + (c + 0.5) * (cfg.y_max - cfg.y_min) / cfg.y_bins, 2),
                "bav_expected": round(float(smoothed_grid[r, c]), 4),
                "actions_count": int(grid_count[r, c]),
            })

        return {
            "grid": smoothed_grid.tolist(),
            "counts": grid_count.tolist(),
            "hotspots": hotspots,
        }

    def save_heatmap_plot(
        self,
        grid_result: dict[str, Any],
        output_path: str = "reports/assets/possession_value_map.png",
    ) -> str:
        """Render and save a court heatmap visualization of the possession value grid."""
        import matplotlib.pyplot as plt

        grid = np.array(grid_result["grid"])
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        fig, ax = plt.subplots(figsize=(8, 7), facecolor="#0f172a")
        ax.set_facecolor("#0f172a")

        im = ax.imshow(
            grid.T,
            origin="lower",
            extent=[self.config.x_min, self.config.x_max, self.config.y_min, self.config.y_max],
            cmap="inferno",
            aspect="equal",
        )
        cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label("Expected Ball Action Value (ΔP)", color="#f8fafc", fontsize=10)
        cbar.ax.yaxis.set_tick_params(color="#f8fafc")
        plt.setp(plt.getp(cbar.ax.axes, "yticklabels"), color="#94a3b8")

        # Hoop reference
        ax.plot([1.575], [0.0], "o", color="#ef4444", markersize=10, label="Basket")

        ax.set_title("Possession Value Map (xT Analogue) — FIBA Half-Court", color="#f8fafc", fontsize=12, pad=12)
        ax.set_xlabel("Distance from Baseline (m)", color="#94a3b8", fontsize=10)
        ax.set_ylabel("Lateral Distance from Center (m)", color="#94a3b8", fontsize=10)
        ax.tick_params(colors="#94a3b8")
        ax.grid(color="#334155", linestyle="--", alpha=0.4)

        plt.tight_layout()
        plt.savefig(out, dpi=150, facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close(fig)

        return str(out)
