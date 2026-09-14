"""Automated data leakage guard assertion tests.

Enforces ADR 0005: Verifies that no feature used in BAV or SCI models
is derived or leaked from the 293-game season aggregate CSV files.
"""


from infrastructure.aggregate_loader import load_aggregates
from use_cases.bav.bav_model import BAV_FEATURE_COLUMNS


def test_bav_features_do_not_leak_from_aggregates():
    """Verify that none of the BAV feature column names exist in season aggregates."""
    aggregates = load_aggregates(include_totals=True)
    aggregate_columns: set[str] = set()

    for _name, df in aggregates.items():
        aggregate_columns.update(df.columns)

    # Identifiers like player_id / game_id are joins, not predictive features
    predictive_features = set(BAV_FEATURE_COLUMNS)

    leaked_columns = predictive_features.intersection(aggregate_columns)
    assert not leaked_columns, f"Data leakage detected! Features present in aggregates: {leaked_columns}"


def test_bav_feature_matrix_leakage_check():
    """Verify BAV state extractor output does not contain any aggregate target metrics."""
    forbidden_substrings = [
        "ppp",
        "points_per_shot",
        "fg_percentage",
        "blowby_rate",
        "score_rate",
        "handler_ppp",
        "screener_ppp",
    ]

    for feat in BAV_FEATURE_COLUMNS:
        for forbidden in forbidden_substrings:
            assert forbidden not in feat.lower(), (
                f"Feature '{feat}' contains aggregate target metric substring '{forbidden}'"
            )


def test_sci_features_do_not_leak_from_aggregates():
    """Verify that SCI graph node features [mx, my, spd, is_ball] do not leak aggregate metrics."""
    aggregates = load_aggregates(include_totals=True)
    aggregate_columns: set[str] = set()
    for _name, df in aggregates.items():
        aggregate_columns.update(df.columns)

    sci_feature_names = {"mean_x", "mean_y", "mean_speed", "is_ball"}
    leaked_columns = sci_feature_names.intersection(aggregate_columns)
    assert not leaked_columns, f"Data leakage in SCI features: {leaked_columns}"

