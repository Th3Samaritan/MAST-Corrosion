"""
streamlit_app.py
================
Professional Streamlit dashboard for the Galvanic Corrosion PINN model.

Launch with:
    streamlit run streamlit_app.py
"""

import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ---------------------------------------------------------------------------
# Page config (MUST be first Streamlit call)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="MAST Galvanic Corrosion PINN",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

st.markdown("""
<style>
    /* ---------- Google Fonts ---------- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* ---------- Root Variables ---------- */
    :root {
        --bg-primary: #0a0e1a;
        --bg-secondary: #111827;
        --bg-card: rgba(17, 24, 39, 0.7);
        --bg-glass: rgba(30, 41, 59, 0.5);
        --border-glass: rgba(100, 160, 255, 0.15);
        --accent-blue: #3b82f6;
        --accent-cyan: #06b6d4;
        --accent-teal: #14b8a6;
        --accent-green: #10b981;
        --accent-red: #ef4444;
        --accent-amber: #f59e0b;
        --accent-purple: #8b5cf6;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --gradient-primary: linear-gradient(135deg, #3b82f6, #06b6d4, #14b8a6);
        --gradient-card: linear-gradient(145deg, rgba(30,41,59,0.6), rgba(17,24,39,0.8));
        --shadow-glow: 0 0 30px rgba(59, 130, 246, 0.1);
    }

    /* ---------- Global Overrides ---------- */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* Main content area */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    /* ---------- Sidebar Styling ---------- */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%) !important;
        border-right: 1px solid rgba(59, 130, 246, 0.2);
    }

    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li {
        color: #cbd5e1;
    }

    /* ---------- Tab Styling ---------- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: rgba(15, 23, 42, 0.6);
        border-radius: 12px;
        padding: 4px;
        border: 1px solid rgba(59, 130, 246, 0.15);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 24px;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        font-size: 0.9rem;
        color: #94a3b8;
        background: transparent;
        border: none;
        transition: all 0.3s ease;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(59,130,246,0.2), rgba(6,182,212,0.2)) !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.1);
    }

    /* ---------- Metric Cards ---------- */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(30,41,59,0.6), rgba(17,24,39,0.8));
        border: 1px solid rgba(100, 160, 255, 0.12);
        border-radius: 16px;
        padding: 20px 24px;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        box-shadow: 0 4px 24px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.05);
        transition: all 0.3s ease;
    }

    div[data-testid="stMetric"]:hover {
        border-color: rgba(59, 130, 246, 0.3);
        box-shadow: 0 8px 32px rgba(59, 130, 246, 0.15), inset 0 1px 0 rgba(255,255,255,0.08);
        transform: translateY(-2px);
    }

    div[data-testid="stMetric"] label {
        color: #94a3b8 !important;
        font-weight: 500;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #f1f5f9 !important;
        font-weight: 700;
        font-size: 1.8rem;
    }

    /* ---------- Select boxes & inputs ---------- */
    .stSelectbox [data-baseweb="select"] > div {
        background: rgba(30, 41, 59, 0.6) !important;
        border: 1px solid rgba(100, 160, 255, 0.15) !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
        backdrop-filter: blur(8px);
        transition: all 0.3s ease;
    }

    .stSelectbox [data-baseweb="select"] > div:hover {
        border-color: rgba(59, 130, 246, 0.4) !important;
    }

    .stSelectbox [data-baseweb="select"] > div:focus-within {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
    }

    /* ---------- Slider ---------- */
    .stSlider [data-baseweb="slider"] [role="slider"] {
        background: linear-gradient(135deg, #3b82f6, #06b6d4) !important;
        border: 2px solid rgba(255,255,255,0.2) !important;
        width: 20px !important;
        height: 20px !important;
    }

    /* ---------- Buttons ---------- */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6, #06b6d4) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px 28px !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        letter-spacing: 0.02em;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3) !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(59, 130, 246, 0.4) !important;
    }

    /* ---------- Expander ---------- */
    .streamlit-expanderHeader {
        background: rgba(30, 41, 59, 0.5) !important;
        border-radius: 10px !important;
        border: 1px solid rgba(100, 160, 255, 0.1) !important;
    }

    /* ---------- DataFrame styling ---------- */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }

    /* ---------- Radio buttons ---------- */
    .stRadio > div {
        gap: 12px;
    }

    .stRadio [data-baseweb="radio"] {
        background: rgba(30, 41, 59, 0.4);
        border-radius: 8px;
        padding: 4px 8px;
        border: 1px solid transparent;
        transition: all 0.2s ease;
    }

    /* ---------- Download button ---------- */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #10b981, #14b8a6) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 16px rgba(16, 185, 129, 0.3) !important;
    }

    /* ---------- Divider ---------- */
    hr {
        border-color: rgba(100, 160, 255, 0.1) !important;
        margin: 1.5rem 0;
    }

    /* ---------- Header gradient text ---------- */
    .gradient-text {
        background: linear-gradient(135deg, #3b82f6, #06b6d4, #14b8a6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800;
    }

    .glass-card {
        background: linear-gradient(145deg, rgba(30,41,59,0.5), rgba(17,24,39,0.7));
        border: 1px solid rgba(100, 160, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        box-shadow: 0 4px 24px rgba(0,0,0,0.15);
        margin-bottom: 16px;
    }

    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.03em;
    }

    .status-online {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }

    .status-offline {
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }

    .verdict-compatible {
        background: linear-gradient(135deg, rgba(16,185,129,0.15), rgba(20,184,166,0.1));
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
    }

    .verdict-unfavorable {
        background: linear-gradient(135deg, rgba(239,68,68,0.15), rgba(245,158,11,0.1));
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
    }

    .verdict-title {
        font-size: 2rem;
        font-weight: 800;
        margin-bottom: 4px;
    }

    .verdict-subtitle {
        font-size: 0.95rem;
        color: #94a3b8;
    }

    .info-row {
        display: flex;
        justify-content: space-between;
        padding: 12px 0;
        border-bottom: 1px solid rgba(100, 160, 255, 0.08);
    }

    .info-label {
        color: #94a3b8;
        font-size: 0.9rem;
    }

    .info-value {
        color: #e2e8f0;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }

    .hero-section {
        text-align: center;
        padding: 20px 0 30px 0;
    }

    .hero-title {
        font-size: 2.8rem;
        font-weight: 900;
        background: linear-gradient(135deg, #3b82f6, #06b6d4, #14b8a6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 8px;
        line-height: 1.1;
    }

    .hero-subtitle {
        font-size: 1.1rem;
        color: #64748b;
        font-weight: 400;
        max-width: 600px;
        margin: 0 auto;
    }

    /* Animate metric values */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    div[data-testid="stMetric"] {
        animation: fadeInUp 0.5s ease forwards;
    }

    /* Pulsing dot for status */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    .pulse-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
        animation: pulse 2s infinite;
    }

    .pulse-dot-green { background: #34d399; box-shadow: 0 0 8px rgba(52,211,153,0.6); }
    .pulse-dot-red { background: #f87171; box-shadow: 0 0 8px rgba(248,113,113,0.6); }

    /* Compact gauge label */
    .gauge-label {
        text-align: center;
        font-size: 0.8rem;
        color: #64748b;
        margin-top: -8px;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Load model and data (cached)
# ---------------------------------------------------------------------------

@st.cache_resource
def init_model():
    """Load model and galvanic data once."""
    from streamlit_utils import load_model, load_galvanic_data
    try:
        model, checkpoint, device = load_model()
        lookup, materials, galv_df = load_galvanic_data()
        return {
            "model": model,
            "checkpoint": checkpoint,
            "device": device,
            "lookup": lookup,
            "materials": materials,
            "galv_df": galv_df,
            "status": "online",
            "error": None,
        }
    except Exception as e:
        return {
            "model": None,
            "checkpoint": None,
            "device": None,
            "lookup": None,
            "materials": None,
            "galv_df": None,
            "status": "offline",
            "error": str(e),
        }


@st.cache_data
def get_training_logs():
    """Load training logs once."""
    from streamlit_utils import load_all_training_logs
    try:
        log1, log2, log3 = load_all_training_logs()
        return log1, log2, log3
    except Exception:
        return None, None, None


# ---------------------------------------------------------------------------
# Plotly theme
# ---------------------------------------------------------------------------

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#94a3b8", size=12),
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis=dict(
        gridcolor="rgba(100,160,255,0.06)",
        zerolinecolor="rgba(100,160,255,0.1)",
    ),
    yaxis=dict(
        gridcolor="rgba(100,160,255,0.06)",
        zerolinecolor="rgba(100,160,255,0.1)",
    ),
    legend=dict(
        bgcolor="rgba(15,23,42,0.8)",
        bordercolor="rgba(100,160,255,0.15)",
        borderwidth=1,
        font=dict(size=11),
    ),
)

COLORS = {
    "blue": "#3b82f6",
    "cyan": "#06b6d4",
    "teal": "#14b8a6",
    "green": "#10b981",
    "red": "#ef4444",
    "amber": "#f59e0b",
    "purple": "#8b5cf6",
    "pink": "#ec4899",
    "slate": "#64748b",
}


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar(state):
    with st.sidebar:
        # Logo / Branding
        st.markdown("""
        <div style="text-align:center; padding: 16px 0 8px 0;">
            <div style="font-size: 2.5rem; margin-bottom: 4px;">⚡</div>
            <div style="font-size: 1.2rem; font-weight: 800; background: linear-gradient(135deg, #3b82f6, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">MAST PINN</div>
            <div style="font-size: 0.75rem; color: #64748b; letter-spacing: 0.1em; text-transform: uppercase;">Galvanic Corrosion Engine</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Model Status
        st.markdown("##### 🔌 Model Status")
        if state["status"] == "online":
            st.markdown("""
            <div class="status-badge status-online">
                <span class="pulse-dot pulse-dot-green"></span>
                Model Online
            </div>
            """, unsafe_allow_html=True)

            ckpt = state["checkpoint"]
            epoch = ckpt.get("epoch", "N/A")
            val_loss = ckpt.get("val_loss", 0)
            args = ckpt.get("args", {})
            st.markdown(f"""
            <div class="glass-card" style="padding:14px 18px; margin-top:12px; font-size:0.82rem;">
                <div class="info-row" style="padding:6px 0;">
                    <span class="info-label">Checkpoint</span>
                    <span class="info-value">Epoch {epoch}</span>
                </div>
                <div class="info-row" style="padding:6px 0;">
                    <span class="info-label">Val Loss</span>
                    <span class="info-value">{val_loss:.6f}</span>
                </div>
                <div class="info-row" style="padding:6px 0;">
                    <span class="info-label">Hidden Dim</span>
                    <span class="info-value">{args.get('hidden_dim', 64)}</span>
                </div>
                <div class="info-row" style="padding:6px 0;">
                    <span class="info-label">MP Layers</span>
                    <span class="info-value">{args.get('num_mp_layers', 3)}</span>
                </div>
                <div class="info-row" style="padding:6px 0; border-bottom:none;">
                    <span class="info-label">Parameters</span>
                    <span class="info-value">{sum(p.numel() for p in state['model'].parameters()):,}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="status-badge status-offline">
                <span class="pulse-dot pulse-dot-red"></span>
                Model Offline
            </div>
            """, unsafe_allow_html=True)
            if state.get("error"):
                st.error(f"Error: {state['error']}")

        st.markdown("---")

        # Info
        st.markdown("##### ℹ️ About")
        st.markdown("""
        <div style="font-size:0.8rem; color:#64748b; line-height:1.6;">
            Physics-Informed Graph Neural Network for predicting galvanic corrosion
            in multi-material assemblies. Uses NNConv message passing with KCL and
            thermodynamic constraints.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("""
        <div style="text-align:center; font-size:0.7rem; color:#475569;">
            Built with Streamlit & PyTorch Geometric<br/>
            © 2026 MAST Consolidate
        </div>
        """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Page: Prediction Engine
# ---------------------------------------------------------------------------

def render_prediction_page(state):
    from streamlit_utils import predict_single

    st.markdown("""
    <div class="hero-section">
        <div class="hero-title">🔬 Prediction Engine</div>
        <div class="hero-subtitle">Predict galvanic corrosion current density and material compatibility for any bimetallic joint configuration</div>
    </div>
    """, unsafe_allow_html=True)

    if state["status"] != "online":
        st.error("⚠️ Model is not loaded. Cannot make predictions.")
        return

    model = state["model"]
    lookup = state["lookup"]
    materials = state["materials"]
    device = state["device"]

    # --- Input Form ---
    col_left, col_spacer, col_right = st.columns([5, 0.5, 5])

    with col_left:
        st.markdown("""
        <div class="glass-card">
            <div style="font-size:1rem; font-weight:700; color:#e2e8f0; margin-bottom:16px;">
                🔧 Material Selection
            </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        anode_material = st.selectbox(
            "⚡ Anode Material (corroding)",
            materials,
            index=len(materials) - 2,  # Zinc by default
            help="The anodic material that will preferentially corrode",
        )

        cathode_material = st.selectbox(
            "🛡️ Cathode Material (protected)",
            materials,
            index=0,  # Platinum by default
            help="The cathodic material that is protected from corrosion",
        )

        # Show potential info
        anode_info = lookup.get(anode_material, {})
        cathode_info = lookup.get(cathode_material, {})
        pot_diff = abs(
            cathode_info.get("potential_sce", 0) - anode_info.get("potential_sce", 0)
        )

        st.markdown(f"""
        <div class="glass-card" style="padding:14px 18px;">
            <div class="info-row" style="padding:6px 0;">
                <span class="info-label">Anode Potential (SCE)</span>
                <span class="info-value" style="color:#ef4444;">{anode_info.get('potential_sce', 0):.2f} V</span>
            </div>
            <div class="info-row" style="padding:6px 0;">
                <span class="info-label">Cathode Potential (SCE)</span>
                <span class="info-value" style="color:#10b981;">{cathode_info.get('potential_sce', 0):.2f} V</span>
            </div>
            <div class="info-row" style="padding:6px 0; border-bottom:none;">
                <span class="info-label">ΔV (Driving Force)</span>
                <span class="info-value" style="color:#3b82f6;">{pot_diff:.2f} V</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown("""
        <div class="glass-card">
            <div style="font-size:1rem; font-weight:700; color:#e2e8f0; margin-bottom:16px;">
                🌍 Environment & Geometry
            </div>
        </div>
        """, unsafe_allow_html=True)

        environment = st.radio(
            "Environment",
            ["Marine (Seawater)", "Industrial (Acidic Rain)", "Rural (Freshwater)"],
            horizontal=True,
        )

        from streamlit_utils import ENVIRONMENT_CONDUCTIVITY
        cond = ENVIRONMENT_CONDUCTIVITY.get(environment, 0.01)
        env_emoji = {"Marine (Seawater)": "🌊", "Industrial (Acidic Rain)": "🏭", "Rural (Freshwater)": "🏞️"}
        st.markdown(f"""
        <div class="glass-card" style="padding:10px 18px; margin-top: -8px;">
            <span class="info-label">{env_emoji.get(environment, '')} Electrolyte conductivity:</span>
            <span class="info-value" style="margin-left:8px;">{cond} S/m</span>
        </div>
        """, unsafe_allow_html=True)

        area_ratio = st.slider(
            "Cathode/Anode Area Ratio",
            min_value=0.01,
            max_value=50.0,
            value=1.0,
            step=0.01,
            format="%.2f",
            help="Ratio of cathode surface area to anode surface area. Higher ratios increase corrosion.",
        )

        # Area ratio gauge
        ratio_color = "#10b981" if area_ratio < 1 else ("#f59e0b" if area_ratio < 10 else "#ef4444")
        ratio_label = "Low risk" if area_ratio < 1 else ("Moderate" if area_ratio < 10 else "High risk")
        st.markdown(f"""
        <div class="glass-card" style="padding:12px 18px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="info-label">Area Ratio Risk</span>
                <span style="color:{ratio_color}; font-weight:700; font-size:0.9rem;">{ratio_label}</span>
            </div>
            <div style="margin-top:8px; height:6px; background:rgba(100,160,255,0.08); border-radius:3px; overflow:hidden;">
                <div style="height:100%; width:{min(area_ratio / 50 * 100, 100):.0f}%; background:linear-gradient(90deg, #10b981, #f59e0b, #ef4444); border-radius:3px; transition: width 0.5s ease;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- Predict Button ---
    st.markdown("<br/>", unsafe_allow_html=True)
    col_btn_l, col_btn_c, col_btn_r = st.columns([3, 4, 3])
    with col_btn_c:
        predict_clicked = st.button("⚡  Run Prediction", use_container_width=True, type="primary")

    if predict_clicked or st.session_state.get("last_prediction"):
        if predict_clicked:
            result = predict_single(
                model, anode_material, cathode_material,
                environment, area_ratio, lookup, device,
            )
            st.session_state["last_prediction"] = result
            st.session_state["last_inputs"] = {
                "anode": anode_material, "cathode": cathode_material,
                "env": environment, "area_ratio": area_ratio,
            }
        else:
            result = st.session_state["last_prediction"]

        st.markdown("<br/>", unsafe_allow_html=True)

        # --- Results ---
        # Verdict banner
        is_compat = result["compatibility_label"] == "Compatible"
        verdict_class = "verdict-compatible" if is_compat else "verdict-unfavorable"
        verdict_icon = "✅" if is_compat else "⚠️"
        verdict_text = "COMPATIBLE" if is_compat else "UNFAVORABLE"
        verdict_color = "#34d399" if is_compat else "#f87171"
        confidence = (1 - result["compatibility_prob"]) if is_compat else result["compatibility_prob"]

        st.markdown(f"""
        <div class="{verdict_class}">
            <div class="verdict-title" style="color:{verdict_color};">
                {verdict_icon} {verdict_text}
            </div>
            <div class="verdict-subtitle">
                Confidence: {confidence * 100:.1f}% &nbsp;|&nbsp; Logit: {result['raw_compat_logit']:.4f}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)

        # Metric cards
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric(
                "Current Density",
                f"{result['current_density']:.6f}",
                "A/m²",
            )
        with m2:
            st.metric(
                "Anode Potential",
                f"{result['v_anode']:.4f}",
                "V (predicted)",
            )
        with m3:
            st.metric(
                "Cathode Potential",
                f"{result['v_cathode']:.4f}",
                "V (predicted)",
            )
        with m4:
            st.metric(
                "Potential Gradient",
                f"{result['delta_v']:.4f}",
                "ΔV",
            )

        # Physics gauge
        st.markdown("<br/>", unsafe_allow_html=True)

        with st.expander("🔍 Detailed Physics Breakdown", expanded=False):
            phys_col1, phys_col2 = st.columns(2)
            with phys_col1:
                st.markdown(f"""
                <div class="glass-card" style="padding:16px 20px;">
                    <div style="font-weight:600; color:#e2e8f0; margin-bottom:12px;">📊 Prediction Details</div>
                    <div class="info-row">
                        <span class="info-label">Raw Current (edge 0)</span>
                        <span class="info-value">{result['current_density']:.8f}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Compatibility Logit</span>
                        <span class="info-value">{result['raw_compat_logit']:.6f}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Compatibility Prob</span>
                        <span class="info-value">{result['compatibility_prob']:.6f}</span>
                    </div>
                    <div class="info-row" style="border-bottom:none;">
                        <span class="info-label">ΔV (predicted nodes)</span>
                        <span class="info-value">{result['delta_v']:.6f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with phys_col2:
                inputs = st.session_state.get("last_inputs", {})
                st.markdown(f"""
                <div class="glass-card" style="padding:16px 20px;">
                    <div style="font-weight:600; color:#e2e8f0; margin-bottom:12px;">⚙️ Input Parameters</div>
                    <div class="info-row">
                        <span class="info-label">Anode</span>
                        <span class="info-value" style="font-size:0.75rem;">{inputs.get('anode', 'N/A')}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Cathode</span>
                        <span class="info-value" style="font-size:0.75rem;">{inputs.get('cathode', 'N/A')}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Environment</span>
                        <span class="info-value" style="font-size:0.75rem;">{inputs.get('env', 'N/A')}</span>
                    </div>
                    <div class="info-row" style="border-bottom:none;">
                        <span class="info-label">Area Ratio</span>
                        <span class="info-value">{inputs.get('area_ratio', 'N/A')}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Page: Training Analytics
# ---------------------------------------------------------------------------

def render_training_page(state):
    st.markdown("""
    <div class="hero-section">
        <div class="hero-title">📊 Training Analytics</div>
        <div class="hero-subtitle">Explore training curves, loss decomposition, and model performance across 200 epochs for all 3 training runs</div>
    </div>
    """, unsafe_allow_html=True)

    log1, log2, log3 = get_training_logs()
    if log1 is None:
        st.warning("Training logs not found.")
        return

    # Model selector
    show_comparison = st.toggle("Compare all training runs", value=False)

    st.markdown("---")

    # --- Loss Curves ---
    st.markdown("#### 📉 Loss Curves")

    fig_loss = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Total Loss", "Component Losses"),
        horizontal_spacing=0.08,
    )

    # Total loss
    fig_loss.add_trace(go.Scatter(
        x=log1["epoch"], y=log1["train_total"],
        name="Train Total (Run 1)", line=dict(color=COLORS["blue"], width=2),
        opacity=0.8,
    ), row=1, col=1)
    fig_loss.add_trace(go.Scatter(
        x=log1["epoch"], y=log1["val_total"],
        name="Val Total (Run 1)", line=dict(color=COLORS["cyan"], width=2, dash="dot"),
    ), row=1, col=1)

    if show_comparison:
        fig_loss.add_trace(go.Scatter(
            x=log2["epoch"], y=log2["train_total"],
            name="Train Total (Run 2)", line=dict(color=COLORS["amber"], width=2),
            opacity=0.6,
        ), row=1, col=1)
        fig_loss.add_trace(go.Scatter(
            x=log2["epoch"], y=log2["val_total"],
            name="Val Total (Run 2)", line=dict(color=COLORS["red"], width=2, dash="dot"),
            opacity=0.6,
        ), row=1, col=1)
        fig_loss.add_trace(go.Scatter(
            x=log3["epoch"], y=log3["train_total"],
            name="Train Total (Run 3)", line=dict(color=COLORS["green"], width=2),
            opacity=0.6,
        ), row=1, col=1)
        fig_loss.add_trace(go.Scatter(
            x=log3["epoch"], y=log3["val_total"],
            name="Val Total (Run 3)", line=dict(color=COLORS["purple"], width=2, dash="dot"),
            opacity=0.6,
        ), row=1, col=1)

    # Component losses
    components = [
        ("val_data", "Data MSE", COLORS["blue"]),
        ("val_cls", "Classification BCE", COLORS["purple"]),
        ("val_kcl", "KCL Penalty", COLORS["amber"]),
        ("val_thermo", "Thermo Penalty", COLORS["teal"]),
    ]
    for col_name, label, color in components:
        fig_loss.add_trace(go.Scatter(
            x=log1["epoch"], y=log1[col_name],
            name=label, line=dict(color=color, width=2),
        ), row=1, col=2)

    layout_no_legend = {k: v for k, v in PLOTLY_LAYOUT.items() if k != "legend"}
    fig_loss.update_layout(
        **layout_no_legend,
        height=420,
        title_text="",
        showlegend=True,
        legend=dict(
            **PLOTLY_LAYOUT["legend"],
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
        ),
    )
    fig_loss.update_xaxes(title_text="Epoch", **PLOTLY_LAYOUT["xaxis"])
    fig_loss.update_yaxes(title_text="Loss", **PLOTLY_LAYOUT["yaxis"])
    fig_loss.update_annotations(font_size=14, font_color="#94a3b8")

    st.plotly_chart(fig_loss, use_container_width=True)

    # --- Metrics ---
    st.markdown("#### 🎯 Performance Metrics")

    fig_metrics = make_subplots(
        rows=1, cols=3,
        subplot_titles=("MAE & RMSE", "Accuracy", "F1 Score"),
        horizontal_spacing=0.06,
    )

    fig_metrics.add_trace(go.Scatter(
        x=log1["epoch"], y=log1["val_mae"],
        name="MAE", line=dict(color=COLORS["cyan"], width=2),
    ), row=1, col=1)
    fig_metrics.add_trace(go.Scatter(
        x=log1["epoch"], y=log1["val_rmse"],
        name="RMSE", line=dict(color=COLORS["blue"], width=2, dash="dash"),
    ), row=1, col=1)
    fig_metrics.add_trace(go.Scatter(
        x=log1["epoch"], y=log1["val_accuracy"],
        name="Accuracy", line=dict(color=COLORS["green"], width=2),
        fill="tozeroy", fillcolor="rgba(16,185,129,0.08)",
    ), row=1, col=2)
    fig_metrics.add_trace(go.Scatter(
        x=log1["epoch"], y=log1["val_f1"],
        name="F1 Score", line=dict(color=COLORS["purple"], width=2),
        fill="tozeroy", fillcolor="rgba(139,92,246,0.08)",
    ), row=1, col=3)

    layout_no_legend = {k: v for k, v in PLOTLY_LAYOUT.items() if k != "legend"}
    fig_metrics.update_layout(
        **layout_no_legend,
        height=380,
        showlegend=True,
        legend=dict(
            **PLOTLY_LAYOUT["legend"],
            orientation="h",
            yanchor="bottom", y=-0.25,
            xanchor="center", x=0.5,
        ),
    )
    fig_metrics.update_xaxes(title_text="Epoch", **PLOTLY_LAYOUT["xaxis"])
    fig_metrics.update_yaxes(**PLOTLY_LAYOUT["yaxis"])
    fig_metrics.update_annotations(font_size=14, font_color="#94a3b8")

    st.plotly_chart(fig_metrics, use_container_width=True)

    # --- Learning Rate ---
    st.markdown("#### 📈 Learning Rate Schedule")
    fig_lr = go.Figure()
    fig_lr.add_trace(go.Scatter(
        x=log1["epoch"], y=log1["lr"],
        name="Learning Rate (Run 1)",
        line=dict(color=COLORS["amber"], width=2),
        fill="tozeroy", fillcolor="rgba(245,158,11,0.06)",
    ))
    if show_comparison:
        fig_lr.add_trace(go.Scatter(
            x=log2["epoch"], y=log2["lr"],
            name="Learning Rate (Run 2)",
            line=dict(color=COLORS["red"], width=2, dash="dash"),
        ))
        fig_lr.add_trace(go.Scatter(
            x=log3["epoch"], y=log3["lr"],
            name="Learning Rate (Run 3)",
            line=dict(color=COLORS["purple"], width=2, dash="dot"),
        ))
    fig_lr.update_layout(
        **PLOTLY_LAYOUT,
        height=300,
        yaxis_title="Learning Rate",
        xaxis_title="Epoch",
    )
    st.plotly_chart(fig_lr, use_container_width=True)

    # --- Final Metrics Summary ---
    st.markdown("#### 🏆 Final Epoch Metrics (Run 1)")
    final = log1.iloc[-1]
    fc1, fc2, fc3, fc4, fc5 = st.columns(5)
    with fc1:
        st.metric("Total Loss", f"{final['val_total']:.6f}")
    with fc2:
        st.metric("MAE", f"{final['val_mae']:.6f}")
    with fc3:
        st.metric("RMSE", f"{final['val_rmse']:.6f}")
    with fc4:
        st.metric("Accuracy", f"{final['val_accuracy']:.4f}")
    with fc5:
        st.metric("F1 Score", f"{final['val_f1']:.4f}")

    # --- Training Images ---
    st.markdown("---")
    st.markdown("#### 🖼️ Training Visualizations")

    from streamlit_utils import TRAINING_IMAGES_1, TRAINING_IMAGES_2, TRAINING_IMAGES_3

    img_tab1, img_tab2, img_tab3 = st.tabs(["Run 1 (Best)", "Run 2", "Run 3"])

    with img_tab1:
        for label, path in TRAINING_IMAGES_1.items():
            if os.path.exists(path):
                st.image(path, caption=label.replace("_", " ").title(), use_container_width=True)

    with img_tab2:
        for label, path in TRAINING_IMAGES_2.items():
            if os.path.exists(path):
                st.image(path, caption=label.replace("_", " ").title(), use_container_width=True)

    with img_tab3:
        for label, path in TRAINING_IMAGES_3.items():
            if os.path.exists(path):
                st.image(path, caption=label.replace("_", " ").title(), use_container_width=True)


# ---------------------------------------------------------------------------
# Page: Batch Analysis
# ---------------------------------------------------------------------------

def render_batch_page(state):
    from streamlit_utils import (
        predict_single, generate_compatibility_heatmap,
        generate_group_heatmap, ENVIRONMENT_NAMES,
    )

    st.markdown("""
    <div class="hero-section">
        <div class="hero-title">🧪 Batch Analysis</div>
        <div class="hero-subtitle">Explore cross-material compatibility heatmaps and run batch predictions</div>
    </div>
    """, unsafe_allow_html=True)

    if state["status"] != "online":
        st.error("⚠️ Model is not loaded.")
        return

    model = state["model"]
    lookup = state["lookup"]
    materials = state["materials"]
    device = state["device"]

    # --- Heatmap Section ---
    st.markdown("#### 🗺️ Compatibility Heatmap")

    hm_col1, hm_col2 = st.columns([3, 1])
    with hm_col2:
        hm_env = st.selectbox("Environment", ENVIRONMENT_NAMES, key="hm_env")
        hm_ratio = st.slider("Area Ratio", 0.1, 10.0, 1.0, 0.1, key="hm_ratio")
        hm_type = st.radio("Heatmap Type", ["Current Density", "Compatibility Prob."], key="hm_type")
        gen_heatmap = st.button("🔄 Generate Heatmap", use_container_width=True)

    with hm_col1:
        if gen_heatmap or st.session_state.get("heatmap_data") is not None:
            if gen_heatmap:
                with st.spinner("Generating heatmap... (predicting all group pairs)"):
                    if hm_type == "Current Density":
                        hm_df = generate_group_heatmap(
                            model, lookup, materials, hm_env, hm_ratio, device
                        )
                    else:
                        hm_df = generate_compatibility_heatmap(
                            model, lookup, materials, hm_env, hm_ratio, device
                        )
                    st.session_state["heatmap_data"] = hm_df
                    st.session_state["heatmap_type"] = hm_type
            else:
                hm_df = st.session_state["heatmap_data"]
                hm_type = st.session_state.get("heatmap_type", "Current Density")

            colorscale = "RdYlGn_r" if hm_type == "Compatibility Prob." else "Viridis"
            title = "Galvanic Current Density (A/m²)" if hm_type == "Current Density" else "Unfavorable Probability"

            fig_hm = go.Figure(data=go.Heatmap(
                z=hm_df.values,
                x=hm_df.columns.tolist(),
                y=hm_df.index.tolist(),
                colorscale=colorscale,
                colorbar=dict(
                    title=dict(text=title, font=dict(size=11, color="#94a3b8")),
                    tickfont=dict(color="#94a3b8"),
                ),
                hovertemplate="Anode: %{y}<br>Cathode: %{x}<br>Value: %{z:.6f}<extra></extra>",
            ))
            fig_hm.update_layout(
                **PLOTLY_LAYOUT,
                height=600,
                xaxis=dict(
                    **PLOTLY_LAYOUT["xaxis"],
                    tickangle=-45, tickfont=dict(size=9),
                    title="Cathode Group",
                ),
                yaxis=dict(
                    **PLOTLY_LAYOUT["yaxis"],
                    tickfont=dict(size=9),
                    title="Anode Group",
                    autorange="reversed",
                ),
            )
            st.plotly_chart(fig_hm, use_container_width=True)
        else:
            st.info("👆 Click **Generate Heatmap** to create a cross-material analysis.")

    # --- CSV Batch Upload ---
    st.markdown("---")
    st.markdown("#### 📤 Batch CSV Prediction")

    st.markdown("""
    <div class="glass-card" style="padding:14px 18px; font-size:0.85rem; color:#94a3b8;">
        Upload a CSV file with columns: <code>Anode</code>, <code>Cathode</code>, <code>Environment</code>, <code>Area_Ratio</code><br/>
        Materials must match names from the galvanic series table exactly.
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")

    if uploaded_file is not None:
        try:
            batch_df = pd.read_csv(uploaded_file)
            st.dataframe(batch_df.head(), use_container_width=True)

            if st.button("🚀 Run Batch Prediction"):
                pairs = []
                for _, row in batch_df.iterrows():
                    pairs.append({
                        "anode": row.get("Anode", ""),
                        "cathode": row.get("Cathode", ""),
                        "environment": row.get("Environment", "Marine (Seawater)"),
                        "area_ratio": float(row.get("Area_Ratio", 1.0)),
                    })

                results = []
                progress = st.progress(0)
                for i, pair in enumerate(pairs):
                    result = predict_single(
                        model, pair["anode"], pair["cathode"],
                        pair["environment"], pair["area_ratio"], lookup, device,
                    )
                    result.update(pair)
                    results.append(result)
                    progress.progress((i + 1) / len(pairs))

                results_df = pd.DataFrame(results)
                st.session_state["batch_results"] = results_df

        except Exception as e:
            st.error(f"Error processing file: {e}")

    if st.session_state.get("batch_results") is not None:
        results_df = st.session_state["batch_results"]
        st.markdown("##### Results")
        st.dataframe(
            results_df[["anode", "cathode", "environment", "area_ratio",
                         "current_density", "compatibility_label", "compatibility_prob"]],
            use_container_width=True,
        )

        csv_data = results_df.to_csv(index=False)
        st.download_button(
            "📥 Download Results CSV",
            csv_data,
            "galvanic_predictions.csv",
            "text/csv",
            use_container_width=True,
        )


# ---------------------------------------------------------------------------
# Page: Galvanic Series Reference
# ---------------------------------------------------------------------------

def render_reference_page(state):
    st.markdown("""
    <div class="hero-section">
        <div class="hero-title">📚 Galvanic Series Reference</div>
        <div class="hero-subtitle">Complete galvanic series in seawater with material groups and electrochemical potentials</div>
    </div>
    """, unsafe_allow_html=True)

    galv_df = state.get("galv_df")
    if galv_df is None:
        try:
            galv_df = pd.read_csv(
                os.path.join(os.path.dirname(__file__), "pdf_table2_galvanic_series.csv")
            )
        except Exception:
            st.error("Could not load galvanic series data.")
            return

    # --- Interactive Chart ---
    st.markdown("#### ⚡ Electrochemical Potential Ladder")

    # Color map for groups
    unique_groups = galv_df["Group"].unique()
    palette = (
        px.colors.qualitative.Set3
        + px.colors.qualitative.Pastel1
        + px.colors.qualitative.Set2
    )
    color_map = {g: palette[i % len(palette)] for i, g in enumerate(unique_groups)}

    fig_series = go.Figure()

    for group in unique_groups:
        mask = galv_df["Group"] == group
        subset = galv_df[mask]
        fig_series.add_trace(go.Bar(
            y=subset["Material"],
            x=subset["Potential_V_SCE"],
            orientation="h",
            name=group[:25],
            marker=dict(
                color=color_map[group],
                opacity=0.85,
                line=dict(width=0.5, color="rgba(255,255,255,0.2)"),
            ),
            hovertemplate="<b>%{y}</b><br>Potential: %{x:.2f} V (SCE)<br>Group: " + group + "<extra></extra>",
        ))

    layout_base = {k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("legend", "yaxis")}
    fig_series.update_layout(
        **layout_base,
        height=max(500, len(galv_df) * 22),
        barmode="relative",
        xaxis_title="Potential vs SCE (V)",
        yaxis=dict(
            **PLOTLY_LAYOUT["yaxis"],
            categoryorder="total ascending",
            tickfont=dict(size=11),
        ),
        legend=dict(
            **{k: v for k, v in PLOTLY_LAYOUT["legend"].items() if k != "font"},
            orientation="v",
            yanchor="top", y=1,
            xanchor="left", x=1.02,
            font=dict(size=9, color="#94a3b8"),
        ),
        annotations=[
            dict(
                x=-1.7, y=-0.5,
                text="← Anodic (Active)",
                showarrow=False,
                font=dict(color=COLORS["red"], size=12, family="Inter"),
                xref="x", yref="paper",
            ),
            dict(
                x=0.25, y=-0.5,
                text="Cathodic (Noble) →",
                showarrow=False,
                font=dict(color=COLORS["green"], size=12, family="Inter"),
                xref="x", yref="paper",
            ),
        ],
    )

    st.plotly_chart(fig_series, use_container_width=True)

    # --- Data Table ---
    st.markdown("---")
    st.markdown("#### 📋 Complete Materials Table")

    # Style the dataframe
    styled_df = galv_df.copy()
    styled_df = styled_df.rename(columns={
        "Rank": "Rank",
        "Material": "Material",
        "Potential_V_SCE": "Potential (V vs SCE)",
        "Group": "Material Group",
    })

    st.dataframe(
        styled_df,
        use_container_width=True,
        height=600,
        column_config={
            "Rank": st.column_config.NumberColumn("Rank", help="Noble → Active ranking"),
            "Material": st.column_config.TextColumn("Material", width="large"),
            "Potential (V vs SCE)": st.column_config.NumberColumn(
                "Potential (V vs SCE)", format="%.2f",
                help="Standard potential vs Saturated Calomel Electrode",
            ),
            "Material Group": st.column_config.TextColumn("Material Group", width="large"),
        },
    )

    # --- Material Groups Reference ---
    st.markdown("---")
    st.markdown("#### 🏷️ Material Groups")

    try:
        groups_df = pd.read_csv(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf_table1_material_groups.csv")
        )
        group_cols = st.columns(4)
        for i, (_, row) in enumerate(groups_df.iterrows()):
            with group_cols[i % 4]:
                st.markdown(f"""
                <div class="glass-card" style="padding:12px 16px; margin-bottom:8px;">
                    <span style="color:#3b82f6; font-weight:700; font-size:1.1rem;">#{row['Group_ID']}</span>
                    <div style="color:#e2e8f0; font-size:0.82rem; margin-top:4px; line-height:1.4;">{row['Category']}</div>
                </div>
                """, unsafe_allow_html=True)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Initialize
    state = init_model()

    # Sidebar
    render_sidebar(state)

    # Main content with tabs
    tab_predict, tab_train, tab_batch, tab_ref = st.tabs([
        "🔬 Prediction Engine",
        "📊 Training Analytics",
        "🧪 Batch Analysis",
        "📚 Galvanic Series",
    ])

    with tab_predict:
        render_prediction_page(state)

    with tab_train:
        render_training_page(state)

    with tab_batch:
        render_batch_page(state)

    with tab_ref:
        render_reference_page(state)


if __name__ == "__main__":
    main()
