# Delivery checkpoints

## 2026-09-30 migration checkpoint

The GitHub repository `Th3Samaritan/MAST-Corrosion` was located at `940fafa`. It is newer than the local snapshot audited below and includes the actual Streamlit UI, NNConv model, three checkpoints and training logs. The new delivery branch is `migration/vercel-render-supabase` in the `upstream/` checkout. Treat the original audit below as historical, not a claim about the newer repository.

- COMPLETE: inspect current GitHub source and remove active Streamlit UI/runtime dependencies; retain inference/training/data.
- COMPLETE: implement Next.js frontend, Render API/Python inference worker, Supabase Auth and private snapshot storage schema.
- COMPLETE: frontend production build, TypeScript, application lint, 15 Node tests and 4 real-model tests (including all three checkpoints).
- COMPLETE: deployment, state, migration and operational documentation.
- PENDING: identify target provider projects/authenticate, apply and test live RLS, verify Docker staging deployment, production browser checks and cutover. Vercel is not signed in; Supabase/Render projects not provided; Docker daemon unavailable locally.

Application lint excludes unchanged generated `components/ui` and `hooks/use-mobile.ts`; the project does not enable React Compiler. Numerical correctness and inference parity are distinct from experimental validation.

---

Scope: MAST-Corrosion scientific audit, evidence review, working engineering application, and reproducible documentation. Audience: founder and corrosion/inspection engineers. Date: 2026-09-08.

Assumptions: begin with uniform metal loss and measurement-led forecasts; no universal material/environment predictor or field accuracy claim without independent experiments. Initial buyer hypothesis: small inspection consultancies and process-asset teams. No customer interviews have occurred.

1. COMPLETE — inspect original files and dataset. Four files; 10,000 synthetic rows, 78 material pairs, three environments; no trained weights, training pipeline, application, experimental labels, or tests.
2. IN PROGRESS — primary-source discovery, targeted scientific and commercial follow-up, reconcile limitations, select scope. Source classes: standards abstracts, original research, institutional datasets, vendor product documentation. Dedicated planning tool unavailable; this file records the plan.
3. PENDING — implement explicit-unit physics engine and application with state handling, provenance, comparison and report workflow.
4. PENDING — numerical benchmark and boundary tests, production build, documentation audit, private deployment where available.
5. PENDING — deliver verified capabilities and name remaining experimental/commercial gates.

## Original prototype audit

- `synthetic_data_generator.py` uses standard EMF values as operating potentials, a constant 0.5 polarization resistance, and inverse conductivity without cell geometry. The output lacks defined current-density units. Multiplying by area ratio is an arbitrary proxy, not a coupled electrode solution.
- Dataset is generated from that proxy plus noise. A good fit would reproduce the generator, not validate field corrosion.
- `synthetic_data_generator(3).py` hardcodes tables despite a function name claiming PDF extraction; no source PDFs exist here. Several potentials and compatibility rules are assigned by heuristic rank distance. They must not be represented as verified standard tables.
- `pinn_architecture.py` supplies a GNN definition and random demonstration only. Node charge balance omits electrode reaction source/sink currents; summing current densities without electrode areas is not charge conservation. For a single edge, the stated zero-net-current penalty favors zero galvanic current.
- Potential output is unanchored; edge direction convention is not sufficiently specified; bidirectional edge handling is ambiguous; edge attributes do not enter message passing. The one-edge squeeze is also shape-fragile.
- Preserve original files for research provenance. The application must not import or train on them as physical truth.

## Research gap matrix

| Claim / decision | Evidence | Confidence / gap | Next step |
|---|---|---|---|
| Series alone does not determine rate | ASTM G82 scope and electrochemical kinetics | High; full standard not acquired | Use measured inputs |
| Current conversion is uniform penetration | ASTM G102-23 public scope | High; no compliance claim | Independent dimensional benchmarks |
| Physics-guided ML is plausible | NIST autonomous scanning droplet cell | Research direction, not product validation | Acquire scoped experimental dataset |
| Inspection workflow has commercial demand | Existing vendor inspection/rate tools | Category evidence; willingness to pay untested | Interview and pilot |
| Universal model can be precise | No supporting evidence | Unsupported | Do not claim or deploy |
