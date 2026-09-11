"""Action sequencer for Basketball Action Value (BAV).

Extracts and chronologically orders on-ball actions (TOUCH, PASS, SHOT, PICK, DRIVE, DRIBBLE)
per chance from SkillCorner dynamic events tables.
"""

from typing import Any

import polars as pl

from domain.value_objects import ActionType

BAV_ACTION_TYPES = (
    ActionType.TOUCH,
    ActionType.PASS,
    ActionType.SHOT,
    ActionType.PICK,
    ActionType.DRIVE,
    ActionType.DRIBBLE,
)


class ActionSequencer:
    """Extracts on-ball action sequences for each chance in temporal order."""

    def extract_sequences(self, events: dict[str, pl.DataFrame], game_id: int | None = None) -> pl.DataFrame:
        """Extract and sequence all actions from event tables.

        Args:
            events: Dictionary mapping event table names to Polars DataFrames.
            game_id: Optional game identifier.

        Returns:
            Polars DataFrame with columns:
            chance_id, action_type, action_id, seq_pos, player_id, start_frame, game_id
        """
        raw_actions: list[dict[str, Any]] = []

        # 1. Touches
        if "touches" in events and not events["touches"].is_empty():
            df = events["touches"]
            p_col = "playerId" if "playerId" in df.columns else ("player_id" if "player_id" in df.columns else None)
            f_col = "startFrame" if "startFrame" in df.columns else "frame"
            id_col = "id" if "id" in df.columns else "touchId"
            if p_col and f_col in df.columns and "chanceId" in df.columns:
                for r in df.select(["chanceId", id_col, p_col, f_col]).iter_rows(named=True):
                    if r["chanceId"] is not None and r[f_col] is not None:
                        raw_actions.append({
                            "chance_id": str(r["chanceId"]),
                            "action_type": ActionType.TOUCH.value,
                            "action_id": str(r[id_col]),
                            "player_id": int(r[p_col]) if r[p_col] is not None else None,
                            "start_frame": int(r[f_col]),
                            "priority": 2,
                        })

        # 2. Passes
        if "passes" in events and not events["passes"].is_empty():
            df = events["passes"]
            p_col = "passerId" if "passerId" in df.columns else ("playerId" if "playerId" in df.columns else None)
            f_col = "startFrame" if "startFrame" in df.columns else "frame"
            if p_col and f_col in df.columns and "chanceId" in df.columns and "id" in df.columns:
                for r in df.select(["chanceId", "id", p_col, f_col]).iter_rows(named=True):
                    if r["chanceId"] is not None and r[f_col] is not None:
                        raw_actions.append({
                            "chance_id": str(r["chanceId"]),
                            "action_type": ActionType.PASS.value,
                            "action_id": str(r["id"]),
                            "player_id": int(r[p_col]) if r[p_col] is not None else None,
                            "start_frame": int(r[f_col]),
                            "priority": 4,
                        })

        # 3. Shots
        if "shots" in events and not events["shots"].is_empty():
            df = events["shots"]
            p_col = "shooterId" if "shooterId" in df.columns else ("playerId" if "playerId" in df.columns else None)
            f_col = "startFrame" if "startFrame" in df.columns else "frame"
            if p_col and f_col in df.columns and "chanceId" in df.columns and "id" in df.columns:
                for r in df.select(["chanceId", "id", p_col, f_col]).iter_rows(named=True):
                    if r["chanceId"] is not None and r[f_col] is not None:
                        raw_actions.append({
                            "chance_id": str(r["chanceId"]),
                            "action_type": ActionType.SHOT.value,
                            "action_id": str(r["id"]),
                            "player_id": int(r[p_col]) if r[p_col] is not None else None,
                            "start_frame": int(r[f_col]),
                            "priority": 5,
                        })

        # 4. Picks
        if "picks" in events and not events["picks"].is_empty():
            df = events["picks"]
            p_col = "ballhandlerId" if "ballhandlerId" in df.columns else (
                "screenerId" if "screenerId" in df.columns else None
            )
            f_col = "startFrame" if "startFrame" in df.columns else "frame"
            if p_col and f_col in df.columns and "chanceId" in df.columns and "id" in df.columns:
                for r in df.select(["chanceId", "id", p_col, f_col]).iter_rows(named=True):
                    if r["chanceId"] is not None and r[f_col] is not None:
                        raw_actions.append({
                            "chance_id": str(r["chanceId"]),
                            "action_type": ActionType.PICK.value,
                            "action_id": str(r["id"]),
                            "player_id": int(r[p_col]) if r[p_col] is not None else None,
                            "start_frame": int(r[f_col]),
                            "priority": 1,
                        })

        # 5. Drives
        if "drives" in events and not events["drives"].is_empty():
            df = events["drives"]
            p_col = "ballhandlerId" if "ballhandlerId" in df.columns else (
                "playerId" if "playerId" in df.columns else None
            )
            f_col = "startFrame" if "startFrame" in df.columns else "frame"
            if p_col and f_col in df.columns and "chanceId" in df.columns and "id" in df.columns:
                for r in df.select(["chanceId", "id", p_col, f_col]).iter_rows(named=True):
                    if r["chanceId"] is not None and r[f_col] is not None:
                        raw_actions.append({
                            "chance_id": str(r["chanceId"]),
                            "action_type": ActionType.DRIVE.value,
                            "action_id": str(r["id"]),
                            "player_id": int(r[p_col]) if r[p_col] is not None else None,
                            "start_frame": int(r[f_col]),
                            "priority": 1,
                        })

        # 6. Dribbles
        if "dribbles" in events and not events["dribbles"].is_empty():
            df = events["dribbles"]
            p_col = "playerId" if "playerId" in df.columns else ("player_id" if "player_id" in df.columns else None)
            f_col = "startFrame" if "startFrame" in df.columns else "frame"
            if p_col and f_col in df.columns and "chanceId" in df.columns and "id" in df.columns:
                for r in df.select(["chanceId", "id", p_col, f_col]).iter_rows(named=True):
                    if r["chanceId"] is not None and r[f_col] is not None:
                        raw_actions.append({
                            "chance_id": str(r["chanceId"]),
                            "action_type": ActionType.DRIBBLE.value,
                            "action_id": str(r["id"]),
                            "player_id": int(r[p_col]) if r[p_col] is not None else None,
                            "start_frame": int(r[f_col]),
                            "priority": 3,
                        })

        if not raw_actions:
            return pl.DataFrame(schema={
                "chance_id": pl.Utf8,
                "action_type": pl.Utf8,
                "action_id": pl.Utf8,
                "seq_pos": pl.Int32,
                "player_id": pl.Int64,
                "start_frame": pl.Int64,
                "game_id": pl.Int64,
            })

        # Sort actions within each chance by start_frame, then priority
        raw_df = pl.DataFrame(
            raw_actions,
            schema={
                "chance_id": pl.Utf8,
                "action_type": pl.Utf8,
                "action_id": pl.Utf8,
                "player_id": pl.Int64,
                "start_frame": pl.Int64,
                "priority": pl.Int32,
            },
        ).sort(["chance_id", "start_frame", "priority", "action_id"])

        # Compute sequential position (0, 1, 2, ...) per chance
        sequenced = (
            raw_df.with_columns(
                pl.int_range(0, pl.len()).over("chance_id").cast(pl.Int32).alias("seq_pos"),
                pl.lit(game_id).cast(pl.Int64).alias("game_id"),
            )
            .select([
                "chance_id",
                "action_type",
                "action_id",
                "seq_pos",
                "player_id",
                "start_frame",
                "game_id",
            ])
        )

        return sequenced


def extract_action_sequences(events: dict[str, pl.DataFrame], game_id: int | None = None) -> pl.DataFrame:
    """Convenience helper to extract sequenced actions."""
    sequencer = ActionSequencer()
    return sequencer.extract_sequences(events=events, game_id=game_id)
