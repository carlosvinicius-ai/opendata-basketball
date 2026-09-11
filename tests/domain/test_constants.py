"""Unit tests for domain constants."""

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


def test_random_seed():
    """Ensure random seed is fixed to 42 across the domain."""
    assert RANDOM_SEED == 42


def test_court_dimensions():
    """Verify standard FIBA court dimensions and breathing room buffer in feet."""
    assert COURT_LENGTH_FT == 91.86
    assert COURT_WIDTH_FT == 49.21
    assert X_BOUND_FT == 45.93
    assert Y_BOUND_FT == 24.605
    assert COURT_BUFFER_FT == 5.0


def test_tracking_frequency():
    """Verify broadcast tracking frame rate is 25 fps."""
    assert FPS == 25


def test_hoop_locations():
    """Verify hoop locations and coordinate conventions.

    Offensive hoop is on the negative x axis (-41.83, 0.0).
    Defensive hoop is on the positive x axis (41.83, 0.0).
    """
    assert OFFENSIVE_HOOP_X_FT == -41.83
    assert OFFENSIVE_HOOP_Y_FT == 0.0
    assert DEFENSIVE_HOOP_X_FT == 41.83
    assert DEFENSIVE_HOOP_Y_FT == 0.0

    assert OFFENSIVE_HOOP_LOCATION == (-41.83, 0.0)
    assert DEFENSIVE_HOOP_LOCATION == (41.83, 0.0)

    assert HOOP_LOCATIONS["offensive"] == OFFENSIVE_HOOP_LOCATION
    assert HOOP_LOCATIONS["defensive"] == DEFENSIVE_HOOP_LOCATION


def test_basketball_physical_specs():
    """Verify basket hardware dimensions."""
    assert HOOP_HEIGHT_FT == 10.0
    assert HOOP_RADIUS_FT == 0.75
