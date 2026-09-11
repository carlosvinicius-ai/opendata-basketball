"""Domain constants for basketball coordinates, tracking frequencies, and seeds.

All units follow FIBA standards converted to feet (origin (0, 0) at court center).
Zero external dependencies allowed.
"""

# Reproducibility
RANDOM_SEED: int = 42

# Court dimensions (FIBA standard: 28.0m x 15.0m converted to feet)
COURT_LENGTH_FT: float = 91.86
COURT_WIDTH_FT: float = 49.21

# Coordinate boundary extents from court center (0, 0)
X_BOUND_FT: float = COURT_LENGTH_FT / 2.0  # 45.93 ft
Y_BOUND_FT: float = COURT_WIDTH_FT / 2.0   # 24.605 ft

# Standard run-off apron / breathing space around court boundary (feet)
COURT_BUFFER_FT: float = 5.0

# Tracking frequency
FPS: int = 25

# Basket / Hoop locations in feet (origin at court center (0, 0))
# Attacking hoop is on the negative x side (-41.83, 0.0)
# Defending hoop is on the positive x side (41.83, 0.0)
OFFENSIVE_HOOP_X_FT: float = -41.83
OFFENSIVE_HOOP_Y_FT: float = 0.0
DEFENSIVE_HOOP_X_FT: float = 41.83
DEFENSIVE_HOOP_Y_FT: float = 0.0

OFFENSIVE_HOOP_LOCATION: tuple[float, float] = (OFFENSIVE_HOOP_X_FT, OFFENSIVE_HOOP_Y_FT)
DEFENSIVE_HOOP_LOCATION: tuple[float, float] = (DEFENSIVE_HOOP_X_FT, DEFENSIVE_HOOP_Y_FT)

HOOP_LOCATIONS: dict[str, tuple[float, float]] = {
    "offensive": OFFENSIVE_HOOP_LOCATION,
    "defensive": DEFENSIVE_HOOP_LOCATION,
}

# Physical basketball specifications (feet)
HOOP_HEIGHT_FT: float = 10.0
HOOP_RADIUS_FT: float = 0.75  # 18 inches diameter = 1.5 ft -> 0.75 ft radius
BACKBOARD_DISTANCE_FT: float = 4.0  # distance from baseline to backboard
