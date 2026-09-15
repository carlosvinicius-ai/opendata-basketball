"""Unit tests for Phase 11 Modular Interactive Scouting Cockpit."""

import json
from pathlib import Path

from presentation.cli import main
from presentation.report_builder import ReportBuilder


def test_modular_cockpit_file_generation(tmp_path: Path) -> None:
    """Verify that build_modular_cockpit generates all required files."""
    builder = ReportBuilder(output_dir=str(tmp_path))
    assets = builder.build_modular_cockpit()
    assert len(assets) >= 3

    expected_files = [
        tmp_path / "index.html",
        tmp_path / "css" / "styles.css",
        tmp_path / "js" / "data_store.js",
        tmp_path / "js" / "court_matrix.js",
        tmp_path / "js" / "radar_chart.js",
        tmp_path / "js" / "scatter_plot.js",
        tmp_path / "js" / "scouting_drawer.js",
        tmp_path / "js" / "dashboard.js",
        tmp_path / "data" / "cockpit_data.json",
    ]

    for f in expected_files:
        assert f.exists(), f"Expected file does not exist: {f}"
        assert f.stat().st_size > 0, f"File is empty: {f}"


def test_cockpit_data_schema_and_integrity(tmp_path: Path) -> None:
    """Verify schema, types, and values in cockpit_data.json."""
    builder = ReportBuilder(output_dir=str(tmp_path))
    builder.build_modular_cockpit()

    json_file = tmp_path / "data" / "cockpit_data.json"
    with open(json_file, encoding="utf-8") as f:
        data = json.load(f)

    # 1. Top-level keys
    assert "metadata" in data
    assert "kpis" in data
    assert "validation" in data
    assert "positional_averages" in data
    assert "court_matrix_14x10" in data
    assert "players" in data

    # 2. Players verification
    players = data["players"]
    assert len(players) >= 5, "Should have at least 5 sample players"
    valid_positions = {"PG", "SG", "SF", "PF", "C"}

    for p in players:
        assert "player_id" in p
        assert "player_name" in p
        assert "team" in p
        assert p["position"] in valid_positions, f"Invalid position: {p['position']}"
        assert "fspv_score" in p
        assert "bav_score" in p
        assert "sci_score" in p
        assert "pnr_efficiency" in p
        assert "scouting_notes" in p

    # 3. 14x10 Court Matrix
    matrix = data["court_matrix_14x10"]
    assert len(matrix) == 140, f"Expected exactly 140 blocks (14x10), got {len(matrix)}"
    for block in matrix:
        assert 0 <= block["col"] < 14
        assert 0 <= block["row"] < 10
        assert "zone_type" in block
        assert "leader_name" in block
        assert -1.0 <= block["balance_ratio"] <= 1.0

    # 4. Positional Averages
    pos_avg = data["positional_averages"]
    for pos in ["PG", "SG", "SF", "PF", "C"]:
        assert pos in pos_avg
        assert "bav" in pos_avg[pos]
        assert "sci" in pos_avg[pos]

    # 5. KPIs
    kpis = data["kpis"]
    assert "top_fspv" in kpis
    assert "top_bav" in kpis
    assert "top_sci" in kpis
    assert "avg_fspv" in kpis


def test_cli_build_report_generates_modular_assets() -> None:
    """Verify that presentation.cli build-report succeeds and produces modular assets."""
    exit_code = main(["build-report"])
    assert exit_code == 0

    assert Path("reports/index.html").exists()
    assert Path("reports/css/styles.css").exists()
    assert Path("reports/js/data_store.js").exists()
    assert Path("reports/data/cockpit_data.json").exists()
