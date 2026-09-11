"""Unit tests for BAVModel and XGBoost training/prediction."""

from pathlib import Path

import numpy as np
import polars as pl

from domain.protocols import IBAVModel
from use_cases.bav.bav_model import BAV_FEATURE_COLUMNS, BAVModel


def test_bav_model_satisfies_protocol():
    """Verify BAVModel implements IBAVModel protocol."""
    model = BAVModel()
    assert isinstance(model, IBAVModel)


def test_bav_model_fit_predict_save_load(tmp_path: Path):
    """Test model fitting, probability calibration range [0, 1], save and load."""
    np.random.seed(42)
    n = 100
    features = {col: np.random.randn(n).tolist() for col in BAV_FEATURE_COLUMNS}
    features["target_scored"] = np.random.choice([0, 1], size=n).tolist()
    features["game_id"] = [114243] * 80 + [188630] * 20

    dataset = pl.DataFrame(features)
    model = BAVModel(n_estimators=10, max_depth=2)

    save_file = tmp_path / "bav_test.json"
    metrics = model.train_and_evaluate(
        dataset,
        train_games=(114243,),
        test_games=(188630,),
        model_save_path=save_file,
    )

    assert "brier_score" in metrics
    assert "auc_roc" in metrics
    assert 0.0 <= metrics["brier_score"] <= 1.0
    assert save_file.exists()

    # Test loading
    loaded_model = BAVModel()
    loaded_model.load_model(save_file)
    preds = loaded_model.predict_proba(dataset[:5])
    assert len(preds) == 5
    assert (preds >= 0.0).all() and (preds <= 1.0).all()
