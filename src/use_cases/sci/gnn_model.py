"""GraphSAGE GNN Model for Space Creation Index (SCI).

Implements ISCIModel protocol from domain.protocols using PyTorch Geometric.
Learns spatial patterns predictive of scoring opportunities and computes
node attributions reflecting off-ball space generation.
"""

from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.metrics import accuracy_score, confusion_matrix, roc_auc_score
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader
from torch_geometric.nn import SAGEConv, global_mean_pool

from domain.constants import RANDOM_SEED
from domain.protocols import ISCIModel


class GraphSAGECore(nn.Module):
    """2-layer GraphSAGE architecture with global mean pooling and binary classification head."""

    def __init__(
        self,
        in_channels: int = 4,
        hidden_dim: int = 64,
        dropout: float = 0.3,
    ) -> None:
        super().__init__()
        self.conv1 = SAGEConv(in_channels, hidden_dim)
        self.conv2 = SAGEConv(hidden_dim, hidden_dim)
        self.dropout = nn.Dropout(dropout)
        self.head = nn.Linear(hidden_dim, 1)

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        batch: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Forward pass.

        Returns:
            logits: Graph-level predictions [batch_size, 1].
            node_emb: Node embeddings before pooling [total_nodes, hidden_dim].
        """
        if batch is None:
            batch = torch.zeros(x.size(0), dtype=torch.long, device=x.device)

        h = self.conv1(x, edge_index)
        h = F.relu(h)
        h = self.dropout(h)

        h = self.conv2(h, edge_index)
        h = F.relu(h)
        node_emb = h

        h_pool = global_mean_pool(h, batch)
        h_pool = self.dropout(h_pool)
        logits = self.head(h_pool)
        return logits, node_emb


class GNNModel(ISCIModel):
    """GNN wrapper that implements the domain.protocols.ISCIModel protocol."""

    def __init__(
        self,
        in_channels: int = 4,
        hidden_dim: int = 64,
        dropout: float = 0.3,
        lr: float = 1e-3,
        weight_decay: float = 1e-4,
        device: str | None = None,
    ) -> None:
        torch.manual_seed(RANDOM_SEED)
        np.random.seed(RANDOM_SEED)

        self.device = torch.device(device if device else ("cuda" if torch.cuda.is_available() else "cpu"))
        self.model = GraphSAGECore(
            in_channels=in_channels,
            hidden_dim=hidden_dim,
            dropout=dropout,
        ).to(self.device)

        self.lr = lr
        self.weight_decay = weight_decay
        self.optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=self.lr,
            weight_decay=self.weight_decay,
        )
        self.criterion = nn.BCEWithLogitsLoss()

    def fit(
        self,
        train_loader: Any,
        val_loader: Any | None = None,
        epochs: int = 50,
        patience: int = 20,
    ) -> dict[str, list[float]]:
        """Fit the GNN model with early stopping on validation loss."""
        self.model.train()
        history: dict[str, list[float]] = {"train_loss": [], "val_loss": []}

        best_val_loss = float("inf")
        patience_counter = 0
        best_state_dict = None

        for _epoch in range(epochs):
            total_train_loss = 0.0
            num_batches = 0

            self.model.train()
            for batch in train_loader:
                batch = batch.to(self.device)
                self.optimizer.zero_grad()

                logits, _ = self.model(batch.x, batch.edge_index, batch.batch)
                y = batch.y.view(-1, 1).float()
                loss = self.criterion(logits, y)

                loss.backward()
                self.optimizer.step()

                total_train_loss += loss.item()
                num_batches += 1

            avg_train_loss = total_train_loss / max(1, num_batches)
            history["train_loss"].append(avg_train_loss)

            # Validation step
            if val_loader is not None:
                self.model.eval()
                total_val_loss = 0.0
                val_batches = 0
                with torch.no_grad():
                    for batch in val_loader:
                        batch = batch.to(self.device)
                        logits, _ = self.model(batch.x, batch.edge_index, batch.batch)
                        y = batch.y.view(-1, 1).float()
                        val_loss = self.criterion(logits, y)
                        total_val_loss += val_loss.item()
                        val_batches += 1

                avg_val_loss = total_val_loss / max(1, val_batches)
                history["val_loss"].append(avg_val_loss)

                if avg_val_loss < best_val_loss:
                    best_val_loss = avg_val_loss
                    best_state_dict = {k: v.cpu().clone() for k, v in self.model.state_dict().items()}
                    patience_counter = 0
                else:
                    patience_counter += 1
                    if patience_counter >= patience:
                        break

        if best_state_dict is not None:
            self.model.load_state_dict(best_state_dict)

        return history

    def predict_proba(self, loader_or_data: Any) -> np.ndarray:
        """Predict probability of scoring for each chance graph."""
        self.model.eval()
        if isinstance(loader_or_data, (Data, list)):
            if isinstance(loader_or_data, Data):
                loader = DataLoader([loader_or_data], batch_size=1, shuffle=False)
            else:
                loader = DataLoader(loader_or_data, batch_size=32, shuffle=False)
        else:
            loader = loader_or_data

        probs: list[float] = []
        with torch.no_grad():
            for batch in loader:
                batch = batch.to(self.device)
                logits, _ = self.model(batch.x, batch.edge_index, batch.batch)
                batch_probs = torch.sigmoid(logits).view(-1).cpu().tolist()
                probs.extend(batch_probs)

        return np.array(probs)

    def evaluate(self, test_loader: Any) -> dict[str, Any]:
        """Compute evaluation metrics: AUC-ROC, Accuracy, Confusion Matrix."""
        self.model.eval()
        all_preds: list[float] = []
        all_targets: list[int] = []

        with torch.no_grad():
            for batch in test_loader:
                batch = batch.to(self.device)
                logits, _ = self.model(batch.x, batch.edge_index, batch.batch)
                probs = torch.sigmoid(logits).view(-1).cpu().tolist()
                targets = batch.y.view(-1).long().cpu().tolist()

                all_preds.extend(probs)
                all_targets.extend(targets)

        y_true = np.array(all_targets)
        y_pred = np.array(all_preds)
        y_bin = (y_pred >= 0.5).astype(int)

        acc = float(accuracy_score(y_true, y_bin)) if len(y_true) > 0 else 0.0
        try:
            auc = float(roc_auc_score(y_true, y_pred)) if len(np.unique(y_true)) > 1 else 0.5
        except Exception:
            auc = 0.5

        cm = confusion_matrix(y_true, y_bin).tolist() if len(y_true) > 0 else []

        return {
            "accuracy": acc,
            "auc_roc": auc,
            "confusion_matrix": cm,
            "num_samples": len(y_true),
        }

    def get_node_attributions(self, data: Any) -> np.ndarray:
        """Compute node-level attribution scores indicating space creation value.

        Uses Input x Gradient (sensitivity saliency) to estimate how each node
        contributes to the predicted scoring opportunity.

        Args:
            data: Single PyG Data object or GraphData.

        Returns:
            np.ndarray of shape [num_nodes] containing attribution scores.
        """
        self.model.eval()

        if not isinstance(data, Data) and hasattr(data, "to_torch_geometric"):
            data = data.to_torch_geometric()

        if not isinstance(data, Data):
            raise ValueError(f"Expected PyG Data object, got {type(data)}")

        x = data.x.clone().detach().to(self.device)
        x.requires_grad = True
        edge_index = data.edge_index.to(self.device)
        batch = torch.zeros(x.size(0), dtype=torch.long, device=self.device)

        logits, _ = self.model(x, edge_index, batch)
        prob = torch.sigmoid(logits)

        # Gradient of predicted probability with respect to node features
        prob.backward(retain_graph=False)

        if x.grad is None:
            return np.zeros(x.size(0))

        # Attribution: dot product of input feature vector with gradient
        attribution = (x.grad * x).sum(dim=-1).detach().cpu().numpy()
        return attribution

    def save(self, path: str = "models/sci_graphsage.pt") -> None:
        """Save model state dictionary to disk."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        torch.save(self.model.state_dict(), target)

    def load(self, path: str = "models/sci_graphsage.pt") -> None:
        """Load model state dictionary from disk."""
        target = Path(path)
        if not target.exists():
            raise FileNotFoundError(f"Model file {path} not found.")
        state = torch.load(target, map_location=self.device, weights_only=True)
        self.model.load_state_dict(state)
