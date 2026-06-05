"""
run_cloud.py
============
One-click cloud training script for Google Colab or similar environments.

Usage on Colab:
    1. Upload all project files to /content/corrosion/
    2. Run: !python run_cloud.py

This script:
    1. Installs dependencies (torch-geometric)
    2. Runs data extraction to generate CSVs
    3. Trains the PINN model
    4. Saves checkpoints and training logs
"""

import subprocess
import sys
import os

# ---------------------------------------------------------------------------
# Step 0: Install dependencies
# ---------------------------------------------------------------------------

def install_dependencies():
    """Install torch-geometric and other dependencies if not present."""
    print("=" * 60)
    print("  Step 0: Checking/Installing Dependencies")
    print("=" * 60)

    try:
        import torch
        print(f"  ✓ PyTorch {torch.__version__}")
        print(f"  ✓ CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"  ✓ GPU: {torch.cuda.get_device_name(0)}")
    except ImportError:
        print("  ✗ PyTorch not found. Please install PyTorch first.")
        print("    pip install torch torchvision")
        sys.exit(1)

    try:
        import torch_geometric
        print(f"  ✓ PyG {torch_geometric.__version__}")
    except ImportError:
        print("  → Installing torch-geometric...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "torch-geometric", "-q"
        ])
        import torch_geometric
        print(f"  ✓ PyG {torch_geometric.__version__}")

    try:
        import sklearn
        print(f"  ✓ scikit-learn {sklearn.__version__}")
    except ImportError:
        print("  → Installing scikit-learn...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "scikit-learn", "-q"
        ])

    for pkg in ["pandas", "numpy", "matplotlib"]:
        try:
            mod = __import__(pkg)
            print(f"  ✓ {pkg} {mod.__version__}")
        except ImportError:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", pkg, "-q"
            ])

    print()


# ---------------------------------------------------------------------------
# Step 1: Data extraction
# ---------------------------------------------------------------------------

def run_data_extraction():
    print("=" * 60)
    print("  Step 1: Extracting Data & Generating Synthetic Dataset")
    print("=" * 60)

    from data_extraction import (
        extract_emf_series,
        extract_material_groups,
        extract_galvanic_series,
        generate_synthetic_data,
    )

    df_emf = extract_emf_series()
    df_groups = extract_material_groups()
    df_galv = extract_galvanic_series()
    df_synth = generate_synthetic_data(df_galv, df_groups, num_samples=25000)

    print(f"\n  Generated files:")
    for f in [
        "pdf_table3_emf_series.csv",
        "pdf_table1_material_groups.csv",
        "pdf_table2_galvanic_series.csv",
        "synthetic_galvanic_joints_full.csv",
    ]:
        size = os.path.getsize(f)
        print(f"    {f:45s}  ({size:,} bytes)")
    print()


# ---------------------------------------------------------------------------
# Step 2: Train
# ---------------------------------------------------------------------------

def run_training():
    print("=" * 60)
    print("  Step 2: Training PINN Model")
    print("=" * 60)

    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"

    subprocess.check_call([
        sys.executable, "train.py",
        "--epochs", "200",
        "--batch_size", "128",
        "--lr", "1e-3",
        "--hidden_dim", "64",
        "--num_mp_layers", "3",
        "--device", device,
    ])


# ---------------------------------------------------------------------------
# Step 3: Summary
# ---------------------------------------------------------------------------

def print_summary():
    print("\n" + "=" * 60)
    print("  Training Complete!")
    print("=" * 60)
    print(f"  Outputs:")
    print(f"    checkpoints/best_model.pt   — Best model checkpoint")
    print(f"    checkpoints/final_model.pt  — Final model checkpoint")
    print(f"    training_log.csv            — Per-epoch metrics")
    print()

    # Quick plot if matplotlib available
    try:
        import pandas as pd
        import matplotlib.pyplot as plt

        log = pd.read_csv("training_log.csv")
        fig, axes = plt.subplots(1, 3, figsize=(15, 4))

        # Loss curves
        axes[0].plot(log["epoch"], log["train_total"], label="Train")
        axes[0].plot(log["epoch"], log["val_total"], label="Val")
        axes[0].set_xlabel("Epoch")
        axes[0].set_ylabel("Total Loss")
        axes[0].set_title("Training & Validation Loss")
        axes[0].legend()
        axes[0].set_yscale("log")

        # MAE
        axes[1].plot(log["epoch"], log["val_mae"], color="orange")
        axes[1].set_xlabel("Epoch")
        axes[1].set_ylabel("MAE")
        axes[1].set_title("Validation MAE")

        # Classification metrics
        axes[2].plot(log["epoch"], log["val_accuracy"], label="Accuracy")
        axes[2].plot(log["epoch"], log["val_f1"], label="F1")
        axes[2].set_xlabel("Epoch")
        axes[2].set_ylabel("Score")
        axes[2].set_title("Classification Metrics")
        axes[2].legend()

        plt.tight_layout()
        plt.savefig("training_curves.png", dpi=150)
        print(f"  Saved training_curves.png")
        plt.show()
    except Exception as e:
        print(f"  (Could not generate plots: {e})")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    install_dependencies()
    run_data_extraction()
    run_training()
    print_summary()
