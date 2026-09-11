"""State feature extractor for Basketball Action Value (BAV).

Builds contextual and spatial game state representations for each sequenced action
at its start frame without leaking full-season aggregate features.
"""

import math
from typing import Any

import polars as pl

from domain.constants import OFFENSIVE_HOOP_X_FT, OFFENSIVE_HOOP_Y_FT

ACTION_TYPE_MAP: dict[str, int] = {
    "PICK": 0,
    "DRIVE": 1,
    "TOUCH": 2,
    "DRIBBLE": 3,
    "PASS": 4,
    "SHOT": 5,
}

START_TYPE_MAP: dict[str, int] = {
    "unknown": 0,
    "inbound": 1,
    "defensive_rebound": 2,
    "offensive_rebound": 3,
    "turnover_won": 4,
    "jump_ball": 5,
    "steal": 6,
}


class StateExtractor:
    """Extracts spatial, temporal, and contextual state features for sequenced actions."""

    def extract_features(
        self,
        sequenced_actions: pl.DataFrame,
        events: dict[str, pl.DataFrame],
        tracking_df: pl.DataFrame | None = None,
    ) -> pl.DataFrame:
        """Construct feature matrix for actions in sequenced_actions.

        Args:
            sequenced_actions: Output of ActionSequencer.
            events: Dynamic events dictionary containing 'chances' and 'touches'.
            tracking_df: Optional tracking DataFrame for high-resolution spatial features.

        Returns:
            DataFrame with feature columns and target label 'target_scored'.
        """
        if sequenced_actions.is_empty():
            return pl.DataFrame()

        # 1. Pull chance metadata (startFrame, outcome, startType)
        chances_df = events.get("chances", pl.DataFrame())
        chance_meta: dict[str, dict[str, Any]] = {}
        if not chances_df.is_empty():
            c_cols = ["id", "startFrame", "outcome", "startType", "ptsScored"]
            available_cols = [c for c in c_cols if c in chances_df.columns]
            for r in chances_df.select(available_cols).iter_rows(named=True):
                cid_str = str(r["id"])
                outcome = str(r.get("outcome") or "")
                pts = int(r.get("ptsScored") or 0)
                scored = 1 if (pts > 0 or "made" in outcome.lower() or outcome in ("FGM", "FGM3", "made_basket")) else 0
                meta_item = {
                    "start_frame": int(r.get("startFrame") or 0),
                    "start_type": str(r.get("startType") or "unknown"),
                    "target_scored": scored,
                }
                chance_meta[cid_str] = meta_item
                # Also store integer key if id is numeric
                if cid_str.isdigit():
                    chance_meta[str(int(cid_str))] = meta_item

        # 2. Build tracking lookup if tracking_df is available
        # Pre-index tracking by frame_idx for fast spatial lookup
        tracking_lookup: dict[int, list[dict[str, Any]]] = {}
        if tracking_df is not None and not tracking_df.is_empty():
            cols_needed = ["frame_idx", "is_ball", "player_id", "x", "y"]
            available = [c for c in cols_needed if c in tracking_df.columns]
            for r in tracking_df.select(available).iter_rows(named=True):
                f_idx = r["frame_idx"]
                if f_idx not in tracking_lookup:
                    tracking_lookup[f_idx] = []
                tracking_lookup[f_idx].append(r)

        feature_rows: list[dict[str, Any]] = []

        # Group actions by chance to compute contextual lag features
        for chance_key, group_df in sequenced_actions.partition_by("chance_id", as_dict=True).items():
            cid_val = chance_key[0] if isinstance(chance_key, tuple) else chance_key
            cid_str = str(cid_val)
            meta = chance_meta.get(cid_str) or chance_meta.get(cid_val) or {"start_frame": 0, "start_type": "unknown", "target_scored": 0}
            chance_start_f = meta["start_frame"]
            chance_start_enc = START_TYPE_MAP.get(meta["start_type"].lower(), 0)
            target_scored = meta["target_scored"]

            prev_action_enc = -1
            sorted_actions = group_df.sort("seq_pos").iter_rows(named=True)

            for act in sorted_actions:
                act_type = act["action_type"]
                act_type_enc = ACTION_TYPE_MAP.get(act_type, -1)
                start_f = act["start_frame"]
                p_id = act["player_id"]
                seq_pos = act["seq_pos"]
                play_dur = max(0, start_f - chance_start_f)

                # Default spatial features
                ball_x = 0.0
                ball_y = 0.0
                shooter_dist_to_hoop = 25.0
                closest_def_dist = 6.0
                n_defenders_paint = 1

                # Extract spatial features from tracking lookup if present
                if start_f in tracking_lookup:
                    frame_objects = tracking_lookup[start_f]
                    ball_coords = None
                    actor_coords = None
                    other_players: list[tuple[float, float]] = []

                    for obj in frame_objects:
                        ox = obj.get("x")
                        oy = obj.get("y")
                        if ox is None or oy is None:
                            continue

                        if obj.get("is_ball"):
                            ball_coords = (float(ox), float(oy))
                        else:
                            opid = obj.get("player_id")
                            if opid == p_id:
                                actor_coords = (float(ox), float(oy))
                            else:
                                other_players.append((float(ox), float(oy)))

                    if ball_coords:
                        ball_x, ball_y = ball_coords
                    if actor_coords:
                        shooter_dist_to_hoop = math.hypot(
                            actor_coords[0] - OFFENSIVE_HOOP_X_FT,
                            actor_coords[1] - OFFENSIVE_HOOP_Y_FT,
                        )
                        if other_players:
                            closest_def_dist = min(
                                math.hypot(actor_coords[0] - px, actor_coords[1] - py)
                                for px, py in other_players
                            )
                    # Count players in the offensive paint (x < -24.0, |y| < 8.0)
                    n_defenders_paint = sum(
                        1 for px, py in other_players if px < -24.0 and abs(py) < 8.0
                    )

                # Proxy clocks if not directly in sequenced actions
                # Approximate 24s shot clock countdown
                shot_clock = max(0.0, 24.0 - (play_dur / 25.0))
                game_clock = 400.0
                period = 1
                dribble_count = 1 if act_type == "DRIBBLE" else 0

                row = {
                    "action_id": act["action_id"],
                    "chance_id": cid_val,
                    "player_id": p_id,
                    "seq_pos": seq_pos,
                    "start_frame": start_f,
                    "game_id": act.get("game_id"),
                    # Spatial features
                    "ball_x": ball_x,
                    "ball_y": ball_y,
                    "shooter_dist_to_hoop": shooter_dist_to_hoop,
                    "closest_def_dist": closest_def_dist,
                    "n_defenders_paint": n_defenders_paint,
                    # Event features
                    "shot_clock": shot_clock,
                    "game_clock": game_clock,
                    "period": period,
                    "dribble_count": dribble_count,
                    "action_type_enc": act_type_enc,
                    # Contextual features
                    "prev_action_type": prev_action_enc,
                    "chance_start_type": chance_start_enc,
                    "play_duration_so_far": play_dur,
                    # Target
                    "target_scored": target_scored,
                }
                feature_rows.append(row)
                prev_action_enc = act_type_enc

        return pl.DataFrame(feature_rows)


def extract_state_features(
    sequenced_actions: pl.DataFrame,
    events: dict[str, pl.DataFrame],
    tracking_df: pl.DataFrame | None = None,
) -> pl.DataFrame:
    """Convenience helper to extract state features."""
    extractor = StateExtractor()
    return extractor.extract_features(
        sequenced_actions=sequenced_actions,
        events=events,
        tracking_df=tracking_df,
    )
