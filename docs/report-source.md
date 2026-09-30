# MAST Corrosion: scientific and product decision

> Historical scope note (2026-09-30): this review inspected the older local folder on 2026-09-08. The subsequently identified GitHub repository at `940fafa` contains a newer NNConv model, three trained checkpoints, Streamlit dashboard and additional datasets. Statements below about absent checkpoints or applications apply only to the original local snapshot. The migration preserves the newer repository's model and validates inference parity; it does not establish field accuracy. See `deployment.md` for the current architecture.

Prepared 8 September 2026 for the founder and engineering reviewers. Scope: existing prototype, defensible rate estimation, potential customers, experimental validation and the first application. Geography: product discovery is global; Nigerian customer and regulatory requirements remain unverified.

## Executive decision

Build an inspection-evidence workspace with deterministic physical calculations first. Do not train a rate predictor on the current synthetic labels and call its test score real-world accuracy. The original project contains a promising assembly representation, but no validated corrosion-rate model. Commercial differentiation should initially be reproducibility and reduced assessment labor. Accurate environmental prediction remains a separate experimental program.

A predictive application does require a model in the mathematical sense. It does not necessarily require a neural network. The first model is a measured-rate estimator plus a conditional constant-rate extrapolation. This answers “at this observed rate, how much thickness would remain?” It does not establish what the rate will be under an untested environment.

## What the original work establishes

The repository contains a graph-network architecture, two synthetic generators and 10,000 generated records. All 78 pairs of 13 metals occur across three environment labels. There are no trained weights, experiments, independent benchmarks, data provenance records, uncertainty estimates or application. Detailed findings are in `checkpoints.md`.

The original rate proxy combines standard potentials, conductivity and area ratio. Standard potentials are equilibrium quantities, while actual corrosion involves reaction kinetics, films, transport and geometry. A galvanic series is specific to its environment and establishes tendencies, with exceptions to simple potential-gap rankings. It does not by itself give penetration rate. [ASTM G82, public scope and significance, 2021](https://store.astm.org/g0082-98r21e01.html).

The second generator claims PDF extraction, but it manually constructs tables and extrapolates compatibility labels with rank-distance rules. The source PDFs are absent. Those claims and constants should be quarantined as legacy research assumptions, not promoted into a materials database.

## Scientific scope and available methods

**Electrochemical conversion.** Use independently estimated corrosion current density, equivalent weight and density. Faraday conversion gives average uniform penetration; alloys and multiple valences require careful equivalent-weight selection. [ASTM G102-23 public scope](https://store.astm.org/standards/g102). Our implementation uses `0.003272 × i × EW / density`, with i in µA/cm², EW in g/equivalent and density in g/cm³, returning mm/year. The coefficient follows Gamry's documented convention. [Gamry DC corrosion calculations](https://help.gamry.com/Framework/experiments_c-dccorrosion.html).

**Polarization resistance.** Infer corrosion current density from area-normalized Rp and explicitly supplied anodic/cathodic Tafel slopes. LPR itself does not determine those slopes; kinetic complications and resistance effects can invalidate a simple interpretation. [Gamry electrochemical measurement guide](https://www.gamry.com/assets/Uploads/resources/Getting-Started-with-Electrochemical-Corrosion-Measurement3.pdf). Entering Ω instead of Ω·cm² creates a potentially substantial unit error. The application must state the unit beside the input.

**Coupon mass loss.** Use corrected mass loss, exposed area, density and exposure duration. This is an average over the exposure, not an instantaneous rate. Cleaning procedure, solution, temperature, gas, geometry and test duration affect interpretation; laboratory tests need cautious transfer to service. [ASTM G31 public scope](https://store.astm.org/standards/g31). The coefficient 87.6 for mg, cm², g/cm³ and hours is dimensionally derived using 8760 hours/year.

**Thickness history.** Fit thickness versus elapsed time for the same inspection location, retain dated observations, and flag inconsistent or unresolved change. A straight line is a baseline assumption, not a mechanistic future model. Time to a supplied minimum thickness uses the current margin divided by positive rate, and is distinct from an authorized inspection interval. [NASA Reliability-Centered Maintenance Guide, 2008](https://www.nasa.gov/wp-content/uploads/2023/06/nasa-rcmguide.pdf). Do not silently combine different locations or substitute nominal wall thickness for a dated measurement.

**Unsupported mechanisms.** Pitting, crevice corrosion, microbiologically influenced corrosion, stress-corrosion cracking, erosion-corrosion, coatings and cathodic protection cannot be summarized as universally safe uniform penetration. The first application must abstain when those mechanisms are selected. It must not label extrapolated time as safe service life, prescribe inspection deadlines or promise failure prevention.

## Why a galvanic neural network is not the first production model

A physically meaningful galvanic solver needs reaction kinetics and electrical/ionic transport. In a uniform-electrolyte-potential lumped approximation, area-weighted net electrode currents sum to zero. Dissolution follows the anodic reaction current, which need not equal the net galvanic current. Geometry, electrolyte voltage drop and polarization curves matter. [COMSOL galvanic modeling](https://doc.comsol.com/6.3/doc/com.comsol.help.edecm/edecm_ug_modeling.05.11.html), [COMSOL corrosion deformation example](https://doc.comsol.com/6.4/doc/com.comsol.help.models.corr.galvanic_corrosion_with_deformation/galvanic_corrosion_with_deformation.html).

The existing GNN penalizes net edge current at each node without reaction source terms, and sums current densities without area weights. This is not a sufficient electrode conservation law. Potential direction alone does not supply kinetics. Repairing these issues still would not manufacture ground truth.

NIST's research direction supports learning physical kinetic parameters, combining electrochemical characterization with statistical models and uncertainty. It is evidence for a future approach, not evidence our model works. [NIST Autonomous Scanning Droplet Cell, updated September 2025](https://www.nist.gov/programs-projects/autonomous-scanning-droplet-cell).

Recommended sequence: transparent measurement baseline → one scoped experimental mechanism → fitted physical parameters → residual or parameter-learning model only if it beats the baseline on unseen studies/assets. Introduce a graph model only when assembly geometry and multi-material interaction data justify its additional complexity.

## Customer problem and competitive position

The product should address the sequence from measurement to evidence review, not just display a number. PHMSA describes integrity work as assessment, information integration, risk analysis and mitigation. This is a US workflow reference, not a Nigerian compliance requirement. [PHMSA integrity management overview](https://primis.phmsa.dot.gov/stakeholder-comms/IM/).

DNV Synergi describes shared inspection history, anomaly management and assessment planning; Cenosco documents dated monitoring values, import and approval, and distinguishes several corrosion-rate bases. These vendor-described workflows show an established category, not proven demand for MAST. [DNV Synergi Pipeline](https://www.dnv.com/services/synergi-pipeline/), [Cenosco monitoring](https://ims-handbook.cenosco.com/docs/corrosion-monitoring), [Cenosco internal assessment](https://ims-handbook.cenosco.com/docs/plss-pl-internal-corrosion-assessment-1).

OLI describes a broader chemistry/electrochemistry engine and API. A future licensed integration might cover environments beyond the first release, but domain coverage, licensing and independent verification require evaluation. [OLI Corrosion Analyzer](https://olisystems.com/software/oli-studio/oli-studio-corrosion-analyzer/).

**Initial buyer hypothesis:** small inspection consultancies and plant integrity teams handling repeated carbon-steel measurements. **Initial job:** import and check evidence, reproduce the rate, compare assessments, communicate assumptions and produce a report. **Commercial experiment:** recruit 3–5 teams; review one anonymized asset/circuit per team; compare analyst time and error handling against their current process. A bounded paid pilot followed by a per-team subscription is a hypothesis, not a validated pricing recommendation. Do not set a market-derived price without interviews.

Pilot metrics: time from raw data to reviewed report; unit/date errors detected; reproducibility by a second engineer; proportion of records with usable provenance; repeat usage; willingness to pay. Establish acceptance thresholds with pilot users before collection. Do not equate calculator accuracy with reduced failure incidence.

## Dataset opportunities and exclusions

| Record | Verified nature | Proposed use and limitation |
|---|---|---|
| [CEIT shore-exposure, Zenodo 13897090](https://zenodo.org/records/13897090) | Six months of ultrasound on one uncoated 5 mm steel sample | Time-series pipeline demonstration. Single specimen; no generalization claim. Verify redistribution terms before bundling. |
| [Cr–Mo CO₂ experiment, Mendeley j4vfxfnt9j.1](https://data.mendeley.com/datasets/j4vfxfnt9j/1) | CC BY 4.0 experimental electrochemical files; narrowly controlled alloy/environment | Candidate method-aware benchmark; not yet ingested or independently reproduced. |
| [Oil-pipeline simulation, Mendeley 4nydhxjymw.1](https://data.mendeley.com/datasets/4nydhxjymw/1) | NORSOK/Monte Carlo synthetic observations | Simulator reproduction only; cannot validate field accuracy. |
| [PHMSA source records](https://www.phmsa.dot.gov/data-and-statistics/pipeline/source-data) | Incidents and infrastructure | Problem segmentation; not a measured-rate training target. |

The application ships illustrative fixtures only. Discovery of a dataset does not mean it was acquired, cleaned, licensed for redistribution or used to validate a model.

## Accuracy and release gates

Separate numerical correctness, measurement quality and predictive accuracy. Unit tests can establish the first. The others require actual experiments, uncertainty metadata and independent testing.

For a future learned model, preserve provenance and group splits by asset/study/time. Keep a completely held-out site; repeated observations must not leak between training and test. Compare against constant-rate and domain-specific physical baselines. Report MAE in mm/year, log-scale error, systematic bias, worst relevant underprediction, interval coverage and results by environment/material regime. Fit preprocessing and uncertainty calibration on training/calibration data only. Reject out-of-domain requests. Set acceptable errors before evaluating the final test set with engineering stakeholders.

A user-input sensitivity range is not a statistical confidence interval. A precise-looking decimal is not proof of measurement resolution. Neither is a model’s self-reported confidence.

## Research limitations and stopping decision

Research covered public standard summaries, original institutional work, experiment records and vendor documentation. Full paid standards were not acquired; no conformance claim is made. Actual buyer budgets, Nigerian requirements, multi-asset field data and independent performance remain unresolved. Searches stopped once source-supported distinctions were sufficient to choose the measurement-led implementation. More broad searches would not resolve the missing experimental or customer evidence.

Search lanes: electrochemical conversion and galvanic-series limits; physics-guided corrosion learning; inspection workflows and commercial products; original corrosion datasets. Critical G82, G102, Gamry and NIST claims were spot-checked by the coordinating agent. The source ledger records provenance. Implementation and release verification are tracked separately.
