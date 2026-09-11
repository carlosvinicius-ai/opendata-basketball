"""Unit tests for BAVScorer."""

from pathlib import Path

import numpy as np
import polars as pl

from use_cases.bav.bav_model import BAV_FEATURE_COLUMNS, BAVModel
from use_cases.bav.bav_scorer import BAVScorer


def test_bav_scorer_action_and_player_aggregation(tmp_path: Path):
    """Verify BAV delta computation and player aggregation."""
    # 1. Fit dummy BAVModel
    np.random.seed(42)
    n = 20
    features = {col: np.random.randn(n).tolist() for col in BAV_FEATURE_COLUMNS}
    features["target_scored"] = [1, 0] * 10
    model = BAVModel(n_estimators=5, max_depth=2)
    model.fit(pl.DataFrame(features), pl.Series("target_scored", features["target_scored"]))

    # 2. Build mock sequenced actions features
    test_features = {col: [1.0, 2.0, 3.0] for col in BAV_FEATURE_COLUMNS}
    test_features["chance_id"] = [100, 100, 100]
    test_features["action_id"] = [1, 2, 3]
    test_features["player_id"] = [501, 501, 502]
    test_features["seq_pos"] = [0, 1, 2]
    feature_df = pl.DataFrame(test_features)

    scorer = BAVScorer(model=model, base_prior_prob=0.5)
    scored_actions = scorer.score_actions(feature_df)

    assert "prob_score" in scored_actions.columns
    assert "bav_value" in scored_actions.columns
    assert len(scored_actions) == 3

    # 3. Aggregate per player
    save_parquet = tmp_path / "bav_scores.parquet"
    player_scores = scorer.aggregate_player_bav(
        scored_actions=scored_actions,
        save_path=save_parquet,
    )

    assert isinstance(player_scores, pl.DataFrame)
    assert len(player_scores) == 2  # players 501 and 502
    assert "bav_per_possession" in player_scores.columns
    assert save_parquet.exists()
