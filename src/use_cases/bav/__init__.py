"""BAV (Basketball Action Value) use case package.

Orchestrates sequential on-ball action extraction, spatial feature engineering,
probabilistic modeling via XGBoost, value scoring, and SHAP explainability.
"""

from use_cases.bav.action_sequencer import (
    BAV_ACTION_TYPES,
    ActionSequencer,
    extract_action_sequences,
)
from use_cases.bav.bav_model import (
    BAV_FEATURE_COLUMNS,
    DEFAULT_TEST_GAMES,
    DEFAULT_TRAIN_GAMES,
    BAVModel,
)
from use_cases.bav.bav_scorer import BAVScorer
from use_cases.bav.shap_explainer import BAVSHAPExplainer
from use_cases.bav.state_extractor import StateExtractor, extract_state_features

__all__ = [
    # Sequencer
    "ActionSequencer",
    "extract_action_sequences",
    "BAV_ACTION_TYPES",
    # State Extractor
    "StateExtractor",
    "extract_state_features",
    # Model
    "BAVModel",
    "BAV_FEATURE_COLUMNS",
    "DEFAULT_TRAIN_GAMES",
    "DEFAULT_TEST_GAMES",
    # Scorer
    "BAVScorer",
    # Explainer
    "BAVSHAPExplainer",
]
