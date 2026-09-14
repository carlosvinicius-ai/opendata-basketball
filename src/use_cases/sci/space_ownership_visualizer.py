"""Space Ownership Visualizer using Voronoi Tessellation.

Calculates and visualizes player space ownership and effective court control
weighted by proximity to the offensive hoop.
"""

import math
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")  # Non-interactive backend for headless environments
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Arc, Circle, Rectangle
from scipy.spatial import Voronoi

from domain.constants import (
    COURT_LENGTH_FT,
    COURT_WIDTH_FT,
    OFFENSIVE_HOOP_X_FT,
    OFFENSIVE_HOOP_Y_FT,
)


class SpaceOwnershipVisualizer:
    """Computes bounded Voronoi spatial control and renders court visualizations."""

    def __init__(self, output_dir: str = "outputs/reports/sci_voronoi") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.half_length = COURT_LENGTH_FT / 2.0
        self.half_width = COURT_WIDTH_FT / 2.0

    def compute_voronoi_areas(
        self,
        player_coords: list[tuple[float, float]],
        player_ids: list[int | None] | None = None,
        is_offense_flags: list[bool] | None = None,
    ) -> list[dict[str, Any]]:
        """Calculate bounded Voronoi areas and hoop-weighted space ownership.

        Args:
            player_coords: List of (x, y) coordinates for players in feet.
            player_ids: Optional player IDs matching player_coords.
            is_offense_flags: Optional offensive team indicators.

        Returns:
            List of dicts containing player_id, area_sqft, and weighted_space.
        """
        n_players = len(player_coords)
        if n_players < 3:
            return []

        # Add 4 bounding boundary points to close infinite Voronoi regions
        bounds_pad = 20.0
        bx_min, bx_max = -self.half_length - bounds_pad, self.half_length + bounds_pad
        by_min, by_max = -self.half_width - bounds_pad, self.half_width + bounds_pad
        dummy_points = [
            (bx_min, by_min),
            (bx_min, by_max),
            (bx_max, by_min),
            (bx_max, by_max),
        ]

        all_points = np.array(player_coords + dummy_points)
        vor = Voronoi(all_points)

        results: list[dict[str, Any]] = []

        for i in range(n_players):
            region_idx = vor.point_region[i]
            region = vor.regions[region_idx]

            # Approximate area for bounded polygon
            if -1 in region or len(region) < 3:
                area = 100.0  # Fallback reasonable default if region open
            else:
                polygon = vor.vertices[region]
                # Clip vertices to court boundaries
                clipped_x = np.clip(polygon[:, 0], -self.half_length, self.half_length)
                clipped_y = np.clip(polygon[:, 1], -self.half_width, self.half_width)

                # Shoelace formula for polygon area
                x = clipped_x
                y = clipped_y
                area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))

            px, py = player_coords[i]
            dist_to_hoop = math.hypot(px - OFFENSIVE_HOOP_X_FT, py - OFFENSIVE_HOOP_Y_FT)
            # Weighted by inverse distance to hoop (space closer to hoop is exponentially more valuable)
            hoop_weight = 25.0 / max(5.0, dist_to_hoop)
            weighted_space = float(area * hoop_weight)

            pid = player_ids[i] if player_ids and i < len(player_ids) else None
            is_off = is_offense_flags[i] if is_offense_flags and i < len(is_offense_flags) else True

            results.append({
                "player_id": pid,
                "coord": (px, py),
                "area_sqft": float(area),
                "dist_to_hoop": float(dist_to_hoop),
                "weighted_space": weighted_space,
                "is_offense": is_off,
            })

        return results

    def plot_voronoi_court(
        self,
        player_coords: list[tuple[float, float]],
        player_ids: list[int | None] | None = None,
        is_offense_flags: list[bool] | None = None,
        filename: str = "voronoi_ownership.png",
        title: str = "Space Creation & Court Ownership (Voronoi)",
    ) -> str:
        """Render and save a court heatmap of space ownership.

        Args:
            player_coords: List of (x, y) coordinates for players.
            player_ids: Player IDs.
            is_offense_flags: True if player is on offense.
            filename: Output PNG filename.
            title: Chart title.

        Returns:
            String path to generated image file.
        """
        metrics = self.compute_voronoi_areas(
            player_coords,
            player_ids,
            is_offense_flags,
        )

        fig, ax = plt.subplots(figsize=(12, 7))
        ax.set_facecolor("#121212")
        fig.patch.set_facecolor("#121212")

        # Draw FIBA Basketball Half Court lines
        court_rect = Rectangle(
            (-self.half_length, -self.half_width),
            COURT_LENGTH_FT,
            COURT_WIDTH_FT,
            fill=False,
            color="#555555",
            lw=2,
        )
        ax.add_patch(court_rect)

        # Center line
        ax.plot([0, 0], [-self.half_width, self.half_width], color="#555555", lw=1.5)
        # Center circle
        center_circle = Circle((0, 0), radius=5.9, fill=False, color="#555555", lw=1.5)
        ax.add_patch(center_circle)

        # Offensive Hoop & Backboard
        hoop = Circle((OFFENSIVE_HOOP_X_FT, OFFENSIVE_HOOP_Y_FT), radius=0.75, fill=True, color="#FFA726")
        ax.add_patch(hoop)
        ax.plot(
            [OFFENSIVE_HOOP_X_FT + 1.31, OFFENSIVE_HOOP_X_FT + 1.31],
            [-3.0, 3.0],
            color="#FFFFFF",
            lw=2,
        )

        # 3-Point Arc
        three_arc = Arc(
            (OFFENSIVE_HOOP_X_FT, OFFENSIVE_HOOP_Y_FT),
            width=44.3,
            height=44.3,
            angle=0,
            theta1=90,
            theta2=270,
            color="#777777",
            lw=1.5,
            linestyle="--",
        )
        ax.add_patch(three_arc)

        # Plot players and space bubbles
        for m in metrics:
            px, py = m["coord"]
            is_off = m["is_offense"]
            color = "#29B6F6" if is_off else "#EF5350"
            size = min(1500, max(200, m["area_sqft"] * 5.0))

            # Space bubble
            ax.scatter(px, py, s=size, color=color, alpha=0.25, edgecolors="none")
            # Player dot
            ax.scatter(px, py, s=120, color=color, edgecolors="#FFFFFF", lw=1.5)

            pid_label = str(m["player_id"]) if m["player_id"] else ""
            ax.annotate(
                f"{pid_label}\n{m['weighted_space']:.1f}",
                (px, py),
                color="#FFFFFF",
                fontsize=8,
                ha="center",
                va="center",
                weight="bold",
            )

        ax.set_xlim(-self.half_length - 2, self.half_length + 2)
        ax.set_ylim(-self.half_width - 2, self.half_width + 2)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(title, color="#FFFFFF", fontsize=14, weight="bold", pad=15)

        target_path = self.output_dir / filename
        plt.tight_layout()
        plt.savefig(target_path, dpi=150, facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close(fig)

        return str(target_path)
