# Vercel, Render and Supabase deployment

Migration prepared 2026-09-30 from GitHub `Th3Samaritan/MAST-Corrosion`, baseline `940fafa`. The older local workspace did not contain the Streamlit implementation; the GitHub source did. This migration preserves that newer model and data.

## Project values

No deployment credentials are committed. Existing account/project identities should be reused once identified. A GitHub repository was found; the target Supabase, Render and Vercel project identities are still unspecified. The local Vercel CLI is not signed in.

| Location | Setting | Value |
|---|---|---|
| Vercel | Root Directory | `app` |
| Vercel | Framework | Next.js |
| Vercel | Node | 22.x or supported newer LTS |
| Vercel | `NEXT_PUBLIC_API_URL` | Exact Render HTTPS URL, no trailing slash |
| Vercel | `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| Vercel | `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | Publishable key (legacy anon accepted) |
| Render | Blueprint | Root `render.yaml` |
| Render | `SUPABASE_URL` | Same project URL |
| Render | `SUPABASE_PUBLISHABLE_KEY` | Same publishable key |
| Render | `ALLOWED_ORIGINS` | Comma-separated exact Vercel origins; no paths, wildcards or trailing slash |
| Render | `PORT` | Platform-supplied; API binds `0.0.0.0` |

Public frontend variables are compiled into the browser bundle. **Never put a service-role, secret API key or database password into a `NEXT_PUBLIC_*` variable.** This architecture does not need a privileged Supabase key: the API verifies the user token against Supabase Auth and forwards that token to PostgREST, where RLS applies. [Supabase API key guidance](https://supabase.com/docs/guides/getting-started/api-keys), [getUser identity validation](https://supabase.com/docs/reference/javascript/auth-getuser).

## 1. Supabase

1. Open the intended project. Apply `supabase/migrations/202609300001_assessments.sql` once with the SQL Editor, or link the CLI project and use `supabase db push`.
2. The table grants authenticated users select/insert/delete on their own rows. Anonymous users have no access. Updates are intentionally unavailable; changed calculations produce a new snapshot.
3. Enable email/password sign-in. Keep email confirmation configured according to your account policy. Set the Auth Site URL to the production Vercel origin so confirmation links return to the application; users then sign in with email/password.
4. Configure production email delivery and its limits before onboarding customers. The UI supports sign-in, account creation, confirmation instructions and sign-out. Password recovery UI is not included in this migration; account recovery remains an operational task.
5. Run `supabase/tests/assessment_isolation.sql` against a disposable/test database after applying the schema. It rolls back its test users and rows. Repeat live end-to-end isolation with two real accounts.

Stored JSON results are unreviewed. A user with a valid token can also write their own rows via PostgREST. Therefore consumers must validate/recalculate inputs rather than treat stored numeric results as signed or certified. The UI already does this on load.

## 2. Render

1. Import the existing repository using the root Blueprint, or create a Docker Web Service using root `Dockerfile` and context `.`.
2. Review the selected service's cost before provisioning. `render.yaml` proposes **standard**, because Python/PyTorch plus the application need memory. This is a deployment proposal, not an assertion of measured peak RAM. Benchmark memory and latency in staging before choosing a smaller tier.
3. Enter the three Render variables above. The API refuses production startup without Supabase configuration and HTTPS browser origins.
4. Verify Git LFS checkpoint contents reach the build context. Docker fails if checkpoint files are only LFS pointer text. If the provider does not fetch LFS, use a CI-built image from an LFS-enabled checkout; do not silently deploy without model weights.
5. Build and wait for `/health` to return `status: ok`. This endpoint is liveness plus a configuration indicator; it does **not** validate database policies or model loading.
6. Sign in through the frontend and invoke model catalog/training/prediction. The worker is started lazily, restricted to repo-owned checkpoints, caches one model, processes one request at a time and bounds the queue.

The API uses a per-process 120 requests/minute limit keyed by socket address, deliberately ignoring untrusted forwarded headers. Behind a shared proxy this may limit a group of callers together. Configure a trusted edge/shared rate limiter before high-traffic or multi-instance operation. Requests are capped at 256 KB; model batches at 400 pairs. There are no arbitrary file-path or model-upload endpoints.

Render routing and health-check behavior follow its [Blueprint reference](https://render.com/docs/blueprint-spec) and [health-check documentation](https://render.com/docs/health-checks). Docker itself was not verified locally because the Docker daemon was unavailable; staging container verification is required.

## 3. Vercel

1. Import `Th3Samaritan/MAST-Corrosion`; set Root Directory to `app`. Preserve the existing project's domain/settings if migrating an existing Vercel project.
2. Use Next.js defaults: install `npm ci`, build `npm run build`. Do not select Vite, Streamlit or a static-export preset. `app/vercel.json` identifies Next.js.
3. Set the three public variables separately for preview and production. Rebuild after changing them; public values are build-time values.
4. Add each permitted preview/production frontend origin to Render's `ALLOWED_ORIGINS`. Do not permit all `*.vercel.app` origins, since other users control deployments there.
5. Verify the preview, then point production at the tested release. [Vercel deployment CLI](https://vercel.com/docs/cli/deploy).

## Cutover checks

- Anonymous visitor can calculate a uniform-loss assessment, but cannot list, save or run private model endpoints without sign-in.
- Account A saves a snapshot and reads it after signing in on another browser. Account B cannot list, read, overwrite or delete A's ID, even by issuing requests manually.
- Invalid/expired bearer token returns 401. Unknown origins are rejected. Oversized JSON returns 413, malformed JSON 400, invalid physics input 422.
- All three model checkpoints load; single and batch outputs match retained inference utilities within tolerance. A quoted-comma material name works in CSV.
- Device saves remain separate from cloud saves; no historical browser data is silently uploaded. Export/import lets the user move selected snapshots.
- API outage shows an error while retaining inputs; retries do not overwrite existing snapshots. Changed inputs invalidate stale calculations.
- Confirmed email signup, logout and token refresh function with the production Auth settings.
- Downloaded Markdown/JSON includes provenance, equation, units, assumptions and unreviewed status.

Only after these checks should the old Streamlit deployment be stopped. This change removes Streamlit source/runtime dependencies in the repository, but does not shut down an existing Streamlit Cloud app or alter its domain automatically.

## Operations and rollback

Keep secrets in provider settings. API logs expose request IDs and generic error events, not bearer tokens or assessment bodies. Monitor API failures, worker timeouts/restarts and memory. Plan Supabase backups according to the chosen account tier; JSON export is a user-owned fallback, not a managed backup system.

Deploy a matched frontend/API revision. The frontend rejects mismatched calculation-engine versions. Preserve checkpoints and calibration metadata alongside every future model change. For rollback, revert the application deployment to the prior revision; the additive assessment table may remain. Do not drop the table during code rollback. Git history retains the old Streamlit UI if it needs to be restored.
