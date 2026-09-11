"""Unit tests for domain entities and immutability rules."""

from dataclasses import FrozenInstanceError

import pytest

from domain.entities import (
    Action,
    Chance,
    Game,
    Player,
    PlayerValue,
    TrackingFrame,
)


def test_player_entity_instantiation_and_immutability():
    """Verify Player instantiation and frozen immutability."""
    player = Player(
        id=101,
        canonical_id=101,
        name="Marcelinho Huertas",
        position="PG",
        team_id=12,
    )
    assert player.id == 101
    assert player.canonical_id == 101
    assert player.name == "Marcelinho Huertas"
    assert player.position == "PG"
    assert player.team_id == 12

    with pytest.raises(FrozenInstanceError):
        player.name = "Different Name"  # type: ignore[misc]


def test_game_entity_instantiation_and_immutability():
    """Verify Game entity creation and properties."""
    game = Game(id=114243, date="2025-10-15", home_team_id=1, away_team_id=2)
    assert game.id == 114243
    assert game.date == "2025-10-15"
    assert game.home_team_id == 1
    assert game.away_team_id == 2

    with pytest.raises(FrozenInstanceError):
        game.home_team_id = 99  # type: ignore[misc]


def test_chance_entity_and_scoring_opportunity():
    """Verify Chance entity behavior and scoring opportunity property."""
    chance = Chance(
        id=5001,
        game_id=114243,
        possession_id=201,
        off_team_id=1,
        def_team_id=2,
        off_players=(101, 102, 103, 104, 105),
        def_players=(201, 202, 203, 204, 205),
        outcome="made_basket",
        usable=True,
    )
    assert chance.id == 5001
    assert chance.outcome == "made_basket"
    assert chance.is_scoring_opportunity is True

    # Unusable chance
    unusable_chance = Chance(
        id=5002,
        game_id=114243,
        possession_id=201,
        off_team_id=1,
        def_team_id=2,
        off_players=(101, 102, 103, 104, 105),
        def_players=(201, 202, 203, 204, 205),
        usable=False,
    )
    assert unusable_chance.is_scoring_opportunity is False

    with pytest.raises(FrozenInstanceError):
        chance.outcome = "missed_basket"  # type: ignore[misc]


def test_action_entity_duration_and_immutability():
    """Verify Action entity duration calculation and immutability."""
    action = Action(
        id=901,
        type="PICK",
        player_id=101,
        chance_id=5001,
        touch_id=45,
        start_frame=100,
        end_frame=150,
        location=(-25.0, 5.0),
    )
    assert action.id == 901
    assert action.type == "PICK"
    assert action.duration_frames == 50
    assert action.location == (-25.0, 5.0)

    with pytest.raises(FrozenInstanceError):
        action.end_frame = 200  # type: ignore[misc]


def test_tracking_frame_entity():
    """Verify TrackingFrame properties and immutability."""
    frame = TrackingFrame(
        frame_idx=1000,
        wall_clock=40000,
        game_clock=580.5,
        period=1,
        shot_clock=18.2,
        players=({"player_id": 101, "x": -10.5, "y": 2.1},),
        ball={"x": -10.0, "y": 2.0, "z": 4.5},
    )
    assert frame.frame_idx == 1000
    assert frame.period == 1
    assert frame.shot_clock == 18.2
    assert len(frame.players) == 1
    assert frame.ball is not None

    with pytest.raises(FrozenInstanceError):
        frame.frame_idx = 1001  # type: ignore[misc]


def test_player_value_entity_and_fspv_score():
    """Verify PlayerValue metrics and fspv_score alias."""
    val = PlayerValue(
        player_id=101,
        bav_score=1.45,
        sci_score=0.85,
        combined_score=1.15,
        games_sample=10,
    )
    assert val.player_id == 101
    assert val.bav_score == 1.45
    assert val.sci_score == 0.85
    assert val.combined_score == 1.15
    assert val.fspv_score == 1.15

    with pytest.raises(FrozenInstanceError):
        val.bav_score = 2.0  # type: ignore[misc]


def test_entities_hashable_and_comparable():
    """Verify that frozen entities can be stored in sets or used as dict keys."""
    p1 = Player(id=1, canonical_id=1, name="A", position="G", team_id=10)
    p2 = Player(id=1, canonical_id=1, name="A", position="G", team_id=10)
    p3 = Player(id=2, canonical_id=2, name="B", position="F", team_id=10)

    assert p1 == p2
    assert p1 != p3
    assert len({p1, p2, p3}) == 2
