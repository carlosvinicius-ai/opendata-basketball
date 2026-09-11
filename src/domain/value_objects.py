"""Domain value objects for basketball spatial coordinates, temporal windows, and taxonomy.

All value objects are immutable and validate invariants.
Zero external dependencies allowed.
"""

import math
from dataclasses import dataclass
from enum import StrEnum

from domain.constants import (
    COURT_BUFFER_FT,
    DEFENSIVE_HOOP_LOCATION,
    OFFENSIVE_HOOP_LOCATION,
    X_BOUND_FT,
    Y_BOUND_FT,
)


@dataclass(frozen=True)
class CourtCoordinate:
    """2D court coordinate in feet with origin (0, 0) at center court.

    Attacking hoop is at negative x (-41.83, 0.0).
    Defending hoop is at positive x (41.83, 0.0).
    """
    x_ft: float
    y_ft: float

    def is_in_bounds(self, tolerance_ft: float = 0.0) -> bool:
        """Check whether coordinate falls within the FIBA court boundaries."""
        x_limit = X_BOUND_FT + tolerance_ft
        y_limit = Y_BOUND_FT + tolerance_ft
        return (-x_limit <= self.x_ft <= x_limit) and (-y_limit <= self.y_ft <= y_limit)

    def is_in_playable_area(self, buffer_ft: float = COURT_BUFFER_FT) -> bool:
        """Check whether coordinate is within the court plus out-of-bounds run-off breathing room."""
        return self.is_in_bounds(tolerance_ft=buffer_ft)

    def validate_in_bounds(self, tolerance_ft: float = COURT_BUFFER_FT) -> None:
        """Validate that coordinate is within acceptable boundaries (court + buffer by default)."""
        if not self.is_in_bounds(tolerance_ft=tolerance_ft):
            x_limit = X_BOUND_FT + tolerance_ft
            y_limit = Y_BOUND_FT + tolerance_ft
            raise ValueError(
                f"Coordinate ({self.x_ft}, {self.y_ft}) exceeds acceptable court boundaries "
                f"[-{x_limit}, {x_limit}] x [-{y_limit}, {y_limit}] ft (tolerance={tolerance_ft} ft)."
            )

    def distance_to(self, other: "CourtCoordinate") -> float:
        """Calculate Euclidean distance to another court coordinate in feet."""
        dx = self.x_ft - other.x_ft
        dy = self.y_ft - other.y_ft
        return math.hypot(dx, dy)

    def distance_to_hoop(self, is_offensive: bool = True) -> float:
        """Calculate Euclidean distance to the designated hoop in feet."""
        hoop_x, hoop_y = OFFENSIVE_HOOP_LOCATION if is_offensive else DEFENSIVE_HOOP_LOCATION
        dx = self.x_ft - hoop_x
        dy = self.y_ft - hoop_y
        return math.hypot(dx, dy)


@dataclass(frozen=True)
class TimeWindow:
    """Temporal play window defined by frame indices and wall clock milliseconds."""
    start_frame: int
    end_frame: int
    start_wall_clock: int
    end_wall_clock: int

    def __post_init__(self) -> None:
        """Validate temporal ordering invariants."""
        if self.start_frame > self.end_frame:
            raise ValueError(
                f"Invalid frame window: start_frame ({self.start_frame}) > end_frame ({self.end_frame})"
            )
        if self.start_wall_clock > self.end_wall_clock:
            raise ValueError(
                f"Invalid wall clock window: start_wall_clock ({self.start_wall_clock}) > "
                f"end_wall_clock ({self.end_wall_clock})"
            )

    @property
    def duration_frames(self) -> int:
        """Duration of window in frames."""
        return self.end_frame - self.start_frame

    @property
    def duration_ms(self) -> int:
        """Duration of window in milliseconds."""
        return self.end_wall_clock - self.start_wall_clock

    @property
    def duration_seconds(self) -> float:
        """Duration of window in seconds based on wall clock milliseconds."""
        return self.duration_ms / 1000.0

    def contains_frame(self, frame_idx: int) -> bool:
        """Check if frame index falls within window (inclusive)."""
        return self.start_frame <= frame_idx <= self.end_frame

    def overlaps(self, other: "TimeWindow") -> bool:
        """Check if this time window overlaps with another."""
        return self.start_frame <= other.end_frame and other.start_frame <= self.end_frame


class ActionType(StrEnum):
    """Types of actions in SkillCorner dynamic events."""
    TOUCH = "TOUCH"
    PASS = "PASS"
    SHOT = "SHOT"
    PICK = "PICK"
    DRIVE = "DRIVE"
    DRIBBLE = "DRIBBLE"
    OFF_BALL_SCREEN = "OFF_BALL_SCREEN"


class CoverageType(StrEnum):
    """Defensive coverage types on pick and roll and screen actions."""
    BLITZ = "BLITZ"
    ICE = "ICE"
    OVER = "OVER"
    SWITCH = "SWITCH"
    UNDER = "UNDER"


class ShotRegion(StrEnum):
    """Court region categories matching SkillCorner markings vocabulary."""
    LEFT_CORNER_3 = "left corner three"
    LEFT_CORNER_2 = "left corner two"
    LEFT_WING_3 = "left wing three"
    LEFT_WING_2 = "left wing two"
    BACKCOURT = "backcourt"
    FAR = "far"
    MIDDLE_3 = "middle three"
    MIDDLE_2 = "middle two"
    KEY = "key"
    RESTRICTED_AREA = "ra"
    RIGHT_WING_3 = "right wing three"
    RIGHT_WING_2 = "right wing two"
    RIGHT_CORNER_3 = "right corner three"
    RIGHT_CORNER_2 = "right corner two"


# Semantic alias: the same regions describe passes, picks, and court zones
CourtRegion = ShotRegion
