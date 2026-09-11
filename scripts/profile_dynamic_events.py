"""Dynamic events schema and cardinality profiler.

Usage:
    python scripts/profile_dynamic_events.py <game_id>
"""

import json
import sys
from pathlib import Path


def profile_dynamic_events(game_id: str | int) -> None:
    path = Path(f"data/matches/{game_id}/{game_id}_dynamic_events.json")
    if not path.exists():
        print(f"Error: file not found at {path}", file=sys.stderr)
        return

    events = json.loads(path.read_bytes())
    print(f"=== Dynamic Events Profile for Game {game_id} ===")
    total_events = 0
    for key, rows in events.items():
        count = len(rows)
        total_events += count
        if rows:
            fields = list(rows[0].keys())
            print(f"{key}: {count} rows | Fields ({len(fields)}): {', '.join(fields[:8])}...")
        else:
            print(f"{key}: 0 rows (empty)")
    print(f"Total events across all tables: {total_events}\n")


if __name__ == "__main__":
    target_id = sys.argv[1] if len(sys.argv) > 1 else "114243"
    profile_dynamic_events(target_id)
