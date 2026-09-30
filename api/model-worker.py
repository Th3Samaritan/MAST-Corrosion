"""Line-delimited JSON worker for the existing PyTorch model; no Streamlit imports.

Only repository-owned checkpoints are loaded. No uploads, paths or pickle files
are accepted through the API. stdout is exclusively the worker protocol.
"""
import csv
import json
import io
import math
import os
from pathlib import Path
import sys

ROOT = Path(os.environ.get("MODEL_ROOT", Path(__file__).resolve().parents[1])).resolve()
sys.path.insert(0, str(ROOT))
RUNS = {"1": ("1st Result", "best_model.pt", "training_log.csv"),
        "2": ("2nd Result", "best_model (1).pt", "training_log (1).csv"),
        "3": ("3rd Result", "best_model.pt", "training_log.csv")}
ENVIRONMENTS = ["Marine (Seawater)", "Industrial (Acidic Rain)", "Rural (Freshwater)"]
CACHE = {}

def catalog():
    with (ROOT / "pdf_table2_galvanic_series.csv").open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def training():
    output = []
    for run, (folder, _, log) in RUNS.items():
        with (ROOT / "Post training" / folder / log).open(encoding="utf-8-sig", newline="") as f:
            rows = [{k: float(v) for k, v in row.items()} for row in csv.DictReader(f)]
        output.append({"run": run, "epochs": len(rows), "history": rows})
    return output

def model_for(run):
    if run not in RUNS:
        raise ValueError("Unknown training run.")
    if run in CACHE:
        return CACHE[run]
    import torch
    from pinn_model import build_model
    torch.set_num_threads(1)
    folder, name, _ = RUNS[run]
    # Restricted loader; legacy checkpoints with unsupported objects must be
    # converted offline, never silently retried with unrestricted pickle.
    checkpoint = torch.load(ROOT / "Post training" / folder / name,
                            map_location="cpu", weights_only=True)
    args = checkpoint.get("args", {})
    model = build_model(node_features=args.get("node_features", 22),
                        edge_features=args.get("edge_features", 6),
                        hidden_dim=args.get("hidden_dim", 64),
                        num_mp_layers=args.get("num_mp_layers", 3),
                        dropout=args.get("dropout", 0.1))
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    CACHE.clear()  # Bound memory to one model per process.
    CACHE[run] = model
    return model

def predict(payload):
    pairs = payload.get("pairs")
    if isinstance(payload.get("csv"), str):
        reader = csv.DictReader(io.StringIO(payload["csv"]))
        if reader.fieldnames != ["anode", "cathode", "environment", "area_ratio"]:
            raise ValueError("CSV columns must be anode,cathode,environment,area_ratio.")
        pairs = []
        for row in reader:
            if None in row or any(v is None for v in row.values()):
                raise ValueError("Malformed CSV row.")
            row["area_ratio"] = float(row["area_ratio"])
            pairs.append(row)
            if len(pairs) > 400:
                raise ValueError("CSV is limited to 400 pairs.")
    if not isinstance(pairs, list) or not 1 <= len(pairs) <= 400:
        raise ValueError("Supply 1–400 pairs.")
    materials = {r["Material"]: r for r in catalog()}
    for pair in pairs:
        if not isinstance(pair, dict) or pair.get("anode") not in materials or pair.get("cathode") not in materials:
            raise ValueError("Choose materials in the model reference.")
        if pair.get("environment") not in ENVIRONMENTS:
            raise ValueError("Choose a supported environment.")
        ratio = pair.get("area_ratio")
        if isinstance(ratio, bool) or not isinstance(ratio, (float, int)) or not math.isfinite(ratio) or not 0.01 <= ratio <= 50:
            raise ValueError("Area ratio must be 0.01–50.")
    import torch
    import numpy as np
    from torch_geometric.data import Data
    from graph_dataset import _group_one_hot, _env_one_hot, ENVIRONMENT_CONDUCTIVITY
    run = str(payload.get("run", "1"))
    model = model_for(run)
    results = []
    for pair in pairs:
        a, c = materials[pair["anode"]], materials[pair["cathode"]]
        def node(row):
            return np.concatenate([[float(row["Potential_V_SCE"]), (float(row["Rank"]) - 1) / (len(materials) - 1)], _group_one_hot(row["Group"])])
        edge = np.concatenate([[abs(float(c["Potential_V_SCE"]) - float(a["Potential_V_SCE"])), np.log1p(pair["area_ratio"]), ENVIRONMENT_CONDUCTIVITY[pair["environment"]]], _env_one_hot(pair["environment"])])
        graph = Data(x=torch.tensor(np.stack([node(a), node(c)]), dtype=torch.float32),
                     edge_index=torch.tensor([[0, 1], [1, 0]], dtype=torch.long),
                     edge_attr=torch.tensor(np.stack([edge, edge]), dtype=torch.float32),
                     batch=torch.zeros(2, dtype=torch.long))
        with torch.inference_mode():
            potentials, currents, logits = model(graph)
        score = torch.sigmoid(logits[0]).item()
        results.append({**pair, "current_proxy": abs(currents[0].item()),
                        "unfavorable_score": score,
                        "classification": "Unfavorable" if score >= 0.5 else "Compatible",
                        "v_anode": potentials[0].item(), "v_cathode": potentials[1].item()})
    return {"run": run, "results": results, "validation": "synthetic-trained research model; not validated mm/year or calibrated probability"}

def dispatch(payload):
    if not isinstance(payload, dict):
        raise ValueError("Expected an object.")
    if payload.get("action") == "catalog":
        return {"materials": catalog(), "environments": ENVIRONMENTS}
    if payload.get("action") == "training":
        return {"runs": training()}
    if payload.get("action") == "predict":
        return predict(payload)
    raise ValueError("Unknown model action.")

if __name__ == "__main__":
    for line in sys.stdin:
        try:
            result = dispatch(json.loads(line))
            print(json.dumps({"ok": True, "data": result}, allow_nan=False), flush=True)
        except ValueError as exc:
            print(json.dumps({"ok": False, "status": 422, "error": str(exc)}), flush=True)
        except Exception:
            print(json.dumps({"ok": False, "status": 503, "error": "Model unavailable. Check Python dependencies, LFS checkpoint files and model compatibility."}), flush=True)
