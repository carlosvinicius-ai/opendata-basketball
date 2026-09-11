"""Domain entities representing primary basketball objects and state.

Entities carry identity, domain rules, and immutability.
Zero external dependencies allowed.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Player:
    """Player entity with identity and canonical mapping."""
    id: int
    canonical_id: int
    name: str
    position: str
    team_id: int


@dataclass(frozen=True)
class Game:
    """Game metadata and match context."""
    id: int
    date: str
    home_team_id: int
    away_team_id: int


@dataclass(frozen=True)
class Chance:
    """Scoring opportunity unit within a possession.

    A possession may contain multiple chances (e.g. following an offensive rebound).
    """
    id: int
    game_id: int
    possession_id: int
    off_team_id: int
    def_team_id: int
    off_players: tuple[int, ...] = field(default_factory=tuple)
    def_players: tuple[int, ...] = field(default_factory=tuple)
    outcome: str = ""
    usable: bool = True

    @property
    def is_scoring_opportunity(self) -> bool:
        """Indicate whether the chance is a valid, usable scoring opportunity."""
        return self.usable and len(self.off_players) > 0


@dataclass(frozen=True)
class Action:
    """Discrete action performed by a player within a chance."""
    id: int
    type: str
    player_id: int
    chance_id: int
    touch_id: int | None = None
    start_frame: int = 0
    end_frame: int = 0
    location: tuple[float, float] = (0.0, 0.0)

    @property
    def duration_frames(self) -> int:
        """Duration of the action in frames."""
        return max(0, self.end_frame - self.start_frame)


@dataclass(frozen=True)
class TrackingFrame:
    """Single tracking snapshot at 25 fps."""
    frame_idx: int
    wall_clock: int
    game_clock: float
    period: int
    shot_clock: float | None
    players: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    ball: dict[str, Any] | None = None


@dataclass(frozen=True)
class PlayerValue:
    """Full Spectrum Player Value combining on-ball (BAV) and off-ball (SCI) scores."""
    player_id: int
    bav_score: float
    sci_score: float
    combined_score: float
    games_sample: int

    @property
    def fspv_score(self) -> float:
        """Alias for combined Full Spectrum Player Value score."""
        return self.combined_score
