"""Unit tests for PlayerValueNormalizer."""

import numpy as np
import polars as pl

from use_cases.player_value.normalizer import PlayerValueNormalizer, compute_z_scores


def test_compute_z_scores_basic():
    """Verify compute_z_scores standardizes a numeric column to mean ~0 and std ~1."""
    df = pl.DataFrame({
        "player_id": [1, 2, 3, 4, 5],
        "score": [10.0, 20.0, 30.0, 40.0, 50.0],
    })

    res = compute_z_scores(df, col="score", out_col="score_z")
    assert "score_z" in res.columns
    z_vals = res["score_z"].to_numpy()
    assert np.isclose(np.mean(z_vals), 0.0, atol=1e-6)
    assert np.isclose(np.std(z_vals, ddof=1), 1.0, atol=1e-6)


def test_compute_z_scores_zero_variance():
    """Verify zero variance does not trigger division by zero error."""
    df = pl.DataFrame({
        "player_id": [1, 2, 3],
        "score": [5.0, 5.0, 5.0],
    })

    res = compute_z_scores(df, col="score", out_col="score_z")
    assert all(v == 0.0 for v in res["score_z"].to_list())


def test_normalizer_bav_and_sci():
    """Verify normalizer handles per-possession calculation and standardizes both metrics."""
    bav_df = pl.DataFrame({
        "player_id": [101, 102, 103],
        "bav_sum": [1.5, 3.0, 4.5],
        "possessions_played": [10, 10, 10],
    })

    sci_df = pl.DataFrame({
        "player_id": [101, 102, 103],
        "player_sci": [0.05, 0.10, 0.15],
    })

    norm = PlayerValueNormalizer()
    nb, ns = norm.normalize_both(bav_df, sci_df)

    assert "bav_z" in nb.columns
    assert "bav_per_possession" in nb.columns
    assert "sci_z" in ns.columns
    assert nb["bav_z"][0] < nb["bav_z"][2]
    assert ns["sci_z"][0] < ns["sci_z"][2]
