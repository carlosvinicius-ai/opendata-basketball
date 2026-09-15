"""Drive Spacing Analysis.

Investigates whether players with high drive rates create or compress spacing,
testing the empirical correlation between drive volume and off-ball SCI.
"""

from typing import Any

import polars as pl
from scipy.stats import spearmanr


class DriveSpacingAnalyzer:
    """Analyzes the interaction between dribble penetration (drives) and spacing."""

    def evaluate_drive_spacing(
        self,
        events: dict[str, pl.DataFrame],
        fspv_df: pl.DataFrame,
    ) -> dict[str, Any]:
        """Compute correlation between drive volume/blowby rate and SCI score.

        Args:
            events: Dictionary containing 'drives' table.
            fspv_df: Leaderboard DataFrame with 'player_id' and 'sci_score'.

        Returns:
            Dictionary with correlation coefficient, p-value, and top penetration creators.
        """
        if "drives" not in events or events["drives"].is_empty():
            return {
                "drive_sci_correlation": 0.0,
                "p_value": 1.0,
                "sample_size": 0,
                "verdict": "Insufficient drive events",
            }

        drives = events["drives"]
        p_col = "playerId" if "playerId" in drives.columns else "ballhandlerId"

        if p_col not in drives.columns:
            return {"sample_size": 0, "verdict": "Player ID missing in drives"}

        drive_counts = (
            drives.filter(pl.col(p_col).is_not_null())
            .group_by(p_col)
            .agg([
                pl.len().cast(pl.Int32).alias("total_drives"),
                pl.col("blowby").sum().cast(pl.Int32).alias("blowby_count")
                if "blowby" in drives.columns else pl.lit(0).alias("blowby_count"),
            ])
            .rename({p_col: "player_id"})
        )

        merged = fspv_df.join(drive_counts, on="player_id", how="inner")

        if len(merged) < 5:
            return {
                "drive_sci_correlation": 0.0,
                "p_value": 1.0,
                "sample_size": len(merged),
                "verdict": "Sample too small for correlation",
            }

        stat, pval = spearmanr(merged["total_drives"].to_numpy(), merged["sci_score"].to_numpy())

        verdict = (
            "Drives actively expand team spacing (positive gravity)"
            if stat > 0.1
            else "Drives compress paint geometry without external spacing benefits"
        )

        return {
            "drive_sci_correlation": round(float(stat), 4),
            "p_value": round(float(pval), 4),
            "sample_size": len(merged),
            "verdict": verdict,
        }
