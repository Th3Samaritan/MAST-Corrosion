# MAST Corrosion

Next.js engineering workspace for Vercel, a Render calculation/model API, and Supabase authentication and private assessment storage. Streamlit is no longer the application runtime.

## Architecture

```text
Vercel · Next.js / React
  ├── Supabase Auth · email/password sessions
  ├── Render API · uniform corrosion calculations
  │     ├── persistent Python worker · original PyTorch GNN checkpoints
  │     └── Supabase Postgres · requests carry verified user JWT + RLS
  └── device-local assessments and downloadable reports
```

The existing galvanic model remains available as a **synthetic-trained research model**. Its current proxy and compatibility scores are not validated penetration rates or calibrated probabilities. The uniform-corrosion engine uses separate, explicit physical calculations for measured thickness, current density, polarization resistance and coupon loss.

## Run locally

Requires Node 22.18+ and Python 3.11+. Install the CPU inference dependencies only if using the galvanic research features.

```sh
npm ci --prefix app
npm ci --prefix api
python -m pip install -r api/requirements.txt
git lfs pull
```

Copy `api/.env.example` to `api/.env` and `app/.env.example` to `app/.env.local`, then enter your project values. Do not commit those files. Apply the Supabase migration before using cloud snapshots.

In separate terminals:

```sh
cd api
npm run dev
```

```sh
cd app
npm run dev
```

The frontend uses port 3000; the API uses port 8000. Without frontend environment values the app runs locally calculated, device-only assessments. If an API URL is configured but unavailable, requests fail visibly and inputs are retained; the app does not silently substitute local results.

## Deploy

Follow [the deployment and cutover guide](docs/deployment.md).

- **Vercel:** import this repository with Root Directory `app`; use the Next.js preset and the three `NEXT_PUBLIC_*` variables in `app/.env.example`.
- **Render:** import root `render.yaml`. Its Docker image includes Node and Python and retains the existing model files. The proposed `standard` service is a paid memory tier; review current cost before creation. No service has been provisioned by this commit.
- **Supabase:** apply `supabase/migrations/202609300001_assessments.sql`; enable email/password auth; use a publishable key, not a service-role key. RLS isolates each user's assessments.

## Application features

| View | Function |
|---|---|
| Assessment | Four uniform-loss methods, validated inputs, conditional thickness forecast, measurement provenance, CSV import, report/JSON export |
| Saved comparisons | Local snapshots, Supabase sign-in, private cloud save/load/delete, paginated records |
| Galvanic research | Three retained checkpoints, single pair, CSV batches, group heatmap, material series and training history |
| Methods & evidence | Equations, assumptions, source links and validation boundaries |

## Verification

```sh
npm test --prefix api
npm run typecheck --prefix app
npm run build --prefix app
python -m unittest discover -s api/tests -p "test_*.py"
```

API tests exercise real HTTP behavior with mocked Supabase responses. They are not a live Supabase RLS test. Run the SQL isolation test against a disposable Supabase database and complete the two-account deployment checks before cutover.

## Repository structure

- `app/`: Vercel frontend and shared uniform-corrosion engine.
- `api/`: Render HTTP API, Python model adapter, tests and dependency pins.
- `supabase/`: schema, row access policies and isolation test.
- `pinn_model.py`, `graph_dataset.py`, `inference.py`: retained research model and inference utilities.
- `Post training/`: original checkpoint files and 200-epoch logs for each run; Git LFS required.
- `train.py`, `run_cloud.py`, original datasets/notebook: research/training workflow retained.
- `docs/`: research, migration, verification and operational documentation.

This is an engineering research preview. Numerical tests do not establish field predictive accuracy, standards conformance, safe service life or an inspection interval.
