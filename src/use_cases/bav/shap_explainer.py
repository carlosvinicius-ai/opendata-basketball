"""SHAP explainability for Basketball Action Value (BAV) model.

Uses shap.TreeExplainer to extract global feature importances and action-level
waterfall attribution breakdowns for the highest and lowest value actions.
"""

import json
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
import shap

from use_cases.bav.bav_model import BAVModel


class BAVSHAPExplainer:
    """Computes TreeExplainer SHAP values for BAV XGBoost predictions."""

    def __init__(self, model: BAVModel) -> None:
        self.model = model
        self.explainer = shap.TreeExplainer(self.model.classifier)

    def explain(
        self,
        feature_df: pl.DataFrame,
        output_dir: Path | str = "outputs/reports/bav_shap",
    ) -> dict[str, Any]:
        """Compute SHAP values, feature importance, and top/bottom action breakdowns.

        Args:
            feature_df: Feature DataFrame with BAV_FEATURE_COLUMNS.
            output_dir: Directory where summary reports are saved.

        Returns:
            Dictionary with 'feature_importance' and 'action_breakdowns'.
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        feature_cols = self.model.feature_columns
        x_mat = feature_df.select(feature_cols).to_numpy()

        # Compute SHAP values
        shap_values = self.explainer.shap_values(x_mat)

        # Global feature importance: mean(|SHAP value|)
        mean_abs_shap = np.mean(np.abs(shap_values), axis=0).tolist()
        feature_importance = [
            {"feature": col, "importance": float(imp)}
            for col, imp in sorted(zip(feature_cols, mean_abs_shap, strict=False), key=lambda x: x[1], reverse=True)
        ]

        # Top 5 actions with highest predicted value and lowest predicted value
        probs = self.model.predict_proba(feature_df)
        sorted_indices = np.argsort(probs)
        top5_indices = sorted_indices[-5:][::-1]
        bottom5_indices = sorted_indices[:5]

        def get_breakdown(indices: np.ndarray) -> list[dict[str, Any]]:
            breakdowns = []
            for idx in indices:
                row_dict = feature_df.row(int(idx), named=True)
                contribs = {
                    col: float(shap_values[idx, i])
                    for i, col in enumerate(feature_cols)
                }
                breakdowns.append({
                    "action_id": row_dict.get("action_id"),
                    "player_id": row_dict.get("player_id"),
                    "chance_id": row_dict.get("chance_id"),
                    "predicted_prob": float(probs[idx]),
                    "feature_contributions": contribs,
                })
            return breakdowns

        report = {
            "feature_importance": feature_importance,
            "top_5_positive_actions": get_breakdown(top5_indices),
            "top_5_negative_actions": get_breakdown(bottom5_indices),
        }

        # Save summary JSON
        with open(out_path / "bav_shap_summary.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        return report
