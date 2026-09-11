"""Season aggregate loader.

Loads and normalizes the 3 aggregate CSV files (shots, drives, picks) covering
the 293 ACB games, applying player alias resolution and totalizer filtering.
"""

from pathlib import Path

import polars as pl

from infrastructure.alias_resolver import AliasResolver, get_alias_resolver

AGGREGATE_FILENAMES = {
    "shots": "acb_shotsaggregates_20252026.csv",
    "drives": "acb_drivesaggregates_20252026.csv",
    "picks": "acb_picksaggregates_20252026.csv",
}


class AggregateLoader:
    """Loader for ACB season aggregate statistics files."""

    def __init__(
        self,
        aggregates_dir: Path | str = "data/aggregates",
        alias_resolver: AliasResolver | None = None,
    ) -> None:
        self.aggregates_dir = Path(aggregates_dir)
        self.alias_resolver = alias_resolver or get_alias_resolver()

    def load_table(self, table_name: str, include_totals: bool = False) -> pl.DataFrame:
        """Load a single aggregate table by name ('shots', 'drives', or 'picks').

        Args:
            table_name: One of 'shots', 'drives', 'picks'.
            include_totals: If False (default), removes rows where team_name == 'total'.
        """
        if table_name not in AGGREGATE_FILENAMES:
            raise ValueError(f"Unknown aggregate table '{table_name}'. Expected one of {list(AGGREGATE_FILENAMES.keys())}")

        file_path = self.aggregates_dir / AGGREGATE_FILENAMES[table_name]
        if not file_path.exists():
            raise FileNotFoundError(f"Aggregate file not found at {file_path}")

        df = pl.read_csv(file_path)

        # Filter out totalizer rows to avoid double-counting traded players
        if not include_totals and "team_name" in df.columns:
            df = df.filter(pl.col("team_name") != "total")

        # Apply player ID alias resolution
        if "player_id" in df.columns:
            df = self.alias_resolver.resolve(df, "player_id")

        return df

    def load_all(self, include_totals: bool = False) -> dict[str, pl.DataFrame]:
        """Load all 3 aggregate tables into a dictionary."""
        return {
            name: self.load_table(name, include_totals=include_totals)
            for name in AGGREGATE_FILENAMES
        }


def load_aggregates(
    aggregates_dir: Path | str = "data/aggregates",
    include_totals: bool = False,
) -> dict[str, pl.DataFrame]:
    """Convenience helper to load all 3 season aggregate tables."""
    loader = AggregateLoader(aggregates_dir=aggregates_dir)
    return loader.load_all(include_totals=include_totals)
