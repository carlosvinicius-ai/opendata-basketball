"""Space Creation Index (SCI) Calculator.

Extracts node attributions from the trained GraphSAGE model across chances
and aggregates them to compute off-ball space generation ratings per player.
"""

from pathlib import Path
from typing import Any

import polars as pl
from torch_geometric.data import Data

from use_cases.sci.gnn_model import GNNModel


class SCICalculator:
    """Calculates player-level Space Creation Index (SCI) scores."""

    def __init__(
        self,
        model: GNNModel | None = None,
        model_path: str = "models/sci_graphsage.pt",
        output_dir: str = "outputs/scores",
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if model is not None:
            self.model = model
        else:
            self.model = GNNModel()
            if Path(model_path).exists():
                self.model.load(model_path)

    def calculate_chance_attributions(self, data: Data) -> list[dict[str, Any]]:
        """Calculate node attributions for a single chance graph.

        Args:
            data: PyG Data object containing chance spatial graph and node_player_ids.

        Returns:
            List of dicts: [{'player_id': int, 'chance_id': Any, 'sci_value': float}]
        """
        attributions = self.model.get_node_attributions(data)
        node_pids = getattr(data, "node_player_ids", [])
        cid = getattr(data, "chance_id", None)
        gid = getattr(data, "game_id", None)

        records: list[dict[str, Any]] = []
        for idx, attr_val in enumerate(attributions):
            pid = node_pids[idx] if idx < len(node_pids) else None
            # Only record player nodes, ignore ball (pid is None)
            if pid is not None:
                records.append({
                    "player_id": int(pid),
                    "chance_id": str(cid) if cid is not None else None,
                    "game_id": gid,
                    "sci_value": float(attr_val),
                })

        return records

    def calculate_player_sci(
        self,
        graphs: list[Data],
        output_path: str = "outputs/scores/sci_scores.parquet",
    ) -> pl.DataFrame:
        """Compute aggregated SCI scores per player across all chance graphs.

        Args:
            graphs: List of chance-level PyG graphs.
            output_path: Destination path for Parquet output.

        Returns:
            Polars DataFrame with player-level aggregated SCI metrics.
        """
        all_records: list[dict[str, Any]] = []

        for graph in graphs:
            if graph.num_nodes > 0:
                chance_records = self.calculate_chance_attributions(graph)
                all_records.extend(chance_records)

        if not all_records:
            empty_schema = {
                "player_id": pl.Int64,
                "player_sci": pl.Float64,
                "chances_played": pl.UInt32,
                "sci_sum": pl.Float64,
                "sci_std": pl.Float64,
            }
            empty_df = pl.DataFrame(schema=empty_schema)
            if output_path:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                empty_df.write_parquet(output_path)
            return empty_df

        chances_df = pl.DataFrame(all_records)

        # Aggregate per player_id
        sci_summary = (
            chances_df.group_by("player_id")
            .agg([
                pl.col("sci_value").mean().alias("player_sci"),
                pl.col("sci_value").count().alias("chances_played"),
                pl.col("sci_value").sum().alias("sci_sum"),
                pl.col("sci_value").std().fill_null(0.0).alias("sci_std"),
            ])
            .sort("player_sci", descending=True)
        )

        if output_path:
            out_p = Path(output_path)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            sci_summary.write_parquet(out_p)

        return sci_summary
