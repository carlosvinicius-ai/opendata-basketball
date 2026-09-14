"""Unit tests for GraphDatasetBuilder."""

from torch_geometric.data import Data

from infrastructure.event_loader import load_events
from use_cases.sci.graph_dataset_builder import GraphDatasetBuilder


def test_graph_dataset_builder_real_chance(tmp_path):
    """Test building graphs for a real chance from game 114243."""
    events = load_events(114243)
    builder = GraphDatasetBuilder(output_dir=str(tmp_path))

    graphs = builder.build_dataset_for_game(
        game_id=114243,
        events=events,
        max_chances=1,
    )

    assert isinstance(graphs, list)
    assert len(graphs) == 1
    data = graphs[0]
    assert isinstance(data, Data)
    assert data.num_nodes > 0
    assert hasattr(data, "node_player_ids")


def test_graph_dataset_builder_cache(tmp_path):
    """Test saving and loading graph dataset cache."""
    builder = GraphDatasetBuilder(output_dir=str(tmp_path))

    # Build and cache
    graphs1 = builder.build_and_save_dataset(
        game_ids=[114243],
        filename="test_cache.pt",
        max_chances_per_game=1,
    )
    assert len(graphs1) == 1
    cache_file = tmp_path / "test_cache.pt"
    assert cache_file.exists()

    # Load from cache
    graphs2 = builder.build_and_save_dataset(
        game_ids=[114243],
        filename="test_cache.pt",
        max_chances_per_game=1,
    )
    assert len(graphs2) == 1
    assert graphs2[0].num_nodes == graphs1[0].num_nodes
