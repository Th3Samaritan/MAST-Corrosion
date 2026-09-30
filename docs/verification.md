# Migration verification — 2026-09-30

## Completed locally

- Next.js 16.3.7 production build and TypeScript compilation.
- Application lint (unchanged vendored UI catalog and generated mobile hook excluded).
- 15 Node tests: Faraday, Stern–Geary, coupon and thickness benchmarks; unresolved trends and minimum reached; input/date/CSV rejection; actual HTTP health/calculation/CORS/preflight; malformed and oversized requests; unauthenticated/expired access; verified ownership on save/read/delete; cursor pagination with timestamp ties; secret-key and origin configuration rejection.
- 4 Python test methods: all three original checkpoints compared with retained inference at area ratios 0.01, 1 and 50; CSV with quoted-comma material name compared with single inference; invalid material/environment/nonfinite/out-of-range ratios rejected; all three 200-epoch logs read successfully.
- Compatible npm security fixes applied; npm audit reported zero vulnerabilities at verification time.
- Production frontend HTTP smoke test returned 200 on localhost. The Node-to-Python protocol also returned 36 materials, 3 training histories and a real prediction.

The independently calculated Faraday fixture is 0.1160894790343075 mm/year for 10 µA/cm², EW 27.9225 g/equivalent and density 7.87 g/cm³ with coefficient 0.003272. An earlier research hand-calculation was corrected in the test fixture; production equation was unchanged.

## Not established by those checks

- No field predictive accuracy, material universality or standards compliance has been demonstrated.
- Supabase HTTP responses were mocked in API tests. Database RLS SQL is supplied but has not been executed against a provisioned project. Two-user end-to-end checks remain required.
- The Docker daemon was unavailable. Python/model parity ran locally with the pinned top-level dependency versions, but Linux image build, memory demand and provider-specific LFS checkout remain staging gates.
- No live Vercel/Render deployment or browser interaction audit is claimed. Existing provider project identities and authenticated access are still required.
- GitHub Actions is supplied to repeat Node/frontend and real-model tests on Linux after push. Its outcome must be checked separately; local success is not a CI result.

## Runtime notes

The original network's current output remains a synthetic proxy. The migration deliberately preserves feature encoding and checkpoint behavior, including any scientific limitations in the learned output. We do not relabel this as a validated physical corrosion rate.

Cloud deletion is explicit and irreversible at the application level; users can export snapshots first. There is no silent upload of device-local history, no service-role key in the browser or API, and no automatic shutdown of the old hosted Streamlit instance.
