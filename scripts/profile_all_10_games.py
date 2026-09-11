"""Profile all 10 sample games and summarize dynamic event cardinalities."""

import json
from pathlib import Path

GAMES = [
    114243, 114234, 114169, 114099, 114086,
    178442, 179612, 184439, 188630, 191313
]

def profile_all():
    table_totals: dict[str, int] = {}
    game_summaries = []

    for gid in GAMES:
        p = Path(f"data/matches/{gid}/{gid}_dynamic_events.json")
        if not p.exists():
            continue
        events = json.loads(p.read_bytes())
        total_game_events = 0
        counts = {}
        for k, rows in events.items():
            cnt = len(rows)
            counts[k] = cnt
            total_game_events += cnt
            table_totals[k] = table_totals.get(k, 0) + cnt
        game_summaries.append((gid, total_game_events, counts))

    print(f"=== Summary Across All {len(game_summaries)} Games ===")
    for k in sorted(table_totals.keys()):
        print(f"  {k:20s}: {table_totals[k]:6d} total events (avg {table_totals[k]/len(game_summaries):.1f}/game)")

    total_all = sum(table_totals.values())
    print(f"\nTotal events across all tables in 10 games: {total_all}")

if __name__ == "__main__":
    profile_all()
