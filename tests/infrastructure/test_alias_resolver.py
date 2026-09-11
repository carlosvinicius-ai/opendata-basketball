"""Unit tests for AliasResolver."""

import polars as pl

from infrastructure.alias_resolver import AliasResolver, resolve


def test_alias_resolver_loads_mapping():
    """Verify alias resolver loads mapping from data/player_id_aliases.csv."""
    resolver = AliasResolver()
    mapping = resolver.mapping
    assert len(mapping) > 0
    # From CSV: 59237 -> 59129 (Nihad Djedovic)
    assert mapping.get(59237) == 59129
    # 92815 -> 59180 (Alex Reyes)
    assert mapping.get(92815) == 59180


def test_alias_resolver_scalar_column():
    """Verify scalar column replacement."""
    df = pl.DataFrame({
        "shooterId": [59237, 92815, 99999],
        "points": [3, 2, 0],
    })
    resolved = resolve(df, "shooterId")
    assert resolved["shooterId"].to_list() == [59129, 59180, 99999]


def test_alias_resolver_list_column():
    """Verify replacement within list columns (such as offPlayerIds)."""
    resolver = AliasResolver()
    df = pl.DataFrame({
        "chance_id": [1, 2],
        "offPlayerIds": [[59237, 100], [92815, 99999]],
    })
    resolved = resolver.resolve(df, "offPlayerIds")
    expected = [[59129, 100], [59180, 99999]]
    assert resolved["offPlayerIds"].to_list() == expected


def test_alias_resolver_all_columns():
    """Verify resolve_all across multiple candidate player columns."""
    resolver = AliasResolver()
    df = pl.DataFrame({
        "passerId": [59237],
        "receiverId": [92815],
        "unrelated": [123],
    })
    resolved = resolver.resolve_all(df)
    assert resolved["passerId"][0] == 59129
    assert resolved["receiverId"][0] == 59180
    assert resolved["unrelated"][0] == 123
