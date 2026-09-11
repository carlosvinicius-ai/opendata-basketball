"""Integration and unit tests for TrackingLoader."""

import polars as pl

from domain.protocols import ITrackingLoader
from infrastructure.tracking_loader import TRACKING_SCHEMA, TrackingLoader


def test_tracking_loader_satisfies_protocol():
    """Verify TrackingLoader satisfies ITrackingLoader protocol."""
    loader = TrackingLoader()
    assert isinstance(loader, ITrackingLoader)


def test_tracking_loader_sample_1000_frames_game_114243():
    """Test streaming and parsing 1000 frames from game 114243."""
    loader = TrackingLoader()
    df = loader.load_tracking(game_id=114243, max_frames=1000)

    # Check schema conformance
    for col_name, expected_dtype in TRACKING_SCHEMA.items():
        assert col_name in df.columns, f"Missing column {col_name}"
        assert df.schema[col_name] == expected_dtype

    # Ensure rows were loaded
    assert len(df) > 0

    # Ensure ball rows exist
    ball_rows = df.filter(pl.col("is_ball"))
    assert len(ball_rows) > 0

    # Ensure player rows exist
    player_rows = df.filter(~pl.col("is_ball"))
    assert len(player_rows) > 0

    # Ensure frame indices span the requested window
    assert df["frame_idx"].min() is not None
    assert df["frame_idx"].max() is not None
