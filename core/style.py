import streamlit as st

COLORS = {
    "bg": "#FAF9F5", "card": "#FFFFFF", "border": "#E8E6DC",
    "text": "#141413", "muted": "#6B6A63",
    "accent": "#D97757", "up": "#5B8C6B", "down": "#C4553D",
    "blue": "#6A9BCC", "olive": "#788C5D",
}
PALETTE = ["#D97757", "#6A9BCC", "#788C5D", "#CBA135", "#9B7BB5", "#8A8880", "#C4553D", "#4F7C82"]

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,400;8..60,500;8..60,600&display=swap');

html, body, .stApp { font-family: 'Inter', sans-serif; }
h1, h2, h3, .hero-title {
    font-family: 'Source Serif 4', Georgia, serif !important;
    font-weight: 500 !important; letter-spacing: -0.01em; color: #141413;
}
.block-container { padding-top: 2.5rem; max-width: 1200px; }
#MainMenu, footer { visibility: hidden; }

.hero-title { font-size: 2.4rem; line-height: 1.15; margin: 0 0 .25rem 0; }
.hero-sub { color: #6B6A63; font-size: 1.02rem; margin-bottom: 1.5rem; }

[data-testid="stMetric"] {
    background: #FFFFFF; border: 1px solid #E8E6DC; border-radius: 14px;
    padding: 14px 18px; box-shadow: 0 1px 2px rgba(20,20,19,.03);
}
[data-testid="stMetricLabel"] { color: #6B6A63; }
[data-testid="stMetricValue"], [data-testid="stMetricValue"] * {
    font-family: 'Source Serif 4', serif !important;
    font-size: 1.4rem !important;
    font-weight: 500 !important;
    line-height: 1.25 !important;
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: clip !important;
}

.stTabs [data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid #E8E6DC; }
.stTabs [data-baseweb="tab"] { border-radius: 8px 8px 0 0; padding: 8px 14px; }
.stTabs [aria-selected="true"] { color: #D97757 !important; }
.stTabs [data-baseweb="tab-highlight"] { background-color: #D97757; }

.stTextInput input, .stNumberInput input {
    border-radius: 10px !important; border-color: #E8E6DC !important; background: #FFFFFF;
}
.stButton > button, .stDownloadButton > button {
    border-radius: 10px; border: 1px solid #E8E6DC; background: #FFFFFF; color: #141413;
}
.stButton > button:hover, .stDownloadButton > button:hover { border-color: #D97757; color: #D97757; }
[data-testid="stExpander"] { border: 1px solid #E8E6DC; border-radius: 14px; background: #FFFFFF; }
hr { border-color: #E8E6DC; }
</style>"""

def inject_css():
    st.markdown(_CSS, unsafe_allow_html=True)

def page_header(title: str, subtitle: str = ""):
    st.markdown(f'<div class="hero-title">{title}</div><div class="hero-sub">{subtitle}</div>',
                unsafe_allow_html=True)

def style_fig(fig, height=450):
    fig.update_layout(
        template="simple_white", height=height,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=COLORS["text"]),
        colorway=PALETTE, margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", y=1.08, x=0),
    )
    fig.update_xaxes(showgrid=False, linecolor=COLORS["border"])
    fig.update_yaxes(gridcolor=COLORS["border"], linecolor=COLORS["border"])
    return fig
