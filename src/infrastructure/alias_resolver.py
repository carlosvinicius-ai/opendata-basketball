"""Player ID alias resolver.

Ensures players with dual IDs across SkillCorner tracking and aggregate feeds
are normalized to their canonical_player_id before any joins or aggregations.
"""

from collections.abc import Sequence
from pathlib import Path

import polars as pl

DEFAULT_ALIASES_PATH = Path("data/player_id_aliases.csv")

COMMON_PLAYER_ID_COLUMNS = (
    "player_id",
    "playerId",
    "canonical_player_id",
    "shooterId",
    "passerId",
    "receiverId",
    "ballhandlerId",
    "screenerId",
    "cutterId",
    "setterId",
    "defenderId",
    "defPlayerId",
    "closestDefId",
    "rebounderId",
    "foulerId",
    "turnoverPlayerId",
    "ballhandlerDefId",
    "screenerDefId",
    "cutterDefId",
    "setterDefId",
    "receiverDefId",
    "startMatchupId",
    "endMatchupId",
    "offPlayerIds",
    "defPlayerIds",
    "intercepting_defender_id",
)


class AliasResolver:
    """Resolves player IDs to their canonical representations using player_id_aliases.csv."""

    def __init__(self, aliases_path: Path | str = DEFAULT_ALIASES_PATH) -> None:
        self.aliases_path = Path(aliases_path)
        self._mapping: dict[int, int] = {}
        self._load()

    def _load(self) -> None:
        """Load aliases CSV into memory mapping."""
        if not self.aliases_path.exists():
            return

        df = pl.read_csv(self.aliases_path)
        if "player_id" in df.columns and "canonical_player_id" in df.columns:
            for row in df.iter_rows(named=True):
                pid = row["player_id"]
                cid = row["canonical_player_id"]
                if pid is not None and cid is not None:
                    self._mapping[int(pid)] = int(cid)

    @property
    def mapping(self) -> dict[int, int]:
        """Return the dictionary of {player_id: canonical_player_id}."""
        return self._mapping.copy()

    def resolve_id(self, player_id: int | None) -> int | None:
        """Resolve a single player ID to its canonical counterpart."""
        if player_id is None:
            return None
        return self._mapping.get(player_id, player_id)

    def resolve(self, df: pl.DataFrame, col: str) -> pl.DataFrame:
        """Resolve player IDs in a specified DataFrame column.

        Handles both scalar integer columns and list columns (e.g. List[Int64]).
        """
        if col not in df.columns or not self._mapping:
            return df

        dtype = df.schema[col]

        # Handle list of player IDs (e.g. offPlayerIds, defPlayerIds in chances)
        if dtype == pl.List or isinstance(dtype, pl.List):
            return df.with_columns(
                pl.col(col).list.eval(
                    pl.element().replace_strict(
                        old=list(self._mapping.keys()),
                        new=list(self._mapping.values()),
                        default=pl.element(),
                    )
                ).alias(col)
            )

        # Handle scalar integer columns
        return df.with_columns(
            pl.col(col).replace_strict(
                old=list(self._mapping.keys()),
                new=list(self._mapping.values()),
                default=pl.col(col),
            ).alias(col)
        )

    def resolve_all(
        self,
        df: pl.DataFrame,
        candidate_cols: Sequence[str] = COMMON_PLAYER_ID_COLUMNS,
    ) -> pl.DataFrame:
        """Resolve all detected player ID columns in the DataFrame."""
        out = df
        for col in candidate_cols:
            if col in out.columns:
                out = self.resolve(out, col)
        return out


# Global singleton helper
_DEFAULT_RESOLVER: AliasResolver | None = None


def get_alias_resolver(aliases_path: Path | str = DEFAULT_ALIASES_PATH) -> AliasResolver:
    """Get or instantiate default AliasResolver."""
    global _DEFAULT_RESOLVER
    if _DEFAULT_RESOLVER is None or _DEFAULT_RESOLVER.aliases_path != Path(aliases_path):
        _DEFAULT_RESOLVER = AliasResolver(aliases_path=aliases_path)
    return _DEFAULT_RESOLVER


def resolve(df: pl.DataFrame, col: str, aliases_path: Path | str = DEFAULT_ALIASES_PATH) -> pl.DataFrame:
    """Convenience function matching TASK.md specification: resolve(df, col)."""
    return get_alias_resolver(aliases_path=aliases_path).resolve(df, col)
