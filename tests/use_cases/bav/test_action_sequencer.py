"""Unit tests for ActionSequencer."""

import polars as pl

from infrastructure.event_loader import load_events
from use_cases.bav.action_sequencer import ActionSequencer


def test_action_sequencer_ordering():
    """Verify actions within a chance are ordered chronologically by startFrame."""
    events = {
        "touches": pl.DataFrame({
            "id": [1],
            "chanceId": [100],
            "playerId": [501],
            "startFrame": [120],
        }),
        "picks": pl.DataFrame({
            "id": [2],
            "chanceId": [100],
            "ballhandlerId": [501],
            "startFrame": [100],
        }),
        "shots": pl.DataFrame({
            "id": [3],
            "chanceId": [100],
            "shooterId": [501],
            "startFrame": [150],
        }),
    }

    sequencer = ActionSequencer()
    df = sequencer.extract_sequences(events, game_id=114243)

    assert len(df) == 3
    # Ordered by startFrame: PICK (100) -> TOUCH (120) -> SHOT (150)
    assert df["action_type"].to_list() == ["PICK", "TOUCH", "SHOT"]
    assert df["seq_pos"].to_list() == [0, 1, 2]
    assert df["start_frame"].to_list() == [100, 120, 150]


def test_action_sequencer_game_114243():
    """Verify action sequencing on actual game 114243 events."""
    events = load_events(114243)
    sequencer = ActionSequencer()
    df = sequencer.extract_sequences(events, game_id=114243)

    assert len(df) > 0
    assert "chance_id" in df.columns
    assert "action_type" in df.columns
    assert "seq_pos" in df.columns

    # Verify every chance starts with seq_pos == 0
    min_seq = df.group_by("chance_id").agg(pl.col("seq_pos").min().alias("min_seq"))
    assert (min_seq["min_seq"] == 0).all()
