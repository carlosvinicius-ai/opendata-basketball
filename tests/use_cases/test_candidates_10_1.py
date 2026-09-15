"""Unit tests for Section 10.1 candidate analytical modules."""

import polars as pl

from presentation.export_pack import OpenDataPackager
from use_cases.bav.possession_value_map import CourtGridConfig, PossessionValueMap
from use_cases.player_value.archetypes import PlayerArchetypeClusterer
from use_cases.player_value.drive_spacing import DriveSpacingAnalyzer
from use_cases.sci.screen_gravity import ScreenGravityAnalyzer


def test_possession_value_map_computation():
    """Verify possession value grid discretization and smoothing."""
    cfg = CourtGridConfig(x_bins=10, y_bins=10, sigma_smooth=0.5)
    pv_map = PossessionValueMap(config=cfg)

    # Synthetic actions with coordinates in meters
    actions_df = pl.DataFrame({
        "ball_x": [2.0, 5.0, 8.0, 2.0, 5.0],
        "ball_y": [0.0, 2.0, -2.0, 0.0, 1.0],
        "bav_value": [0.15, 0.08, -0.05, 0.20, 0.10],
    })

    result = pv_map.compute_grid(actions_df)
    assert "grid" in result
    assert "counts" in result
    assert "hotspots" in result
    assert len(result["grid"]) == 10
    assert len(result["grid"][0]) == 10
    assert len(result["hotspots"]) > 0
    assert result["hotspots"][0]["bav_expected"] > 0


def test_player_archetype_clusterer():
    """Verify K-Means clustering into offensive archetypes."""
    clusterer = PlayerArchetypeClusterer(n_clusters=4, random_state=42)

    fspv_df = pl.DataFrame({
        "player_id": [1, 2, 3, 4, 5, 6, 7, 8],
        "player_name": [f"Player {i}" for i in range(1, 9)],
        "team": ["Team A"] * 8,
        "bav_score": [1.5, 1.2, -0.8, -1.0, 0.8, -0.2, 0.1, -0.5],
        "sci_score": [1.8, -0.5, 1.6, -1.2, -0.7, 1.1, -0.1, -0.9],
        "fspv_score": [1.65, 0.35, 0.40, -1.10, 0.05, 0.45, 0.00, -0.70],
    })

    enriched = clusterer.fit_predict(fspv_df)
    assert "cluster_id" in enriched.columns
    assert "archetype_name" in enriched.columns
    assert enriched["cluster_id"].n_unique() <= 4

    summary = clusterer.save_summary(enriched, "outputs/scores/test_archetypes.json")
    assert "n_clusters" in summary
    assert "top_per_archetype" in summary


def test_screen_gravity_analyzer():
    """Verify off-ball screen frequency aggregation."""
    analyzer = ScreenGravityAnalyzer()

    mock_events = {
        "off_ball_screens": pl.DataFrame({
            "screenerId": [101, 101, 102, 103, 101],
            "chanceId": ["c1", "c2", "c3", "c4", "c5"],
        })
    }
    mock_sci = pl.DataFrame({
        "player_id": [101, 102, 103],
        "player_sci": [0.45, 0.20, -0.10],
    })

    res = analyzer.analyze_screens(mock_events, sci_df=mock_sci)
    assert len(res) == 3
    assert res.filter(pl.col("screener_id") == 101)["screens_set"][0] == 3
    assert "player_sci" in res.columns


def test_drive_spacing_analyzer():
    """Verify drive volume vs SCI correlation analysis."""
    analyzer = DriveSpacingAnalyzer()

    mock_events = {
        "drives": pl.DataFrame({
            "playerId": [1, 1, 1, 2, 2, 3, 3, 3, 3, 4, 5, 5],
            "blowby": [True, False, True, False, False, True, True, False, True, False, False, False],
        })
    }
    mock_fspv = pl.DataFrame({
        "player_id": [1, 2, 3, 4, 5],
        "sci_score": [1.2, -0.4, 1.5, -0.8, -0.2],
    })

    res = analyzer.evaluate_drive_spacing(mock_events, mock_fspv)
    assert "drive_sci_correlation" in res
    assert "p_value" in res
    assert res["sample_size"] == 5


def test_open_data_packager(tmp_path):
    """Verify open data packaging outputs."""
    packager = OpenDataPackager(export_dir=str(tmp_path / "open_data"))
    exported = packager.export_all(scores_dir="outputs/scores")
    assert "manifest" in exported
    assert (tmp_path / "open_data" / "README.md").exists()
