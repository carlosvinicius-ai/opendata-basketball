"""Player value combiner for Full Spectrum Player Value (FSPV).

Combines on-ball (BAV) and off-ball (SCI) standardized ratings into a single
unified metric, ranking players and enriching them with team/player metadata.
"""

import json
from pathlib import Path
from typing import Any

import polars as pl

from domain.protocols import IPlayerValueAggregator
from use_cases.player_value.normalizer import PlayerValueNormalizer


class PlayerValueCombiner(IPlayerValueAggregator):
    """Combines BAV and SCI scores to produce Full Spectrum Player Value (FSPV) rankings."""

    def __init__(
        self,
        alpha: float = 0.5,
        normalizer: PlayerValueNormalizer | None = None,
        output_dir: str = "outputs/scores",
    ) -> None:
        """Initialize combiner.

        Args:
            alpha: Weight for BAV score (default 0.5 for equal 50/50 balance).
            normalizer: Optional custom normalizer.
            output_dir: Directory to persist player rankings.
        """
        self.alpha = alpha
        self.normalizer = normalizer or PlayerValueNormalizer()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def combine(
        self,
        bav_scores: Any,
        sci_scores: Any,
        player_metadata: dict[int, dict[str, str]] | None = None,
        output_filename: str = "player_value_rankings.json",
    ) -> pl.DataFrame:
        """Combine BAV and SCI metrics into unified player rankings.

        Args:
            bav_scores: pl.DataFrame, file path, or sequence containing BAV scores.
            sci_scores: pl.DataFrame, file path, or sequence containing SCI scores.
            player_metadata: Optional dict mapping player_id -> {'name': ..., 'team': ..., 'position': ...}.
            output_filename: Name of the JSON output file.

        Returns:
            Polars DataFrame with the ranked leaderboard.
        """
        # Load from file if strings are passed
        if isinstance(bav_scores, str):
            bav_df = pl.read_parquet(bav_scores)
        elif isinstance(bav_scores, pl.DataFrame):
            bav_df = bav_scores
        else:
            bav_df = pl.DataFrame(bav_scores)

        if isinstance(sci_scores, str):
            sci_df = pl.read_parquet(sci_scores)
        elif isinstance(sci_scores, pl.DataFrame):
            sci_df = sci_scores
        else:
            sci_df = pl.DataFrame(sci_scores)

        # Normalize metrics
        norm_bav = self.normalizer.normalize_bav(bav_df)
        norm_sci = self.normalizer.normalize_sci(sci_df)

        # Select relevant columns for merge
        bav_cols = ["player_id", "bav_z"]
        if "bav_per_possession" in norm_bav.columns:
            bav_cols.append("bav_per_possession")
        if "possessions_played" in norm_bav.columns:
            bav_cols.append("possessions_played")

        sci_cols = ["player_id", "sci_z"]
        if "player_sci" in norm_sci.columns:
            sci_cols.append("player_sci")
        if "chances_played" in norm_sci.columns:
            sci_cols.append("chances_played")

        bav_sub = norm_bav.select([c for c in bav_cols if c in norm_bav.columns])
        sci_sub = norm_sci.select([c for c in sci_cols if c in norm_sci.columns])

        # Join datasets by player_id
        if bav_sub.is_empty() and sci_sub.is_empty():
            return pl.DataFrame(schema={
                "player_id": pl.Int64,
                "player_name": pl.Utf8,
                "team": pl.Utf8,
                "bav_score": pl.Float64,
                "sci_score": pl.Float64,
                "fspv_score": pl.Float64,
                "fspv_percentile": pl.Float64,
            })

        if bav_sub.is_empty():
            merged = sci_sub.with_columns(pl.lit(0.0).alias("bav_z"))
        elif sci_sub.is_empty():
            merged = bav_sub.with_columns(pl.lit(0.0).alias("sci_z"))
        else:
            merged = bav_sub.join(sci_sub, on="player_id", how="full", coalesce=True)
            merged = merged.with_columns([
                pl.col("bav_z").fill_null(0.0),
                pl.col("sci_z").fill_null(0.0),
            ])

        # Compute FSPV combined score
        merged = merged.with_columns(
            (self.alpha * pl.col("bav_z") + (1.0 - self.alpha) * pl.col("sci_z")).alias("fspv_score")
        ).sort("fspv_score", descending=True)

        n_players = len(merged)
        # Compute percentile: top player is ~100th percentile
        percentiles: list[float] = []
        for rank_idx in range(n_players):
            if n_players <= 1:
                pct = 100.0
            else:
                pct = round(100.0 * (n_players - rank_idx) / n_players, 2)
            percentiles.append(pct)

        merged = merged.with_columns(pl.Series("fspv_percentile", percentiles))

        # Metadata enrichment
        meta = player_metadata or {}
        player_names: list[str] = []
        teams: list[str] = []
        positions: list[str] = []

        for pid in merged["player_id"].to_list():
            p_info = meta.get(int(pid), {})
            player_names.append(p_info.get("name") or f"Player #{pid}")
            teams.append(p_info.get("team") or "Unknown")
            positions.append(p_info.get("position") or "N/A")

        final_df = merged.with_columns([
            pl.Series("player_name", player_names),
            pl.Series("team", teams),
            pl.Series("position", positions),
            pl.col("bav_z").alias("bav_score"),
            pl.col("sci_z").alias("sci_score"),
        ]).select([
            "player_id",
            "player_name",
            "team",
            "position",
            "bav_score",
            "sci_score",
            "fspv_score",
            "fspv_percentile",
        ])

        # Save to JSON
        out_path = self.output_dir / output_filename
        records = final_df.to_dicts()
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

        return final_df
