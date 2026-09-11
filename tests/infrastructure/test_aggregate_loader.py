"""Unit tests for AggregateLoader."""

import polars as pl

from infrastructure.aggregate_loader import AggregateLoader, load_aggregates


def test_aggregate_loader_loads_all_tables():
    """Verify AggregateLoader loads shots, drives, and picks tables."""
    loader = AggregateLoader()
    tables = loader.load_all()

    assert set(tables.keys()) == {"shots", "drives", "picks"}
    for _name, df in tables.items():
        assert isinstance(df, pl.DataFrame)
        assert len(df) > 0
        assert "player_id" in df.columns


def test_aggregate_loader_filters_totalizer_rows():
    """Verify include_totals=False filters out team_name == 'total'."""
    loader = AggregateLoader()

    # Without totals (default)
    df_no_totals = loader.load_table("shots", include_totals=False)
    assert df_no_totals.filter(pl.col("team_name") == "total").is_empty()

    # With totals
    df_with_totals = loader.load_table("shots", include_totals=True)
    assert not df_with_totals.filter(pl.col("team_name") == "total").is_empty()
    assert len(df_with_totals) > len(df_no_totals)


def test_aggregate_loader_applies_aliases():
    """Verify that dual-id players are mapped to canonical IDs in aggregates."""
    tables = load_aggregates(include_totals=False)
    shots_df = tables["shots"]

    # Player 59237 should have been mapped to 59129
    assert shots_df.filter(pl.col("player_id") == 59237).is_empty()
    assert not shots_df.filter(pl.col("player_id") == 59129).is_empty()
