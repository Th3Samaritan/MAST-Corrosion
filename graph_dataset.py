"""
graph_dataset.py
================
Converts the synthetic galvanic joint dataset into PyTorch Geometric
graph objects suitable for training the Physics-Informed GNN.

Each bimetallic joint becomes a 2-node graph:
  - Node 0 = Anode material
  - Node 1 = Cathode material
  - Bidirectional edge between them

Node features:
  - EMF standard potential (V)
  - Galvanic series potential vs SCE (V)
  - Group ID one-hot encoding (20 classes)
  - Galvanic rank (normalised 0-1)

Edge features:
  - Potential difference (V)
  - Cathode/Anode area ratio (log-scaled)
  - Electrolyte conductivity (S/m)
  - Environment one-hot encoding (3 classes)

Targets:
  - y_regression: galvanic current density (A/m²)
  - y_classification: compatibility label (0=Compatible, 1=Unfavorable)
"""

import pandas as pd
import numpy as np
import torch
from torch_geometric.data import Data, InMemoryDataset
from sklearn.model_selection import train_test_split


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MATERIAL_GROUPS = [
    "Magnesium",
    "Zinc, Zinc Coating",
    "Cadmium, Beryllium",
    "Aluminum, Mg-Coated Aluminum, Zn-Coated Aluminum",
    "Cu-Coated Aluminum",
    "Steels-Carbon, Low Alloy",
    "Lead",
    "Tin, Tin-Lead, Indium",
    "St. Steels-Martensitic, Ferritic",
    "Chromium, Molybdenum, Tungsten",
    "St. Steels-Aust., PH, Super Strength, Heat Resistant",
    "Brass-Lead Bronze",
    "Brass-Low Copper, Bronze-Low Copper",
    "Brass-High Copper, Bronze-High Copper",
    "Copper-High Nickel, Monel",
    "Nickel, Cobalt",
    "Titanium",
    "Silver",
    "Palladium, Rhodium, Gold, Platinum",
    "Graphite",
]

GROUP_TO_IDX = {g: i for i, g in enumerate(MATERIAL_GROUPS)}
NUM_GROUPS = len(MATERIAL_GROUPS)

ENVIRONMENT_NAMES = [
    "Marine (Seawater)",
    "Industrial (Acidic Rain)",
    "Rural (Freshwater)",
]
ENV_TO_IDX = {e: i for i, e in enumerate(ENVIRONMENT_NAMES)}
NUM_ENVS = len(ENVIRONMENT_NAMES)

ENVIRONMENT_CONDUCTIVITY = {
    "Marine (Seawater)": 5.0,
    "Industrial (Acidic Rain)": 0.1,
    "Rural (Freshwater)": 0.01,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_galvanic_lookup(galvanic_csv: str) -> dict:
    """Build material → (potential, rank) lookup from the galvanic series CSV."""
    df = pd.read_csv(galvanic_csv)
    n = len(df)
    lookup = {}
    for _, row in df.iterrows():
        lookup[row["Material"]] = {
            "potential_sce": row["Potential_V_SCE"],
            "rank_norm": (row["Rank"] - 1) / (n - 1),  # normalise to [0, 1]
            "group": row["Group"],
        }
    return lookup


def _load_emf_lookup(emf_csv: str) -> dict:
    """Build equilibrium → EMF potential lookup."""
    df = pd.read_csv(emf_csv)
    return dict(zip(df["Equilibrium"], df["Potential_V"]))


def _group_one_hot(group_name: str) -> np.ndarray:
    """Return a one-hot vector for a material group."""
    vec = np.zeros(NUM_GROUPS, dtype=np.float32)
    idx = GROUP_TO_IDX.get(group_name, -1)
    if idx >= 0:
        vec[idx] = 1.0
    return vec


def _env_one_hot(env_name: str) -> np.ndarray:
    """Return a one-hot vector for an environment."""
    vec = np.zeros(NUM_ENVS, dtype=np.float32)
    idx = ENV_TO_IDX.get(env_name, -1)
    if idx >= 0:
        vec[idx] = 1.0
    return vec


# ---------------------------------------------------------------------------
# Core conversion
# ---------------------------------------------------------------------------

def row_to_graph(row: pd.Series, galvanic_lookup: dict) -> Data:
    """
    Convert one row of the synthetic dataset into a PyG Data object.

    Returns a 2-node graph (anode, cathode) with a bidirectional edge.
    """
    anode_name = row["Anode_Alloy"]
    cathode_name = row["Cathode_Alloy"]
    anode_group = row["Anode_Table1_Group"]
    cathode_group = row["Cathode_Table1_Group"]

    # ----- Node features -----
    anode_info = galvanic_lookup.get(anode_name, {})
    cathode_info = galvanic_lookup.get(cathode_name, {})

    def _node_feat(name, group, info):
        pot_sce = info.get("potential_sce", 0.0)
        rank = info.get("rank_norm", 0.5)
        oh = _group_one_hot(group)
        return np.concatenate([[pot_sce, rank], oh]).astype(np.float32)

    x_anode = _node_feat(anode_name, anode_group, anode_info)
    x_cathode = _node_feat(cathode_name, cathode_group, cathode_info)
    x = np.stack([x_anode, x_cathode])  # (2, F_node)

    # ----- Edge features (bidirectional) -----
    delta_v = row["Potential_Difference_V"]
    area_ratio = row["Cathode_Anode_Area_Ratio"]
    log_area_ratio = np.log1p(area_ratio)  # log-scale for stability
    env = row["Environment"]
    # Use CSV column if available (new format), else fall back to lookup
    if "Electrolyte_Conductivity_Sm" in row.index:
        conductivity = row["Electrolyte_Conductivity_Sm"]
    else:
        conductivity = ENVIRONMENT_CONDUCTIVITY.get(env, 0.01)
    env_oh = _env_one_hot(env)

    edge_feat = np.concatenate(
        [[delta_v, log_area_ratio, conductivity], env_oh]
    ).astype(np.float32)

    # Bidirectional: anode→cathode and cathode→anode
    edge_index = torch.tensor([[0, 1], [1, 0]], dtype=torch.long)
    edge_attr = np.stack([edge_feat, edge_feat])  # same features for both directions

    # ----- Targets -----
    y_reg = row["Target_Galvanic_Current_Density"]
    y_cls = 1.0 if row["PDF_Compatibility_Status"] == "Unfavorable" else 0.0

    return Data(
        x=torch.tensor(x, dtype=torch.float),
        edge_index=edge_index,
        edge_attr=torch.tensor(edge_attr, dtype=torch.float),
        y_regression=torch.tensor([y_reg], dtype=torch.float),
        y_classification=torch.tensor([y_cls], dtype=torch.float),
    )


# ---------------------------------------------------------------------------
# Dataset builder
# ---------------------------------------------------------------------------

class GalvanicJointDataset(InMemoryDataset):
    """
    PyTorch Geometric InMemoryDataset for galvanic corrosion joints.

    Args:
        root: Directory containing the CSV files.
        synthetic_csv: Filename of the synthetic joint data.
        galvanic_csv: Filename of the galvanic series CSV.
        split: One of 'train', 'val', 'test', or None (all data).
        train_ratio: Fraction of data for training.
        val_ratio: Fraction of data for validation.
        seed: Random seed for reproducibility.
    """

    def __init__(
        self,
        root: str,
        synthetic_csv: str = "synthetic_galvanic_joints_full.csv",
        galvanic_csv: str = "pdf_table2_galvanic_series.csv",
        split: str = None,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        seed: int = 42,
        transform=None,
        pre_transform=None,
    ):
        self._synthetic_csv = synthetic_csv
        self._galvanic_csv = galvanic_csv
        self._split = split
        self._train_ratio = train_ratio
        self._val_ratio = val_ratio
        self._seed = seed
        super().__init__(root, transform, pre_transform)
        self.load(self.processed_paths[0])

    @property
    def raw_file_names(self):
        return [self._synthetic_csv, self._galvanic_csv]

    @property
    def processed_file_names(self):
        suffix = self._split if self._split else "all"
        return [f"galvanic_joints_{suffix}.pt"]

    def process(self):
        import os

        synth_path = os.path.join(self.raw_dir, self._synthetic_csv)
        galv_path = os.path.join(self.raw_dir, self._galvanic_csv)

        # If files aren't in raw_dir, check root
        if not os.path.exists(synth_path):
            synth_path = os.path.join(self.root, self._synthetic_csv)
        if not os.path.exists(galv_path):
            galv_path = os.path.join(self.root, self._galvanic_csv)

        df_synth = pd.read_csv(synth_path)
        galvanic_lookup = _load_galvanic_lookup(galv_path)

        # Convert all rows to graphs
        all_graphs = []
        for idx, row in df_synth.iterrows():
            graph = row_to_graph(row, galvanic_lookup)
            if self.pre_transform is not None:
                graph = self.pre_transform(graph)
            all_graphs.append(graph)

        # Split
        if self._split is not None:
            n = len(all_graphs)
            indices = list(range(n))
            train_idx, temp_idx = train_test_split(
                indices, train_size=self._train_ratio, random_state=self._seed
            )
            relative_val = self._val_ratio / (1 - self._train_ratio)
            val_idx, test_idx = train_test_split(
                temp_idx, train_size=relative_val, random_state=self._seed
            )

            split_map = {"train": train_idx, "val": val_idx, "test": test_idx}
            selected = split_map.get(self._split, indices)
            all_graphs = [all_graphs[i] for i in selected]

        self.save(all_graphs, self.processed_paths[0])


# ---------------------------------------------------------------------------
# Standalone builder (no InMemoryDataset overhead)
# ---------------------------------------------------------------------------

def build_graph_list(
    synthetic_csv: str,
    galvanic_csv: str,
    split: str = None,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    seed: int = 42,
):
    """
    Build a list of PyG Data objects directly from CSV files.
    Useful when you don't want InMemoryDataset filesystem conventions.

    Returns:
        list[Data] or tuple of (train, val, test) lists.
    """
    df_synth = pd.read_csv(synthetic_csv)
    galvanic_lookup = _load_galvanic_lookup(galvanic_csv)

    all_graphs = [row_to_graph(row, galvanic_lookup) for _, row in df_synth.iterrows()]

    if split is None:
        return all_graphs

    n = len(all_graphs)
    indices = list(range(n))
    train_idx, temp_idx = train_test_split(
        indices, train_size=train_ratio, random_state=seed
    )
    relative_val = val_ratio / (1 - train_ratio)
    val_idx, test_idx = train_test_split(
        temp_idx, train_size=relative_val, random_state=seed
    )

    train_graphs = [all_graphs[i] for i in train_idx]
    val_graphs = [all_graphs[i] for i in val_idx]
    test_graphs = [all_graphs[i] for i in test_idx]

    return train_graphs, val_graphs, test_graphs


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os

    project_dir = os.path.dirname(os.path.abspath(__file__))
    synth_csv = os.path.join(project_dir, "synthetic_galvanic_joints_full.csv")
    galv_csv = os.path.join(project_dir, "pdf_table2_galvanic_series.csv")

    if not os.path.exists(synth_csv):
        print(f"ERROR: {synth_csv} not found. Run data_extraction.py first.")
        exit(1)

    print("Building graph dataset from synthetic data...")
    train, val, test = build_graph_list(synth_csv, galv_csv, split="train")

    print(f"\n  Train: {len(train)} graphs")
    print(f"  Val:   {len(val)} graphs")
    print(f"  Test:  {len(test)} graphs")

    # Inspect first graph
    g = train[0]
    print(f"\n  Sample graph:")
    print(f"    Nodes: {g.x.shape}  (2 nodes × {g.x.shape[1]} features)")
    print(f"    Edges: {g.edge_index.shape}  (bidirectional)")
    print(f"    Edge attr: {g.edge_attr.shape}")
    print(f"    y_regression: {g.y_regression.item():.5f}")
    print(f"    y_classification: {g.y_classification.item()}")
