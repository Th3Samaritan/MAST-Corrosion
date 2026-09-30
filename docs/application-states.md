# Application state and process reference

| Area | State | Behavior |
|---|---|---|
| Assessment | illustrative initial | Clearly marked sample, local deterministic example only |
| Assessment | editing | Result invalidated; new calculation required |
| Assessment | calculating | Submit/export disabled; inputs retained; stale async completion discarded |
| Assessment | valid | Rate, basis, conditional forecast and review notes shown |
| Assessment | invalid / unsupported | Explicit error; no invented prediction |
| Forecast | positive resolved rate | Constant-rate scenario and input/sensitivity range |
| Forecast | zero / increasing / unresolved | No finite safe-life claim |
| Forecast | minimum reached | Zero time and engineering-review message |
| Device storage | available | Explicit save; up to 100 records; no automatic cloud migration |
| Device storage | unavailable / corrupt | Existing data preserved; file export remains available |
| Cloud | unconfigured | Configuration message; local functions continue |
| Cloud | signed out | Sign-in / account creation form |
| Cloud | confirmation pending | Email confirmation instructions |
| Cloud | session restoring | Loading message |
| Cloud | signed in | Private paginated snapshot list, save/load/delete |
| Cloud | saving / loading / deleting | Controls disabled; specific failure visible; current inputs retained |
| Cloud | sign-out / identity change | Prior user's list cleared; stale responses discarded |
| Cloud | delete requested | Explicit destructive confirmation |
| Model | unloaded | Reference/training actions; no automatic inference cost |
| Model | pending | Loading status, inputs retained; queue and timeout bounded |
| Model | invalid / unavailable | Validation or unavailable response, not synthetic fallback |
| Model | completed | Last completed run and input pair retained beside outputs |
| Reports | imported | Revalidate shape, dates and numbers; recompute rather than trusting stored result |
| New assessment | requested | Confirm before clearing unsaved inputs |

Uniform-loss calculation source is `app/lib/corrosion.ts`, shared by browser and Render to avoid duplicated equations. API ownership comes from Supabase Auth, not a client `user_id`. Row access is separately enforced by Postgres. Saved results remain unreviewed. Frontend render/escape is React-based; imported CSV/JSON is never executed as HTML or code.

Model feature construction preserves the original two-node graph, 22 node features, 6 edge features, bidirectional edge order and environment encoding. Original model training is retained and not rerun by this migration. The current proxy is intentionally separated from the measured mm/year engine.
