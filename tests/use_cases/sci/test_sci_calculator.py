"""Unit tests for SCICalculator."""

import polars as pl
import torch
from torch_geometric.data import Data

from use_cases.sci.gnn_model import GNNModel
from use_cases.sci.sci_calculator import SCICalculator


def _create_mock_graph() -> Data:
    """Helper mock graph."""
    x = torch.tensor([
        [10.0, 5.0, 4.0, 0.0],
        [-15.0, -2.0, 3.0, 0.0],
        [0.0, 0.0, 6.0, 1.0],
    ], dtype=torch.float32)
    edge_index = torch.tensor([
        [0, 1, 1, 2],
        [1, 0, 2, 1],
    ], dtype=torch.long)
    y = torch.tensor([1], dtype=torch.long)
    data = Data(x=x, edge_index=edge_index, y=y, num_nodes=3)
    data.node_player_ids = [101, 102, None]  # 2 players, 1 ball
    data.chance_id = "test-chance-1"
    data.game_id = 114243
    return data


def test_sci_calculator_aggregation(tmp_path):
    """Test calculating node attributions and aggregating player-level SCI scores."""
    model = GNNModel(hidden_dim=16)
    calc = SCICalculator(model=model, output_dir=str(tmp_path))

    g1 = _create_mock_graph()
    g2 = _create_mock_graph()
    g2.chance_id = "test-chance-2"

    parquet_out = str(tmp_path / "sci_scores.parquet")
    df = calc.calculate_player_sci([g1, g2], output_path=parquet_out)

    assert isinstance(df, pl.DataFrame)
    assert len(df) == 2  # 2 players
    assert set(df["player_id"].to_list()) == {101, 102}
    assert "player_sci" in df.columns
    assert "chances_played" in df.columns
    assert df["chances_played"][0] == 2
    assert (tmp_path / "sci_scores.parquet").exists()
