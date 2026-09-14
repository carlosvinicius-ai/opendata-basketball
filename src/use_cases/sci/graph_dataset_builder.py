"""Graph dataset builder for Space Creation Index (SCI).

Iterates over chances from ACB games, extracts tracking frames,
aggregates player spatial features, and constructs spatial graphs
compatible with PyTorch Geometric.
"""

from pathlib import Path
from typing import Any

import polars as pl
import torch
from torch_geometric.data import Data

from infrastructure.event_loader import load_events
from infrastructure.graph_builder import GraphBuilder
from infrastructure.tracking_loader import load_tracking


class GraphDatasetBuilder:
    """Builds and caches a dataset of chance-level PyTorch Geometric graphs."""

    def __init__(
        self,
        distance_threshold_ft: float = 35.0,
        output_dir: str = "outputs/features",
    ) -> None:
        self.distance_threshold_ft = distance_threshold_ft
        self.output_dir = Path(output_dir)
        self.graph_builder = GraphBuilder(distance_threshold_ft=distance_threshold_ft)

    def build_dataset_for_game(
        self,
        game_id: int,
        events: dict[str, pl.DataFrame] | None = None,
        max_chances: int | None = None,
    ) -> list[Data]:
        """Build graphs for all usable chances in a single game."""
        if events is None:
            events = load_events(game_id)

        if "chances" not in events or events["chances"].is_empty():
            return []

        chances_df = events["chances"]
        if "usable" in chances_df.columns:
            chances_df = chances_df.filter(pl.col("usable"))

        if max_chances is not None and max_chances > 0:
            chances_df = chances_df.head(max_chances)

        graphs: list[Data] = []

        for row in chances_df.iter_rows(named=True):
            cid = row["id"]
            start_f = int(row.get("startFrame") or 0)
            end_f = int(row.get("endFrame") or start_f)
            outcome = str(row.get("outcome") or "")
            pts = int(row.get("ptsScored") or 0)
            off_team_id = row.get("offensiveTeamId")

            # Determine scoring outcome
            is_scored = (
                "made"
                if (pts > 0 or "made" in outcome.lower() or outcome in ("FGM", "FGM3", "made_basket"))
                else "missed"
            )

            tracking_df = load_tracking(
                game_id=game_id,
                frame_start=start_f,
                frame_end=end_f,
            )

            graph_data = self.graph_builder.build_chance_graph(
                chance_tracking_df=tracking_df,
                chance_outcome=is_scored,
                off_team_id=off_team_id,
                chance_id=cid,
                game_id=game_id,
            )

            pyg_data = graph_data.to_torch_geometric()
            if isinstance(pyg_data, Data) and pyg_data.num_nodes > 0:
                graphs.append(pyg_data)

        return graphs

    def build_and_save_dataset(
        self,
        game_ids: list[int],
        filename: str = "sci_graph_dataset.pt",
        max_chances_per_game: int | None = None,
        force_rebuild: bool = False,
    ) -> list[Data]:
        """Build dataset across multiple games and persist as PyTorch pt file."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        target_path = self.output_dir / filename

        if target_path.exists() and not force_rebuild:
            loaded: Any = torch.load(target_path, weights_only=False)
            if isinstance(loaded, list):
                return loaded

        all_graphs: list[Data] = []
        for gid in game_ids:
            game_graphs = self.build_dataset_for_game(
                game_id=gid,
                max_chances=max_chances_per_game,
            )
            all_graphs.extend(game_graphs)

        torch.save(all_graphs, target_path)
        return all_graphs
