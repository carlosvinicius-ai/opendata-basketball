"""Normalizer for player valuation metrics (BAV and SCI).

Transforms raw marginal on-ball and off-ball contributions into standardized
z-scores (mean=0, std=1) and per-possession rates across the sampled games.
"""

import polars as pl


def compute_z_scores(
    df: pl.DataFrame,
    col: str,
    out_col: str | None = None,
) -> pl.DataFrame:
    """Compute z-score normalization for a given column in a Polars DataFrame.

    Handles zero standard deviation or empty DataFrame edge cases gracefully.
    """
    if df.is_empty() or col not in df.columns:
        return df

    target_col = out_col or f"{col}_z"
    mean_val = df[col].mean()
    std_val = df[col].std()

    if mean_val is None or std_val is None or std_val == 0.0:
        return df.with_columns(pl.lit(0.0).alias(target_col))

    return df.with_columns(
        ((pl.col(col) - mean_val) / std_val).alias(target_col)
    )


class PlayerValueNormalizer:
    """Normalizes BAV and SCI scores to standardized scales for fair combination."""

    def normalize_bav(self, bav_df: pl.DataFrame) -> pl.DataFrame:
        """Normalize BAV ratings, computing per-possession rate if needed.

        Expects columns like 'player_id' and 'player_bav' (or 'bav_sum' & 'possessions_played').
        """
        if bav_df.is_empty():
            return bav_df

        working_df = bav_df
        # If per-possession rate is not present but totals exist, compute it
        if "bav_per_possession" not in working_df.columns:
            if "bav_sum" in working_df.columns and "possessions_played" in working_df.columns:
                working_df = working_df.with_columns(
                    pl.when(pl.col("possessions_played") > 0)
                    .then(pl.col("bav_sum") / pl.col("possessions_played"))
                    .otherwise(0.0)
                    .alias("bav_per_possession")
                )
            elif "player_bav" in working_df.columns:
                working_df = working_df.with_columns(
                    pl.col("player_bav").alias("bav_per_possession")
                )
            else:
                working_df = working_df.with_columns(pl.lit(0.0).alias("bav_per_possession"))

        return compute_z_scores(working_df, col="bav_per_possession", out_col="bav_z")

    def normalize_sci(self, sci_df: pl.DataFrame) -> pl.DataFrame:
        """Normalize SCI ratings to z-scores.

        Expects columns like 'player_id' and 'player_sci'.
        """
        if sci_df.is_empty():
            return sci_df

        working_df = sci_df
        if "player_sci" not in working_df.columns:
            if "sci_value" in working_df.columns:
                working_df = working_df.with_columns(pl.col("sci_value").alias("player_sci"))
            else:
                working_df = working_df.with_columns(pl.lit(0.0).alias("player_sci"))

        return compute_z_scores(working_df, col="player_sci", out_col="sci_z")

    def normalize_both(
        self,
        bav_df: pl.DataFrame,
        sci_df: pl.DataFrame,
    ) -> tuple[pl.DataFrame, pl.DataFrame]:
        """Normalize both BAV and SCI DataFrames."""
        norm_bav = self.normalize_bav(bav_df)
        norm_sci = self.normalize_sci(sci_df)
        return norm_bav, norm_sci
