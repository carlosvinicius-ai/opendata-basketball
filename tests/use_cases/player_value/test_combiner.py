"""Unit tests for PlayerValueCombiner."""

import json

import polars as pl

from domain.protocols import IPlayerValueAggregator
from use_cases.player_value.combiner import PlayerValueCombiner


def test_combiner_satisfies_protocol():
    """Verify PlayerValueCombiner implements IPlayerValueAggregator."""
    combiner = PlayerValueCombiner()
    assert isinstance(combiner, IPlayerValueAggregator)


def test_combiner_merge_and_ranking(tmp_path):
    """Verify BAV and SCI combination, percentile calculation, and JSON persistence."""
    bav_df = pl.DataFrame({
        "player_id": [101, 102, 103],
        "player_bav": [0.10, 0.20, 0.30],
        "possessions_played": [20, 20, 20],
    })

    sci_df = pl.DataFrame({
        "player_id": [101, 102, 103],
        "player_sci": [0.02, 0.05, 0.08],
        "chances_played": [15, 15, 15],
    })

    metadata = {
        103: {"name": "Facundo Campazzo", "team": "Real Madrid", "position": "PG"},
        102: {"name": "Nico Laprovittola", "team": "FC Barcelona", "position": "SG"},
        101: {"name": "Sergio Llull", "team": "Real Madrid", "position": "SG"},
    }

    combiner = PlayerValueCombiner(alpha=0.5, output_dir=str(tmp_path))
    rankings_df = combiner.combine(
        bav_scores=bav_df,
        sci_scores=sci_df,
        player_metadata=metadata,
        output_filename="test_rankings.json",
    )

    assert isinstance(rankings_df, pl.DataFrame)
    assert len(rankings_df) == 3
    assert "fspv_score" in rankings_df.columns
    assert "fspv_percentile" in rankings_df.columns

    # Highest scorer should be player 103
    top_player = rankings_df.row(0, named=True)
    assert top_player["player_id"] == 103
    assert top_player["player_name"] == "Facundo Campazzo"
    assert top_player["team"] == "Real Madrid"
    assert top_player["fspv_percentile"] == 100.0

    # Verify JSON file created
    json_path = tmp_path / "test_rankings.json"
    assert json_path.exists()
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 3
    assert data[0]["player_name"] == "Facundo Campazzo"
