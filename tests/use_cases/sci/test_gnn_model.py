"""Unit tests for GNNModel (GraphSAGE)."""

import numpy as np
import torch
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader

from domain.protocols import ISCIModel
from use_cases.sci.gnn_model import GNNModel


def _create_mock_graph(label: int = 1) -> Data:
    """Helper to generate a mock PyG Data object."""
    x = torch.tensor([
        [10.0, 5.0, 4.0, 0.0],
        [-15.0, -2.0, 3.0, 0.0],
        [0.0, 0.0, 6.0, 1.0],  # Ball
    ], dtype=torch.float32)
    edge_index = torch.tensor([
        [0, 1, 1, 2],
        [1, 0, 2, 1],
    ], dtype=torch.long)
    y = torch.tensor([label], dtype=torch.long)
    data = Data(x=x, edge_index=edge_index, y=y, num_nodes=3)
    data.node_player_ids = [101, 102, None]
    data.chance_id = "test-chance"
    return data


def test_gnn_model_satisfies_protocol():
    """Verify GNNModel adheres to ISCIModel protocol."""
    model = GNNModel()
    assert isinstance(model, ISCIModel)


def test_gnn_model_train_eval_attributions(tmp_path):
    """Verify training loop, evaluation, attribution extraction, and model save/load."""
    train_graphs = [_create_mock_graph(1), _create_mock_graph(0)] * 5
    val_graphs = [_create_mock_graph(1), _create_mock_graph(0)] * 2

    train_loader = DataLoader(train_graphs, batch_size=2, shuffle=True)
    val_loader = DataLoader(val_graphs, batch_size=2, shuffle=False)

    model = GNNModel(hidden_dim=16)
    history = model.fit(train_loader, val_loader, epochs=3, patience=2)

    assert "train_loss" in history
    assert len(history["train_loss"]) == 3

    # Prediction
    sample = _create_mock_graph(1)
    probs = model.predict_proba(sample)
    assert len(probs) == 1
    assert 0.0 <= probs[0] <= 1.0

    # Evaluation
    metrics = model.evaluate(val_loader)
    assert "accuracy" in metrics
    assert "auc_roc" in metrics
    assert metrics["num_samples"] == 4

    # Node Attributions
    attributions = model.get_node_attributions(sample)
    assert isinstance(attributions, np.ndarray)
    assert len(attributions) == 3

    # Save & Load
    save_path = str(tmp_path / "model.pt")
    model.save(save_path)

    new_model = GNNModel(hidden_dim=16)
    new_model.load(save_path)
    new_probs = new_model.predict_proba(sample)
    assert np.isclose(probs[0], new_probs[0], atol=1e-5)
