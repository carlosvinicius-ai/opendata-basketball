"""Unit tests for standalone HTML5 ReportBuilder."""

from pathlib import Path

from presentation.report_builder import ReportBuilder


def test_report_builder_html_generation(tmp_path):
    """Verify ReportBuilder produces a valid, standalone HTML5 document with embedded assets."""
    scores_dir = tmp_path / "scores"
    reports_dir = tmp_path / "reports"
    scores_dir.mkdir()
    reports_dir.mkdir()

    builder = ReportBuilder(scores_dir=str(scores_dir), output_dir=str(reports_dir))

    mock_rankings = [
        {"player_id": 1, "player_name": "Facundo Campazzo", "team": "Real Madrid", "position": "PG", "bav_score": 2.1, "sci_score": 1.5, "fspv_score": 1.8, "fspv_percentile": 99.0},
        {"player_id": 2, "player_name": "Nico Laprovittola", "team": "FC Barcelona", "position": "SG", "bav_score": 1.7, "sci_score": 1.2, "fspv_score": 1.45, "fspv_percentile": 97.5},
        {"player_id": 3, "player_name": "Edy Tavares", "team": "Real Madrid", "position": "C", "bav_score": 0.5, "sci_score": 2.2, "fspv_score": 1.35, "fspv_percentile": 95.0},
    ]

    mock_validation = {
        "validation_metrics": {
            "points_per_shot": {"spearman_rho": 0.55, "p_value": 0.01},
            "handler_ppp": {"spearman_rho": 0.50, "p_value": 0.02},
        },
        "face_validity_top5": mock_rankings,
        "status": "PASS",
    }

    out_file = builder.build_report(
        rankings=mock_rankings,
        validation=mock_validation,
        output_filename="test_report.html",
    )

    report_path = Path(out_file)
    assert report_path.exists()
    assert report_path.stat().st_size > 5000  # Standalone HTML with embedded assets

    content = report_path.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "Chart.js" in content or "chart.umd" in content
    assert "Facundo Campazzo" in content
    assert "Real Madrid" in content
    assert "data:image/png;base64," in content  # Embedded base64 charts
    assert "Full Spectrum Player Value" in content
    assert "Leaderboard" in content
