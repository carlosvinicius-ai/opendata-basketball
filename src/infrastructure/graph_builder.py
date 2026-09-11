"""Spatial graph builder for GNN / Space Creation Index (SCI).

Constructs graph representations of chance-level tracking sequences where
nodes represent players (and ball) and edges represent spatial Euclidean relationships.
"""

import math
from dataclasses import dataclass, field
from typing import Any

import polars as pl


@dataclass
class GraphData:
    """Graph representation of a basketball chance.

    Compatible with torch_geometric.data.Data.
    """
    x: list[list[float]]  # Node feature matrix: [num_nodes, num_features]
    edge_index: list[list[int]]  # Edge indices: [2, num_edges]
    edge_attr: list[list[float]]  # Edge features: [num_edges, num_edge_features]
    y: int  # Target label (1 if chance resulted in made basket, else 0)
    node_player_ids: list[int | None] = field(default_factory=list)
    num_nodes: int = 0

    def to_torch_geometric(self) -> Any:
        """Convert to torch_geometric.data.Data if torch and torch_geometric are installed."""
        try:
            import torch
            from torch_geometric.data import Data

            return Data(
                x=torch.tensor(self.x, dtype=torch.float32),
                edge_index=torch.tensor(self.edge_index, dtype=torch.long),
                edge_attr=torch.tensor(self.edge_attr, dtype=torch.float32),
                y=torch.tensor([self.y], dtype=torch.long),
                num_nodes=self.num_nodes,
            )
        except ImportError:
            return self


class GraphBuilder:
    """Builds spatial graphs from tracking DataFrames for individual chances."""

    def __init__(self, distance_threshold_ft: float = 30.0) -> None:
        self.distance_threshold_ft = distance_threshold_ft

    def build_chance_graph(
        self,
        chance_tracking_df: pl.DataFrame,
        chance_outcome: str = "",
        off_team_id: int | None = None,
    ) -> GraphData:
        """Construct graph from tracking frames of a single chance.

        Args:
            chance_tracking_df: Tracking rows filtered to chance frame window.
            chance_outcome: e.g. 'made_basket', 'missed_basket'.
            off_team_id: Identifier of attacking team.

        Returns:
            GraphData object containing node features, edges, distances, and label.
        """
        label = 1 if "made" in chance_outcome.lower() or chance_outcome == "made_basket" else 0

        if chance_tracking_df.is_empty():
            return GraphData(x=[], edge_index=[[], []], edge_attr=[], y=label, num_nodes=0)

        # Aggregate player and ball statistics over the chance window
        # Group by player_id / is_ball
        nodes_summary = (
            chance_tracking_df.group_by(["is_ball", "player_id"])
            .agg([
                pl.col("x").mean().alias("mean_x"),
                pl.col("y").mean().alias("mean_y"),
                pl.col("speed").mean().alias("mean_speed"),
            ])
            .sort(["is_ball", "player_id"])
        )

        node_features: list[list[float]] = []
        node_coords: list[tuple[float, float]] = []
        node_player_ids: list[int | None] = []

        for row in nodes_summary.iter_rows(named=True):
            is_ball = row["is_ball"]
            pid = row["player_id"]
            mx = float(row["mean_x"]) if row["mean_x"] is not None else 0.0
            my = float(row["mean_y"]) if row["mean_y"] is not None else 0.0
            spd = float(row["mean_speed"]) if row["mean_speed"] is not None else 0.0

            # Feature vector: [mean_x, mean_y, mean_speed, is_ball]
            node_features.append([mx, my, spd, 1.0 if is_ball else 0.0])
            node_coords.append((mx, my))
            node_player_ids.append(pid)

        num_nodes = len(node_features)
        edge_src: list[int] = []
        edge_dst: list[int] = []
        edge_attr: list[list[float]] = []

        # Connect pairs of nodes with spatial distance
        for i in range(num_nodes):
            for j in range(num_nodes):
                if i != j:
                    xi, yi = node_coords[i]
                    xj, yj = node_coords[j]
                    dist = math.hypot(xi - xj, yi - yj)
                    if dist <= self.distance_threshold_ft:
                        edge_src.append(i)
                        edge_dst.append(j)
                        edge_attr.append([dist])

        graph = GraphData(
            x=node_features,
            edge_index=[edge_src, edge_dst],
            edge_attr=edge_attr,
            y=label,
            node_player_ids=node_player_ids,
            num_nodes=num_nodes,
        )

        return graph


def build_chance_graph(
    chance_tracking_df: pl.DataFrame,
    chance_outcome: str = "",
    off_team_id: int | None = None,
) -> GraphData:
    """Convenience helper to build a chance graph."""
    builder = GraphBuilder()
    return builder.build_chance_graph(
        chance_tracking_df=chance_tracking_df,
        chance_outcome=chance_outcome,
        off_team_id=off_team_id,
    )
