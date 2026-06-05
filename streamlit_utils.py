"""
streamlit_utils.py
==================
Backend utilities for the Galvanic Corrosion PINN Streamlit dashboard.

Handles:
  - Model loading from checkpoint
  - Inference graph construction (PyG Data objects)
  - Single and batch prediction
  - Training log parsing
  - Heatmap data generation
"""

import os
import torch
import numpy as np
import pandas as pd
from torch_geometric.data import Data

from pinn_model import GalvanicCorrosionPINN, build_model
from graph_dataset import (
    MATERIAL_GROUPS,
    GROUP_TO_IDX,
    NUM_GROUPS,
    ENVIRONMENT_NAMES,
    ENV_TO_IDX,
    NUM_ENVS,
    ENVIRONMENT_CONDUCTIVITY,
    _load_galvanic_lookup,
    _group_one_hot,
    _env_one_hot,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BEST_MODEL_PATH = os.path.join(
    PROJECT_DIR, "Post training", "1st Result", "best_model.pt"
)
TRAINING_LOG_1 = os.path.join(
    PROJECT_DIR, "Post training", "1st Result", "training_log.csv"
)
TRAINING_LOG_2 = os.path.join(
    PROJECT_DIR, "Post training", "2nd Result", "training_log (1).csv"
)
TRAINING_LOG_3 = os.path.join(
    PROJECT_DIR, "Post training", "3rd Result", "training_log.csv"
)
GALVANIC_CSV = os.path.join(PROJECT_DIR, "pdf_table2_galvanic_series.csv")
SYNTHETIC_CSV = os.path.join(PROJECT_DIR, "synthetic_galvanic_joints_full.csv")

# Training images
TRAINING_IMAGES_1 = {
    "data_exploration": os.path.join(
        PROJECT_DIR, "Post training", "1st Result", "data_exploration.png"
    ),
    "training_curves": os.path.join(
        PROJECT_DIR, "Post training", "1st Result", "training_curves.png"
    ),
    "prediction_analysis": os.path.join(
        PROJECT_DIR, "Post training", "1st Result", "prediction_analysis.png"
    ),
}
TRAINING_IMAGES_2 = {
    "data_exploration": os.path.join(
        PROJECT_DIR, "Post training", "2nd Result", "data_exploration (1).png"
    ),
    "training_curves": os.path.join(
        PROJECT_DIR, "Post training", "2nd Result", "training_curves (1).png"
    ),
    "prediction_analysis": os.path.join(
        PROJECT_DIR, "Post training", "2nd Result", "prediction_analysis (1).png"
    ),
}
TRAINING_IMAGES_3 = {
    "data_exploration": os.path.join(
        PROJECT_DIR, "Post training", "3rd Result", "data_exploration.png"
    ),
    "training_curves": os.path.join(
        PROJECT_DIR, "Post training", "3rd Result", "training_curves.png"
    ),
    "prediction_analysis": os.path.join(
        PROJECT_DIR, "Post training", "3rd Result", "prediction_analysis.png"
    ),
}


# ---------------------------------------------------------------------------
# Galvanic data
# ---------------------------------------------------------------------------

def load_galvanic_data():
    """Load the galvanic series lookup and material list."""
    lookup = _load_galvanic_lookup(GALVANIC_CSV)
    df = pd.read_csv(GALVANIC_CSV)
    materials = df["Material"].tolist()
    return lookup, materials, df


# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------

def load_model(model_path: str = None, device: str = "cpu"):
    """
    Load the best model from checkpoint.

    Returns:
        model: GalvanicCorrosionPINN in eval mode
        checkpoint: full checkpoint dict
        device: torch.device used
    """
    if model_path is None:
        model_path = BEST_MODEL_PATH

    device = torch.device(device)
    checkpoint = torch.load(model_path, map_location=device, weights_only=False)

    # Reconstruct model from checkpoint args or defaults
    args = checkpoint.get("args", {})
    model = build_model(
        node_features=args.get("node_features", 22),
        edge_features=args.get("edge_features", 6),
        hidden_dim=args.get("hidden_dim", 64),
        num_mp_layers=args.get("num_mp_layers", 3),
        dropout=args.get("dropout", 0.1),
    )

    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()

    return model, checkpoint, device


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_prediction_graph(
    anode_name: str,
    cathode_name: str,
    environment: str,
    area_ratio: float,
    galvanic_lookup: dict,
) -> Data:
    """
    Build a PyG Data object for a single prediction.

    Args:
        anode_name: Name of the anode material (from galvanic series)
        cathode_name: Name of the cathode material
        environment: One of the three environment names
        area_ratio: Cathode/Anode surface area ratio
        galvanic_lookup: Material lookup dict from load_galvanic_data()

    Returns:
        PyG Data object ready for model inference
    """
    anode_info = galvanic_lookup.get(anode_name, {})
    cathode_info = galvanic_lookup.get(cathode_name, {})

    anode_group = anode_info.get("group", "")
    cathode_group = cathode_info.get("group", "")

    # Node features
    def _node_feat(info, group):
        pot_sce = info.get("potential_sce", 0.0)
        rank = info.get("rank_norm", 0.5)
        oh = _group_one_hot(group)
        return np.concatenate([[pot_sce, rank], oh]).astype(np.float32)

    x_anode = _node_feat(anode_info, anode_group)
    x_cathode = _node_feat(cathode_info, cathode_group)
    x = np.stack([x_anode, x_cathode])

    # Edge features
    pot_anode = anode_info.get("potential_sce", 0.0)
    pot_cathode = cathode_info.get("potential_sce", 0.0)
    delta_v = abs(pot_cathode - pot_anode)
    log_area_ratio = np.log1p(area_ratio)
    conductivity = ENVIRONMENT_CONDUCTIVITY.get(environment, 0.01)
    env_oh = _env_one_hot(environment)

    edge_feat = np.concatenate(
        [[delta_v, log_area_ratio, conductivity], env_oh]
    ).astype(np.float32)

    edge_index = torch.tensor([[0, 1], [1, 0]], dtype=torch.long)
    edge_attr = np.stack([edge_feat, edge_feat])

    return Data(
        x=torch.tensor(x, dtype=torch.float),
        edge_index=edge_index,
        edge_attr=torch.tensor(edge_attr, dtype=torch.float),
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------

def predict_single(
    model,
    anode_name: str,
    cathode_name: str,
    environment: str,
    area_ratio: float,
    galvanic_lookup: dict,
    device=None,
) -> dict:
    """
    Run a single prediction.

    Returns dict with:
        current_density: predicted galvanic current density (A/m²)
        compatibility_prob: probability of being unfavorable (0-1)
        compatibility_label: "Compatible" or "Unfavorable"
        v_anode: predicted anode potential
        v_cathode: predicted cathode potential
        delta_v: potential difference
    """
    if device is None:
        device = next(model.parameters()).device

    graph = build_prediction_graph(
        anode_name, cathode_name, environment, area_ratio, galvanic_lookup
    )
    graph = graph.to(device)

    # Add batch vector (single graph)
    graph.batch = torch.zeros(graph.x.size(0), dtype=torch.long, device=device)

    with torch.no_grad():
        v_nodes, i_edges, compat = model(graph)

    # Extract results
    v_anode = v_nodes[0].item()
    v_cathode = v_nodes[1].item()
    current_density = abs(i_edges[0].item())  # forward edge
    compat_prob = torch.sigmoid(compat[0]).item()

    return {
        "current_density": current_density,
        "compatibility_prob": compat_prob,
        "compatibility_label": "Unfavorable" if compat_prob >= 0.5 else "Compatible",
        "v_anode": v_anode,
        "v_cathode": v_cathode,
        "delta_v": abs(v_cathode - v_anode),
        "raw_compat_logit": compat[0].item(),
    }


def predict_batch(
    model,
    pairs: list,
    galvanic_lookup: dict,
    device=None,
) -> list:
    """
    Run predictions on a batch of material pairs.

    Args:
        pairs: list of dicts with keys: anode, cathode, environment, area_ratio

    Returns:
        list of prediction dicts
    """
    results = []
    for pair in pairs:
        result = predict_single(
            model,
            pair["anode"],
            pair["cathode"],
            pair["environment"],
            pair["area_ratio"],
            galvanic_lookup,
            device,
        )
        result["anode"] = pair["anode"]
        result["cathode"] = pair["cathode"]
        result["environment"] = pair["environment"]
        result["area_ratio"] = pair["area_ratio"]
        results.append(result)
    return results


# ---------------------------------------------------------------------------
# Training logs
# ---------------------------------------------------------------------------

def load_training_log(path: str = None) -> pd.DataFrame:
    """Load and return a training log CSV as DataFrame."""
    if path is None:
        path = TRAINING_LOG_1
    return pd.read_csv(path)


def load_both_training_logs():
    """Load both training logs for comparison."""
    log1 = load_training_log(TRAINING_LOG_1)
    log2 = load_training_log(TRAINING_LOG_2)
    return log1, log2


def load_all_training_logs():
    """Load all three training logs for comparison."""
    log1 = load_training_log(TRAINING_LOG_1)
    log2 = load_training_log(TRAINING_LOG_2)
    log3 = load_training_log(TRAINING_LOG_3)
    return log1, log2, log3


# ---------------------------------------------------------------------------
# Heatmap data
# ---------------------------------------------------------------------------

def generate_group_heatmap(
    model,
    galvanic_lookup: dict,
    materials: list,
    environment: str = "Marine (Seawater)",
    area_ratio: float = 1.0,
    device=None,
) -> pd.DataFrame:
    """
    Generate a compatibility heatmap across all material groups.

    Uses one representative material per group for efficiency.
    Returns DataFrame indexed and columned by group names.
    """
    # Pick one representative material per group
    group_reps = {}
    for mat in materials:
        info = galvanic_lookup.get(mat, {})
        group = info.get("group", "")
        if group and group not in group_reps:
            group_reps[group] = mat

    groups = list(group_reps.keys())
    n = len(groups)

    # Create heatmap matrix
    matrix = np.zeros((n, n))
    for i, g_anode in enumerate(groups):
        for j, g_cathode in enumerate(groups):
            result = predict_single(
                model,
                group_reps[g_anode],
                group_reps[g_cathode],
                environment,
                area_ratio,
                galvanic_lookup,
                device,
            )
            matrix[i, j] = result["current_density"]

    # Short group names for display
    short_names = []
    for g in groups:
        if len(g) > 20:
            short_names.append(g[:18] + "…")
        else:
            short_names.append(g)

    return pd.DataFrame(matrix, index=short_names, columns=short_names)


def generate_compatibility_heatmap(
    model,
    galvanic_lookup: dict,
    materials: list,
    environment: str = "Marine (Seawater)",
    area_ratio: float = 1.0,
    device=None,
) -> pd.DataFrame:
    """
    Generate a compatibility probability heatmap across material groups.
    """
    group_reps = {}
    for mat in materials:
        info = galvanic_lookup.get(mat, {})
        group = info.get("group", "")
        if group and group not in group_reps:
            group_reps[group] = mat

    groups = list(group_reps.keys())
    n = len(groups)
    matrix = np.zeros((n, n))

    for i, g_anode in enumerate(groups):
        for j, g_cathode in enumerate(groups):
            result = predict_single(
                model,
                group_reps[g_anode],
                group_reps[g_cathode],
                environment,
                area_ratio,
                galvanic_lookup,
                device,
            )
            matrix[i, j] = result["compatibility_prob"]

    short_names = []
    for g in groups:
        if len(g) > 20:
            short_names.append(g[:18] + "…")
        else:
            short_names.append(g)

    return pd.DataFrame(matrix, index=short_names, columns=short_names)
