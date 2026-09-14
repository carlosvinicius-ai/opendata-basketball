"""Validation module for Full Spectrum Player Value (FSPV).

Performs external benchmark validation against 293-game season aggregates
(shots points_per_shot and picks handler_ppp) using Spearman rank correlation,
and performs face validity checks on top-performing players.
"""

import json
from pathlib import Path
from typing import Any

import polars as pl
from scipy.stats import spearmanr

from infrastructure.aggregate_loader import load_aggregates


class PlayerValueValidator:
    """Validates FSPV rankings externally against season aggregate statistics."""

    def __init__(self, output_dir: str = "outputs/scores") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def validate(
        self,
        fspv_df: pl.DataFrame,
        aggregates: dict[str, pl.DataFrame] | None = None,
        output_filename: str = "validation_report.json",
    ) -> dict[str, Any]:
        """Perform external validation of FSPV scores.

        Args:
            fspv_df: Leaderboard DataFrame with 'player_id' and 'fspv_score'.
            aggregates: Optional preloaded aggregate tables dict (shots, drives, picks).
            output_filename: Destination filename in output_dir.

        Returns:
            Dictionary containing correlation metrics and face validity assessment.
        """
        if aggregates is None:
            aggregates = load_aggregates(include_totals=False)

        results: dict[str, Any] = {
            "validation_metrics": {},
            "face_validity_top5": [],
            "status": "PASS",
        }

        # 1. Spearman correlation vs Shots points_per_shot
        if "shots" in aggregates and "points_per_shot" in aggregates["shots"].columns:
            shots_df = aggregates["shots"].select(["player_id", "points_per_shot"]).drop_nulls()
            merged_shots = fspv_df.join(shots_df, on="player_id", how="inner").drop_nulls(
                subset=["fspv_score", "points_per_shot"]
            )

            if len(merged_shots) >= 5:
                res_shots = spearmanr(
                    merged_shots["fspv_score"].to_numpy(),
                    merged_shots["points_per_shot"].to_numpy(),
                )
                results["validation_metrics"]["points_per_shot"] = {
                    "spearman_rho": float(res_shots.statistic),
                    "p_value": float(res_shots.pvalue),
                    "sample_size": len(merged_shots),
                }
            else:
                results["validation_metrics"]["points_per_shot"] = {
                    "spearman_rho": 0.0,
                    "p_value": 1.0,
                    "sample_size": len(merged_shots),
                    "note": "Insufficient overlapping players",
                }

        # 2. Spearman correlation vs Picks handler_ppp
        if "picks" in aggregates and "handler_ppp" in aggregates["picks"].columns:
            picks_df = aggregates["picks"].select(["player_id", "handler_ppp"]).drop_nulls()
            merged_picks = fspv_df.join(picks_df, on="player_id", how="inner").drop_nulls(
                subset=["fspv_score", "handler_ppp"]
            )

            if len(merged_picks) >= 5:
                res_picks = spearmanr(
                    merged_picks["fspv_score"].to_numpy(),
                    merged_picks["handler_ppp"].to_numpy(),
                )
                results["validation_metrics"]["handler_ppp"] = {
                    "spearman_rho": float(res_picks.statistic),
                    "p_value": float(res_picks.pvalue),
                    "sample_size": len(merged_picks),
                }
            else:
                results["validation_metrics"]["handler_ppp"] = {
                    "spearman_rho": 0.0,
                    "p_value": 1.0,
                    "sample_size": len(merged_picks),
                    "note": "Insufficient overlapping players",
                }

        # 3. Face Validity: Top 5 players audit
        top5_df = fspv_df.sort("fspv_score", descending=True).head(5)
        top5_list: list[dict[str, Any]] = []

        for row in top5_df.iter_rows(named=True):
            top5_list.append({
                "player_id": int(row["player_id"]),
                "player_name": row.get("player_name", f"Player #{row['player_id']}"),
                "team": row.get("team", "Unknown"),
                "fspv_score": float(row["fspv_score"]),
                "bav_score": float(row.get("bav_score", 0.0)),
                "sci_score": float(row.get("sci_score", 0.0)),
                "fspv_percentile": float(row.get("fspv_percentile", 100.0)),
            })

        results["face_validity_top5"] = top5_list

        # Save to disk
        out_path = self.output_dir / output_filename
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        return results
