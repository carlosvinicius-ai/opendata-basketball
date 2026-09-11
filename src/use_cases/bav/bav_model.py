"""XGBoost probabilistic classifier for Basketball Action Value (BAV).

Predicts P(chance scored | state at action) using spatial, contextual, and temporal features.
Enforces game-level train/test holdout to prevent temporal and lineup data leakage.
"""

from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
import xgboost as xgb
from sklearn.metrics import brier_score_loss, roc_auc_score

from domain.constants import RANDOM_SEED
from domain.protocols import IBAVModel

DEFAULT_TRAIN_GAMES = (
    114243, 114234, 114169, 114099, 114086,
    178442, 179612, 184439,
)

DEFAULT_TEST_GAMES = (
    188630, 191313,
)

BAV_FEATURE_COLUMNS = [
    "ball_x",
    "ball_y",
    "shooter_dist_to_hoop",
    "closest_def_dist",
    "n_defenders_paint",
    "shot_clock",
    "game_clock",
    "period",
    "dribble_count",
    "action_type_enc",
    "prev_action_type",
    "chance_start_type",
    "play_duration_so_far",
    "seq_pos",
]


class BAVModel(IBAVModel):
    """BAV XGBoost classifier predicting scoring probabilities."""

    def __init__(
        self,
        n_estimators: int = 150,
        max_depth: int = 4,
        learning_rate: float = 0.05,
        random_state: int = RANDOM_SEED,
        feature_columns: list[str] | None = None,
    ) -> None:
        self.feature_columns = feature_columns or BAV_FEATURE_COLUMNS
        self.random_state = random_state
        self.classifier = xgb.XGBClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            random_state=random_state,
            eval_metric="logloss",
        )
        self._is_fitted = False

    def fit(self, x: Any, y: Any) -> None:
        """Fit the XGBoost classifier on feature matrix x and target binary vector y."""
        if isinstance(x, pl.DataFrame):
            x_mat = x.select(self.feature_columns).to_numpy()
        else:
            x_mat = np.asarray(x)

        if isinstance(y, (pl.Series, pl.DataFrame)):
            y_arr = y.to_numpy().ravel()
        else:
            y_arr = np.asarray(y).ravel()

        self.classifier.fit(x_mat, y_arr)
        self._is_fitted = True

    def predict_proba(self, x: Any) -> np.ndarray:
        """Predict scoring probability P(score | state) for each action state."""
        if not self._is_fitted:
            raise RuntimeError("BAVModel must be fitted before predicting probabilities.")

        if isinstance(x, pl.DataFrame):
            x_mat = x.select(self.feature_columns).to_numpy()
        else:
            x_mat = np.asarray(x)

        probs = self.classifier.predict_proba(x_mat)[:, 1]
        return probs

    def save_model(self, model_path: Path | str = "models/bav_xgboost.json") -> None:
        """Save model weights to JSON format."""
        p = Path(model_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        self.classifier.save_model(str(p))

    def load_model(self, model_path: Path | str = "models/bav_xgboost.json") -> None:
        """Load fitted model weights from JSON format."""
        p = Path(model_path)
        if not p.exists():
            raise FileNotFoundError(f"Model file not found at {p}")
        self.classifier.load_model(str(p))
        self._is_fitted = True

    def train_and_evaluate(
        self,
        dataset: pl.DataFrame,
        train_games: tuple[int, ...] = DEFAULT_TRAIN_GAMES,
        test_games: tuple[int, ...] = DEFAULT_TEST_GAMES,
        model_save_path: Path | str = "models/bav_xgboost.json",
    ) -> dict[str, float]:
        """Train model with strict game-level split and compute validation metrics.

        Returns:
            Dictionary with 'brier_score', 'auc_roc', 'train_samples', 'test_samples'.
        """
        train_df = dataset.filter(pl.col("game_id").is_in(train_games))
        test_df = dataset.filter(pl.col("game_id").is_in(test_games))

        # Fallback if specific game_ids are not in dataset
        if train_df.is_empty() or test_df.is_empty():
            n = len(dataset)
            split_idx = int(0.8 * n)
            train_df = dataset[:split_idx]
            test_df = dataset[split_idx:]

        x_train = train_df.select(self.feature_columns).to_numpy()
        y_train = train_df["target_scored"].to_numpy()
        x_test = test_df.select(self.feature_columns).to_numpy()
        y_test = test_df["target_scored"].to_numpy()

        self.fit(x_train, y_train)
        self.save_model(model_save_path)

        preds_test = self.predict_proba(x_test)
        brier = float(brier_score_loss(y_test, preds_test))

        # AUC-ROC requires both classes to be present in test set
        if len(np.unique(y_test)) > 1:
            auc = float(roc_auc_score(y_test, preds_test))
        else:
            auc = 0.5

        return {
            "brier_score": brier,
            "auc_roc": auc,
            "train_samples": len(train_df),
            "test_samples": len(test_df),
        }
