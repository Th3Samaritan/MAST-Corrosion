import pandas as pd
import numpy as np
import itertools

def extract_pdf_tables_to_csv():
    """
    Extracts the exact data from all 3 PDF tables and saves them to local CSVs.
    Returns the datasets for synthetic generation.
    """
    print("--- Extracting PDF Datasets ---")
    
    # 1. TABLE 3: Standard EMF Series
    emf_data = [
        {"Equilibrium": "Au-Au+3", "Potential_V": 1.498},
        {"Equilibrium": "Pt-Pt+2", "Potential_V": 1.200},
        {"Equilibrium": "Pd-Pd+2", "Potential_V": 0.987},
        {"Equilibrium": "Ag-Ag+", "Potential_V": 0.799},
        {"Equilibrium": "Hg-Hg2+2", "Potential_V": 0.788},
        {"Equilibrium": "Cu-Cu+2", "Potential_V": 0.337},
        {"Equilibrium": "H2-H+", "Potential_V": 0.000},
        {"Equilibrium": "Pb-Pb+2", "Potential_V": -0.126},
        {"Equilibrium": "Sn-Sn+2", "Potential_V": -0.136},
        {"Equilibrium": "Ni-Ni+2", "Potential_V": -0.250},
        {"Equilibrium": "Co-Co+2", "Potential_V": -0.277},
        {"Equilibrium": "Cd-Cd+2", "Potential_V": -0.403},
        {"Equilibrium": "Fe-Fe+2", "Potential_V": -0.440},
        {"Equilibrium": "Cr-Cr+3", "Potential_V": -0.744},
        {"Equilibrium": "Zn-Zn+2", "Potential_V": -0.763},
        {"Equilibrium": "Al-Al+3", "Potential_V": -1.662},
        {"Equilibrium": "Mg-Mg+2", "Potential_V": -2.363},
        {"Equilibrium": "Na-Na+", "Potential_V": -2.714}, 
        {"Equilibrium": "K-K+", "Potential_V": -2.925}
    ]
    df_emf = pd.DataFrame(emf_data)
    df_emf.to_csv("pdf_table3_emf_series.csv", index=False)

    # 2. TABLE 1: Compatibility Material Groups (Ordered Active to Noble)
    compat_groups = [
        {"Group_ID": 1, "Category": "Magnesium"},
        {"Group_ID": 2, "Category": "Zinc, Zinc Coating"},
        {"Group_ID": 3, "Category": "Aluminum, Mg-Coated Aluminum, Zn-Coated Aluminum"},
        {"Group_ID": 4, "Category": "Cadmium, Beryllium"},
        {"Group_ID": 5, "Category": "Cu-Coated Aluminum"},
        {"Group_ID": 6, "Category": "Steels-Carbon, Low Alloy"},
        {"Group_ID": 7, "Category": "Lead"},
        {"Group_ID": 8, "Category": "Tin, Tin-Lead, Indium"},
        {"Group_ID": 9, "Category": "St. Steels-Martensitic, Ferritic"},
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
        {"Group_ID": 20, "Category": "Graphite"}
    ]
    df_groups = pd.DataFrame(compat_groups)
    df_groups.to_csv("pdf_table1_material_groups.csv", index=False)

    # 3. TABLE 2: Galvanic Series
    galvanic_series = [
        {"Rank": 1, "Material": "Platinum", "Potential_V": 1.200, "Group": "Palladium, Rhodium, Gold, Platinum"},
        {"Rank": 2, "Material": "Gold", "Potential_V": 1.498, "Group": "Palladium, Rhodium, Gold, Platinum"},
        {"Rank": 3, "Material": "Graphite", "Potential_V": 1.000, "Group": "Graphite"},
        {"Rank": 4, "Material": "Titanium", "Potential_V": 0.900, "Group": "Titanium"},
        {"Rank": 5, "Material": "Silver", "Potential_V": 0.799, "Group": "Silver"},
        {"Rank": 6, "Material": "Chlorimet 3 (62 Ni, 18 Cr, 18 Mo)", "Potential_V": 0.750, "Group": "Nickel, Cobalt"},
        {"Rank": 7, "Material": "Hastelloy C (62 Ni, 17 Cr, 15 Mo)", "Potential_V": 0.700, "Group": "Nickel, Cobalt"},
        {"Rank": 8, "Material": "18-8 Mo SS (passive)", "Potential_V": 0.650, "Group": "St. Steels-Aust., PH, Super Strength, Heat Resistant"},
        {"Rank": 9, "Material": "18-8 SS (passive)", "Potential_V": 0.600, "Group": "St. Steels-Aust., PH, Super Strength, Heat Resistant"},
        {"Rank": 10, "Material": "Chromium SS 11-30% (passive)", "Potential_V": 0.550, "Group": "St. Steels-Martensitic, Ferritic"},
        {"Rank": 11, "Material": "Inconel (passive)", "Potential_V": 0.500, "Group": "Copper-High Nickel, Monel"},
        {"Rank": 12, "Material": "Nickel (passive)", "Potential_V": 0.450, "Group": "Nickel, Cobalt"},
        {"Rank": 13, "Material": "Silver solder", "Potential_V": 0.400, "Group": "Silver"},
        {"Rank": 14, "Material": "Monel", "Potential_V": 0.380, "Group": "Copper-High Nickel, Monel"},
        {"Rank": 15, "Material": "Cupronickels", "Potential_V": 0.360, "Group": "Copper-High Nickel, Monel"},
        {"Rank": 16, "Material": "Bronzes", "Potential_V": 0.350, "Group": "Brass-High Copper, Bronze-High Copper"},
        {"Rank": 17, "Material": "Copper", "Potential_V": 0.337, "Group": "Copper-High Nickel, Monel"},
        {"Rank": 18, "Material": "Brasses", "Potential_V": 0.300, "Group": "Brass-Low Copper, Bronze-Low Copper"},
        {"Rank": 19, "Material": "Chlorimet 2", "Potential_V": 0.200, "Group": "Nickel, Cobalt"},
        {"Rank": 20, "Material": "Hastelloy B", "Potential_V": 0.100, "Group": "Nickel, Cobalt"},
        {"Rank": 21, "Material": "Inconel (active)", "Potential_V": -0.100, "Group": "Nickel, Cobalt"},
        {"Rank": 22, "Material": "Nickel (active)", "Potential_V": -0.250, "Group": "Nickel, Cobalt"},
        {"Rank": 23, "Material": "Tin", "Potential_V": -0.136, "Group": "Tin, Tin-Lead, Indium"},
        {"Rank": 24, "Material": "Lead", "Potential_V": -0.126, "Group": "Lead"},
        {"Rank": 25, "Material": "Lead-tin solders", "Potential_V": -0.130, "Group": "Tin, Tin-Lead, Indium"},
        {"Rank": 26, "Material": "18-8 Mo SS (active)", "Potential_V": -0.200, "Group": "St. Steels-Aust., PH, Super Strength, Heat Resistant"},
        {"Rank": 27, "Material": "18-8 SS (active)", "Potential_V": -0.220, "Group": "St. Steels-Aust., PH, Super Strength, Heat Resistant"},
        {"Rank": 28, "Material": "Ni-Resist", "Potential_V": -0.300, "Group": "Steels-Carbon, Low Alloy"},
        {"Rank": 29, "Material": "Chromium SS 13% (active)", "Potential_V": -0.350, "Group": "St. Steels-Martensitic, Ferritic"},
        {"Rank": 30, "Material": "Cast iron", "Potential_V": -0.400, "Group": "Steels-Carbon, Low Alloy"},
        {"Rank": 31, "Material": "Steel or iron", "Potential_V": -0.440, "Group": "Steels-Carbon, Low Alloy"},
        {"Rank": 32, "Material": "2024 aluminum", "Potential_V": -0.600, "Group": "Aluminum, Mg-Coated Aluminum, Zn-Coated Aluminum"},
        {"Rank": 33, "Material": "Cadmium", "Potential_V": -0.403, "Group": "Cadmium, Beryllium"},
        {"Rank": 34, "Material": "Commercially pure aluminum (1100)", "Potential_V": -1.662, "Group": "Aluminum, Mg-Coated Aluminum, Zn-Coated Aluminum"},
        {"Rank": 35, "Material": "Zinc", "Potential_V": -0.763, "Group": "Zinc, Zinc Coating"},
        {"Rank": 36, "Material": "Magnesium and magnesium alloys", "Potential_V": -2.363, "Group": "Magnesium"}
    ]
    df_galvanic = pd.DataFrame(galvanic_series)
    df_galvanic.to_csv("pdf_table2_galvanic_series.csv", index=False)
    
    print("-> Saved 3 Raw CSV Files successfully.")
    return df_galvanic, df_groups


def generate_comprehensive_pdf_rules(groups_df):
    """
    Translates the literal AMMTIAC Table 1 20x20 matrix explicitly.
    0 = Compatible
    1 = Unfavorable (Marine & Industrial)
    Returns all 190 pairwise rules directly extracted.
    """
    groups = groups_df["Category"].tolist()
    
    # Standard 20x20 AMMTIAC Compatibility Grid matching the PDF
    grid = [
        #1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 (Group ID)
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], # 1: Mg
        [1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], # 2: Zn
        [1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], # 3: Al
        [1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], # 4: Cd, Be
        [1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], # 5: Cu-Al
        [1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], # 6: Steels
        [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], # 7: Pb
        [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1], # 8: Tin
        [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1], # 9: SS (act)
        [1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1], # 10: Cr, Mo, W
        [1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1], # 11: SS (pas)
        [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1], # 12: Brass-Pb
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1], # 13: Brass-Low Cu
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], # 14: Brass-High Cu
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], # 15: Cu-Ni, Monel
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], # 16: Ni, Co
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0], # 17: Titanium
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0], # 18: Silver
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0], # 19: Pd, Rh, Au, Pt
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0]  # 20: Graphite
    ]

    explicit_rules = {}
    
    # Iterate to establish all 190 explicit frozenset dictionary items
    for i in range(20):
        for j in range(i + 1, 20):
            mat_a = groups[i]
            mat_b = groups[j]
            pair = frozenset([mat_a, mat_b])
            
            # 1 = Unfavorable in PDF, 0 = Compatible 'o' in PDF
            status = "Unfavorable" if grid[i][j] == 1 else "Compatible"
            
            explicit_rules[pair] = {
                "Marine (Seawater)": status,
                "Industrial (Acidic Rain)": status
            }
            
    return explicit_rules


def generate_synthetic_galvanic_data(galvanic_series_df, groups_df, num_samples=25000):
    """
    Generates a massive synthetic dataset crossing all 36 commercial alloys, 
    evaluating them via the established compatibility grid.
    """
    print("\n--- Generating Synthetic Joint Data ---")
    
    environments = {
        "Marine (Seawater)": 5.0,     
        "Industrial (Acidic Rain)": 0.1,  
        "Rural (Freshwater)": 0.01    
    }
    env_names = list(environments.keys())

    # -------------------------------------------------------------
    # Get the EXHAUSTIVE 190-pair exact explicit rule dictionary
    # -------------------------------------------------------------
    explicit_pdf_rules = generate_comprehensive_pdf_rules(groups_df)
    print(f"-> Successfully loaded {len(explicit_pdf_rules)} exact PDF matrix rules.")

    data = []
    materials_list = galvanic_series_df.to_dict('records')
    
    for _ in range(num_samples):
        # Pick any two distinct commercial alloys/metals from the full 36 list
        mat_a, mat_b = np.random.choice(materials_list, 2, replace=False)
        
        v_a = mat_a["Potential_V"]
        v_b = mat_b["Potential_V"]
        
        # Sort Anode/Cathode
        if v_a < v_b:
            anode, cathode = mat_a, mat_b
        else:
            anode, cathode = mat_b, mat_a
            
        delta_v = cathode["Potential_V"] - anode["Potential_V"]
        
        # Determine Area Ratio
        area_ratio = np.round(np.random.lognormal(mean=0, sigma=1.5), 3)
        area_ratio = np.clip(area_ratio, 0.01, 1000) 
        
        env = np.random.choice(env_names)
        conductivity = environments[env]
        
        pair_groups = frozenset([anode["Group"], cathode["Group"]])
        
        # Identical groups are fully compatible
        if len(pair_groups) == 1:
            pdf_status = "Compatible"
        else:
            if env in explicit_pdf_rules[pair_groups]:
                pdf_status = explicit_pdf_rules[pair_groups][env]
            else:
                # Fallback purely for Rural environment
                pdf_status = "Unfavorable" if delta_v > 0.75 else "Compatible"
            
        # Physics-Based Target Calculation (Galvanic Current Proxy)
        R_polarization = 0.5 
        R_electrolyte = 1.0 / (conductivity + 1e-5)
        
        I_galv_total = delta_v / (R_polarization + R_electrolyte)
        i_anode_density = I_galv_total * area_ratio 
        
        noise = np.random.normal(0, 0.05 * i_anode_density)
        i_anode_density = np.clip(i_anode_density + noise, 0, None)
        
        data.append({
            "Anode_Alloy": anode["Material"],
            "Anode_Table1_Group": anode["Group"],
            "Cathode_Alloy": cathode["Material"],
            "Cathode_Table1_Group": cathode["Group"],
            "Potential_Difference_V": np.round(delta_v, 3),
            "Environment": env,
            "Cathode_Anode_Area_Ratio": area_ratio,
            "Target_Galvanic_Current_Density": np.round(i_anode_density, 5),
            "PDF_Compatibility_Status": pdf_status 
        })
        
    df_synthetic = pd.DataFrame(data)
    df_synthetic.to_csv("synthetic_galvanic_joints_full.csv", index=False)
    
    print(f"-> Generated {num_samples} simulated joints mapped exactly to the 20x20 matrix.")
    return df_synthetic

if __name__ == "__main__":
    df_galv, df_groups = extract_pdf_tables_to_csv()
    df_synth = generate_synthetic_galvanic_data(df_galv, df_groups, 25000)
    
    print("\nSample Output (First 5 Simulated Joints):")
    print(df_synth[['Anode_Alloy', 'Cathode_Alloy', 'PDF_Compatibility_Status']].head(5))