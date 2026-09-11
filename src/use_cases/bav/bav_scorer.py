"""BAV (Basketball Action Value) action and player scorer.

Computes action-level value deltas:
    BAV(a_i) = P(score | state_i) - P(score | state_{i-1})
and aggregates total BAV per player normalized by possessions or chances played.
"""

from pathlib import Path

import polars as pl

from use_cases.bav.bav_model import BAVModel


class BAVScorer:
    """Calculates action-level BAV deltas and aggregates ratings per player."""

    def __init__(self, model: BAVModel, base_prior_prob: float = 0.48) -> None:
        self.model = model
        self.base_prior_prob = base_prior_prob

    def score_actions(self, feature_df: pl.DataFrame) -> pl.DataFrame:
        """Compute action-level BAV scores for all actions in feature_df.

        Returns:
            DataFrame with columns including 'prob_score' and 'bav_value'.
        """
        if feature_df.is_empty():
            return feature_df.with_columns(
                pl.lit(0.0).alias("prob_score"),
                pl.lit(0.0).alias("bav_value"),
            )

        # 1. Predict P(score | state) for all actions
        probs = self.model.predict_proba(feature_df)
        df = feature_df.with_columns(pl.Series("prob_score", probs))

        # 2. Compute delta BAV within each chance
        # For the first action (seq_pos == 0), previous prob is base_prior_prob
        scored_actions = (
            df.sort(["chance_id", "seq_pos"])
            .with_columns(
                pl.col("prob_score").shift(1).over("chance_id").fill_null(self.base_prior_prob).alias("prev_prob_score")
            )
            .with_columns(
                (pl.col("prob_score") - pl.col("prev_prob_score")).alias("bav_value")
            )
        )

        return scored_actions

    def aggregate_player_bav(
        self,
        scored_actions: pl.DataFrame,
        possessions_per_player: dict[int, int] | None = None,
        save_path: Path | str = "outputs/scores/bav_scores.parquet",
    ) -> pl.DataFrame:
        """Aggregate total and normalized BAV per player.

        Args:
            scored_actions: Output of score_actions containing 'player_id' and 'bav_value'.
            possessions_per_player: Optional dictionary mapping player_id -> count of possessions played.
            save_path: Target path for output parquet file.

        Returns:
            DataFrame with columns: player_id, total_bav, actions_count, possessions_played, bav_per_possession.
        """
        # Filter actions with valid player_id
        valid_actions = scored_actions.filter(pl.col("player_id").is_not_null())

        if valid_actions.is_empty():
            agg_df = pl.DataFrame(schema={
                "player_id": pl.Int64,
                "total_bav": pl.Float64,
                "actions_count": pl.Int32,
                "possessions_played": pl.Int32,
                "bav_per_possession": pl.Float64,
            })
        else:
            agg_df = (
                valid_actions.group_by("player_id")
                .agg([
                    pl.col("bav_value").sum().alias("total_bav"),
                    pl.len().cast(pl.Int32).alias("actions_count"),
                    pl.col("chance_id").n_unique().cast(pl.Int32).alias("chances_played"),
                ])
                .sort("total_bav", descending=True)
            )

            # Map possessions_played or default to chances_played
            pos_played_list: list[int] = []
            for r in agg_df.iter_rows(named=True):
                pid = r["player_id"]
                if possessions_per_player and pid in possessions_per_player:
                    pos_played_list.append(max(1, possessions_per_player[pid]))
                else:
                    pos_played_list.append(max(1, r["chances_played"]))

            agg_df = agg_df.with_columns(
                pl.Series("possessions_played", pos_played_list, dtype=pl.Int32)
            ).with_columns(
                (pl.col("total_bav") / pl.col("possessions_played")).alias("bav_per_possession")
            )

        # Save to parquet if path provided
        if save_path:
            p = Path(save_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            agg_df.write_parquet(p)

        return agg_df
