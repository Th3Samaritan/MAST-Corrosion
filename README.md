<p align="center">
  <h1 align="center">⚡ MAST-Corrosion</h1>
  <p align="center">
    <strong>Physics-Informed Graph Neural Network for Galvanic Corrosion Prediction</strong>
  </p>
  <p align="center">
    <a href="#features">Features</a> •
    <a href="#architecture">Architecture</a> •
    <a href="#installation">Installation</a> •
    <a href="#usage">Usage</a> •
    <a href="#dashboard">Dashboard</a> •
    <a href="#project-structure">Structure</a>
  </p>
</p>

---

## Overview

MAST-Corrosion is a **Physics-Informed Neural Network (PINN)** built on **PyTorch Geometric** that predicts galvanic corrosion behaviour in multi-material assemblies. The model enforces electrochemical constraints — Kirchhoff's Current Law (KCL) and thermodynamic consistency — directly in the loss function, ensuring physically plausible predictions even on unseen material pairs.

An interactive **Streamlit dashboard** provides real-time predictions, training analytics, batch analysis, and a complete galvanic series reference.

## Features

- **Graph-based architecture** — Materials as nodes, electrolytic joints as edges, using NNConv message passing
- **Multi-task prediction** — Simultaneous regression (current density) and classification (compatibility)
- **Physics-informed losses** — KCL conservation and thermodynamic consistency penalties
- **Interactive dashboard** — Professional Streamlit UI with 4 analysis tabs
- **Batch analysis** — Cross-material heatmaps and CSV batch predictions
- **3 trained model checkpoints** — With full training logs and visualisations

## Architecture

```
Input Graph (2 nodes, bidirectional edges)
    │
    ├── Node features: [potential_SCE, rank, group_one_hot(20)]
    └── Edge features: [ΔV, log(area_ratio), conductivity, env_one_hot(3)]
    │
    ▼
┌─────────────────────────────┐
│   Node Embedding (Linear)   │
└─────────────┬───────────────┘
              │
    ┌─────────▼─────────┐
    │  NNConv × 3       │  ← Edge-conditioned message passing
    │  + LayerNorm      │     with residual connections
    │  + Residual       │
    └─────────┬─────────┘
              │
    ┌─────────┼─────────────────┐
    │         │                 │
    ▼         ▼                 ▼
┌────────┐ ┌──────────┐ ┌──────────────┐
│V_nodes │ │ I_edges  │ │  Compat(B,1) │
│ (N,1)  │ │  (E,1)   │ │  (sigmoid)   │
└────────┘ └──────────┘ └──────────────┘
 Potential   Current      Compatibility
             Density      Probability
```

### Physics-Informed Loss

| Component | Description | Weight |
|-----------|-------------|--------|
| **Data MSE** | Predicted vs true current density | 1.0 |
| **Classification BCE** | Predicted vs true compatibility | λ_cls = 0.5 |
| **KCL Penalty** | Net current at each node → 0 | λ_kcl = 0.1 |
| **Thermodynamic** | Current flows anode → cathode | λ_thermo = 0.1 |

## Installation

### Prerequisites
- Python 3.10+
- [Git LFS](https://git-lfs.github.com/) (for model checkpoint files)

### Setup

```bash
# Clone the repository
git clone https://github.com/<your-username>/MAST-Corrosion.git
cd MAST-Corrosion

# Pull LFS files (model checkpoints)
git lfs pull

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/macOS)
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

> **Note:** For CPU-only setups, install PyTorch separately first:
> ```bash
> pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
> pip install torch-geometric
> ```

## Usage

### Launch the Dashboard

```bash
streamlit run streamlit_app.py
```

The dashboard opens at `http://localhost:8501` with four tabs:

| Tab | Description |
|-----|-------------|
| 🔬 **Prediction Engine** | Single material pair prediction with physics breakdown |
| 📊 **Training Analytics** | Loss curves, metrics, LR schedules across 3 training runs |
| 🧪 **Batch Analysis** | Compatibility heatmaps and CSV batch predictions |
| 📚 **Galvanic Series** | Interactive reference chart with electrochemical potentials |

### Train a New Model

```bash
python train.py
```

### Run on Cloud (Colab / GCP)

```bash
python run_cloud.py
```

## Dashboard

The Streamlit dashboard features a dark glassmorphism design with:

- **Real-time predictions** for any anode/cathode material pair
- **Environment selection** (Marine, Industrial, Rural) with conductivity display
- **Area ratio sensitivity** with risk gauges
- **Compatibility verdict** with confidence scores
- **Cross-material heatmaps** for systematic analysis
- **Training run comparison** across 3 model checkpoints
- **Interactive galvanic series** chart with 30+ materials

## Project Structure

```
MAST-Corrosion/
├── streamlit_app.py                 # Streamlit dashboard (main UI)
├── streamlit_utils.py               # Backend: model loading, inference, heatmaps
├── pinn_model.py                    # GNN architecture + physics-informed loss
├── pinn_architecture.py             # Original architecture (reference)
├── graph_dataset.py                 # PyG dataset: feature engineering, graph construction
├── train.py                         # Training loop with validation
├── run_cloud.py                     # Cloud training entry point
├── data_extraction.py               # PDF table extraction to CSV
├── synthetic_data_generator(4).py   # Synthetic training data generation
├── requirements.txt                 # Python dependencies
│
├── pdf_table1_material_groups.csv   # Material group categories
├── pdf_table2_galvanic_series.csv   # Galvanic series (potentials)
├── pdf_table3_emf_series.csv        # EMF series reference
├── synthetic_galvanic_joints_full.csv    # Training dataset (small)
├── synthetic_galvanic_joints_full_1.csv  # Training dataset (large)
│
├── Galvanic_Corrosion_PINN_Cloud.ipynb   # Colab notebook
│
└── Post training/
    ├── 1st Result/                  # Best model checkpoint + logs
    │   ├── best_model.pt
    │   ├── training_log.csv
    │   └── *.png                    # Training visualisations
    ├── 2nd Result/                  # Second training run
    └── 3rd Result/                  # Third training run
```

## Data

The model is trained on synthetic galvanic joint data derived from the **MIL-STD-889D** galvanic series in seawater, covering:

- **30+ materials** across 17 material groups
- **3 environments**: Marine (seawater), Industrial (acidic rain), Rural (freshwater)
- **Variable area ratios**: 0.01 – 50.0

## License

This project is part of the MAST Consolidate research programme.

---

<p align="center">
  Built with PyTorch Geometric & Streamlit<br/>
  © 2026 MAST Consolidate
</p>
