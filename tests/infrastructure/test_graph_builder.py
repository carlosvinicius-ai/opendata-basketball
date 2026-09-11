"""Unit and integration tests for GraphBuilder."""

import polars as pl

from infrastructure.event_loader import load_events
from infrastructure.graph_builder import GraphBuilder, GraphData
from infrastructure.tracking_loader import load_tracking


def test_graph_builder_basic_construction():
    """Verify GraphBuilder creates valid GraphData on mock tracking slice."""
    df = pl.DataFrame({
        "frame_idx": [1, 1, 2, 2],
        "wall_clock": [40, 40, 80, 80],
        "game_clock": [600.0, 600.0, 599.0, 599.0],
        "period": [1, 1, 1, 1],
        "shot_clock": [24.0, 24.0, 23.0, 23.0],
        "player_id": [101, None, 101, None],
        "x": [0.0, 2.0, 0.0, 2.0],
        "y": [0.0, 0.0, 0.0, 0.0],
        "z": [0.0, 1.0, 0.0, 1.0],
        "speed": [5.0, 10.0, 5.0, 10.0],
        "is_detected": [True, True, True, True],
        "pred_error": [0.5, 0.5, 0.5, 0.5],
        "is_ball": [False, True, False, True],
    })

    builder = GraphBuilder(distance_threshold_ft=10.0)
    graph = builder.build_chance_graph(df, chance_outcome="made_basket")

    assert isinstance(graph, GraphData)
    assert graph.num_nodes == 2
    assert len(graph.x) == 2
    assert len(graph.edge_index) == 2
    assert len(graph.edge_index[0]) == 2  # Bidirectional edge between the 2 nodes
    assert graph.y == 1


def test_graph_builder_10_chances_game_114243():
    """Test graph construction on 10 actual chances from game 114243."""
    events = load_events(114243)
    chances_df = events["chances"].filter(pl.col("usable")).head(10)
    assert len(chances_df) >= 10

    builder = GraphBuilder(distance_threshold_ft=35.0)

    # Test for first 10 chances
    for row in chances_df.iter_rows(named=True):
        start_f = row["startFrame"]
        end_f = row["endFrame"]
        outcome = row.get("outcome", "")

        tracking_df = load_tracking(
            game_id=114243,
            frame_start=start_f,
            frame_end=end_f,
        )

        graph = builder.build_chance_graph(
            chance_tracking_df=tracking_df,
            chance_outcome=outcome,
        )

        assert isinstance(graph, GraphData)
        if len(tracking_df) > 0:
            assert graph.num_nodes > 0
            assert len(graph.x) == graph.num_nodes
            assert len(graph.edge_index[0]) == len(graph.edge_index[1])
            assert len(graph.edge_attr) == len(graph.edge_index[0])
            assert graph.y in (0, 1)
