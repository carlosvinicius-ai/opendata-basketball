"""Player Archetypes Clustering.

Applies unsupervised K-Means clustering over (BAV_z, SCI_z) to classify
players into distinct offensive profiles.
"""

import json
from pathlib import Path
from typing import Any

import polars as pl
from sklearn.cluster import KMeans

ARCHETYPE_LABELS = {
    "dual_threat": "Dual-Threat Star",
    "ball_creator": "Primary Ball Creator",
    "space_anchor": "Off-Ball Gravity Anchor",
    "system_rotation": "System / Rotation Contributor",
}


class PlayerArchetypeClusterer:
    """Clusters players based on normalized on-ball and off-ball contributions."""

    def __init__(self, n_clusters: int = 4, random_state: int = 42) -> None:
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)

    def fit_predict(self, fspv_df: pl.DataFrame) -> pl.DataFrame:
        """Fit K-Means clustering and annotate players with archetypes.

        Args:
            fspv_df: Leaderboard DataFrame with 'bav_score' and 'sci_score'.

        Returns:
            DataFrame with added 'cluster_id' and 'archetype_name' columns.
        """
        if fspv_df.is_empty():
            return fspv_df.with_columns([
                pl.Series("cluster_id", [], dtype=pl.Int32),
                pl.Series("archetype_name", [], dtype=pl.Utf8),
            ])

        pts = fspv_df.select(["bav_score", "sci_score"]).to_numpy()

        if len(pts) < self.n_clusters:
            # Fallback for tiny samples
            return fspv_df.with_columns([
                pl.lit(0).cast(pl.Int32).alias("cluster_id"),
                pl.lit("Evaluated Player").alias("archetype_name"),
            ])

        cluster_ids = self.kmeans.fit_predict(pts)
        centroids = self.kmeans.cluster_centers_

        # Map cluster IDs to semantic names based on centroid coordinates
        cluster_names: dict[int, str] = {}
        for c_id, (bav_c, sci_c) in enumerate(centroids):
            if bav_c >= 0.2 and sci_c >= 0.2:
                cluster_names[c_id] = ARCHETYPE_LABELS["dual_threat"]
            elif bav_c >= 0.2 and sci_c < 0.2:
                cluster_names[c_id] = ARCHETYPE_LABELS["ball_creator"]
            elif bav_c < 0.2 and sci_c >= 0.2:
                cluster_names[c_id] = ARCHETYPE_LABELS["space_anchor"]
            else:
                cluster_names[c_id] = ARCHETYPE_LABELS["system_rotation"]

        # Ensure all clusters get distinct or sensible labels
        archetype_col = [cluster_names[cid] for cid in cluster_ids]

        enriched_df = fspv_df.with_columns([
            pl.Series("cluster_id", cluster_ids, dtype=pl.Int32),
            pl.Series("archetype_name", archetype_col, dtype=pl.Utf8),
        ])

        return enriched_df

    def save_summary(
        self,
        enriched_df: pl.DataFrame,
        output_path: str = "outputs/scores/player_archetypes.json",
    ) -> dict[str, Any]:
        """Save archetype summary and centroid distribution to JSON."""
        centroids = self.kmeans.cluster_centers_.tolist() if hasattr(self.kmeans, "cluster_centers_") else []
        counts = enriched_df.group_by("archetype_name").len().to_dicts()

        summary = {
            "n_clusters": self.n_clusters,
            "centroids": centroids,
            "archetype_counts": counts,
            "top_per_archetype": {},
        }

        for row in enriched_df.iter_rows(named=True):
            arch = row["archetype_name"]
            if arch not in summary["top_per_archetype"]:
                summary["top_per_archetype"][arch] = []
            if len(summary["top_per_archetype"][arch]) < 3:
                summary["top_per_archetype"][arch].append({
                    "player_name": row.get("player_name", f"Player #{row['player_id']}"),
                    "team": row.get("team", "Unknown"),
                    "fspv_score": round(float(row["fspv_score"]), 2),
                    "bav_score": round(float(row["bav_score"]), 2),
                    "sci_score": round(float(row["sci_score"]), 2),
                })

        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        return summary
