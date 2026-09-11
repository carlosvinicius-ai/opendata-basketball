"""Unit tests for domain protocols and DIP interfaces using pure dummy classes."""

from typing import Any

from domain.protocols import (
    IBAVModel,
    IEventLoader,
    IPlayerValueAggregator,
    ISCIModel,
    ITrackingLoader,
)


class DummyTrackingLoader:
    def load_tracking(self, game_id: int) -> Any:
        return {"game_id": game_id, "frames": []}


class DummyEventLoader:
    def load_events(self, game_id: int) -> dict[str, Any]:
        return {"chances": [], "shots": []}


class DummyBAVModel:
    def fit(self, x: Any, y: Any) -> None:
        pass

    def predict_proba(self, x: Any) -> Any:
        return [0.45]


class DummySCIModel:
    def fit(self, train_loader: Any, val_loader: Any) -> None:
        pass

    def get_node_attributions(self, data: Any) -> Any:
        return [0.1, 0.2, 0.3]


class DummyPlayerValueAggregator:
    def combine(self, bav_scores: Any, sci_scores: Any) -> Any:
        return {"ranking": []}


class IncompleteLoader:
    """Class missing required protocol methods."""
    pass


def test_protocol_runtime_checkable():
    """Verify runtime checkability and interface compliance for domain protocols."""
    tracking_loader = DummyTrackingLoader()
    assert isinstance(tracking_loader, ITrackingLoader)

    event_loader = DummyEventLoader()
    assert isinstance(event_loader, IEventLoader)

    bav_model = DummyBAVModel()
    assert isinstance(bav_model, IBAVModel)

    sci_model = DummySCIModel()
    assert isinstance(sci_model, ISCIModel)

    aggregator = DummyPlayerValueAggregator()
    assert isinstance(aggregator, IPlayerValueAggregator)


def test_protocol_rejection_of_incomplete_implementation():
    """Verify that classes missing protocol methods are rejected by isinstance."""
    incomplete = IncompleteLoader()
    assert not isinstance(incomplete, ITrackingLoader)
    assert not isinstance(incomplete, IEventLoader)
    assert not isinstance(incomplete, IBAVModel)
    assert not isinstance(incomplete, ISCIModel)
    assert not isinstance(incomplete, IPlayerValueAggregator)
