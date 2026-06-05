"""
data_extraction.py — Galvanic Corrosion PINN: Data Extraction & Synthetic Data Generation
==========================================================================================

Replaces synthetic_data_generator(4).py with corrected data from the AMMTIAC
PDF tables.  All corrections are documented inline.

Key fixes vs. the original script:
  1. Group ordering (Table 1): Cd/Be → position 3, Al → position 4
  2. Galvanic series (Table 2): published seawater potentials vs SCE
  3. Compatibility matrix: separate Marine (M) and Industrial (I) grids
  4. Material-dependent polarization resistance (R_p)
  5. EMF series (Table 3): retained as-is (already correct)

Dependencies: pandas, numpy  (NO torch / ML imports)
"""

import pandas as pd
import numpy as np
import itertools
import os

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def _safe_to_csv(df: pd.DataFrame, filepath: str, **kwargs) -> str:
    """
    Write a DataFrame to CSV, handling PermissionError when the file is
    locked (e.g. open in Excel).  Falls back to an alternate filename.
    Returns the path actually written.
    """
    try:
        df.to_csv(filepath, **kwargs)
        return filepath
    except PermissionError:
        base, ext = os.path.splitext(filepath)
        for suffix in range(1, 100):
            alt = f"{base}_{suffix}{ext}"
            if not os.path.exists(alt):
                try:
                    df.to_csv(alt, **kwargs)
                    print(f"  ⚠ Original file locked; wrote to: {alt}")
                    return alt
                except PermissionError:
                    continue
        raise


# ═══════════════════════════════════════════════════════════════════════════
# 1.  EMF Series  (Table 3) — Standard Electrode Potentials
# ═══════════════════════════════════════════════════════════════════════════

def extract_emf_series() -> pd.DataFrame:
    """
    Returns the Standard EMF Series (Table 3 from PDF).
    Values are standard electrode potentials in volts vs SHE.
    Saves to pdf_table3_emf_series.csv.
    """
    emf_data = [
        {"Equilibrium": "Au-Au+3",    "Potential_V":  1.498},
        {"Equilibrium": "Pt-Pt+2",    "Potential_V":  1.200},
        {"Equilibrium": "Pd-Pd+2",    "Potential_V":  0.987},
        {"Equilibrium": "Ag-Ag+",     "Potential_V":  0.799},
        {"Equilibrium": "Hg-Hg2+2",   "Potential_V":  0.788},
        {"Equilibrium": "Cu-Cu+2",    "Potential_V":  0.337},
        {"Equilibrium": "H2-H+",      "Potential_V":  0.000},
        {"Equilibrium": "Pb-Pb+2",    "Potential_V": -0.126},
        {"Equilibrium": "Sn-Sn+2",    "Potential_V": -0.136},
        {"Equilibrium": "Ni-Ni+2",    "Potential_V": -0.250},
        {"Equilibrium": "Co-Co+2",    "Potential_V": -0.277},
        {"Equilibrium": "Cd-Cd+2",    "Potential_V": -0.403},
        {"Equilibrium": "Fe-Fe+2",    "Potential_V": -0.440},
        {"Equilibrium": "Cr-Cr+3",    "Potential_V": -0.744},
        {"Equilibrium": "Zn-Zn+2",    "Potential_V": -0.763},
        {"Equilibrium": "Al-Al+3",    "Potential_V": -1.662},
        {"Equilibrium": "Mg-Mg+2",    "Potential_V": -2.363},
        {"Equilibrium": "Na-Na+",     "Potential_V": -2.714},
        {"Equilibrium": "K-K+",       "Potential_V": -2.925},
    ]
    df = pd.DataFrame(emf_data)
    out_path = os.path.join(OUTPUT_DIR, "pdf_table3_emf_series.csv")
    out_path = _safe_to_csv(df, out_path, index=False)
    print(f"  [Table 3] EMF Series → {out_path}  ({len(df)} entries)")
    return df


# ═══════════════════════════════════════════════════════════════════════════
# 2.  Material Groups  (Table 1) — CORRECTED ordering
# ═══════════════════════════════════════════════════════════════════════════

def extract_material_groups() -> pd.DataFrame:
    """
    Returns the 20 compatibility material groups (Table 1) ordered
    active → noble exactly as printed in the PDF.

    CORRECTION: The original code had Al at position 3 and Cd/Be at
    position 4.  The PDF clearly lists Cd/Be at position 3 and Al at
    position 4.
    """
    compat_groups = [
        {"Group_ID":  1, "Category": "Magnesium"},
        {"Group_ID":  2, "Category": "Zinc, Zinc Coating"},
        {"Group_ID":  3, "Category": "Cadmium, Beryllium"},                          # ← CORRECTED (was pos 4)
        {"Group_ID":  4, "Category": "Aluminum, Mg-Coated Aluminum, Zn-Coated Aluminum"},  # ← CORRECTED (was pos 3)
        {"Group_ID":  5, "Category": "Cu-Coated Aluminum"},
        {"Group_ID":  6, "Category": "Steels-Carbon, Low Alloy"},
        {"Group_ID":  7, "Category": "Lead"},
        {"Group_ID":  8, "Category": "Tin, Tin-Lead, Indium"},
        {"Group_ID":  9, "Category": "St. Steels-Martensitic, Ferritic"},
        {"Group_ID": 10, "Category": "Chromium, Molybdenum, Tungsten"},
        {"Group_ID": 11, "Category": "St. Steels-Aust., PH, Super Strength, Heat Resistant"},
        {"Group_ID": 12, "Category": "Brass-Lead Bronze"},
        {"Group_ID": 13, "Category": "Brass-Low Copper, Bronze-Low Copper"},
        {"Group_ID": 14, "Category": "Brass-High Copper, Bronze-High Copper"},
        {"Group_ID": 15, "Category": "Copper-High Nickel, Monel"},
        {"Group_ID": 16, "Category": "Nickel, Cobalt"},
        {"Group_ID": 17, "Category": "Titanium"},
        {"Group_ID": 18, "Category": "Silver"},
        {"Group_ID": 19, "Category": "Palladium, Rhodium, Gold, Platinum"},
        {"Group_ID": 20, "Category": "Graphite"},
    ]
    df = pd.DataFrame(compat_groups)
    out_path = os.path.join(OUTPUT_DIR, "pdf_table1_material_groups.csv")
    out_path = _safe_to_csv(df, out_path, index=False)
    print(f"  [Table 1] Material Groups → {out_path}  ({len(df)} groups)")
    return df


# ═══════════════════════════════════════════════════════════════════════════
# 3.  Galvanic Series  (Table 2) — Published seawater potentials vs SCE
# ═══════════════════════════════════════════════════════════════════════════

def extract_galvanic_series() -> pd.DataFrame:
    """
    Returns the galvanic series for flowing seawater with published
    potentials vs SCE (Saturated Calomel Electrode).

    CORRECTION: The original code used EMF (SHE) potentials from Table 3
    mixed with invented values.  The PDF Table 2 only shows RANKINGS,
    not potentials.  We now use standard published seawater galvanic
    series potentials (volts vs SCE) from Fontana, Jones, and MIL-STD-889.

    Group assignments use the CORRECTED group ordering (Cd/Be = 3, Al = 4).
    """
    galvanic_series = [
        # --- Noble end ---
        {"Rank":  1, "Material": "Platinum",
         "Potential_V_SCE":  0.22,
         "Group": "Palladium, Rhodium, Gold, Platinum"},

        {"Rank":  2, "Material": "Gold",
         "Potential_V_SCE":  0.16,
         "Group": "Palladium, Rhodium, Gold, Platinum"},

        {"Rank":  3, "Material": "Graphite",
         "Potential_V_SCE":  0.13,
         "Group": "Graphite"},

        {"Rank":  4, "Material": "Titanium",
         "Potential_V_SCE":  0.06,
         "Group": "Titanium"},

        {"Rank":  5, "Material": "Silver",
         "Potential_V_SCE":  0.04,
         "Group": "Silver"},

        {"Rank":  6, "Material": "Chlorimet 3 (62 Ni, 18 Cr, 18 Mo)",
         "Potential_V_SCE": -0.04,
         "Group": "Nickel, Cobalt"},

        {"Rank":  7, "Material": "Hastelloy C (62 Ni, 17 Cr, 15 Mo)",
         "Potential_V_SCE": -0.04,
         "Group": "Nickel, Cobalt"},

        {"Rank":  8, "Material": "18-8 Mo SS (passive)",
         "Potential_V_SCE": -0.05,
         "Group": "St. Steels-Aust., PH, Super Strength, Heat Resistant"},

        {"Rank":  9, "Material": "18-8 SS (passive)",
         "Potential_V_SCE": -0.08,
         "Group": "St. Steels-Aust., PH, Super Strength, Heat Resistant"},

        {"Rank": 10, "Material": "Chromium SS 11-30% (passive)",
         "Potential_V_SCE": -0.10,
         "Group": "St. Steels-Martensitic, Ferritic"},

        {"Rank": 11, "Material": "Inconel (passive) (80 Ni, 13 Cr, 7 Fe)",
         "Potential_V_SCE": -0.12,
         "Group": "Copper-High Nickel, Monel"},

        {"Rank": 12, "Material": "Nickel (passive)",
         "Potential_V_SCE": -0.12,
         "Group": "Nickel, Cobalt"},

        {"Rank": 13, "Material": "Silver solder",
         "Potential_V_SCE": -0.14,
         "Group": "Silver"},

        {"Rank": 14, "Material": "Monel (70 Ni, 30 Cu)",
         "Potential_V_SCE": -0.15,
         "Group": "Copper-High Nickel, Monel"},

        {"Rank": 15, "Material": "Cupronickels (60-90 Cu, 40-10 Ni)",
         "Potential_V_SCE": -0.17,
         "Group": "Copper-High Nickel, Monel"},

        {"Rank": 16, "Material": "Bronzes (Cu-Sn)",
         "Potential_V_SCE": -0.18,
         "Group": "Brass-High Copper, Bronze-High Copper"},

        {"Rank": 17, "Material": "Copper",
         "Potential_V_SCE": -0.20,
         "Group": "Copper-High Nickel, Monel"},

        {"Rank": 18, "Material": "Brasses (Cu-Zn)",
         "Potential_V_SCE": -0.23,
         "Group": "Brass-Low Copper, Bronze-Low Copper"},

        {"Rank": 19, "Material": "Chlorimet 2",
         "Potential_V_SCE": -0.28,
         "Group": "Nickel, Cobalt"},

        {"Rank": 20, "Material": "Hastelloy B (65 Ni, 28 Mo, 6 Fe)",
         "Potential_V_SCE": -0.33,
         "Group": "Nickel, Cobalt"},

        {"Rank": 21, "Material": "Inconel (active)",
         "Potential_V_SCE": -0.35,
         "Group": "Nickel, Cobalt"},

        {"Rank": 22, "Material": "Nickel (active)",
         "Potential_V_SCE": -0.35,
         "Group": "Nickel, Cobalt"},

        {"Rank": 23, "Material": "Tin",
         "Potential_V_SCE": -0.42,
         "Group": "Tin, Tin-Lead, Indium"},

        {"Rank": 24, "Material": "Lead",
         "Potential_V_SCE": -0.47,
         "Group": "Lead"},

        {"Rank": 25, "Material": "Lead-tin solders",
         "Potential_V_SCE": -0.50,
         "Group": "Tin, Tin-Lead, Indium"},

        {"Rank": 26, "Material": "18-8 Mo SS (active)",
         "Potential_V_SCE": -0.53,
         "Group": "St. Steels-Aust., PH, Super Strength, Heat Resistant"},

        {"Rank": 27, "Material": "18-8 SS (active)",
         "Potential_V_SCE": -0.53,
         "Group": "St. Steels-Aust., PH, Super Strength, Heat Resistant"},

        {"Rank": 28, "Material": "Ni-Resist (high nickel cast iron)",
         "Potential_V_SCE": -0.55,
         "Group": "Steels-Carbon, Low Alloy"},

        {"Rank": 29, "Material": "Chromium SS 13% (active)",
         "Potential_V_SCE": -0.57,
         "Group": "St. Steels-Martensitic, Ferritic"},

        {"Rank": 30, "Material": "Cast iron",
         "Potential_V_SCE": -0.61,
         "Group": "Steels-Carbon, Low Alloy"},

        {"Rank": 31, "Material": "Steel or iron",
         "Potential_V_SCE": -0.61,
         "Group": "Steels-Carbon, Low Alloy"},

        {"Rank": 32, "Material": "2024 aluminum (4.5 Cu, 1.5 Mg, 0.6 Mn)",
         "Potential_V_SCE": -0.69,
         "Group": "Aluminum, Mg-Coated Aluminum, Zn-Coated Aluminum"},

        {"Rank": 33, "Material": "Cadmium",
         "Potential_V_SCE": -0.70,
         "Group": "Cadmium, Beryllium"},

        {"Rank": 34, "Material": "Commercially pure aluminum (1100)",
         "Potential_V_SCE": -0.73,
         "Group": "Aluminum, Mg-Coated Aluminum, Zn-Coated Aluminum"},

        {"Rank": 35, "Material": "Zinc",
         "Potential_V_SCE": -1.03,
         "Group": "Zinc, Zinc Coating"},

        {"Rank": 36, "Material": "Magnesium and magnesium alloys",
         "Potential_V_SCE": -1.60,
         "Group": "Magnesium"},
        # --- Active end ---
    ]
    df = pd.DataFrame(galvanic_series)
    out_path = os.path.join(OUTPUT_DIR, "pdf_table2_galvanic_series.csv")
    out_path = _safe_to_csv(df, out_path, index=False)
    print(f"  [Table 2] Galvanic Series → {out_path}  ({len(df)} materials)")
    return df


# ═══════════════════════════════════════════════════════════════════════════
# 4.  Compatibility Rules  (Table 1 matrix) — Separate M and I grids
# ═══════════════════════════════════════════════════════════════════════════

def generate_compatibility_rules(groups_df: pd.DataFrame) -> dict:
    """
    Translates the 20×20 AMMTIAC Table 1 compatibility matrix into a
    lookup dictionary keyed by frozenset({group_A, group_B}).

    Returns dict mapping:
        frozenset({group_A, group_B}) → {
            "Marine (Seawater)": "Compatible" | "Unfavorable",
            "Industrial (Acidic Rain)": "Compatible" | "Unfavorable"
        }

    CORRECTION: The original code had a single grid and the wrong
    row/column ordering (Al at 3, Cd/Be at 4).  This version:
      - Uses the corrected ordering: Cd/Be at position 3, Al at position 4
      - Maintains TWO separate grids (Marine and Industrial)

    NOTE: In the scanned PDF source, the Marine (M) and Industrial (I)
    sub-rows appear identical for all 190 pairs.  Both grids below are
    therefore set to the same values.  The two-grid STRUCTURE is preserved
    so that future updates with higher-quality scans can differentiate them.

    Grid encoding:  1 = Unfavorable,  0 = Compatible
    """
    groups = groups_df["Category"].tolist()

    # ── CORRECTED 20×20 grid (rows/cols 3 & 4 swapped from old code) ──
    # Columns:  1   2   3   4   5   6   7   8   9  10  11  12  13  14  15  16  17  18  19  20
    grid_marine = [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],  #  1: Magnesium
        [1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],  #  2: Zinc
        [1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],  #  3: Cd/Be  ← was row 4
        [1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],  #  4: Al     ← was row 3
        [1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],  #  5: Cu-Al
        [1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],  #  6: Steels
        [1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],  #  7: Lead
        [1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1],  #  8: Tin
        [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1],  #  9: SS Mart/Ferr
        [1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1],  # 10: Cr/Mo/W
        [1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1],  # 11: SS Aust/PH
        [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1],  # 12: Brass-Pb Brz
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],  # 13: Brass-Low Cu
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],  # 14: Brass-High Cu
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],  # 15: Cu-Ni/Monel
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],  # 16: Ni/Co
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],  # 17: Titanium
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0],  # 18: Silver
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0],  # 19: Pd/Rh/Au/Pt
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0],  # 20: Graphite
    ]

    # Industrial grid — identical to Marine in current scan (see docstring)
    grid_industrial = [row[:] for row in grid_marine]  # deep copy

    # Build the lookup dictionary
    explicit_rules = {}

    for i in range(20):
        for j in range(i + 1, 20):
            mat_a = groups[i]
            mat_b = groups[j]
            pair = frozenset([mat_a, mat_b])

            marine_status = "Unfavorable" if grid_marine[i][j] == 1 else "Compatible"
            industrial_status = "Unfavorable" if grid_industrial[i][j] == 1 else "Compatible"

            explicit_rules[pair] = {
                "Marine (Seawater)": marine_status,
                "Industrial (Acidic Rain)": industrial_status,
            }

    return explicit_rules


# ═══════════════════════════════════════════════════════════════════════════
# 5.  Polarization Resistance Lookup  (material-dependent)
# ═══════════════════════════════════════════════════════════════════════════

# Mapping from group category → R_p (Ω·m²)
_RP_TABLE = {
    # Active metals
    "Magnesium":                                                     0.1,
    "Zinc, Zinc Coating":                                            0.1,
    "Cadmium, Beryllium":                                            0.1,
    "Aluminum, Mg-Coated Aluminum, Zn-Coated Aluminum":             0.1,
    "Cu-Coated Aluminum":                                            0.1,
    # Carbon / low-alloy steels
    "Steels-Carbon, Low Alloy":                                      0.3,
    "Lead":                                                          0.3,
    "Tin, Tin-Lead, Indium":                                         0.3,
    # Stainless steels (passive)
    "St. Steels-Martensitic, Ferritic":                              5.0,
    "Chromium, Molybdenum, Tungsten":                                5.0,
    "St. Steels-Aust., PH, Super Strength, Heat Resistant":         5.0,
    # Copper alloys
    "Brass-Lead Bronze":                                             1.0,
    "Brass-Low Copper, Bronze-Low Copper":                           1.0,
    "Brass-High Copper, Bronze-High Copper":                         1.0,
    "Copper-High Nickel, Monel":                                     1.0,
    # Nickel alloys
    "Nickel, Cobalt":                                                2.0,
    # Noble metals
    "Titanium":                                                     10.0,
    "Silver":                                                       10.0,
    "Palladium, Rhodium, Gold, Platinum":                           10.0,
    "Graphite":                                                     10.0,
}

_DEFAULT_RP = 0.5  # fallback


def get_polarization_resistance(group_name: str) -> float:
    """
    Returns the polarization resistance R_p (Ω·m²) for a given
    material group.  Uses published order-of-magnitude values rather
    than the previous constant 0.5 for all materials.
    """
    return _RP_TABLE.get(group_name, _DEFAULT_RP)


# ═══════════════════════════════════════════════════════════════════════════
# 6.  Synthetic Data Generator
# ═══════════════════════════════════════════════════════════════════════════

def generate_synthetic_data(
    galvanic_df: pd.DataFrame,
    groups_df: pd.DataFrame,
    num_samples: int = 25000,
) -> pd.DataFrame:
    """
    Generates *num_samples* synthetic galvanic joint records by randomly
    pairing materials from the 36-entry galvanic series, assigning random
    environments and area ratios, then computing a physics-based galvanic
    current density target.

    Improvements over the original generator:
      • Uses CORRECTED compatibility rules (separate M / I grids)
      • Uses material-dependent polarization resistance
      • Potential column is Potential_V_SCE (seawater vs SCE)
    """
    print("\n--- Generating Synthetic Joint Data ---")

    # Environment conductivities (S/m)
    environments = {
        "Marine (Seawater)":      5.0,
        "Industrial (Acidic Rain)": 0.1,
        "Rural (Freshwater)":     0.01,
    }
    env_names = list(environments.keys())

    # Load the exhaustive 190-pair compatibility rules
    explicit_pdf_rules = generate_compatibility_rules(groups_df)
    print(f"  → Loaded {len(explicit_pdf_rules)} exact PDF matrix rules.")

    materials_list = galvanic_df.to_dict("records")
    data = []

    rng = np.random.default_rng()  # modern NumPy RNG

    for _ in range(num_samples):
        # ── Pick two distinct materials ──
        idx_a, idx_b = rng.choice(len(materials_list), size=2, replace=False)
        mat_a = materials_list[idx_a]
        mat_b = materials_list[idx_b]

        v_a = mat_a["Potential_V_SCE"]
        v_b = mat_b["Potential_V_SCE"]

        # Assign anode (more negative) and cathode (more positive)
        if v_a < v_b:
            anode, cathode = mat_a, mat_b
        else:
            anode, cathode = mat_b, mat_a

        delta_v = cathode["Potential_V_SCE"] - anode["Potential_V_SCE"]

        # ── Area ratio (cathode-to-anode) ──
        area_ratio = float(np.clip(
            rng.lognormal(mean=0, sigma=1.5), 0.01, 1000
        ))
        area_ratio = round(area_ratio, 3)

        # ── Environment ──
        env = rng.choice(env_names)
        conductivity = environments[env]

        # ── Compatibility status from PDF matrix ──
        pair_groups = frozenset([anode["Group"], cathode["Group"]])

        if len(pair_groups) == 1:
            # Same group → always compatible
            pdf_status = "Compatible"
        elif pair_groups in explicit_pdf_rules:
            rule = explicit_pdf_rules[pair_groups]
            if env in rule:
                pdf_status = rule[env]
            else:
                # Rural environment: fallback heuristic
                pdf_status = "Unfavorable" if delta_v > 0.25 else "Compatible"
        else:
            # Should never happen with a complete matrix, but be safe
            pdf_status = "Unfavorable" if delta_v > 0.25 else "Compatible"

        # ── Physics-based galvanic current density (target variable) ──
        R_p_anode   = get_polarization_resistance(anode["Group"])
        R_p_cathode = get_polarization_resistance(cathode["Group"])
        R_p_total   = R_p_anode + R_p_cathode          # series combination
        R_electrolyte = 1.0 / (conductivity + 1e-5)

        I_galv_total = delta_v / (R_p_total + R_electrolyte)
        i_anode_density = I_galv_total * area_ratio     # A/m²

        # Add realistic measurement noise (±5 %)
        noise = rng.normal(0, 0.05 * abs(i_anode_density))
        i_anode_density = max(i_anode_density + noise, 0.0)

        data.append({
            "Anode_Alloy":                  anode["Material"],
            "Anode_Table1_Group":           anode["Group"],
            "Anode_Group_ID":               _group_id(groups_df, anode["Group"]),
            "Cathode_Alloy":                cathode["Material"],
            "Cathode_Table1_Group":         cathode["Group"],
            "Cathode_Group_ID":             _group_id(groups_df, cathode["Group"]),
            "Potential_Difference_V":       round(delta_v, 4),
            "Environment":                  env,
            "Electrolyte_Conductivity_Sm":  conductivity,
            "Cathode_Anode_Area_Ratio":     area_ratio,
            "R_p_Anode_Ohm_m2":            R_p_anode,
            "R_p_Cathode_Ohm_m2":          R_p_cathode,
            "Target_Galvanic_Current_Density": round(i_anode_density, 6),
            "PDF_Compatibility_Status":     pdf_status,
        })

    df_synthetic = pd.DataFrame(data)
    out_path = os.path.join(OUTPUT_DIR, "synthetic_galvanic_joints_full.csv")
    out_path = _safe_to_csv(df_synthetic, out_path, index=False)
    print(f"  → Generated {num_samples} synthetic joints → {out_path}")
    return df_synthetic


def _group_id(groups_df: pd.DataFrame, group_name: str) -> int:
    """Helper: look up Group_ID for a given category name."""
    match = groups_df.loc[groups_df["Category"] == group_name, "Group_ID"]
    return int(match.iloc[0]) if len(match) > 0 else -1


# ═══════════════════════════════════════════════════════════════════════════
# 7.  Main entry point
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("  Galvanic Corrosion PINN — Data Extraction & Synthetic Generation")
    print("=" * 70)

    # ── Step 1: Extract reference tables ──
    print("\n[1/4] Extracting EMF Series (Table 3)…")
    df_emf = extract_emf_series()

    print("\n[2/4] Extracting Material Groups (Table 1) — corrected ordering…")
    df_groups = extract_material_groups()

    print("\n[3/4] Extracting Galvanic Series (Table 2) — published SCE potentials…")
    df_galvanic = extract_galvanic_series()

    # ── Step 2: Verify compatibility rules ──
    print("\n[4/4] Building compatibility rules…")
    rules = generate_compatibility_rules(df_groups)
    n_compat = sum(1 for v in rules.values() if v["Marine (Seawater)"] == "Compatible")
    n_unfav  = sum(1 for v in rules.values() if v["Marine (Seawater)"] == "Unfavorable")
    print(f"  → 190 pair rules:  {n_compat} Compatible, {n_unfav} Unfavorable (Marine)")

    # ── Step 3: Generate synthetic dataset ──
    df_synth = generate_synthetic_data(df_galvanic, df_groups, num_samples=25000)

    # ── Summaries ──
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)

    print("\n── Material Groups (corrected order) ──")
    for _, row in df_groups.iterrows():
        print(f"  {row['Group_ID']:2d}. {row['Category']}")

    print(f"\n── Galvanic Series: {len(df_galvanic)} materials, "
          f"potential range [{df_galvanic['Potential_V_SCE'].min():.2f}, "
          f"{df_galvanic['Potential_V_SCE'].max():.2f}] V vs SCE")

    print(f"\n── EMF Series: {len(df_emf)} equilibria")

    print(f"\n── Synthetic Dataset: {len(df_synth)} rows")
    print(f"   Columns: {list(df_synth.columns)}")
    print(f"\n   Environment distribution:")
    print(df_synth["Environment"].value_counts().to_string(header=False))
    print(f"\n   Compatibility status distribution:")
    print(df_synth["PDF_Compatibility_Status"].value_counts().to_string(header=False))

    print("\n── Sample rows (first 5) ──")
    sample_cols = [
        "Anode_Alloy", "Cathode_Alloy", "Potential_Difference_V",
        "Environment", "Target_Galvanic_Current_Density",
        "PDF_Compatibility_Status",
    ]
    print(df_synth[sample_cols].head(5).to_string(index=False))

    print("\n✓ All files written successfully.")
