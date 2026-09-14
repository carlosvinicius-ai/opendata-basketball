"""Unit tests for PlayerValueValidator."""

import json

import polars as pl

from use_cases.player_value.validator import PlayerValueValidator


def test_validator_with_mock_aggregates(tmp_path):
    """Verify validator computes Spearman correlations and extracts top 5 face validity."""
    fspv_df = pl.DataFrame({
        "player_id": [1, 2, 3, 4, 5, 6],
        "player_name": ["P1", "P2", "P3", "P4", "P5", "P6"],
        "team": ["T1", "T1", "T2", "T2", "T3", "T3"],
        "bav_score": [1.0, 0.8, 0.6, 0.4, 0.2, 0.0],
        "sci_score": [1.0, 0.9, 0.7, 0.5, 0.3, 0.1],
        "fspv_score": [1.0, 0.85, 0.65, 0.45, 0.25, 0.05],
        "fspv_percentile": [100.0, 83.3, 66.7, 50.0, 33.3, 16.7],
    })

    mock_aggregates = {
        "shots": pl.DataFrame({
            "player_id": [1, 2, 3, 4, 5, 6],
            "points_per_shot": [1.3, 1.2, 1.1, 0.9, 0.8, 0.7],
        }),
        "picks": pl.DataFrame({
            "player_id": [1, 2, 3, 4, 5, 6],
            "handler_ppp": [1.1, 1.05, 0.95, 0.85, 0.75, 0.65],
        }),
    }

    validator = PlayerValueValidator(output_dir=str(tmp_path))
    report = validator.validate(
        fspv_df=fspv_df,
        aggregates=mock_aggregates,
        output_filename="test_val_report.json",
    )

    assert "validation_metrics" in report
    assert "points_per_shot" in report["validation_metrics"]
    assert "handler_ppp" in report["validation_metrics"]

    rho_shots = report["validation_metrics"]["points_per_shot"]["spearman_rho"]
    rho_picks = report["validation_metrics"]["handler_ppp"]["spearman_rho"]

    # Since rankings are monotonic with points_per_shot, rho should be ~1.0
    assert rho_shots > 0.9
    assert rho_picks > 0.9

    # Top 5 face validity
    top5 = report["face_validity_top5"]
    assert len(top5) == 5
    assert top5[0]["player_id"] == 1
    assert top5[0]["fspv_score"] == 1.0

    # JSON persisted
    json_path = tmp_path / "test_val_report.json"
    assert json_path.exists()
    with open(json_path, encoding="utf-8") as f:
        saved = json.load(f)
    assert saved["status"] == "PASS"
