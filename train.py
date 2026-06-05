"""
train.py
========
Complete training pipeline for the Galvanic Corrosion PINN.

Designed to be run on cloud (Colab, GCP, AWS, etc.) with GPU support.
All data files should be present in the same directory.

Usage:
    python train.py [--epochs 200] [--batch_size 128] [--lr 1e-3] [--device cuda]

Outputs:
    - checkpoints/best_model.pt      Best model by validation loss
    - checkpoints/final_model.pt     Final model after all epochs
    - training_log.csv               Per-epoch loss and metric log
"""

import os
import sys
import csv
import time
import argparse
from datetime import datetime

import numpy as np
import torch
import torch.nn.functional as F
from torch.optim import Adam
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch_geometric.loader import DataLoader

# Local imports
from graph_dataset import build_graph_list
from pinn_model import GalvanicCorrosionPINN, PhysicsInformedLoss, build_model


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def compute_metrics(model, loader, criterion, device):
    """
    Evaluate the model on a DataLoader and return aggregated metrics.

    Returns:
        dict with keys: loss_total, loss_data, loss_cls, loss_kcl, loss_thermo,
                         mae, rmse, accuracy, f1
    """
    model.eval()
    total_losses = {"total": 0, "data": 0, "classification": 0, "kcl": 0, "thermo": 0}
    all_y_true_reg = []
    all_y_pred_reg = []
    all_y_true_cls = []
    all_y_pred_cls = []
    n_batches = 0

    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            v_nodes, i_edges, compat = model(batch)

            # Build targets
            # For edges: we only predict on forward edges (anode→cathode, index 0::2)
            # But since both edges have same targets, just use all
            i_true = batch.y_regression.unsqueeze(-1) if batch.y_regression.dim() == 1 else batch.y_regression

            # Match i_edges shape to i_true
            # Each graph has 2 edges, but 1 target value
            # Average the 2 edge predictions per graph
            num_graphs = batch.num_graphs
            # Reshape: (num_graphs * 2, 1) → take every other (anode→cathode direction)
            i_pred_per_graph = i_edges[0::2]  # forward direction only

            if i_pred_per_graph.shape[0] != i_true.shape[0]:
                # Fallback: average all edges per graph
                i_pred_per_graph = i_edges.view(num_graphs, 2, 1).mean(dim=1)

            compat_true = batch.y_classification.unsqueeze(-1) if batch.y_classification.dim() == 1 else batch.y_classification

            losses = criterion(
                v_nodes, i_edges, i_pred_per_graph, i_true,
                compat, compat_true, batch.edge_index
            )

            for k in total_losses:
                total_losses[k] += losses[k].item()
            n_batches += 1

            all_y_true_reg.append(i_true.cpu().numpy())
            all_y_pred_reg.append(i_pred_per_graph.cpu().numpy())
            all_y_true_cls.append(compat_true.cpu().numpy())
            all_y_pred_cls.append(torch.sigmoid(compat).cpu().numpy())

    # Average losses
    for k in total_losses:
        total_losses[k] /= max(n_batches, 1)

    # Regression metrics
    y_true = np.concatenate(all_y_true_reg)
    y_pred = np.concatenate(all_y_pred_reg)
    mae = np.mean(np.abs(y_true - y_pred))
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))

    # Classification metrics
    cls_true = np.concatenate(all_y_true_cls).flatten()
    cls_pred = (np.concatenate(all_y_pred_cls).flatten() >= 0.5).astype(float)
    accuracy = np.mean(cls_true == cls_pred)

    # F1 score
    tp = np.sum((cls_pred == 1) & (cls_true == 1))
    fp = np.sum((cls_pred == 1) & (cls_true == 0))
    fn = np.sum((cls_pred == 0) & (cls_true == 1))
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-8)

    return {
        "loss_total": total_losses["total"],
        "loss_data": total_losses["data"],
        "loss_cls": total_losses["classification"],
        "loss_kcl": total_losses["kcl"],
        "loss_thermo": total_losses["thermo"],
        "mae": mae,
        "rmse": rmse,
        "accuracy": accuracy,
        "f1": f1,
    }


# ---------------------------------------------------------------------------
# Training loop
# ---------------------------------------------------------------------------

def train_one_epoch(model, loader, criterion, optimizer, device):
    """Train for one epoch and return average losses."""
    model.train()
    total_losses = {"total": 0, "data": 0, "classification": 0, "kcl": 0, "thermo": 0}
    n_batches = 0

    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()

        v_nodes, i_edges, compat = model(batch)

        # Build targets
        i_true = batch.y_regression.unsqueeze(-1) if batch.y_regression.dim() == 1 else batch.y_regression
        num_graphs = batch.num_graphs

        # Forward direction edges only
        i_pred_per_graph = i_edges[0::2]
        if i_pred_per_graph.shape[0] != i_true.shape[0]:
            i_pred_per_graph = i_edges.view(num_graphs, 2, 1).mean(dim=1)

        compat_true = batch.y_classification.unsqueeze(-1) if batch.y_classification.dim() == 1 else batch.y_classification

        losses = criterion(
            v_nodes, i_edges, i_pred_per_graph, i_true,
            compat, compat_true, batch.edge_index
        )

        losses["total"].backward()

        # Gradient clipping for stability
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

        optimizer.step()

        for k in total_losses:
            total_losses[k] += losses[k].item()
        n_batches += 1

    for k in total_losses:
        total_losses[k] /= max(n_batches, 1)

    return total_losses


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Train Galvanic Corrosion PINN")
    parser.add_argument("--epochs", type=int, default=200, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=128, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-3, help="Initial learning rate")
    parser.add_argument("--hidden_dim", type=int, default=64, help="Hidden dimension")
    parser.add_argument("--num_mp_layers", type=int, default=3, help="Message passing layers")
    parser.add_argument("--dropout", type=float, default=0.1, help="Dropout rate")
    parser.add_argument("--lambda_kcl", type=float, default=0.1, help="KCL loss weight")
    parser.add_argument("--lambda_thermo", type=float, default=0.1, help="Thermo loss weight")
    parser.add_argument("--lambda_cls", type=float, default=0.5, help="Classification loss weight")
    parser.add_argument("--device", type=str, default="auto", help="Device: cuda, cpu, or auto")
    parser.add_argument("--data_dir", type=str, default=".", help="Directory with CSV data files")
    parser.add_argument("--checkpoint_dir", type=str, default="checkpoints", help="Checkpoint directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    # ---- Device ----
    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)
    print(f"Using device: {device}")

    # ---- Seed ----
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(args.seed)

    # ---- Data ----
    print("\nLoading and converting dataset to graphs...")
    synth_csv = os.path.join(args.data_dir, "synthetic_galvanic_joints_full.csv")
    galv_csv = os.path.join(args.data_dir, "pdf_table2_galvanic_series.csv")

    if not os.path.exists(synth_csv):
        print(f"ERROR: {synth_csv} not found. Run data_extraction.py first.")
        sys.exit(1)

    train_graphs, val_graphs, test_graphs = build_graph_list(
        synth_csv, galv_csv, split="train", seed=args.seed
    )
    print(f"  Train: {len(train_graphs)}  |  Val: {len(val_graphs)}  |  Test: {len(test_graphs)}")

    train_loader = DataLoader(train_graphs, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_graphs, batch_size=args.batch_size, shuffle=False)
    test_loader = DataLoader(test_graphs, batch_size=args.batch_size, shuffle=False)

    # ---- Inspect feature dimensions ----
    sample = train_graphs[0]
    node_features = sample.x.shape[1]
    edge_features = sample.edge_attr.shape[1]
    print(f"  Node features: {node_features}")
    print(f"  Edge features: {edge_features}")

    # ---- Model ----
    model = build_model(
        node_features=node_features,
        edge_features=edge_features,
        hidden_dim=args.hidden_dim,
        num_mp_layers=args.num_mp_layers,
        dropout=args.dropout,
    ).to(device)

    total_params = sum(p.numel() for p in model.parameters())
    print(f"\nModel: {model.__class__.__name__}  ({total_params:,} parameters)")

    # ---- Optimizer & Scheduler ----
    optimizer = Adam(model.parameters(), lr=args.lr, weight_decay=1e-5)
    scheduler = CosineAnnealingLR(optimizer, T_max=args.epochs, eta_min=args.lr * 0.01)

    # ---- Loss ----
    criterion = PhysicsInformedLoss(
        lambda_kcl=args.lambda_kcl,
        lambda_thermo=args.lambda_thermo,
        lambda_cls=args.lambda_cls,
    )

    # ---- Checkpointing ----
    os.makedirs(args.checkpoint_dir, exist_ok=True)
    best_val_loss = float("inf")

    # ---- Logging ----
    log_path = os.path.join(args.data_dir, "training_log.csv")
    log_fields = [
        "epoch", "lr",
        "train_total", "train_data", "train_cls", "train_kcl", "train_thermo",
        "val_total", "val_data", "val_cls", "val_kcl", "val_thermo",
        "val_mae", "val_rmse", "val_accuracy", "val_f1",
    ]

    with open(log_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=log_fields)
        writer.writeheader()

    # ---- Training ----
    print(f"\n{'='*70}")
    print(f"  Training for {args.epochs} epochs")
    print(f"  LR: {args.lr}  |  Batch: {args.batch_size}  |  Hidden: {args.hidden_dim}")
    print(f"  λ_KCL: {args.lambda_kcl}  |  λ_Thermo: {args.lambda_thermo}  |  λ_Cls: {args.lambda_cls}")
    print(f"{'='*70}\n")

    start_time = time.time()

    for epoch in range(1, args.epochs + 1):
        epoch_start = time.time()

        # Train
        train_losses = train_one_epoch(model, train_loader, criterion, optimizer, device)

        # Validate
        val_metrics = compute_metrics(model, val_loader, criterion, device)

        # Step scheduler
        current_lr = optimizer.param_groups[0]["lr"]
        scheduler.step()

        # Log
        log_row = {
            "epoch": epoch,
            "lr": current_lr,
            "train_total": train_losses["total"],
            "train_data": train_losses["data"],
            "train_cls": train_losses["classification"],
            "train_kcl": train_losses["kcl"],
            "train_thermo": train_losses["thermo"],
            "val_total": val_metrics["loss_total"],
            "val_data": val_metrics["loss_data"],
            "val_cls": val_metrics["loss_cls"],
            "val_kcl": val_metrics["loss_kcl"],
            "val_thermo": val_metrics["loss_thermo"],
            "val_mae": val_metrics["mae"],
            "val_rmse": val_metrics["rmse"],
            "val_accuracy": val_metrics["accuracy"],
            "val_f1": val_metrics["f1"],
        }
        with open(log_path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=log_fields)
            writer.writerow(log_row)

        # Checkpoint
        if val_metrics["loss_total"] < best_val_loss:
            best_val_loss = val_metrics["loss_total"]
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "scheduler_state_dict": scheduler.state_dict(),
                "val_loss": best_val_loss,
                "args": vars(args),
            }, os.path.join(args.checkpoint_dir, "best_model.pt"))
            marker = " ★"
        else:
            marker = ""

        # Print progress
        epoch_time = time.time() - epoch_start
        if epoch % 10 == 0 or epoch == 1 or marker:
            print(
                f"Epoch {epoch:4d}/{args.epochs} "
                f"| Train Loss: {train_losses['total']:.5f} "
                f"| Val Loss: {val_metrics['loss_total']:.5f} "
                f"| MAE: {val_metrics['mae']:.5f} "
                f"| Acc: {val_metrics['accuracy']:.3f} "
                f"| F1: {val_metrics['f1']:.3f} "
                f"| LR: {current_lr:.1e} "
                f"| {epoch_time:.1f}s{marker}"
            )

    # Save final model
    torch.save({
        "epoch": args.epochs,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "scheduler_state_dict": scheduler.state_dict(),
        "val_loss": val_metrics["loss_total"],
        "args": vars(args),
    }, os.path.join(args.checkpoint_dir, "final_model.pt"))

    total_time = time.time() - start_time
    print(f"\n{'='*70}")
    print(f"  Training complete in {total_time/60:.1f} minutes")
    print(f"  Best validation loss: {best_val_loss:.6f}")
    print(f"  Checkpoints saved to: {args.checkpoint_dir}/")
    print(f"  Training log saved to: {log_path}")
    print(f"{'='*70}")

    # ---- Final evaluation on test set ----
    print(f"\n--- Test Set Evaluation ---")

    # Load best model
    ckpt = torch.load(os.path.join(args.checkpoint_dir, "best_model.pt"), map_location=device)
    model.load_state_dict(ckpt["model_state_dict"])

    test_metrics = compute_metrics(model, test_loader, criterion, device)
    print(f"  Total Loss:  {test_metrics['loss_total']:.6f}")
    print(f"  Data MSE:    {test_metrics['loss_data']:.6f}")
    print(f"  Class. BCE:  {test_metrics['loss_cls']:.6f}")
    print(f"  KCL Penalty: {test_metrics['loss_kcl']:.6f}")
    print(f"  Thermo Pen.: {test_metrics['loss_thermo']:.6f}")
    print(f"  MAE:         {test_metrics['mae']:.6f}")
    print(f"  RMSE:        {test_metrics['rmse']:.6f}")
    print(f"  Accuracy:    {test_metrics['accuracy']:.4f}")
    print(f"  F1 Score:    {test_metrics['f1']:.4f}")


if __name__ == "__main__":
    main()
