"""Season aggregates missingness and shape auditor.

Usage:
    python scripts/check_aggregates_missingness.py
"""

from pathlib import Path

import polars as pl


def check_aggregates_missingness(aggregates_dir: str = "data/aggregates") -> None:
    agg_dir = Path(aggregates_dir)
    print("=== Checking Season Aggregates Missingness ===")
    for fname in [
        "acb_shotsaggregates_20252026.csv",
        "acb_drivesaggregates_20252026.csv",
        "acb_picksaggregates_20252026.csv",
    ]:
        p = agg_dir / fname
        if not p.exists():
            print(f"Warning: {p} does not exist.")
            continue

        df = pl.read_csv(p)
        null_counts = df.null_count()
        high_null = []
        for col in df.columns:
            cnt = null_counts[col][0]
            if cnt > 0:
                pct = (cnt / len(df)) * 100.0
                high_null.append((col, cnt, f"{pct:.1f}%"))

        print(f"\n{fname}: {df.shape[0]} rows x {df.shape[1]} cols")
        print(f"  Columns with nulls: {len(high_null)} / {len(df.columns)}")
        if high_null:
            top_null = sorted(high_null, key=lambda x: x[1], reverse=True)[:5]
            print(f"  Top 5 null columns: {top_null}")
        else:
            print("  Zero nulls detected.")


if __name__ == "__main__":
    check_aggregates_missingness()
