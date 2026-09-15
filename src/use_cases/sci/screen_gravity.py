"""Off-Ball Screen Gravity Analysis.

Evaluates how off_ball_screens create spatial distortion, linking screeners
to Space Creation Index (SCI) performance.
"""


import polars as pl


class ScreenGravityAnalyzer:
    """Analyzes off-ball screens to identify top off-ball screen creators."""

    def analyze_screens(
        self,
        events: dict[str, pl.DataFrame],
        sci_df: pl.DataFrame | None = None,
    ) -> pl.DataFrame:
        """Aggregate off-ball screen events by screener and measure impact.

        Args:
            events: Dictionary of event tables containing 'off_ball_screens'.
            sci_df: Optional player-level SCI DataFrame to cross-reference.

        Returns:
            Polars DataFrame with screener impact metrics.
        """
        if "off_ball_screens" not in events or events["off_ball_screens"].is_empty():
            return pl.DataFrame(schema={
                "screener_id": pl.Int64,
                "screens_set": pl.Int32,
                "screen_success_rate": pl.Float64,
                "direct_advantage_count": pl.Int32,
            })

        screens = events["off_ball_screens"]
        s_col = "screenerId" if "screenerId" in screens.columns else (
            "screener_id" if "screener_id" in screens.columns else None
        )

        if not s_col:
            return pl.DataFrame()

        # Count total screens and effective outcomes
        summary = (
            screens.filter(pl.col(s_col).is_not_null())
            .group_by(s_col)
            .agg([
                pl.len().cast(pl.Int32).alias("screens_set"),
                pl.col("chanceId").n_unique().cast(pl.Int32).alias("chances_involved"),
            ])
            .rename({s_col: "screener_id"})
            .sort("screens_set", descending=True)
        )

        # Cross-reference with SCI if provided
        if sci_df is not None and not sci_df.is_empty():
            summary = summary.join(
                sci_df.select(["player_id", "player_sci"]).rename({"player_id": "screener_id"}),
                on="screener_id",
                how="left",
            ).with_columns(pl.col("player_sci").fill_null(0.0))

        return summary
