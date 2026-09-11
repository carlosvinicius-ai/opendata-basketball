"""Integration and unit tests for EventLoader."""

import polars as pl

from domain.protocols import IEventLoader
from infrastructure.event_loader import EVENT_TABLE_NAMES, EventLoader


def test_event_loader_satisfies_protocol():
    """Verify EventLoader satisfies IEventLoader protocol."""
    loader = EventLoader()
    assert isinstance(loader, IEventLoader)


def test_event_loader_game_114243():
    """Test loading all 20 event tables for sample game 114243."""
    loader = EventLoader()
    events = loader.load_events(114243)

    # Check that all 20 tables exist in output
    for table_name in EVENT_TABLE_NAMES:
        assert table_name in events, f"Missing table {table_name}"
        assert isinstance(events[table_name], pl.DataFrame)

    # Verify primary tables are non-empty
    assert len(events["possessions"]) > 0
    assert len(events["chances"]) > 0
    assert len(events["shots"]) > 0
    assert len(events["passes"]) > 0
    assert len(events["touches"]) > 0

    # Verify Fix 1: closeouts.touchWallClock is cast to Int64 if present
    if len(events["closeouts"]) > 0 and "touchWallClock" in events["closeouts"].columns:
        assert events["closeouts"].schema["touchWallClock"] == pl.Int64

    # Verify Fix 2: passes.toReceiverId was renamed to intercepting_defender_id
    if len(events["passes"]) > 0:
        assert "toReceiverId" not in events["passes"].columns
        assert "intercepting_defender_id" in events["passes"].columns
