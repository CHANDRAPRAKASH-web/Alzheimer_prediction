"""
=========================================================
Aid Axis - Healthcare Visual Design System & CSS Tokens

Provides a refined, professional healthcare aesthetic:
- Deep Charcoal / Dark Navy Backgrounds (#0B0F19, #0F172A)
- Muted Lavender / Soft Violet Accents (#A78BFA, #8B5CF6)
- Sage Green / Soft Teal Secondary Accents (#14B8A6, #2DD4BF)
- Card Containers with Subtle Borders (#1E293B, #151E2E)
- Warm Off-White Typography (#F8FAFC, #F1F5F9)
=========================================================
"""

import streamlit as st

HEALTHCARE_CSS = """
<style>
/* Global Layout and Typography */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    color: #F1F5F9;
}

/* App Background */
.stApp {
    background-color: #0B0F19;
    color: #F1F5F9;
}

/* Sidebar Styling */
section[data-testid="stSidebar"] {
    background-color: #0F1626;
    border-right: 1px solid #1E293B;
}

section[data-testid="stSidebar"] h1, 
section[data-testid="stSidebar"] h2, 
section[data-testid="stSidebar"] h3 {
    color: #F8FAFC !important;
}

/* Card Styling */
.aidaxis-card {
    background-color: #151E2E;
    border: 1px solid #233148;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    transition: transform 0.15s ease, border-color 0.15s ease;
}

.aidaxis-card:hover {
    border-color: #3B4F6F;
}

.aidaxis-card-accent {
    border-left: 4px solid #A78BFA !important;
}

.aidaxis-card-violet {
    border-left: 4px solid #8B5CF6 !important;
}

.aidaxis-card-teal {
    border-left: 4px solid #14B8A6 !important;
}

.aidaxis-card-amber {
    border-left: 4px solid #F59E0B !important;
}

/* Metric Display Elements */
.aidaxis-stat-label {
    font-size: 0.85rem;
    font-weight: 500;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.35rem;
}

.aidaxis-stat-val {
    font-size: 1.85rem;
    font-weight: 700;
    color: #F8FAFC;
    line-height: 1.2;
}

.aidaxis-stat-sub {
    font-size: 0.82rem;
    color: #64748B;
    margin-top: 0.25rem;
}

/* Badges */
.aidaxis-badge {
    display: inline-block;
    padding: 0.25rem 0.65rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.025em;
}

.aidaxis-badge-violet {
    background-color: rgba(167, 139, 250, 0.15);
    color: #C4B5FD;
    border: 1px solid rgba(167, 139, 250, 0.3);
}

.aidaxis-badge-teal {
    background-color: rgba(20, 184, 166, 0.15);
    color: #5EEAD4;
    border: 1px solid rgba(20, 184, 166, 0.3);
}

.aidaxis-badge-amber {
    background-color: rgba(245, 158, 11, 0.15);
    color: #FCD34D;
    border: 1px solid rgba(245, 158, 11, 0.3);
}

/* Callout and Notice Boxes */
.aidaxis-notice {
    background-color: #121A29;
    border: 1px solid #233148;
    border-left: 4px solid #6366F1;
    border-radius: 8px;
    padding: 0.9rem 1.2rem;
    font-size: 0.875rem;
    color: #CBD5E1;
    margin: 1rem 0;
}

.aidaxis-disclaimer {
    background-color: #141722;
    border: 1px solid #282D3E;
    border-left: 4px solid #F59E0B;
    border-radius: 8px;
    padding: 0.85rem 1.15rem;
    font-size: 0.825rem;
    color: #94A3B8;
    margin: 1.25rem 0;
}

/* Custom Step Progress Header */
.step-container {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #151E2E;
    padding: 0.75rem 1.25rem;
    border-radius: 8px;
    border: 1px solid #233148;
    margin-bottom: 1.5rem;
}

/* Override Streamlit Progress Bar */
div[data-testid="stProgress"] > div > div > div > div {
    background-color: #A78BFA !important;
}

/* Form input labels */
label[data-testid="stWidgetLabel"] p {
    color: #E2E8F0 !important;
    font-weight: 500;
    font-size: 0.95rem;
}

/* Primary Button Styling */
button[kind="primary"] {
    background-color: #7C3AED !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.25rem !important;
    box-shadow: 0 2px 8px rgba(124, 58, 237, 0.3) !important;
}

button[kind="primary"]:hover {
    background-color: #8B5CF6 !important;
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.45) !important;
}

/* Secondary Button Styling */
button[kind="secondary"] {
    background-color: #1E293B !important;
    color: #E2E8F0 !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
}

button[kind="secondary"]:hover {
    background-color: #283548 !important;
    border-color: #475569 !important;
}

/* Headers */
h1 {
    color: #F8FAFC !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
}

h2, h3 {
    color: #E2E8F0 !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em;
}
</style>
"""


def apply_healthcare_theme():
    """
    Applies the custom healthcare visual theme into the active Streamlit app.
    """
    st.markdown(HEALTHCARE_CSS, unsafe_allow_html=True)


def render_metric_card(
    title: str,
    value: str,
    subtitle: str = "",
    accent_type: str = "violet"
):
    """
    Renders a unified metric card with clean typography.
    """
    border_class = f"aidaxis-card-{accent_type}" if accent_type else ""
    st.markdown(
        f"""
        <div class="aidaxis-card {border_class}">
            <div class="aidaxis-stat-label">{title}</div>
            <div class="aidaxis-stat-val">{value}</div>
            {f'<div class="aidaxis-stat-sub">{subtitle}</div>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True
    )
