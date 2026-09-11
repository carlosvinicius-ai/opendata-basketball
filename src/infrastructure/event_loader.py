"""Dynamic events loader.

Loads and normalizes the 20 Game Intelligence event tables from {gameId}_dynamic_events.json
into typed Polars DataFrames, applying alias resolution and data fixes.
"""

import json
from pathlib import Path
from typing import Any

import polars as pl

from domain.protocols import IEventLoader
from infrastructure.alias_resolver import AliasResolver, get_alias_resolver

EVENT_TABLE_NAMES = (
    "possessions",
    "chances",
    "chance_players",
    "matchups",
    "shots",
    "free_throws",
    "rebounds",
    "turnovers",
    "fouls",
    "timeouts",
    "passes",
    "touches",
    "dribbles",
    "picks",
    "handoffs",
    "off_ball_screens",
    "drives",
    "isolations",
    "posts",
    "closeouts",
)


class EventLoader(IEventLoader):
    """Concrete loader for SkillCorner dynamic event files implementing IEventLoader."""

    def __init__(
        self,
        base_data_dir: Path | str = "data",
        alias_resolver: AliasResolver | None = None,
    ) -> None:
        self.base_data_dir = Path(base_data_dir)
        self.alias_resolver = alias_resolver or get_alias_resolver()

    def get_event_file_path(self, game_id: int) -> Path:
        """Resolve path to dynamic events JSON for game_id."""
        # Check data/matches/{gameId}/{gameId}_dynamic_events.json
        p = self.base_data_dir / "matches" / str(game_id) / f"{game_id}_dynamic_events.json"
        if p.exists():
            return p
        # Fallback check directly under base_data_dir
        p_direct = self.base_data_dir / f"{game_id}_dynamic_events.json"
        if p_direct.exists():
            return p_direct
        raise FileNotFoundError(f"Dynamic events file not found for game_id={game_id} at {p}")

    def load_events(self, game_id: int) -> dict[str, pl.DataFrame]:
        """Load and parse dynamic events for game_id.

        Returns:
            Dictionary mapping event table name to typed Polars DataFrame.
        """
        file_path = self.get_event_file_path(game_id)
        raw_content = file_path.read_bytes()
        events_dict: dict[str, Any] = json.loads(raw_content)

        dataframes: dict[str, pl.DataFrame] = {}

        for table_name in EVENT_TABLE_NAMES:
            rows = events_dict.get(table_name, [])
            if not rows:
                df = pl.DataFrame()
            else:
                df = pl.DataFrame(rows)

            # Apply domain and known-data-issue fixes
            df = self._apply_table_fixes(table_name, df)

            # Apply player ID alias resolution
            if not df.is_empty():
                df = self.alias_resolver.resolve_all(df)

            dataframes[table_name] = df

        return dataframes

    def _apply_table_fixes(self, table_name: str, df: pl.DataFrame) -> pl.DataFrame:
        """Apply known schema fixes and corrections documented in DATA-STRUCTURE.md."""
        if df.is_empty():
            return df

        # Fix 1: closeouts.touchWallClock is delivered as String -> cast to Int64
        if table_name == "closeouts" and "touchWallClock" in df.columns:
            df = df.with_columns(
                pl.col("touchWallClock").cast(pl.Int64, strict=False).alias("touchWallClock")
            )

        # Fix 2: passes.toReceiverId in SkillCorner actually indicates intercepting defender
        # Rename to intercepting_defender_id
        if table_name == "passes" and "toReceiverId" in df.columns:
            df = df.rename({"toReceiverId": "intercepting_defender_id"})

        return df


def load_events(game_id: int, base_data_dir: Path | str = "data") -> dict[str, pl.DataFrame]:
    """Convenience helper to load dynamic events for a game."""
    loader = EventLoader(base_data_dir=base_data_dir)
    return loader.load_events(game_id)
