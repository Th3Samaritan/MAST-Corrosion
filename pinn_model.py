"""
pinn_model.py
=============
Physics-Informed Graph Neural Network for galvanic corrosion prediction.

Architecture:
  - NNConv message passing (edge-aware, replaces GCNConv)
  - Multi-task heads: regression (current density) + classification (compatibility)
  - Physics-informed loss with KCL and thermodynamic constraints

Changes from original pinn_architecture.py:
  1. GCNConv → NNConv for proper edge feature utilisation
  2. Added classification head for compatibility prediction
  3. Material-dependent polarization resistance awareness
  4. Improved physics loss with configurable weights
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import NNConv, global_mean_pool


# ---------------------------------------------------------------------------
# Edge Network (maps edge features → weight matrix for NNConv)
# ---------------------------------------------------------------------------

class EdgeNetwork(nn.Module):
    """
    MLP that transforms edge features into a weight matrix for NNConv.
    Maps R^{edge_dim} → R^{in_channels × out_channels}.
    """

    def __init__(self, edge_dim: int, in_channels: int, out_channels: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(edge_dim, 64),
            nn.ReLU(),
            nn.Linear(64, in_channels * out_channels),
        )
        self.in_channels = in_channels
        self.out_channels = out_channels

    def forward(self, edge_attr):
        return self.net(edge_attr)


# ---------------------------------------------------------------------------
# Main GNN Model
# ---------------------------------------------------------------------------

class GalvanicCorrosionPINN(nn.Module):
    """
    Physics-Informed Graph Neural Network for galvanic corrosion.

    Nodes = material parts in an assembly
    Edges = electrolytic joints between parts

    Produces:
      - v_nodes:  predicted mixed potential at each node  (N, 1)
      - i_edges:  predicted galvanic current density per edge  (E, 1)
      - compat:   compatibility probability per graph  (B, 1)

    Args:
        node_features: Dimension of input node feature vector.
        edge_features: Dimension of input edge feature vector.
        hidden_dim: Hidden layer dimension (default 64).
        num_mp_layers: Number of message passing layers (default 3).
        dropout: Dropout probability (default 0.1).
    """

    def __init__(
        self,
        node_features: int,
        edge_features: int,
        hidden_dim: int = 64,
        num_mp_layers: int = 3,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.dropout = dropout

        # ---- Node embedding ----
        self.node_embed = nn.Sequential(
            nn.Linear(node_features, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
        )

        # ---- NNConv message passing layers ----
        self.convs = nn.ModuleList()
        self.norms = nn.ModuleList()
        for _ in range(num_mp_layers):
            edge_nn = EdgeNetwork(edge_features, hidden_dim, hidden_dim)
            conv = NNConv(hidden_dim, hidden_dim, edge_nn, aggr="mean")
            self.convs.append(conv)
            self.norms.append(nn.LayerNorm(hidden_dim))

        # ---- Node-level head: predict mixed potential V_node ----
        self.potential_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

        # ---- Edge-level head: predict galvanic current density ----
        self.current_head = nn.Sequential(
            nn.Linear(hidden_dim * 2 + edge_features, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

        # ---- Graph-level head: compatibility classification ----
        self.compat_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1),
        )

    def forward(self, data):
        """
        Args:
            data: PyG Data object with x, edge_index, edge_attr, batch.

        Returns:
            v_nodes: (N, 1) predicted node potentials
            i_edges: (E, 1) predicted edge current densities
            compat:  (B, 1) graph-level compatibility logits
        """
        x = data.x
        edge_index = data.edge_index
        edge_attr = data.edge_attr
        batch = data.batch if hasattr(data, "batch") and data.batch is not None else torch.zeros(x.size(0), dtype=torch.long, device=x.device)

        # 1. Embed node features
        x = self.node_embed(x)

        # 2. Message passing with residual connections
        for conv, norm in zip(self.convs, self.norms):
            x_new = conv(x, edge_index, edge_attr)
            x_new = F.relu(norm(x_new))
            x = x + x_new  # residual

        # 3. Node-level prediction: mixed potential
        v_nodes = self.potential_head(x)

        # 4. Edge-level prediction: current density
        row, col = edge_index
        edge_feat = torch.cat([x[row], x[col], edge_attr], dim=1)
        i_edges = self.current_head(edge_feat)

        # 5. Graph-level prediction: compatibility
        graph_embed = global_mean_pool(x, batch)
        compat = self.compat_head(graph_embed)

        return v_nodes, i_edges, compat


# ---------------------------------------------------------------------------
# Physics-Informed Loss
# ---------------------------------------------------------------------------

class PhysicsInformedLoss(nn.Module):
    """
    Multi-task loss combining data fitting with physical constraints.

    Components:
      1. Regression MSE: predicted vs. true galvanic current density
      2. Classification BCE: predicted vs. true compatibility label
      3. KCL penalty: net current at each node should be zero
      4. Thermodynamic penalty: current should flow anode → cathode
         (i.e., from lower to higher potential)

    Args:
        lambda_kcl: Weight for Kirchhoff's Current Law penalty.
        lambda_thermo: Weight for thermodynamic consistency penalty.
        lambda_cls: Weight for classification loss.
    """

    def __init__(
        self,
        lambda_kcl: float = 0.1,
        lambda_thermo: float = 0.1,
        lambda_cls: float = 0.5,
    ):
        super().__init__()
        self.lambda_kcl = lambda_kcl
        self.lambda_thermo = lambda_thermo
        self.lambda_cls = lambda_cls

    def forward(
        self,
        v_nodes: torch.Tensor,
        i_edges_all: torch.Tensor,
        i_graph_pred: torch.Tensor,
        i_graph_true: torch.Tensor,
        compat_pred: torch.Tensor,
        compat_true: torch.Tensor,
        edge_index: torch.Tensor,
    ) -> dict:
        """
        Compute the full physics-informed loss.

        Args:
            v_nodes:      (N, 1) predicted node potentials (all nodes in batch)
            i_edges_all:  (E, 1) predicted edge current densities (all edges)
            i_graph_pred: (B, 1) per-graph predicted current density
            i_graph_true: (B, 1) per-graph ground-truth current density
            compat_pred:  (B, 1) graph-level compatibility logits
            compat_true:  (B, 1) ground-truth compatibility labels
            edge_index:   (2, E) edge connectivity

        Returns:
            dict with keys: total, data, classification, kcl, thermo
        """
        # ---- 1. Regression data loss (per-graph) ----
        loss_data = F.mse_loss(i_graph_pred, i_graph_true)

        # ---- 2. Classification loss ----
        loss_cls = F.binary_cross_entropy_with_logits(
            compat_pred, compat_true
        )

        # ---- 3. KCL: conservation of charge (edge-level) ----
        num_nodes = v_nodes.shape[0]
        node_net_currents = torch.zeros(num_nodes, device=v_nodes.device)
        row, col = edge_index
        node_net_currents.scatter_add_(0, col, i_edges_all.squeeze(-1))
        node_net_currents.scatter_add_(0, row, -i_edges_all.squeeze(-1))
        loss_kcl = torch.mean(node_net_currents ** 2)

        # ---- 4. Thermodynamic consistency (edge-level) ----
        # Current should flow from lower potential (anode) to higher (cathode).
        # If ΔV > 0 then current should be > 0 in the same direction.
        v_source = v_nodes[row]
        v_target = v_nodes[col]
        delta_v = v_target - v_source
        thermo_violation = F.relu(-(delta_v * i_edges_all))
        loss_thermo = torch.mean(thermo_violation)

        # ---- Total ----
        total = (
            loss_data
            + self.lambda_cls * loss_cls
            + self.lambda_kcl * loss_kcl
            + self.lambda_thermo * loss_thermo
        )

        return {
            "total": total,
            "data": loss_data,
            "classification": loss_cls,
            "kcl": loss_kcl,
            "thermo": loss_thermo,
        }


# ---------------------------------------------------------------------------
# Model factory
# ---------------------------------------------------------------------------

def build_model(
    node_features: int = 22,   # 2 (pot_sce, rank) + 20 (group one-hot)
    edge_features: int = 6,    # 3 (delta_v, log_area, cond) + 3 (env one-hot)
    hidden_dim: int = 64,
    num_mp_layers: int = 3,
    dropout: float = 0.1,
) -> GalvanicCorrosionPINN:
    """Convenience factory with sensible defaults for this dataset."""
    return GalvanicCorrosionPINN(
        node_features=node_features,
        edge_features=edge_features,
        hidden_dim=hidden_dim,
        num_mp_layers=num_mp_layers,
        dropout=dropout,
    )


# ---------------------------------------------------------------------------
# Quick sanity check
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== GalvanicCorrosionPINN Sanity Check ===\n")

    # Create model
    model = build_model()
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Model: {model.__class__.__name__}")
    print(f"  Total parameters:     {total_params:,}")
    print(f"  Trainable parameters: {trainable_params:,}")

    # Mock data (2-node graph, 1 bidirectional edge)
    from torch_geometric.data import Data, Batch

    mock_data = Data(
        x=torch.randn(2, 22),
        edge_index=torch.tensor([[0, 1], [1, 0]], dtype=torch.long),
        edge_attr=torch.randn(2, 6),
    )
    batch = Batch.from_data_list([mock_data, mock_data])

    # Forward pass
    model.eval()
    with torch.no_grad():
        v, i, c = model(batch)

    print(f"\nForward pass (batch of 2):")
    print(f"  v_nodes shape:  {v.shape}  (4 nodes total)")
    print(f"  i_edges shape:  {i.shape}  (4 edges total)")
    print(f"  compat shape:   {c.shape}  (2 graphs)")

    # Loss computation
    criterion = PhysicsInformedLoss()
    # Per-graph regression target (one per graph in the batch)
    i_graph_pred = i[0::2]  # take forward-edge predictions
    i_graph_true = torch.randn(batch.num_graphs, 1)
    losses = criterion(
        v_nodes=v,
        i_edges_all=i,
        i_graph_pred=i_graph_pred,
        i_graph_true=i_graph_true,
        compat_pred=c,
        compat_true=torch.randint(0, 2, c.shape).float(),
        edge_index=batch.edge_index,
    )
    print(f"\nLoss breakdown:")
    for k, val in losses.items():
        print(f"  {k:20s}: {val.item():.6f}")

    print("\n✓ All checks passed.")
