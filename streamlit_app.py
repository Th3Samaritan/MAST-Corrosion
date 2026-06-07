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

    /* ================================================================
       DESIGN SYSTEM — Minimalist Black & White
       Dark mode (:root default) / Light mode (overridden by LIGHT_THEME_CSS)
       ================================================================ */

    /* ---------- Dark Mode (Ink) — Default ---------- */
    :root {
        --bg-primary: #0a0a0a;
        --bg-secondary: #141414;
        --bg-card: rgba(22, 22, 22, 0.72);
        --bg-glass: rgba(28, 28, 28, 0.6);
        --bg-sidebar: #0d0d0d;
        --bg-elevated: #1c1c1c;
        --border-subtle: rgba(255, 255, 255, 0.06);
        --border-medium: rgba(255, 255, 255, 0.11);
        --border-hover: rgba(255, 255, 255, 0.22);
        --border-strong: rgba(255, 255, 255, 0.34);

        /* Accent is the contrast itself — true monochrome */
        --accent: #fafafa;
        --accent-ink: #ededed;
        --accent-glow: rgba(255, 255, 255, 0.07);
        --accent-subtle: rgba(255, 255, 255, 0.04);
        --accent-inverse: #0a0a0a;

        --text-primary: #fafafa;
        --text-secondary: #b8b8b8;
        --text-muted: #6e6e6e;
        --text-faint: #3f3f3f;

        --shadow-sm: 0 1px 2px rgba(0,0,0,0.5);
        --shadow-md: 0 4px 18px rgba(0,0,0,0.35);
        --shadow-lg: 0 12px 40px rgba(0,0,0,0.55);

        --orb-opacity: 0.025;
        --orb-color-1: #f5f5f5;
        --orb-color-2: #888888;

        /* Semantic — used only where they aid interpretation */
        --success: #10b981;
        --success-soft: #34d399;
        --success-bg: rgba(16, 185, 129, 0.09);
        --success-border: rgba(16, 185, 129, 0.22);

        --warning: #f59e0b;
        --warning-soft: #fbbf24;
        --warning-bg: rgba(245, 158, 11, 0.09);
        --warning-border: rgba(245, 158, 11, 0.22);

        --danger: #f43f5e;
        --danger-soft: #fb7185;
        --danger-bg: rgba(244, 63, 94, 0.09);
        --danger-border: rgba(244, 63, 94, 0.24);

        --info: #818cf8;
        --info-soft: #a5b4fc;

        /* Domain meaning */
        --anode: var(--danger);          /* corroding */
        --cathode: var(--success);       /* protected */
        --gradient: var(--info);         /* driving force */

        --risk-low: var(--success);
        --risk-med: var(--warning);
        --risk-high: var(--danger);

        --verdict-green: var(--success-soft);
        --verdict-green-bg: var(--success-bg);
        --verdict-green-border: var(--success-border);
        --verdict-red: var(--danger-soft);
        --verdict-red-bg: var(--danger-bg);
        --verdict-red-border: var(--danger-border);

        --t: 0.3s;
    }

    /* Light-mode variable overrides are emitted conditionally by inject_theme() at runtime */

    /* ================================================================
       GLOBAL
       ================================================================ */

    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background: var(--bg-primary) !important;
        transition: background var(--t) ease, color var(--t) ease;
    }

    /* ---------- Floating Orb Background Animation ---------- */
    .stApp::before,
    .stApp::after {
        content: '';
        position: fixed;
        border-radius: 50%;
        filter: blur(100px);
        opacity: var(--orb-opacity);
        pointer-events: none;
        z-index: 0;
        transition: opacity var(--t) ease;
    }
    .stApp::before {
        width: 500px;
        height: 500px;
        background: var(--orb-color-1);
        top: -120px;
        right: -80px;
        animation: orb-float 25s ease-in-out infinite;
    }
    .stApp::after {
        width: 380px;
        height: 380px;
        background: var(--orb-color-2);
        bottom: -80px;
        left: -60px;
        animation: orb-float 25s ease-in-out infinite reverse;
        animation-delay: -12s;
    }
    @keyframes orb-float {
        0%, 100% { transform: translate(0, 0) scale(1); }
        25% { transform: translate(40px, -25px) scale(1.06); }
        50% { transform: translate(-15px, 35px) scale(0.94); }
        75% { transform: translate(25px, 15px) scale(1.03); }
    }

    /* ---------- Main Content ---------- */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
        position: relative;
        z-index: 1;
    }

    /* ================================================================
       SIDEBAR
       ================================================================ */

    section[data-testid="stSidebar"] {
        background: var(--bg-sidebar) !important;
        border-right: 1px solid var(--border-subtle) !important;
        transition: background var(--t) ease, border-color var(--t) ease;
    }

    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li {
        color: var(--text-secondary);
        transition: color var(--t) ease;
    }

    /* ================================================================
       TABS
       ================================================================ */

    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background: var(--bg-card);
        border-radius: 10px;
        padding: 4px;
        border: 1px solid var(--border-subtle);
        transition: background var(--t) ease, border-color var(--t) ease;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 7px;
        padding: 10px 24px;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        font-size: 0.88rem;
        color: var(--text-muted);
        background: transparent;
        border: none;
        transition: all var(--t) ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: var(--text-secondary);
    }

    .stTabs [aria-selected="true"] {
        background: var(--bg-elevated) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-medium) !important;
        font-weight: 600;
        box-shadow: var(--shadow-sm);
    }

    /* ================================================================
       METRIC CARDS
       ================================================================ */

    div[data-testid="stMetric"] {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 14px;
        padding: 20px 24px;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        box-shadow: var(--shadow-sm);
        transition: all var(--t) ease;
    }

    div[data-testid="stMetric"]:hover {
        border-color: var(--border-hover);
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }

    div[data-testid="stMetric"] label {
        color: var(--text-muted) !important;
        font-weight: 500;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        transition: color var(--t) ease;
    }

    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
        font-weight: 700;
        font-size: 1.8rem;
        transition: color var(--t) ease;
    }

    /* ================================================================
       FORM ELEMENTS
       ================================================================ */

    .stSelectbox [data-baseweb="select"] > div {
        background: var(--bg-glass) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
        backdrop-filter: blur(8px);
        transition: all var(--t) ease;
    }

    .stSelectbox [data-baseweb="select"] > div:hover {
        border-color: var(--border-hover) !important;
    }

    .stSelectbox [data-baseweb="select"] > div:focus-within {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 2px var(--accent-glow) !important;
    }

    .stSlider [data-baseweb="slider"] [role="slider"] {
        background: var(--accent) !important;
        border: 2px solid var(--bg-primary) !important;
        width: 18px !important;
        height: 18px !important;
        box-shadow: 0 0 0 1px var(--border-strong);
        transition: background var(--t) ease, box-shadow var(--t) ease;
    }
    .stSlider [data-baseweb="slider"] [role="slider"]:hover {
        box-shadow: 0 0 0 4px var(--accent-glow);
    }

    .stRadio > div {
        gap: 10px;
    }

    .stRadio [data-baseweb="radio"] {
        background: var(--bg-glass);
        border-radius: 8px;
        padding: 4px 8px;
        border: 1px solid transparent;
        transition: all var(--t) ease;
    }

    /* ================================================================
       BUTTONS
       ================================================================ */

    .stButton > button {
        background: var(--accent) !important;
        color: var(--accent-inverse) !important;
        border: 1px solid var(--accent) !important;
        border-radius: 10px !important;
        padding: 12px 28px !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        letter-spacing: 0.02em;
        transition: all var(--t) ease !important;
        box-shadow: var(--shadow-sm) !important;
    }

    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: var(--shadow-md) !important;
        filter: brightness(0.95);
    }

    .stDownloadButton > button {
        background: transparent !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-medium) !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        box-shadow: none !important;
        transition: all var(--t) ease !important;
    }

    .stDownloadButton > button:hover {
        border-color: var(--border-strong) !important;
        background: var(--accent-subtle) !important;
    }

    /* ================================================================
       EXPANDER / DATAFRAME
       ================================================================ */

    .streamlit-expanderHeader {
        background: var(--bg-glass) !important;
        border-radius: 10px !important;
        border: 1px solid var(--border-subtle) !important;
        transition: all var(--t) ease;
    }

    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }

    /* ================================================================
       DIVIDER
       ================================================================ */

    hr {
        border-color: var(--border-subtle) !important;
        margin: 1.5rem 0;
        transition: border-color var(--t) ease;
    }

    /* ================================================================
       CUSTOM COMPONENT CLASSES
       ================================================================ */

    .glass-card {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 14px;
        padding: 24px;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        box-shadow: var(--shadow-sm);
        margin-bottom: 16px;
        transition: all var(--t) ease;
    }

    .glass-card:hover {
        border-color: var(--border-medium);
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
        transition: all var(--t) ease;
    }

    .status-online {
        background: var(--verdict-green-bg);
        color: var(--verdict-green);
        border: 1px solid var(--verdict-green-border);
    }

    .status-offline {
        background: var(--verdict-red-bg);
        color: var(--verdict-red);
        border: 1px solid var(--verdict-red-border);
    }

    /* ---------- Verdict Banners ---------- */
    .verdict-compatible {
        background: var(--bg-card);
        border: 1px solid var(--verdict-green-border);
        border-left: 4px solid var(--verdict-green);
        border-radius: 14px;
        padding: 28px 32px;
        text-align: center;
        transition: all var(--t) ease;
    }

    .verdict-unfavorable {
        background: var(--bg-card);
        border: 1px solid var(--verdict-red-border);
        border-left: 4px solid var(--verdict-red);
        border-radius: 14px;
        padding: 28px 32px;
        text-align: center;
        transition: all var(--t) ease;
    }

    .verdict-title {
        font-size: 1.8rem;
        font-weight: 800;
        margin-bottom: 6px;
        letter-spacing: -0.02em;
    }

    .verdict-subtitle {
        font-size: 0.9rem;
        color: var(--text-muted);
        font-family: 'JetBrains Mono', monospace;
        transition: color var(--t) ease;
    }

    /* ---------- Info Rows ---------- */
    .info-row {
        display: flex;
        justify-content: space-between;
        padding: 12px 0;
        border-bottom: 1px solid var(--border-subtle);
        transition: border-color var(--t) ease;
    }

    .info-label {
        color: var(--text-muted);
        font-size: 0.88rem;
        transition: color var(--t) ease;
    }

    .info-value {
        color: var(--text-primary);
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
        transition: color var(--t) ease;
    }

    /* ---------- Hero Section ---------- */
    .hero-section {
        text-align: center;
        padding: 24px 0 32px 0;
    }

    .hero-title {
        font-size: 2.6rem;
        font-weight: 900;
        color: var(--text-primary);
        margin-bottom: 10px;
        line-height: 1.1;
        letter-spacing: -0.03em;
        transition: color var(--t) ease;
    }

    .hero-subtitle {
        font-size: 1.05rem;
        color: var(--text-muted);
        font-weight: 400;
        max-width: 580px;
        margin: 0 auto;
        line-height: 1.5;
        transition: color var(--t) ease;
    }

    /* ---------- Section Headers ---------- */
    .section-label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--text-muted);
        margin-bottom: 16px;
        transition: color var(--t) ease;
    }

    /* ---------- Animations ---------- */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }

    div[data-testid="stMetric"] {
        animation: fadeInUp 0.4s ease forwards;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
    }

    .pulse-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        display: inline-block;
        animation: pulse 2s infinite;
    }

    .pulse-dot-green { background: var(--verdict-green); box-shadow: 0 0 6px var(--verdict-green-border); }
    .pulse-dot-red { background: var(--verdict-red); box-shadow: 0 0 6px var(--verdict-red-border); }

    .gauge-label {
        text-align: center;
        font-size: 0.8rem;
        color: var(--text-muted);
        margin-top: -8px;
        transition: color var(--t) ease;
    }

    /* ---------- Theme Toggle Button ---------- */
    .theme-toggle-wrapper {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        padding: 10px 0;
        font-size: 0.82rem;
        color: var(--text-secondary);
        transition: color var(--t) ease;
    }

    /* ================================================================
       MOBILE RESPONSIVE
       ================================================================ */

    @media (max-width: 768px) {
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
        }

        .hero-title {
            font-size: 1.6rem !important;
        }

        .hero-subtitle {
            font-size: 0.88rem !important;
        }

        .hero-section {
            padding: 12px 0 16px 0 !important;
        }

        div[data-testid="stMetric"] {
            padding: 14px 16px;
            border-radius: 12px;
        }

        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            font-size: 1.3rem;
        }

        .stTabs [data-baseweb="tab-list"] {
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            flex-wrap: nowrap;
        }

        .stTabs [data-baseweb="tab"] {
            padding: 8px 14px;
            font-size: 0.8rem;
            white-space: nowrap;
        }

        .glass-card {
            padding: 14px;
            border-radius: 12px;
        }

        .verdict-title {
            font-size: 1.3rem !important;
        }

        .info-row {
            flex-direction: column;
            gap: 2px;
            padding: 8px 0;
        }

        .info-value {
            font-size: 0.85rem;
        }

        .stButton > button {
            padding: 10px 20px !important;
            font-size: 0.9rem !important;
        }

        .stApp::before { width: 250px; height: 250px; }
        .stApp::after { width: 200px; height: 200px; }
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Dark / Light mode toggle (CSS class injection)
# ---------------------------------------------------------------------------

LIGHT_THEME_CSS = """
<style>
:root {
    --bg-primary: #f8f7f4;
    --bg-secondary: #eeede9;
    --bg-card: rgba(255, 255, 255, 0.86);
    --bg-glass: rgba(252, 252, 250, 0.72);
    --bg-sidebar: #f2f1ed;
    --bg-elevated: #ffffff;
    --border-subtle: rgba(10, 10, 10, 0.07);
    --border-medium: rgba(10, 10, 10, 0.11);
    --border-hover: rgba(10, 10, 10, 0.22);
    --border-strong: rgba(10, 10, 10, 0.34);

    --accent: #0a0a0a;
    --accent-ink: #1a1a1a;
    --accent-glow: rgba(10, 10, 10, 0.07);
    --accent-subtle: rgba(10, 10, 10, 0.04);
    --accent-inverse: #ffffff;

    --text-primary: #0a0a0a;
    --text-secondary: #3f3f3f;
    --text-muted: #8a8a8a;
    --text-faint: #c4c4c4;

    --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
    --shadow-md: 0 4px 18px rgba(0,0,0,0.06);
    --shadow-lg: 0 12px 40px rgba(0,0,0,0.08);

    --orb-opacity: 0.05;
    --orb-color-1: #d4d4d4;
    --orb-color-2: #a8a8a8;

    --success: #047857;
    --success-soft: #059669;
    --success-bg: rgba(4, 120, 87, 0.07);
    --success-border: rgba(4, 120, 87, 0.2);

    --warning: #c2410c;
    --warning-soft: #d97706;
    --warning-bg: rgba(194, 65, 12, 0.06);
    --warning-border: rgba(194, 65, 12, 0.18);

    --danger: #be123c;
    --danger-soft: #dc2626;
    --danger-bg: rgba(190, 18, 60, 0.06);
    --danger-border: rgba(190, 18, 60, 0.2);

    --info: #4338ca;
    --info-soft: #6366f1;

    --anode: var(--danger);
    --cathode: var(--success);
    --gradient: var(--info);

    --risk-low: var(--success);
    --risk-med: var(--warning);
    --risk-high: var(--danger);

    --verdict-green: var(--success);
    --verdict-green-bg: var(--success-bg);
    --verdict-green-border: var(--success-border);
    --verdict-red: var(--danger);
    --verdict-red-bg: var(--danger-bg);
    --verdict-red-border: var(--danger-border);
}

/* Streamlit's own surfaces — force-paint so the toggle takes hold everywhere */
.stApp,
.stApp > header,
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div,
[data-testid="stHeader"] {
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
}
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div {
    background-color: var(--bg-sidebar) !important;
}
.stApp p, .stApp label, .stApp span, .stApp li,
.stMarkdown, .stMarkdown p, .stMarkdown li,
.stRadio label, .stSelectbox label, .stSlider label, .stToggle label {
    color: var(--text-primary);
}
</style>
"""

def sync_theme_from_widget():
    """Read the toggle widget's state (set by prior rerun) and update theme_mode
    BEFORE any CSS is emitted, so the page paints with the correct theme on the
    same rerun the user clicks the toggle."""
    if "theme_toggle" in st.session_state:
        st.session_state["theme_mode"] = (
            "light" if st.session_state["theme_toggle"] else "dark"
        )
    elif "theme_mode" not in st.session_state:
        st.session_state["theme_mode"] = "dark"

def inject_theme():
    """Emit light-mode CSS variable overrides when the user has toggled light mode.
    Dark mode is the default in :root, so no override is needed for it."""
    if st.session_state.get("theme_mode") == "light":
        st.markdown(LIGHT_THEME_CSS, unsafe_allow_html=True)

sync_theme_from_widget()
inject_theme()


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
# Plotly theme (mode-aware)
# ---------------------------------------------------------------------------

def get_plotly_layout():
    """Return Plotly layout dict that adapts to current theme mode."""
    is_light = st.session_state.get("theme_mode", "dark") == "light"
    text_color = "#52525b" if is_light else "#a1a1aa"
    grid_color = "rgba(0,0,0,0.05)" if is_light else "rgba(255,255,255,0.05)"
    zero_color = "rgba(0,0,0,0.08)" if is_light else "rgba(255,255,255,0.07)"
    legend_bg = "rgba(255,255,255,0.9)" if is_light else "rgba(14,14,17,0.9)"
    legend_border = "rgba(0,0,0,0.08)" if is_light else "rgba(255,255,255,0.08)"

    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=text_color, size=12),
        margin=dict(l=40, r=20, t=40, b=40),
        xaxis=dict(gridcolor=grid_color, zerolinecolor=zero_color),
        yaxis=dict(gridcolor=grid_color, zerolinecolor=zero_color),
        legend=dict(
            bgcolor=legend_bg,
            bordercolor=legend_border,
            borderwidth=1,
            font=dict(size=11, color=text_color),
        ),
    )

# Backward-compatible: static reference for code that reads PLOTLY_LAYOUT directly
PLOTLY_LAYOUT = get_plotly_layout()

COLORS = {
    # Refined palette — semantic where it matters, neutral elsewhere
    "ink": "#fafafa",
    "graphite": "#a1a1aa",
    "slate": "#71717a",
    "silver": "#d4d4d8",

    # Domain semantics (used for anode/cathode/risk)
    "anode": "#f43f5e",       # corroding
    "cathode": "#10b981",     # protected
    "warning": "#f59e0b",
    "gradient": "#a78bfa",    # potential gradient / driving force

    # Generic series accents (used in multi-series charts only)
    "blue": "#818cf8",
    "cyan": "#22d3ee",
    "teal": "#2dd4bf",
    "green": "#10b981",
    "red": "#f43f5e",
    "amber": "#f59e0b",
    "purple": "#a78bfa",
    "pink": "#f472b6",
}


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar(state):
    with st.sidebar:
        # Logo / Branding
        st.markdown("""
        <div style="text-align:center; padding: 16px 0 8px 0;">
            <div style="font-size: 2rem; margin-bottom: 6px; letter-spacing: -0.02em; font-weight: 900; color: var(--text-primary); transition: color var(--t) ease;">MAST</div>
            <div style="font-size: 0.7rem; color: var(--text-muted); letter-spacing: 0.12em; text-transform: uppercase; transition: color var(--t) ease;">Galvanic Corrosion Engine</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Theme Toggle — sync_theme_from_widget() at top of run reads this on next rerun
        st.toggle(
            "☀️ Light Mode",
            value=st.session_state.get("theme_mode", "dark") == "light",
            key="theme_toggle",
        )

        st.markdown("---")

        # Model Status
        st.markdown("##### Model Status")
        if state["status"] == "online":
            st.markdown("""
            <div class="status-badge status-online">
                <span class="pulse-dot pulse-dot-green"></span>
                Online
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
                Offline
            </div>
            """, unsafe_allow_html=True)
            if state.get("error"):
                st.error(f"Error: {state['error']}")

        st.markdown("---")

        # Info
        st.markdown("##### About")
        st.markdown("""
        <div style="font-size:0.8rem; color: var(--text-muted); line-height:1.6; transition: color var(--t) ease;">
            Physics-Informed Graph Neural Network for predicting galvanic corrosion
            in multi-material assemblies. Uses NNConv message passing with KCL and
            thermodynamic constraints.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("""
        <div style="text-align:center; font-size:0.7rem; color: var(--text-muted); transition: color var(--t) ease;">
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
            <div style="font-size:1rem; font-weight:700; color:var(--text-primary); margin-bottom:16px;">
                🔧 Material Selection
            </div>
        </div>
        """, unsafe_allow_html=True)

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
                <span class="info-value" style="color:var(--anode);">{anode_info.get('potential_sce', 0):.2f} V</span>
            </div>
            <div class="info-row" style="padding:6px 0;">
                <span class="info-label">Cathode Potential (SCE)</span>
                <span class="info-value" style="color:var(--cathode);">{cathode_info.get('potential_sce', 0):.2f} V</span>
            </div>
            <div class="info-row" style="padding:6px 0; border-bottom:none;">
                <span class="info-label">ΔV (Driving Force)</span>
                <span class="info-value" style="color:var(--gradient);">{pot_diff:.2f} V</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown("""
        <div class="glass-card">
            <div style="font-size:1rem; font-weight:700; color:var(--text-primary); margin-bottom:16px;">
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

        # Area ratio gauge — semantic color, neutral track
        ratio_var = "--risk-low" if area_ratio < 1 else ("--risk-med" if area_ratio < 10 else "--risk-high")
        ratio_label = "Low risk" if area_ratio < 1 else ("Moderate" if area_ratio < 10 else "High risk")
        st.markdown(f"""
        <div class="glass-card" style="padding:12px 18px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="info-label">Area Ratio Risk</span>
                <span style="color:var({ratio_var}); font-weight:700; font-size:0.9rem; letter-spacing:0.02em;">{ratio_label}</span>
            </div>
            <div style="margin-top:10px; height:5px; background:var(--border-subtle); border-radius:3px; overflow:hidden;">
                <div style="height:100%; width:{min(area_ratio / 50 * 100, 100):.0f}%; background:linear-gradient(90deg, var(--risk-low), var(--risk-med), var(--risk-high)); border-radius:3px; transition: width 0.5s ease;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- Predict Button ---
    st.markdown("<br/>", unsafe_allow_html=True)
    col_btn_l, col_btn_c, col_btn_r = st.columns([3, 4, 3])
    with col_btn_c:
        predict_clicked = st.button("⚡  Run Prediction", width="stretch", type="primary")

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
        verdict_var = "--verdict-green" if is_compat else "--verdict-red"
        confidence = (1 - result["compatibility_prob"]) if is_compat else result["compatibility_prob"]

        st.markdown(f"""
        <div class="{verdict_class}">
            <div class="verdict-title" style="color:var({verdict_var});">
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
                    <div style="font-weight:600; color:var(--text-primary); margin-bottom:12px;">📊 Prediction Details</div>
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
                    <div style="font-weight:600; color:var(--text-primary); margin-bottom:12px;">⚙️ Input Parameters</div>
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
    _muted = PLOTLY_LAYOUT["font"]["color"]
    fig_loss.update_annotations(font_size=14, font_color=_muted)

    st.plotly_chart(fig_loss, width="stretch")

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
    fig_metrics.update_annotations(font_size=14, font_color=PLOTLY_LAYOUT["font"]["color"])

    st.plotly_chart(fig_metrics, width="stretch")

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
    st.plotly_chart(fig_lr, width="stretch")

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
                st.image(path, caption=label.replace("_", " ").title(), width="stretch")

    with img_tab2:
        for label, path in TRAINING_IMAGES_2.items():
            if os.path.exists(path):
                st.image(path, caption=label.replace("_", " ").title(), width="stretch")

    with img_tab3:
        for label, path in TRAINING_IMAGES_3.items():
            if os.path.exists(path):
                st.image(path, caption=label.replace("_", " ").title(), width="stretch")


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
        gen_heatmap = st.button("🔄 Generate Heatmap", width="stretch")

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

            # Compatibility prob: red(unfavorable)→green(compatible). Current density: monochrome→amber for high
            colorscale = "RdYlGn_r" if hm_type == "Compatibility Prob." else "Cividis"
            title = "Galvanic Current Density (A/m²)" if hm_type == "Current Density" else "Unfavorable Probability"
            _muted_cb = PLOTLY_LAYOUT["font"]["color"]

            fig_hm = go.Figure(data=go.Heatmap(
                z=hm_df.values,
                x=hm_df.columns.tolist(),
                y=hm_df.index.tolist(),
                colorscale=colorscale,
                colorbar=dict(
                    title=dict(text=title, font=dict(size=11, color=_muted_cb)),
                    tickfont=dict(color=_muted_cb),
                    outlinewidth=0,
                ),
                hovertemplate="Anode: %{y}<br>Cathode: %{x}<br>Value: %{z:.6f}<extra></extra>",
            ))
            layout_no_axes = {k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("xaxis", "yaxis")}
            fig_hm.update_layout(
                **layout_no_axes,
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
            st.plotly_chart(fig_hm, width="stretch")
        else:
            st.info("👆 Click **Generate Heatmap** to create a cross-material analysis.")

    # --- CSV Batch Upload ---
    st.markdown("---")
    st.markdown("#### 📤 Batch CSV Prediction")

    st.markdown("""
    <div class="glass-card" style="padding:14px 18px; font-size:0.85rem; color:var(--text-secondary);">
        Upload a CSV file with columns: <code>Anode</code>, <code>Cathode</code>, <code>Environment</code>, <code>Area_Ratio</code><br/>
        Materials must match names from the galvanic series table exactly.
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")

    if uploaded_file is not None:
        try:
            batch_df = pd.read_csv(uploaded_file)
            st.dataframe(batch_df.head(), width="stretch")

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
            width="stretch",
        )

        csv_data = results_df.to_csv(index=False)
        st.download_button(
            "📥 Download Results CSV",
            csv_data,
            "galvanic_predictions.csv",
            "text/csv",
            width="stretch",
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
            font=dict(size=9, color=PLOTLY_LAYOUT["font"]["color"]),
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

    st.plotly_chart(fig_series, width="stretch")

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
        width="stretch",
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
                    <span style="color:var(--text-primary); font-weight:800; font-size:1.05rem; font-family:'JetBrains Mono', monospace; letter-spacing:-0.02em;">#{row['Group_ID']}</span>
                    <div style="color:var(--text-secondary); font-size:0.82rem; margin-top:4px; line-height:1.4;">{row['Category']}</div>
                </div>
                """, unsafe_allow_html=True)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Refresh Plotly layout so theme toggle propagates to charts
    global PLOTLY_LAYOUT
    PLOTLY_LAYOUT = get_plotly_layout()

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
