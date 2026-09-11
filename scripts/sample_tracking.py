"""Tracking frame sampler and profile inspector.

Usage:
    python scripts/sample_tracking.py <game_id> [sample_frames]
"""

import gzip
import json
import sys
from pathlib import Path


def sample_tracking(game_id: str | int, sample_frames: int = 1000) -> None:
    path = Path(f"data/matches/{game_id}/{game_id}_tracking_data.jsonl.gz")
    if not path.exists():
        print(f"Error: file not found at {path}", file=sys.stderr)
        return

    frames_count = 0
    player_counts = []
    min_frame = float("inf")
    max_frame = float("-inf")
    columns = set()

    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            d = json.loads(line)
            idx = d.get("frameIdx", 0)
            min_frame = min(min_frame, idx)
            max_frame = max(max_frame, idx)
            columns.update(d.keys())

            home_p = d.get("homePlayers") or []
            away_p = d.get("awayPlayers") or []
            unified_p = d.get("players") or []
            total_players = len(home_p) + len(away_p) + len(unified_p)
            player_counts.append(total_players)

            frames_count += 1
            if frames_count >= sample_frames:
                break

    avg_players = sum(player_counts) / len(player_counts) if player_counts else 0.0
    print(f"=== Tracking Data Sample for Game {game_id} ({frames_count} frames) ===")
    print(f"Columns: {sorted(columns)}")
    print(f"Frame range sampled: {min_frame} - {max_frame}")
    print(f"Average players tracked per frame: {avg_players:.2f}")
    print(f"Max players in a frame: {max(player_counts) if player_counts else 0}")
    print(f"Min players in a frame: {min(player_counts) if player_counts else 0}\n")


if __name__ == "__main__":
    target_id = sys.argv[1] if len(sys.argv) > 1 else "114243"
    n_frames = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    sample_tracking(target_id, n_frames)
