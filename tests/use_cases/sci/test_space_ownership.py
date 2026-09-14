"""Unit tests for SpaceOwnershipVisualizer."""

from pathlib import Path

from use_cases.sci.space_ownership_visualizer import SpaceOwnershipVisualizer


def test_space_ownership_calculation_and_plotting(tmp_path):
    """Test Voronoi area calculation and plot generation."""
    viz = SpaceOwnershipVisualizer(output_dir=str(tmp_path))

    # 10 player coordinates (5 offense, 5 defense) on FIBA half court
    player_coords = [
        (-20.0, 0.0), (-25.0, 10.0), (-25.0, -10.0), (-35.0, 15.0), (-35.0, -15.0),
        (-22.0, 2.0), (-27.0, 8.0), (-27.0, -8.0), (-33.0, 13.0), (-33.0, -13.0),
    ]
    player_ids = [101, 102, 103, 104, 105, 201, 202, 203, 204, 205]
    is_offense = [True] * 5 + [False] * 5

    metrics = viz.compute_voronoi_areas(
        player_coords=player_coords,
        player_ids=player_ids,
        is_offense_flags=is_offense,
    )

    assert len(metrics) == 10
    for m in metrics:
        assert "area_sqft" in m
        assert m["area_sqft"] > 0
        assert "weighted_space" in m
        assert m["weighted_space"] > 0

    # Test plot generation
    img_path = viz.plot_voronoi_court(
        player_coords=player_coords,
        player_ids=player_ids,
        is_offense_flags=is_offense,
        filename="test_voronoi.png",
    )

    assert Path(img_path).exists()
    assert Path(img_path).stat().st_size > 1000  # Non-empty image file
