"""Domain protocols and interfaces.

All interfaces follow the Dependency Inversion Principle (DIP).
Implementations in infrastructure/ or use_cases/ must conform to these interfaces.
Zero external dependencies allowed.
"""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ITrackingLoader(Protocol):
    """Interface for loading tracking frame data."""

    def load_tracking(self, game_id: int) -> Any:
        """Load tracking data for a specific game ID.

        Args:
            game_id: SkillCorner unique match identifier.

        Returns:
            Structured tracking collection or DataFrame.
        """
        ...


@runtime_checkable
class IEventLoader(Protocol):
    """Interface for loading dynamic event tables."""

    def load_events(self, game_id: int) -> dict[str, Any]:
        """Load all dynamic event tables for a specific game ID.

        Args:
            game_id: SkillCorner unique match identifier.

        Returns:
            Dictionary mapping table names to event collections or DataFrames.
        """
        ...


@runtime_checkable
class IBAVModel(Protocol):
    """Interface for Basketball Action Value (BAV) prediction model."""

    def fit(self, x: Any, y: Any) -> None:
        """Fit the BAV model on training features and target labels.

        Args:
            x: Action-level feature matrix.
            y: Binary target indicating chance scoring outcome.
        """
        ...

    def predict_proba(self, x: Any) -> Any:
        """Predict scoring probability for each action state.

        Args:
            x: Action-level feature matrix.

        Returns:
            Array or sequence of scoring probabilities in [0.0, 1.0].
        """
        ...


@runtime_checkable
class ISCIModel(Protocol):
    """Interface for Space Creation Index (SCI) Graph Neural Network model."""

    def fit(self, train_loader: Any, val_loader: Any) -> None:
        """Fit the GNN model on spatial graph data.

        Args:
            train_loader: DataLoader yielding chance-level PyG graph batches.
            val_loader: Validation DataLoader for monitoring generalization.
        """
        ...

    def get_node_attributions(self, data: Any) -> Any:
        """Compute node-level attribution / importance scores for players on court.

        Args:
            data: Single chance spatial graph or batch.

        Returns:
            Node attribution scores indicating off-ball space creation value.
        """
        ...


@runtime_checkable
class IPlayerValueAggregator(Protocol):
    """Interface for combining BAV and SCI into a unified Full Spectrum Player Value."""

    def combine(self, bav_scores: Any, sci_scores: Any) -> Any:
        """Combine and normalize on-ball and off-ball metrics.

        Args:
            bav_scores: Collection of BAV ratings per player.
            sci_scores: Collection of SCI ratings per player.

        Returns:
            Unified leaderboard ranking players by Full Spectrum Player Value.
        """
        ...
