"""Unit tests for domain value objects, enums, and geometric constraints."""

import math

import pytest

from domain.constants import X_BOUND_FT, Y_BOUND_FT
from domain.value_objects import (
    ActionType,
    CourtCoordinate,
    CourtRegion,
    CoverageType,
    ShotRegion,
    TimeWindow,
)


def test_court_coordinate_bounds():
    """Verify coordinate bounds detection against FIBA court dimensions and breathing room buffer."""
    center = CourtCoordinate(0.0, 0.0)
    assert center.is_in_bounds() is True
    assert center.is_in_playable_area() is True

    corner = CourtCoordinate(X_BOUND_FT, Y_BOUND_FT)
    assert corner.is_in_bounds() is True
    assert corner.is_in_playable_area() is True

    # Slightly out of lines (e.g. step out of bounds by 1 ft)
    out_step = CourtCoordinate(X_BOUND_FT + 1.0, 0.0)
    assert out_step.is_in_bounds() is False  # Strictly out of court lines
    assert out_step.is_in_playable_area() is True  # Within 5 ft breathing room buffer

    # Within buffer validates by default
    out_step.validate_in_bounds()

    # Strictly out-of-bounds validation raises ValueError when tolerance=0
    with pytest.raises(ValueError, match="exceeds acceptable court boundaries"):
        out_step.validate_in_bounds(tolerance_ft=0.0)

    # Completely outside arena/tracking limits (e.g. 100 ft)
    wild_coord = CourtCoordinate(X_BOUND_FT + 20.0, 0.0)
    assert wild_coord.is_in_playable_area() is False
    with pytest.raises(ValueError, match="exceeds acceptable court boundaries"):
        wild_coord.validate_in_bounds()


def test_court_coordinate_distances():
    """Verify Euclidean distance calculations between coordinates and to hoops."""
    c1 = CourtCoordinate(0.0, 0.0)
    c2 = CourtCoordinate(3.0, 4.0)
    assert math.isclose(c1.distance_to(c2), 5.0)

    # Distance to offensive hoop (-41.83, 0.0)
    at_hoop = CourtCoordinate(-41.83, 0.0)
    assert math.isclose(at_hoop.distance_to_hoop(is_offensive=True), 0.0)

    # Distance from center to defensive hoop (41.83, 0.0)
    assert math.isclose(c1.distance_to_hoop(is_offensive=False), 41.83)


def test_time_window_valid_durations():
    """Verify TimeWindow duration calculations."""
    tw = TimeWindow(start_frame=100, end_frame=150, start_wall_clock=4000, end_wall_clock=6000)
    assert tw.duration_frames == 50
    assert tw.duration_ms == 2000
    assert tw.duration_seconds == 2.0
    assert tw.contains_frame(125) is True
    assert tw.contains_frame(99) is False
    assert tw.contains_frame(151) is False


def test_time_window_invariants():
    """Verify that inverted frame or clock bounds raise ValueError."""
    with pytest.raises(ValueError, match="Invalid frame window"):
        TimeWindow(start_frame=200, end_frame=100, start_wall_clock=1000, end_wall_clock=2000)

    with pytest.raises(ValueError, match="Invalid wall clock window"):
        TimeWindow(start_frame=100, end_frame=200, start_wall_clock=3000, end_wall_clock=2000)


def test_time_window_overlap():
    """Verify temporal overlap checking."""
    tw1 = TimeWindow(start_frame=10, end_frame=30, start_wall_clock=100, end_wall_clock=300)
    tw2 = TimeWindow(start_frame=25, end_frame=40, start_wall_clock=250, end_wall_clock=400)
    tw3 = TimeWindow(start_frame=35, end_frame=50, start_wall_clock=350, end_wall_clock=500)

    assert tw1.overlaps(tw2) is True
    assert tw2.overlaps(tw1) is True
    assert tw1.overlaps(tw3) is False


def test_action_type_enum():
    """Verify all ActionType enum values and string compatibility."""
    expected_actions = {
        "TOUCH",
        "PASS",
        "SHOT",
        "PICK",
        "DRIVE",
        "DRIBBLE",
        "OFF_BALL_SCREEN",
    }
    actual_actions = {item.value for item in ActionType}
    assert actual_actions == expected_actions

    # String equality behavior
    assert ActionType.TOUCH == "TOUCH"
    assert ActionType.SHOT == "SHOT"


def test_coverage_type_enum():
    """Verify CoverageType enum values."""
    expected_coverages = {"BLITZ", "ICE", "OVER", "SWITCH", "UNDER"}
    actual_coverages = {item.value for item in CoverageType}
    assert actual_coverages == expected_coverages
    assert CoverageType.ICE == "ICE"


def test_shot_region_enum_completeness():
    """Verify that ShotRegion covers all 14 SkillCorner court regions."""
    expected_regions = {
        "left corner three",
        "left corner two",
        "left wing three",
        "left wing two",
        "backcourt",
        "far",
        "middle three",
        "middle two",
        "key",
        "ra",
        "right wing three",
        "right wing two",
        "right corner three",
        "right corner two",
    }
    actual_regions = {item.value for item in ShotRegion}
    assert actual_regions == expected_regions

    # Verify alias
    assert CourtRegion is ShotRegion
    assert CourtRegion.RESTRICTED_AREA.value == "ra"
    assert CourtRegion.KEY.value == "key"
