"""Domain layer: Pure entities, value objects, business rules, constants, and protocols.

ZERO external dependencies allowed (no pandas, polars, torch, or I/O of any kind).
"""

from domain.constants import (
    COURT_BUFFER_FT,
    COURT_LENGTH_FT,
    COURT_WIDTH_FT,
    DEFENSIVE_HOOP_LOCATION,
    DEFENSIVE_HOOP_X_FT,
    DEFENSIVE_HOOP_Y_FT,
    FPS,
    HOOP_HEIGHT_FT,
    HOOP_LOCATIONS,
    HOOP_RADIUS_FT,
    OFFENSIVE_HOOP_LOCATION,
    OFFENSIVE_HOOP_X_FT,
    OFFENSIVE_HOOP_Y_FT,
    RANDOM_SEED,
    X_BOUND_FT,
    Y_BOUND_FT,
)
from domain.entities import (
    Action,
    Chance,
    Game,
    Player,
    PlayerValue,
    TrackingFrame,
)
from domain.protocols import (
    IBAVModel,
    IEventLoader,
    IPlayerValueAggregator,
    ISCIModel,
    ITrackingLoader,
)
from domain.value_objects import (
    ActionType,
    CourtCoordinate,
    CourtRegion,
    CoverageType,
    ShotRegion,
    TimeWindow,
)

__all__ = [
    # Constants
    "RANDOM_SEED",
    "COURT_LENGTH_FT",
    "COURT_WIDTH_FT",
    "COURT_BUFFER_FT",
    "X_BOUND_FT",
    "Y_BOUND_FT",
    "FPS",
    "OFFENSIVE_HOOP_X_FT",
    "OFFENSIVE_HOOP_Y_FT",
    "DEFENSIVE_HOOP_X_FT",
    "DEFENSIVE_HOOP_Y_FT",
    "OFFENSIVE_HOOP_LOCATION",
    "DEFENSIVE_HOOP_LOCATION",
    "HOOP_LOCATIONS",
    "HOOP_HEIGHT_FT",
    "HOOP_RADIUS_FT",
    # Entities
    "Player",
    "Game",
    "Chance",
    "Action",
    "TrackingFrame",
    "PlayerValue",
    # Value Objects
    "CourtCoordinate",
    "TimeWindow",
    "ActionType",
    "CoverageType",
    "ShotRegion",
    "CourtRegion",
    # Protocols
    "ITrackingLoader",
    "IEventLoader",
    "IBAVModel",
    "ISCIModel",
    "IPlayerValueAggregator",
]
