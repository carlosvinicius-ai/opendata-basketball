"""Unit tests for StateExtractor."""

import polars as pl

from use_cases.bav.state_extractor import StateExtractor


def test_state_extractor_feature_generation():
    """Verify state features are extracted for sequenced actions."""
    sequenced = pl.DataFrame({
        "chance_id": [1, 1],
        "action_type": ["TOUCH", "SHOT"],
        "action_id": [10, 11],
        "seq_pos": [0, 1],
        "player_id": [101, 101],
        "start_frame": [100, 150],
        "game_id": [114243, 114243],
    })

    events = {
        "chances": pl.DataFrame({
            "id": [1],
            "startFrame": [90],
            "outcome": ["made_basket"],
            "startType": ["inbound"],
        }),
    }

    extractor = StateExtractor()
    features_df = extractor.extract_features(sequenced, events)

    assert len(features_df) == 2
    assert "ball_x" in features_df.columns
    assert "shooter_dist_to_hoop" in features_df.columns
    assert "target_scored" in features_df.columns
    assert features_df["target_scored"][0] == 1
    assert features_df["target_scored"][1] == 1

    # First action has prev_action_type == -1
    assert features_df["prev_action_type"][0] == -1
    # Second action has prev_action_type == TOUCH encoding (2)
    assert features_df["prev_action_type"][1] == 2
