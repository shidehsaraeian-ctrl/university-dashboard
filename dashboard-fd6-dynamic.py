from __future__ import annotations

import base64
import io
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="داشبورد مدیریتی هوشمند دانشگاه‌های زیرنظر گرگان",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent

DIGIT_TRANSLATION = str.maketrans(
    "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
    "01234567890123456789",
)

TOTAL_LABELS = {
    "مجموع", "جمع", "جمع کل", "کل", "کل مجموعه",
    "کلمجموعه", "مجموعه", "total",
}

UNIVERSITY_COLORS = {
    "گرگان": "#1E40AF",
    "آق قلا": "#0E7490",
    "گمیشان": "#7C3AED",
    "کردکوی": "#059669",
    "بندرترکمن": "#D97706",
}

FALLBACK_COLORS = [
    "#1E40AF", "#0E7490", "#7C3AED", "#059669",
    "#D97706", "#DC2626", "#DB2777", "#0D9488",
]

FINANCIAL_SEMESTER_OPTIONS = ["4054061"]
PREDICTION_SEMESTER_OPTIONS = ["4054061", "4054062", "4054063"]

ALL_SCOPE = "🏛️ کل دانشگاه‌ها"

FALLBACK_LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.95"/>
      <stop offset="100%" stop-color="#DBEAFE" stop-opacity="0.85"/>
    </linearGradient>
  </defs>
  <circle cx="60" cy="60" r="52" fill="url(#g)" opacity="0.18"/>
  <circle cx="60" cy="60" r="42" fill="none" stroke="white" stroke-width="2.5" opacity="0.85"/>
  <path d="M35 55 L60 42 L85 55 L60 68 Z" fill="white" opacity="0.95"/>
  <path d="M42 60 L42 74 Q60 84 78 74 L78 60" fill="none" stroke="white" stroke-width="2.5" stroke-linejoin="round"/>
  <circle cx="60" cy="55" r="3" fill="#1E40AF"/>
  <text x="60" y="98" font-family="Arial, sans-serif" font-size="12" font-weight="700"
        text-anchor="middle" fill="white" opacity="0.95">IAU</text>
</svg>"""


def get_logo_data_uri() -> str:
    mime_map = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "svg": "image/svg+xml",
        "webp": "image/webp",
    }
    for ext, mime in mime_map.items():
        path = BASE_DIR / f"azad-logo.{ext}"
        if path.exists():
            data = base64.b64encode(path.read_bytes()).decode()
            return f"data:{mime};base64,{data}"
    data = base64.b64encode(FALLBACK_LOGO_SVG.encode()).decode()
    return f"data:image/svg+xml;base64,{data}"


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700;800;900&display=swap');

    * { font-family: 'Vazirmatn', Tahoma, Arial, sans-serif !important; }

    .stApp { background: linear-gradient(180deg, #EEF2F9 0%, #F7F9FC 100%); }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2.5rem;
        max-width: 1500px;
    }

    .main-header {
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 55%, #06B6D4 100%);
        border-radius: 18px;
        padding: 24px 32px;
        margin-bottom: 22px;
        box-shadow: 0 12px 32px rgba(30, 58, 138, 0.18);
        direction: rtl;
        position: relative;
        overflow: hidden;
    }
    .main-header::before {
        content: '';
        position: absolute;
        top: -50%; right: -10%;
        width: 420px; height: 420px;
        background: radial-gradient(circle, rgba(255,255,255,0.14) 0%, transparent 70%);
        border-radius: 50%;
    }
    .main-header::after {
        content: '';
        position: absolute;
        bottom: -60%; left: -5%;
        width: 320px; height: 320px;
        background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
        border-radius: 50%;
    }
    .header-inner {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 24px;
        position: relative;
        z-index: 2;
        direction: rtl;
    }
    .header-text { flex: 1; text-align: right; }
    .header-text h1 {
        color: #FFFFFF; margin: 0;
        font-size: 1.65rem; font-weight: 700;
        line-height: 1.5;
    }
    .header-text p {
        color: rgba(255,255,255,0.9);
        margin: 8px 0 0 0;
        font-size: 0.94rem;
    }
    .header-logo {
        flex-shrink: 0;
        width: 90px;
        height: 90px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(255,255,255,0.10);
        border: 1.5px solid rgba(255,255,255,0.25);
        border-radius: 18px;
        padding: 8px;
        backdrop-filter: blur(6px);
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.12);
    }
    .header-logo img {
        width: 100%;
        height: 100%;
        object-fit: contain;
        display: block;
    }

    .kpi-card {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 18px 22px;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.05);
        border: 1px solid #E5E9F2;
        transition: all 0.25s ease;
        direction: rtl;
        min-height: 130px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 26px rgba(15, 23, 42, 0.10);
        border-color: #CBD5E1;
    }
    .kpi-label {
        color: #64748B;
        font-size: 0.84rem;
        font-weight: 500;
        margin-bottom: 6px;
        line-height: 1.4;
    }
    .kpi-value {
        color: #0F172A;
        font-size: 1.5rem;
        font-weight: 700;
        line-height: 1.25;
        font-variant-numeric: tabular-nums;
        letter-spacing: -0.3px;
        word-break: break-word;
    }
    .kpi-unit {
        color: #94A3B8;
        font-size: 0.78rem;
        font-weight: 500;
        margin-top: 4px;
    }
    .accent-blue { border-top: 3px solid #2563EB; }
    .accent-red { border-top: 3px solid #DC2626; }
    .accent-green { border-top: 3px solid #059669; }
    .accent-purple { border-top: 3px solid #7C3AED; }
    .accent-orange { border-top: 3px solid #D97706; }
    .accent-cyan { border-top: 3px solid #0891B2; }
    .accent-slate { border-top: 3px solid #64748B; }

    .section-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 26px 0 14px 0;
        direction: rtl;
        font-size: 1.1rem;
        font-weight: 700;
        color: #0F172A;
        flex-wrap: wrap;
    }
    .section-header::before {
        content: '';
        width: 4px; height: 22px;
        background: linear-gradient(180deg, #2563EB, #06B6D4);
        border-radius: 3px;
    }

    .sub-header-rtl {
        direction: rtl;
        text-align: right;
        font-size: 1.02rem;
        font-weight: 700;
        color: #0F172A;
        margin: 20px 0 10px 0;
    }

    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.76rem;
        font-weight: 600;
        background: #DBEAFE;
        color: #1E40AF;
    }
    .badge-green { background: #D1FAE5; color: #065F46; }
    .badge-orange { background: #FEF3C7; color: #92400E; }
    .badge-red { background: #FEE2E2; color: #991B1B; }
    .badge-purple { background: #EDE9FE; color: #5B21B6; }

    .explain-box {
        background: linear-gradient(135deg, #F0F9FF 0%, #EFF6FF 100%);
        border-right: 4px solid #3B82F6;
        border-radius: 12px;
        padding: 14px 18px;
        margin: 8px 0 16px 0;
        direction: rtl;
        text-align: right;
        color: #1E3A8A;
        font-size: 0.87rem;
        line-height: 1.85;
    }
    .explain-box b { color: #1E40AF; }

    .rtl-alert {
        direction: rtl;
        text-align: right;
        background: linear-gradient(135deg, #F0F9FF 0%, #EFF6FF 100%);
        border-right: 4px solid #3B82F6;
        border-radius: 12px;
        padding: 14px 18px;
        margin: 8px 0 16px 0;
        color: #1E3A8A;
        font-size: 0.9rem;
        line-height: 1.85;
    }

    .welcome-box {
        background: #FFFFFF;
        border-radius: 18px;
        padding: 46px 40px;
        text-align: center;
        direction: rtl;
        box-shadow: 0 12px 32px rgba(15, 23, 42, 0.08);
        border: 1px solid #E5E9F2;
        margin-top: 30px;
    }
    .welcome-box .welcome-icon {
        font-size: 3rem;
        display: block;
        margin-bottom: 14px;
    }
    .welcome-box .welcome-title {
        color: #1E3A8A;
        font-size: 1.3rem;
        font-weight: 700;
        margin-bottom: 14px;
    }
    .welcome-box .welcome-text {
        color: #475569;
        font-size: 0.98rem;
        line-height: 2;
    }
    .welcome-box .welcome-hint {
        display: inline-block;
        margin-top: 18px;
        background: #EFF6FF;
        color: #1E40AF;
        padding: 10px 20px;
        border-radius: 10px;
        font-size: 0.9rem;
        font-weight: 600;
    }

    .center-notice {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 260px;
        text-align: center;
        padding: 30px;
    }
    .center-notice-inner {
        background: #FFFFFF;
        border: 1px solid #E5E9F2;
        border-radius: 16px;
        padding: 32px 40px;
        max-width: 560px;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
        direction: rtl;
        color: #334155;
        font-size: 0.95rem;
        line-height: 2;
    }
    .center-notice-icon {
        font-size: 2.2rem;
        margin-bottom: 8px;
        display: block;
    }

    .pretty-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        border-radius: 14px;
        overflow: hidden;
        direction: rtl;
        font-family: 'Vazirmatn', Tahoma, Arial;
        font-size: 13.5px;
        box-shadow: 0 6px 22px rgba(15, 23, 42, 0.07);
        background: #FFFFFF;
        border: 1px solid #E5E9F2;
        margin-top: 6px;
    }
    .pretty-table thead th {
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 60%, #3B82F6 100%);
        color: #FFFFFF;
        font-weight: 800;
        font-size: 13.5px;
        text-align: right;
        padding: 14px 16px;
        white-space: nowrap;
        letter-spacing: 0.2px;
        border: none;
    }
    .pretty-table tbody td {
        text-align: right;
        padding: 12px 16px;
        color: #1E293B;
        font-weight: 600;
        font-variant-numeric: tabular-nums;
        border-bottom: 1px solid #E8EDF5;
        transition: background-color 0.15s ease;
    }
    .pretty-table tbody tr:nth-child(even) td {
        background-color: #F8FAFC;
    }
    .pretty-table tbody tr:hover td {
        background-color: #EFF6FF;
    }
    .pretty-table tbody tr:last-child td {
        border-bottom: none;
    }

    .admin-grid-header {
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 60%, #3B82F6 100%);
        color: #FFFFFF !important;
        font-weight: 800 !important;
        font-size: 13.5px !important;
        text-align: right;
        direction: rtl;
        padding: 14px 16px;
        min-height: 52px;
        display: flex;
        align-items: center;
        box-shadow: 0 4px 12px rgba(30, 58, 138, 0.14);
        border-radius: 10px;
        letter-spacing: 0.2px;
    }
    .admin-grid-cell {
        background: #FFFFFF;
        color: #1E293B !important;
        font-weight: 700 !important;
        font-size: 13.5px !important;
        text-align: right;
        direction: rtl;
        padding: 12px 16px;
        min-height: 52px;
        display: flex;
        align-items: center;
        font-variant-numeric: tabular-nums;
        border: 1px solid #E5E9F2;
        border-radius: 10px;
    }
    .admin-grid-cell.zebra {
        background: #F8FAFC;
    }
    .admin-grid-cell:hover {
        background: #EFF6FF;
    }

    div[data-testid="stNumberInput"] {
        margin-bottom: 0 !important;
    }
    div[data-testid="stNumberInput"] > div {
        border: none !important;
        background: transparent !important;
    }
    div[data-testid="stNumberInput"] input {
        background: #FFFFFF !important;
        color: #0F172A !important;
        font-weight: 800 !important;
        font-size: 14px !important;
        padding: 12px 16px !important;
        text-align: center !important;
        direction: ltr !important;
        border: 1px solid #E5E9F2 !important;
        border-radius: 10px !important;
        min-height: 52px !important;
        font-family: 'Vazirmatn', Tahoma, Arial !important;
        font-variant-numeric: tabular-nums !important;
        transition: all 0.15s ease !important;
    }
    div[data-testid="stNumberInput"] input:hover {
        border-color: #BFDBFE !important;
        background: #F8FAFC !important;
    }
    div[data-testid="stNumberInput"] input:focus {
        border-color: #2563EB !important;
        background: #FFFFFF !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15) !important;
    }
    div[data-testid="stNumberInput"] button {
        background: #EFF6FF !important;
        color: #1E40AF !important;
        border: 1px solid #DBEAFE !important;
        border-radius: 8px !important;
        font-weight: 800 !important;
    }
    div[data-testid="stNumberInput"] button:hover {
        background: #DBEAFE !important;
    }

    div[data-testid="stHorizontalBlock"] {
        gap: 6px !important;
        margin-bottom: 6px !important;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #F4F8FF 0%, #E6EEFB 60%, #DCE7F9 100%);
        border-right: 1px solid #D6E2F5;
        box-shadow: 2px 0 14px rgba(30, 58, 138, 0.06);
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] label {
        direction: rtl;
        text-align: right;
        color: #1E3A8A;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h4,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4 {
        direction: rtl !important;
        text-align: right !important;
        color: #1E40AF !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        direction: rtl;
        text-align: right;
    }
    [data-testid="stSidebar"] hr {
        border-color: #D6E2F5;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploader"] {
        background: rgba(255,255,255,0.55);
        border-radius: 12px;
        padding: 8px;
    }
    [data-testid="stSidebar"] div[data-baseweb="select"] > div {
        background: rgba(255,255,255,0.85);
        border-color: #D6E2F5;
        direction: rtl;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        direction: rtl;
        border-bottom: 2px solid #E5E9F2;
    }
    .stTabs [data-baseweb="tab"] {
        height: 46px;
        padding: 0 22px;
        background-color: transparent;
        border-radius: 10px 10px 0 0;
        font-weight: 600;
        color: #64748B;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF;
        color: #1E40AF;
        border-bottom: 3px solid #1E40AF;
    }

    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #E5E9F2;
    }

    .stButton > button {
        border-radius: 10px;
        font-weight: 500;
    }

    .stDownloadButton > button {
        background: linear-gradient(135deg, #1E40AF, #3B82F6);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 24px;
        font-weight: 600;
    }
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #1E3A8A, #2563EB);
    }

    div[data-testid="stMetric"] { display: none; }
    </style>
    """,
    unsafe_allow_html=True,
)


def normalize_text(value) -> str:
    if pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = text.replace("ي", "ی").replace("ك", "ک")
    text = text.replace("\u200c", " ").replace("\u200f", "").replace("\u200e", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_number(value) -> float:
    if pd.isna(value):
        return np.nan
    if isinstance(value, (int, float, np.number)):
        result = float(value)
        return result if np.isfinite(result) else np.nan

    text = str(value).strip().translate(DIGIT_TRANSLATION)
    if text.lower() in {"", "-", "—", "nan", "none", "null"}:
        return np.nan

    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1]

    text = (
        text.replace("٬", "").replace(",", "").replace("٫", ".")
        .replace("−", "-").replace("\u200c", "")
        .replace("\u200e", "").replace("\u200f", "")
        .replace("ریال", "").replace("تومان", "")
    )
    text = re.sub(r"\s+", "", text)

    try:
        result = float(text)
    except (ValueError, TypeError):
        return np.nan
    if not np.isfinite(result):
        return np.nan
    return -abs(result) if negative else result


def is_total_label(value) -> bool:
    text = normalize_text(value).replace(" ", "").lower()
    return text in {x.replace(" ", "").lower() for x in TOTAL_LABELS}


def fmt_int(value):
    if value is None or pd.isna(value):
        return "—"
    return f"{value:,.0f}"


def fmt_rial(value):
    if value is None or pd.isna(value):
        return "—"
    return f"{value:,.0f}"


def fmt_pct(value, decimals=1):
    if value is None or pd.isna(value):
        return "—"
    return f"{value:+.{decimals}f}%" if abs(value) < 1000 else f"{value:,.{decimals}f}%"


def kpi_card(label, value, unit="", accent="blue"):
    return f"""
    <div class="kpi-card accent-{accent}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-unit">{unit}</div>
    </div>
    """


def explain_box(text):
    return f'<div class="explain-box">{text}</div>'


def rtl_alert(text):
    return f'<div class="rtl-alert">{text}</div>'


def sub_header(text):
    return f'<div class="sub-header-rtl">{text}</div>'


def center_notice(icon, text):
    return f"""
    <div class="center-notice">
        <div class="center-notice-inner">
            <span class="center-notice-icon">{icon}</span>
            {text}
        </div>
    </div>
    """


def render_pretty_table(df: pd.DataFrame):
    html = df.to_html(
        escape=False,
        index=False,
        classes="pretty-table",
        border=0,
        na_rep="—",
    )
    st.markdown(html, unsafe_allow_html=True)


@st.cache_data(show_spinner=False, max_entries=8)
def read_workbook(content: bytes) -> dict[str, pd.DataFrame]:
    sheets = pd.read_excel(io.BytesIO(content), sheet_name=None, engine="openpyxl")
    cleaned = {}
    for sheet_name, frame in sheets.items():
        frame = frame.dropna(how="all").copy()
        frame = frame.dropna(axis=1, how="all")

        names, seen = [], {}
        for original in frame.columns:
            name = normalize_text(original) or "ستون_بدون_نام"
            seen[name] = seen.get(name, 0) + 1
            suffix = f" [{seen[name]}]" if seen[name] > 1 else ""
            names.append(name + suffix)
        frame.columns = names
        cleaned[sheet_name] = frame.reset_index(drop=True)
    return cleaned


def style_figure(fig, height=430):
    fig.update_layout(
        template="plotly_white",
        height=height,
        font=dict(family="Vazirmatn, Tahoma, Arial", size=13, color="#334155"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=25, r=160, t=70, b=55),
        legend=dict(
            orientation="v",
            yanchor="middle", y=0.5,
            xanchor="left", x=1.02,
            font=dict(size=12, family="Vazirmatn", weight="bold"),
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#E5E9F2",
            borderwidth=1,
        ),
        hoverlabel=dict(
            bgcolor="#FFFFFF", font_size=13, font_family="Vazirmatn, Tahoma",
            bordercolor="#CBD5E1",
        ),
    )
    fig.update_xaxes(
        showgrid=True, gridcolor="#E2E8F0", zeroline=False,
        title_font=dict(size=14, color="#0F172A", family="Vazirmatn, Tahoma", weight="bold"),
        tickfont=dict(size=12.5, color="#1E293B", family="Vazirmatn, Tahoma", weight="bold"),
    )
    fig.update_yaxes(
        showgrid=False, zeroline=False,
        title_font=dict(size=14, color="#0F172A", family="Vazirmatn, Tahoma", weight="bold"),
        tickfont=dict(size=12.5, color="#1E293B", family="Vazirmatn, Tahoma", weight="bold"),
    )
    return fig


def excel_safe_frame(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()

    def protect(value):
        if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
            return "'" + value
        return value

    for column in result.select_dtypes(include=["object", "string"]).columns:
        result[column] = result[column].map(protect)
    return result


def make_excel(sheets: dict[str, pd.DataFrame]) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for sheet_name, frame in sheets.items():
            safe_name = sheet_name[:31]
            excel_safe_frame(frame).to_excel(writer, sheet_name=safe_name, index=False)
            ws = writer.sheets[safe_name]
            ws.sheet_view.rightToLeft = True
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            for cells in ws.columns:
                letter = cells[0].column_letter
                max_length = max(
                    (len(str(c.value)) if c.value is not None else 0) for c in cells
                )
                ws.column_dimensions[letter].width = min(max(max_length + 2, 14), 45)
    return buffer.getvalue()


def extract_student_long(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["university", "semester_code", "students"])

    semester_col = None
    for col in frame.columns:
        if any(k in col for k in ("نیمسال", "آمار کل", "ترم", "سال تحصیلی", "آمار ورودی")):
            semester_col = col
            break
    if semester_col is None:
        semester_col = frame.columns[-1]

    uni_cols = [
        c for c in frame.columns
        if c != semester_col and not is_total_label(c)
    ]

    records = []
    for _, row in frame.iterrows():
        raw_sem = row[semester_col]
        try:
            sem_code = str(int(float(raw_sem)))
        except (ValueError, TypeError):
            sem_code = normalize_text(raw_sem)
        if not sem_code or sem_code.lower() == "nan":
            continue
        for uni in uni_cols:
            val = parse_number(row[uni])
            if pd.notna(val):
                records.append({
                    "university": normalize_text(uni),
                    "semester_code": sem_code,
                    "students": val,
                })

    return pd.DataFrame(records)


def extract_financial(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()

    uni_col = None
    for col in frame.columns:
        if any(k in col for k in ("شرح", "دانشگاه", "واحد", "مرکز")):
            uni_col = col
            break
    if uni_col is None:
        uni_col = frame.columns[-1]

    metric_map = {}
    for col in frame.columns:
        if col == uni_col:
            continue
        if "عدم مراجعه" in col:
            metric_map[col] = "not_referred"
        elif "تقسیط" in col:
            metric_map[col] = "installment"
        elif "بدهی" in col:
            metric_map[col] = "debt"
        elif "تعداد" in col:
            metric_map[col] = "debtor_count"

    records = []
    for _, row in frame.iterrows():
        uni = normalize_text(row[uni_col])
        if not uni or is_total_label(uni):
            continue
        rec = {"university": uni}
        for src, internal in metric_map.items():
            rec[internal] = parse_number(row[src])
        records.append(rec)
    return pd.DataFrame(records)


def extract_perf_data(df: pd.DataFrame):
    if df is None or df.empty:
        return None
    try:
        df.columns = [normalize_text(c) for c in df.columns]
        
        title_col = next((c for c in df.columns if "عنوان" in c), df.columns[-1])
        curr_col = next((c for c in df.columns if "وضعیت فعلی" in c), df.columns[1])
        hist_col = next((c for c in df.columns if "عملکرد" in c), df.columns[3])
        
        items_map = {
            "in_tuition": "درآمد شهریه ای",
            "in_outsourcing": "درآمد غیرشهریه ای (برون سپاری)",
            "in_workshop": "درآمد غیرشهریه ای (برگزاری کارگاه)",
            "ex_faculty": "هزینه پرسنلی هیات علمی (حقوق و حق التدریس)",
            "ex_official": "هزینه پرسنلی رسمی و قراردادی",
            "ex_corporate": "هزینه پرسنلی شرکتی",
            "ex_guest": "هزینه حق التدریس اساتید مدعو",
            "ex_rent": "هزینه اجاره",
            "ex_other": "هزینه های جاری (سایر)",
        }
        
        data = {}
        for key, keyword in items_map.items():
            mask = df[title_col].astype(str).str.contains(keyword.split(" (")[0], regex=False, na=False)
            if mask.any():
                row = df[mask].iloc[0]
                val_curr = parse_number(row[curr_col])
                val_hist = parse_number(row[hist_col])
                data[key] = {
                    "title": keyword,
                    "curr": val_curr if pd.notna(val_curr) else 0.0,
                    "hist": val_hist if pd.notna(val_hist) else 0.0,
                }
            else:
                data[key] = {"title": keyword, "curr": 0.0, "hist": 0.0}
                
        tot_inc_curr = data["in_tuition"]["curr"] + data["in_outsourcing"]["curr"] + data["in_workshop"]["curr"]
        tot_inc_hist = data["in_tuition"]["hist"] + data["in_outsourcing"]["hist"] + data["in_workshop"]["hist"]
        
        tot_exp_curr = sum(data[k]["curr"] for k in ["ex_faculty", "ex_official", "ex_corporate", "ex_guest", "ex_rent", "ex_other"])
        tot_exp_hist = sum(data[k]["hist"] for k in ["ex_faculty", "ex_official", "ex_corporate", "ex_guest", "ex_rent", "ex_other"])
        
        data["in_total"] = {"title": "مجموع درآمد سال مالی", "curr": tot_inc_curr, "hist": tot_inc_hist}
        data["ex_total"] = {"title": "مجموع هزینه های سال مالی", "curr": tot_exp_curr, "hist": tot_exp_hist}
        data["profit"] = {"title": "سود و زیان", "curr": tot_inc_curr - tot_exp_curr, "hist": tot_inc_hist - tot_exp_hist}
        
        return data
    except Exception as e:
        st.error(f"خطا در خواندن فایل عملکرد مالی: {e}")
        return None


def list_excel_files():
    if not BASE_DIR.exists():
        return []
    return sorted([f.name for f in BASE_DIR.iterdir() if f.is_file() and f.suffix.lower() == ".xlsx"])


def read_file_by_name(filename: str):
    if not filename:
        return None
    path = BASE_DIR / filename
    return path.read_bytes() if path.exists() else None


LOGO_URI = get_logo_data_uri()

st.markdown(
    f"""
    <div class="main-header">
        <div class="header-inner">
            <div class="header-text">
                <h1>🎓 داشبورد مدیریتی هوشمند دانشگاه‌های زیرنظر واحد گرگان</h1>
                <p>روند دانشجویان فعال، تحلیل بدهی و تقسیط، مقایسه عملکرد دانشگاه‌ها به همراه پیش بینی</p>
            </div>
            <div class="header-logo">
                <img src="{LOGO_URI}" alt="لوگوی دانشگاه آزاد اسلامی" />
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### ⚙️ منابع داده")
    
    repo_files = list_excel_files()
    
    if repo_files:
        def pick_file(label, default_kw, optional=False):
            options = [""] + repo_files if optional else repo_files
            if not options:
                return None
            
            default_idx = 0
            for i, f in enumerate(options):
                if default_kw in f:
                    default_idx = i
                    break
            
            sel = st.selectbox(label, options, index=default_idx, key=f"sel_{label}")
            return read_file_by_name(sel) if sel else None
            
        student_bytes = pick_file("فایل دانشجویان فعال", "uni-proj.xlsx")
        financial_bytes = pick_file("فایل اطلاعات مالی بر اساس بدهی و تقسیط", "uni-proj2.xlsx")
        proj3_bytes = pick_file("فایل آمار ورودی جدید", "uni-proj3.xlsx", optional=True)
        perf_bytes = pick_file("فایل عملکرد مالی بر اساس سود و زیان", "uni-proj4.xlsx", optional=True)
    else:
        student_bytes = None
        financial_bytes = None
        proj3_bytes = None
        perf_bytes = None

if student_bytes is None or financial_bytes is None:
    st.markdown(
        """
        <div class="welcome-box">
            <span class="welcome-icon">📂</span>
            <div class="welcome-title">به داشبورد مدیریتی خوش آمدید</div>
            <div class="welcome-text">
                فایل‌های اکسل مورد نیاز در مخزن یافت نشدند. لطفاً فایل‌های زیر را در مخزن گیت‌هاب قرار دهید:<br>
                • <b>فایل دانشجویان فعال (uni-proj.xlsx)</b><br>
                • <b>فایل اطلاعات مالی بر اساس بدهی و تقسیط (uni-proj2.xlsx)</b>
            </div>
            <div class="welcome-hint">⬅️ پس از قرار دادن فایل‌ها، صفحه را مجدداً بارگذاری کنید</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

try:
    student_sheets = read_workbook(student_bytes)
    financial_sheets = read_workbook(financial_bytes)
except Exception as exc:
    st.error("خواندن فایل اکسل ناموفق بود.")
    with st.expander("جزئیات خطا"):
        st.code(str(exc))
    st.stop()

proj3_sheets = read_workbook(proj3_bytes) if proj3_bytes else {}
perf_sheets = read_workbook(perf_bytes) if perf_bytes else {}

with st.sidebar:
    st.divider()
    student_sheet = st.selectbox(
        "شیت دانشجویان", list(student_sheets.keys()), key="student_sheet"
    )
    financial_sheet = st.selectbox(
        "شیت مالی بر اساس بدهی و تقسیط", list(financial_sheets.keys()), key="financial_sheet"
    )
    proj3_sheet = None
    if proj3_sheets:
        proj3_sheet = st.selectbox(
            "شیت آمار ورودی جدید", list(proj3_sheets.keys()), key="proj3_sheet"
        )
    perf_sheet = None
    if perf_sheets:
        perf_sheet = st.selectbox(
            "شیت عملکرد مالی بر حسب سود و زیان", list(perf_sheets.keys()), key="perf_sheet"
        )

student_raw = student_sheets[student_sheet]
financial_raw = financial_sheets[financial_sheet]

if student_raw.empty or financial_raw.empty:
    st.warning("یکی از شیت‌های انتخاب‌شده خالی است.")
    st.stop()

student_long = extract_student_long(student_raw)
financial_df = extract_financial(financial_raw)

if student_long.empty:
    st.error("داده دانشجویان قابل استخراج نبود.")
    st.stop()

if financial_df.empty:
    st.warning("داده مالی قابل استخراج نبود. ادامه با داده دانشجویان.")

semesters = sorted(student_long["semester_code"].unique())
first_sem = semesters[0]
latest_sem = semesters[-1]

proj3_last_students = {}
proj3_latest_sem = "—"
if proj3_sheets and proj3_sheet:
    try:
        p3_df = extract_student_long(proj3_sheets[proj3_sheet])
        if not p3_df.empty:
            p3_latest = p3_df["semester_code"].max()
            proj3_latest_sem = p3_latest
            p3_latest_df = p3_df[p3_df["semester_code"] == p3_latest]
            proj3_last_students = dict(zip(p3_latest_df["university"], p3_latest_df["students"]))
    except Exception:
        pass

with st.sidebar:
    st.divider()
    st.markdown("### 📅 انتخاب نیمسال‌ها")

    selected_financial_sem = st.selectbox(
        "نیمسال داده مالی",
        options=FINANCIAL_SEMESTER_OPTIONS,
        index=0,
        key="selected_financial_sem",
        help="نیمسال متناظر با داده‌های فایل مالی.",
    )

    selected_prediction_sem = st.selectbox(
        "نیمسال هدف پیش‌بینی",
        options=PREDICTION_SEMESTER_OPTIONS,
        index=0,
        key="selected_prediction_sem",
        help="نیمسالی که پیش‌بینی تعداد دانشجویان برای آن انجام می‌شود.",
    )

prediction_offset = PREDICTION_SEMESTER_OPTIONS.index(selected_prediction_sem)

latest_students = (
    student_long[student_long["semester_code"] == latest_sem]
    [["university", "students"]]
    .rename(columns={"students": "students_latest"})
)
first_students = (
    student_long[student_long["semester_code"] == first_sem]
    [["university", "students"]]
    .rename(columns={"students": "students_first"})
)

combined = latest_students.merge(financial_df, on="university", how="outer")
combined = combined.merge(first_students, on="university", how="left")

if "debt" in combined.columns:
    combined["debt_per_student"] = (
        combined["debt"]
        / combined["students_latest"].where(combined["students_latest"] > 0)
    )

if "installment" in combined.columns and "debt" in combined.columns:
    total_claims = combined["debt"] + combined["installment"]
    combined["installment_share"] = (
        combined["installment"] / total_claims.where(total_claims > 0) * 100
    )

if "not_referred" in combined.columns and "debtor_count" in combined.columns:
    combined["contacted_count"] = (
        combined["debtor_count"] - combined["not_referred"]
    )
    combined["contact_rate"] = (
        combined["contacted_count"]
        / combined["debtor_count"].where(combined["debtor_count"] > 0)
        * 100
    )

if "students_first" in combined.columns:
    base = combined["students_first"].where(combined["students_first"] > 0)
    combined["growth_pct"] = (
        (combined["students_latest"] - combined["students_first"]) / base * 100
    )

combined = combined.sort_values("students_latest", ascending=False).reset_index(drop=True)

universities = combined["university"].tolist()
scope_options = [ALL_SCOPE] + universities
color_map = {
    u: UNIVERSITY_COLORS.get(u, FALLBACK_COLORS[i % len(FALLBACK_COLORS)])
    for i, u in enumerate(universities)
}

if "selected_scope" not in st.session_state:
    st.session_state["selected_scope"] = "گرگان" if "گرگان" in universities else ALL_SCOPE
if st.session_state["selected_scope"] not in scope_options:
    st.session_state["selected_scope"] = (
        "گرگان" if "گرگان" in universities else ALL_SCOPE
    )

with st.sidebar:
    st.divider()
    st.markdown("### 🔎 محدوده نمایش")
    selected_university = st.selectbox(
        "دانشگاه / محدوده",
        scope_options,
        key="selected_scope",
        help="گزینه «کل دانشگاه‌ها» تمام دانشگاه‌ها را در یک نمودار مقایسه می‌کند.",
    )

selected_data = (
    combined
    if selected_university == ALL_SCOPE
    else combined[combined["university"] == selected_university]
)

scope_title = "کل دانشگاه‌ها" if selected_university == ALL_SCOPE else selected_university
is_all_scope = selected_university == ALL_SCOPE

st.markdown(
    f"""
    <div class="section-header">
        📍 نمای مدیریتی: {scope_title}
    </div>
    """,
    unsafe_allow_html=True,
)

total_students = selected_data["students_latest"].sum(min_count=1)
total_debt = selected_data["debt"].sum(min_count=1) if "debt" in selected_data else np.nan
total_installment = (
    selected_data["installment"].sum(min_count=1)
    if "installment" in selected_data else np.nan
)
total_not_referred = (
    selected_data["not_referred"].sum(min_count=1)
    if "not_referred" in selected_data else np.nan
)
total_debtors = (
    selected_data["debtor_count"].sum(min_count=1)
    if "debtor_count" in selected_data else np.nan
)

paired = (
    selected_data.dropna(subset=["students_latest", "debt"])
    if "debt" in selected_data else pd.DataFrame()
)
debt_per_student = (
    paired["debt"].sum() / paired["students_latest"].sum()
    if not paired.empty and paired["students_latest"].sum() > 0
    else np.nan
)

st.markdown(
    '<div class="section-header">📊 شاخص‌های کلیدی</div>',
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        kpi_card(
            f"دانشجویان فعال — نیمسال {latest_sem}",
            fmt_int(total_students), "نفر", "blue",
        ),
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        kpi_card(
            f"مانده بدهی — نیمسال {selected_financial_sem}",
            fmt_rial(total_debt), "ریال", "red",
        ),
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        kpi_card(
            f"مبلغ تقسیط‌شده — نیمسال {selected_financial_sem}",
            fmt_rial(total_installment), "ریال", "green",
        ),
        unsafe_allow_html=True,
    )
with c4:
    st.markdown(
        kpi_card(
            "بدهی سرانه",
            fmt_rial(debt_per_student), "ریال به‌ازای هر دانشجو", "purple",
        ),
        unsafe_allow_html=True,
    )

c5, c6, c7, c8 = st.columns(4)
with c5:
    st.markdown(
        kpi_card(
            "تعداد واحدها" if is_all_scope else "دانشگاه",
            fmt_int(len(selected_data)), "واحد" if is_all_scope else "دانشگاه", "cyan",
        ),
        unsafe_allow_html=True,
    )
with c6:
    st.markdown(
        kpi_card(
            f"تعداد بدهکاران — نیمسال {selected_financial_sem}",
            fmt_int(total_debtors), "نفر", "orange",
        ),
        unsafe_allow_html=True,
    )
with c7:
    st.markdown(
        kpi_card(
            f"عدم مراجعه — نیمسال {selected_financial_sem}",
            fmt_int(total_not_referred), "نفر", "slate",
        ),
        unsafe_allow_html=True,
    )
with c8:
    growth_txt = "—"
    if "growth_pct" in selected_data.columns:
        first_total = selected_data["students_first"].sum(min_count=1)
        if pd.notna(first_total) and first_total > 0 and pd.notna(total_students):
            growth_txt = fmt_pct((total_students - first_total) / first_total * 100)
    st.markdown(
        kpi_card(
            f"رشد از نیمسال {first_sem} تا {latest_sem}",
            growth_txt, "درصد", "green",
        ),
        unsafe_allow_html=True,
    )

st.markdown(
    explain_box(
        "<b>بدهی سرانه</b> به معنای میانگین سهم هر دانشجوی فعال از کل مانده بدهی واحد است.<br>"
        "<b>فرمول:</b> مجموع مانده بدهی ÷ مجموع دانشجویان فعال"
    ),
    unsafe_allow_html=True,
)


tab_overview, tab_trend, tab_financial, tab_compare, tab_fin_perf = st.tabs([
    "📊 نمای کلی",
    "📈 روند دانشجویان",
    "💰 تحلیل مالی",
    "🏛️ مقایسه تفصیلی",
    "📈 خلاصه عملکرد مالی و پیش‌بینی وضعیت",
])


with tab_overview:
    if not is_all_scope:
        st.markdown(
            center_notice(
                "🏛️",
                "این بخش فقط در حالت <b>«کل دانشگاه‌ها»</b> فعال است.<br>"
                "برای مشاهده نمای کلی، از منوی کناری گزینه «کل دانشگاه‌ها» را انتخاب کنید.",
            ),
            unsafe_allow_html=True,
        )
    else:
        left, right = st.columns([1.15, 1])

        with left:
            chart_df = selected_data.dropna(
                subset=["students_first", "students_latest"]
            ).copy()

            if not chart_df.empty:
                overview_long = pd.concat(
                    [
                        chart_df[["university", "students_first"]]
                        .rename(columns={"students_first": "students"})
                        .assign(نیمسال=f"نیمسال {first_sem}"),
                        chart_df[["university", "students_latest"]]
                        .rename(columns={"students_latest": "students"})
                        .assign(نیمسال=f"نیمسال {latest_sem}"),
                    ],
                    ignore_index=True,
                )

                fig = px.bar(
                    overview_long,
                    x="students",
                    y="university",
                    color="نیمسال",
                    orientation="h",
                    barmode="group",
                    text="students",
                    color_discrete_map={
                        f"نیمسال {first_sem}": "#60A5FA",
                        f"نیمسال {latest_sem}": "#1E40AF",
                    },
                )
                fig.update_traces(
                    texttemplate="<b>%{text:,.0f}</b>",
                    textposition="auto",
                    insidetextfont=dict(size=11, color="#FFFFFF", family="Vazirmatn, Tahoma", weight="bold"),
                    outsidetextfont=dict(size=11, color="#0F172A", family="Vazirmatn, Tahoma", weight="bold"),
                )
                fig.update_layout(
                    title=dict(
                        text=f"تعداد دانشجویان در نیمسال {first_sem} و نیمسال {latest_sem}",
                        font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold"),
                    ),
                    xaxis_title="تعداد دانشجو",
                    yaxis_title="دانشگاه",
                    bargap=0.25,
                )
                st.plotly_chart(
                    style_figure(fig, height=max(400, 65 * len(chart_df) + 140)),
                    use_container_width=True,
                )

        with right:
            if "debt" in selected_data.columns:
                pie_df = selected_data.dropna(subset=["debt"]).copy()
                pie_df = pie_df[pie_df["debt"] > 0]

                if not pie_df.empty:
                    fig = px.pie(
                        pie_df,
                        names="university",
                        values="debt",
                        hole=0.62,
                        color="university",
                        color_discrete_map=color_map,
                    )
                    fig.update_traces(
                        textposition="inside",
                        textinfo="percent",
                        textfont=dict(size=14, color="#FFFFFF", family="Vazirmatn, Tahoma", weight="bold"),
                        hovertemplate=(
                            "<b>%{label}</b><br>"
                            "%{value:,.0f} ریال<br>"
                            "%{percent}<extra></extra>"
                        ),
                    )
                    fig.update_layout(
                        title=dict(
                            text="سهم دانشگاه‌ها از مانده بدهی",
                            font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold"),
                        ),
                        showlegend=True,
                        legend=dict(
                            orientation="v", yanchor="middle", y=0.5,
                            xanchor="left", x=1.02,
                            font=dict(size=12, family="Vazirmatn", weight="bold"),
                        ),
                        margin=dict(l=25, r=25, t=60, b=40),
                    )
                    st.plotly_chart(style_figure(fig, 480), use_container_width=True)

        st.markdown(
            '<div class="section-header">📋 جدول خلاصه مدیریتی</div>',
            unsafe_allow_html=True,
        )

        summary_display = pd.DataFrame({
            "دانشگاه": selected_data["university"],
            f"تعداد دانشجویان در نیمسال {first_sem}": selected_data.get(
                "students_first", pd.Series([np.nan] * len(selected_data))
            ).map(fmt_int),
            f"تعداد دانشجویان در نیمسال {latest_sem}": selected_data["students_latest"].map(fmt_int),
            "رشد": selected_data.get(
                "growth_pct", pd.Series([np.nan] * len(selected_data))
            ).map(lambda v: fmt_pct(v) if pd.notna(v) else "—"),
            "بدهی (ریال)": selected_data.get(
                "debt", pd.Series([np.nan] * len(selected_data))
            ).map(fmt_rial),
            "تقسیط (ریال)": selected_data.get(
                "installment", pd.Series([np.nan] * len(selected_data))
            ).map(fmt_rial),
            "بدهی سرانه (ریال)": selected_data.get(
                "debt_per_student", pd.Series([np.nan] * len(selected_data))
            ).map(fmt_rial),
        })
        render_pretty_table(summary_display)


with tab_trend:
    st.markdown(
        '<div class="section-header">📈 روند تعداد دانشجویان — مهرماه و بهمن‌ماه</div>',
        unsafe_allow_html=True,
    )

    trend_scope = student_long.copy()
    if not is_all_scope:
        trend_scope = trend_scope[trend_scope["university"] == selected_university]

    trend_agg = (
        trend_scope.groupby("semester_code", as_index=False)["students"]
        .sum(min_count=1)
        .sort_values("semester_code")
    )

    mehr_data = trend_agg[trend_agg["semester_code"].str.endswith("1")]
    bahman_data = trend_agg[trend_agg["semester_code"].str.endswith("2")]

    if trend_agg.empty:
        st.info("داده‌ای برای نمایش روند موجود نیست.")
    else:
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=mehr_data["semester_code"],
            y=mehr_data["students"],
            name="نیمسال‌های مهرماه",
            mode="lines+markers+text",
            text=mehr_data["students"].map(lambda v: f"<b>{v:,.0f}</b>"),
            textposition="top center",
            textfont=dict(size=11, color="#991B1B", family="Vazirmatn, Tahoma", weight="bold"),
            line=dict(color="#DC2626", width=3),
            marker=dict(size=12, line=dict(width=2, color="#FFFFFF")),
            hovertemplate="<b>%{x}</b><br>مهرماه: %{y:,.0f}<extra></extra>",
        ))

        fig.add_trace(go.Scatter(
            x=bahman_data["semester_code"],
            y=bahman_data["students"],
            name="نیمسال‌های بهمن‌ماه",
            mode="lines+markers+text",
            text=bahman_data["students"].map(lambda v: f"<b>{v:,.0f}</b>"),
            textposition="bottom center",
            textfont=dict(size=11, color="#0E7490", family="Vazirmatn, Tahoma", weight="bold"),
            line=dict(color="#0891B2", width=3),
            marker=dict(size=12, line=dict(width=2, color="#FFFFFF")),
            hovertemplate="<b>%{x}</b><br>بهمن‌ماه: %{y:,.0f}<extra></extra>",
        ))

        fig.update_layout(
            title=dict(
                text=f"روند دانشجویان فعال — {scope_title}",
                font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold"),
            ),
            hovermode="x unified",
            xaxis=dict(
                title="کد نیمسال",
                type="category",
                categoryorder="array",
                categoryarray=list(trend_agg["semester_code"]),
            ),
            yaxis_title="تعداد دانشجو",
        )
        st.plotly_chart(style_figure(fig, 540), use_container_width=True)

    st.markdown(
        '<div class="section-header">🔥 نقشه حرارتی (کد نیمسال × دانشگاه)</div>',
        unsafe_allow_html=True,
    )

    heat_data = student_long.pivot_table(
        index="university",
        columns="semester_code",
        values="students",
        aggfunc="sum",
    ).reindex(columns=semesters)

    if not is_all_scope:
        heat_data = heat_data.loc[[selected_university]]

    heat_height = max(
        500 if is_all_scope else 320,
        80 * len(heat_data) + 220,
    )

    fig = px.imshow(
        heat_data,
        text_auto=".0f",
        aspect="auto",
        color_continuous_scale=[
            [0.0, "#EFF6FF"],
            [0.25, "#BFDBFE"],
            [0.5, "#60A5FA"],
            [0.75, "#2563EB"],
            [1.0, "#1E3A8A"],
        ],
        labels=dict(x="کد نیمسال", y="دانشگاه", color="تعداد"),
    )
    fig.update_traces(
        textfont=dict(size=14, family="Vazirmatn, Tahoma", color="#0F172A", weight="bold"),
        xgap=3, ygap=3,
    )
    fig.update_layout(
        title=dict(
            text="توزیع تعداد دانشجو در نیمسال‌ها و دانشگاه‌ها",
            font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold"),
        ),
        margin=dict(l=25, r=25, t=60, b=50),
        coloraxis_colorbar=dict(
            title=dict(text="تعداد", font=dict(size=12, weight="bold")),
            thickness=14, len=0.75,
            tickfont=dict(size=11, weight="bold"),
        ),
    )
    fig.update_xaxes(
        tickangle=0,
        tickfont=dict(size=12, family="Vazirmatn", weight="bold"),
        side="bottom",
    )
    fig.update_yaxes(
        tickfont=dict(size=13, family="Vazirmatn", weight="bold"),
    )
    st.plotly_chart(
        style_figure(fig, heat_height),
        use_container_width=True,
    )

    st.markdown(
        '<div class="section-header">📊 تحلیل رشد/افت دانشجویان</div>',
        unsafe_allow_html=True,
    )

    growth_source = combined.copy()
    if not is_all_scope:
        growth_source = growth_source[growth_source["university"] == selected_university]

    growth_df = growth_source[
        ["university", "students_first", "students_latest", "growth_pct"]
    ].copy()
    growth_df.columns = [
        "دانشگاه",
        f"نیمسال {first_sem}",
        f"نیمسال {latest_sem}",
        "رشد (%)",
    ]

    def color_growth(val):
        if pd.isna(val):
            return "—"
        if val > 0:
            return f'<span style="color:#059669; font-weight:800;">{val:+.1f}%</span>'
        if val < 0:
            return f'<span style="color:#DC2626; font-weight:800;">{val:+.1f}%</span>'
        return f'<span style="color:#64748B; font-weight:700;">{val:+.1f}%</span>'

    growth_display = pd.DataFrame({
        "دانشگاه": growth_df["دانشگاه"],
        f"نیمسال {first_sem}": growth_df[f"نیمسال {first_sem}"].map(fmt_int),
        f"نیمسال {latest_sem}": growth_df[f"نیمسال {latest_sem}"].map(fmt_int),
        "رشد (%)": growth_df["رشد (%)"].map(color_growth),
    })
    render_pretty_table(growth_display)

    st.markdown(
        f'<div class="section-header">🔮 پیش‌بینی تعداد دانشجویان برای نیمسال {selected_prediction_sem}</div>',
        unsafe_allow_html=True,
    )

    prediction_universities = universities if is_all_scope else [selected_university]

    prediction_records = []
    for uni in prediction_universities:
        uni_series = student_long[
            student_long["university"] == uni
        ].sort_values("semester_code")

        y = uni_series["students"].values.astype(float)
        if len(y) >= 2:
            x = np.arange(len(y))
            slope, intercept = np.polyfit(x, y, 1)
            predicted = slope * (len(y) + prediction_offset) + intercept
        else:
            predicted = np.nan

        last_students_val = proj3_last_students.get(uni, y[-1] if len(y) else np.nan)

        prediction_records.append({
            "university": uni,
            "last_students": int(last_students_val) if pd.notna(last_students_val) else np.nan,
            "predicted": int(round(predicted)) if pd.notna(predicted) else np.nan,
        })

    st.markdown(
        sub_header("✍️ ورود مقدار واقعی توسط ادمین"),
        unsafe_allow_html=True,
    )

    header_labels = [
        "دانشگاه",
        f"آخرین تعداد ورودی جدید دانشجویان ({proj3_latest_sem})",
        f"پیش‌بینی نیمسال {selected_prediction_sem}",
        "واقعی (ورودی ادمین)",
    ]

    header_cols = st.columns([1.6, 1.8, 1.6, 1.8], gap="small")
    for i, label in enumerate(header_labels):
        with header_cols[i]:
            st.markdown(
                f'<div class="admin-grid-header">{label}</div>',
                unsafe_allow_html=True,
            )

    actual_values = {}
    for idx, rec in enumerate(prediction_records):
        row_cols = st.columns([1.6, 1.8, 1.6, 1.8], gap="small")
        zebra = "zebra" if idx % 2 == 1 else ""

        with row_cols[0]:
            st.markdown(
                f'<div class="admin-grid-cell {zebra}">{rec["university"]}</div>',
                unsafe_allow_html=True,
            )
        with row_cols[1]:
            st.markdown(
                f'<div class="admin-grid-cell {zebra}">{fmt_int(rec["last_students"])}</div>',
                unsafe_allow_html=True,
            )
        with row_cols[2]:
            st.markdown(
                f'<div class="admin-grid-cell {zebra}">{fmt_int(rec["predicted"])}</div>',
                unsafe_allow_html=True,
            )
        with row_cols[3]:
            actual_values[rec["university"]] = st.number_input(
                f"واقعی — {rec['university']}",
                min_value=0,
                value=0,
                step=1,
                key=f"actual_{rec['university']}_{selected_university}_{selected_prediction_sem}",
                label_visibility="collapsed",
            )

    computed = pd.DataFrame([
        {
            "دانشگاه": r["university"],
            "پیش‌بینی": r["predicted"],
            "واقعی": actual_values.get(r["university"], 0),
        }
        for r in prediction_records
    ])

    computed["خطا"] = computed["واقعی"] - computed["پیش‌بینی"]
    computed["خطای نسبی (%)"] = np.where(
        computed["واقعی"] > 0,
        computed["خطا"] / computed["واقعی"] * 100,
        np.nan,
    )
    computed["دقت (%)"] = 100 - computed["خطای نسبی (%)"].abs()

    st.markdown(
        sub_header("📊 نتیجه مقایسه پیش‌بینی با مقدار واقعی"),
        unsafe_allow_html=True,
    )

    def get_closeness_label(actual, pred):
        if pd.isna(actual) or pd.isna(pred) or actual == 0:
            return "—"
        diff_ratio = abs(actual - pred) / actual
        if diff_ratio <= 0.05:
            return '<span style="color:#059669; font-weight:800;">بسیار نزدیک</span>'
        if diff_ratio <= 0.15:
            return '<span style="color:#D97706; font-weight:800;">نزدیک</span>'
        return '<span style="color:#DC2626; font-weight:800;">دور از پیش‌بینی</span>'

    computed_display = pd.DataFrame({
        "دانشگاه": computed["دانشگاه"],
        "پیش‌بینی": computed["پیش‌بینی"].map(fmt_int),
        "واقعی": computed["واقعی"].map(fmt_int),
        "وضعیت مقدار واقعی به مقدار پیش بینی شده": [
            get_closeness_label(row["واقعی"], row["پیش‌بینی"]) for _, row in computed.iterrows()
        ],
    })
    render_pretty_table(computed_display)

    valid_rows = computed[computed["واقعی"] > 0]

    if not valid_rows.empty:
        st.markdown(
            sub_header("📊 نمودار مقایسه پیش‌بینی و مقدار واقعی"),
            unsafe_allow_html=True,
        )

        chart_pred = pd.DataFrame(
            [
                {"دانشگاه": r["دانشگاه"], "نوع": "پیش‌بینی", "تعداد": r["پیش‌بینی"]}
                for _, r in valid_rows.iterrows()
            ] + [
                {"دانشگاه": r["دانشگاه"], "نوع": "واقعی", "تعداد": r["واقعی"]}
                for _, r in valid_rows.iterrows()
            ]
        )

        fig = px.bar(
            chart_pred,
            x="دانشگاه",
            y="تعداد",
            color="نوع",
            barmode="group",
            text="تعداد",
            color_discrete_map={"پیش‌بینی": "#3B82F6", "واقعی": "#059669"},
        )
        fig.update_traces(
            texttemplate="<b>%{text:,.0f}</b>",
            textposition="auto",
            insidetextfont=dict(size=12, color="#FFFFFF", family="Vazirmatn, Tahoma", weight="bold"),
            outsidetextfont=dict(size=12, color="#0F172A", family="Vazirmatn, Tahoma", weight="bold"),
        )
        fig.update_layout(
            title=dict(
                text=f"پیش‌بینی در مقابل مقدار واقعی — نیمسال {selected_prediction_sem}",
                font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold"),
            ),
            xaxis_title="دانشگاه",
            yaxis_title="تعداد دانشجو",
            bargap=0.3,
        )
        st.plotly_chart(style_figure(fig, 460), use_container_width=True)
    else:
        st.markdown(
            rtl_alert(
                "برای محاسبه دقت پیش‌بینی، لطفاً مقدار «واقعی» هر دانشگاه را "
                "در فیلدهای بالا وارد کنید."
            ),
            unsafe_allow_html=True,
        )


with tab_financial:
    if "debt" not in selected_data.columns:
        st.info("داده بدهی در فایل مالی شناسایی نشد.")
    else:
        st.markdown(
            f"""
            <div class="section-header">
                💰 تحلیل مالی
                <span class="badge badge-orange">نیمسال {selected_financial_sem}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        left, right = st.columns(2)

        with left:
            fin_df = selected_data.dropna(subset=["debt"]).copy()
            fin_df = fin_df.sort_values("debt", ascending=True)

            fig = go.Figure()
            fig.add_bar(
                name="مانده بدهی",
                y=fin_df["university"],
                x=fin_df["debt"],
                orientation="h",
                marker=dict(color="#DC2626", line=dict(width=0)),
                text=fin_df["debt"].map(lambda v: f"<b>{v:,.0f}</b>"),
                textposition="auto",
                insidetextfont=dict(size=10, color="#FFFFFF", family="Vazirmatn, Tahoma", weight="bold"),
                outsidetextfont=dict(size=10, color="#991B1B", family="Vazirmatn, Tahoma", weight="bold"),
                hovertemplate="<b>%{y}</b><br>بدهی: %{x:,.0f} ریال<extra></extra>",
            )
            if "installment" in fin_df.columns:
                fig.add_bar(
                    name="مبلغ تقسیط‌شده",
                    y=fin_df["university"],
                    x=fin_df["installment"],
                    orientation="h",
                    marker=dict(color="#059669", line=dict(width=0)),
                    text=fin_df["installment"].map(lambda v: f"<b>{v:,.0f}</b>"),
                    textposition="auto",
                    insidetextfont=dict(size=10, color="#FFFFFF", family="Vazirmatn, Tahoma", weight="bold"),
                    outsidetextfont=dict(size=10, color="#065F46", family="Vazirmatn, Tahoma", weight="bold"),
                    hovertemplate="<b>%{y}</b><br>تقسیط: %{x:,.0f} ریال<extra></extra>",
                )
            fig.update_layout(
                title=dict(
                    text="مقایسه بدهی و تقسیط (ریال)",
                    font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold"),
                ),
                barmode="group",
                xaxis_title="ریال",
                yaxis_title="دانشگاه",
                bargap=0.3,
                margin=dict(l=25, r=200, t=70, b=55),
            )
            st.plotly_chart(
                style_figure(fig, max(440, 65 * len(fin_df) + 160)),
                use_container_width=True,
            )

        with right:
            per_capita = selected_data.dropna(subset=["debt_per_student"]).copy()
            per_capita = per_capita.sort_values("debt_per_student")

            if not per_capita.empty:
                per_capita_display = per_capita["debt_per_student"] / 1_000_000
                fig = px.bar(
                    per_capita,
                    x=per_capita_display,
                    y="university",
                    orientation="h",
                    labels={
                        "x": "میلیون ریال به‌ازای هر دانشجو",
                        "university": "دانشگاه",
                    },
                    color="university",
                    color_discrete_map=color_map,
                    text=per_capita_display.map(lambda v: f"<b>{v:,.1f}</b>"),
                )
                fig.update_traces(
                    textposition="auto",
                    insidetextfont=dict(size=11, color="#FFFFFF", family="Vazirmatn, Tahoma", weight="bold"),
                    outsidetextfont=dict(size=11, color="#0F172A", family="Vazirmatn, Tahoma", weight="bold"),
                )
                fig.update_layout(
                    title=dict(
                        text="بدهی سرانه هر دانشجو (میلیون ریال)",
                        font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold"),
                    ),
                    showlegend=False,
                    bargap=0.35,
                    xaxis_title="میلیون ریال",
                    yaxis_title="دانشگاه",
                    margin=dict(l=25, r=140, t=70, b=55),
                )
                st.plotly_chart(
                    style_figure(fig, max(440, 65 * len(per_capita) + 160)),
                    use_container_width=True,
                )

        st.markdown(
            '<div class="section-header">📐 شاخص‌های تحلیلی مالی</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            explain_box(
                "<b>۱) سهم تقسیط از کل مطالبات:</b> نسبتی از مطالبات دانشگاه "
                "(بدهی + تقسیط) که به اقساط تبدیل شده است.<br>"
                "<b>فرمول:</b> تقسیط ÷ (بدهی + تقسیط) × ۱۰۰<br><br>"
                "<b>۲) نرخ مراجعه بدهکاران:</b> نسبتی از بدهکاران که مراجعه کرده‌اند "
                "(معادل ۱۰۰ منهای نسبت «عدم مراجعه»).<br>"
                "<b>فرمول:</b> (تعداد بدهکاران − عدم مراجعه) ÷ تعداد بدهکاران × ۱۰۰"
            ),
            unsafe_allow_html=True,
        )

        a1, a2 = st.columns(2)

        with a1:
            inst_df = selected_data.dropna(subset=["installment_share"]).copy()
            inst_df = inst_df.sort_values("installment_share")

            if not inst_df.empty:
                fig = px.bar(
                    inst_df,
                    x="installment_share",
                    y="university",
                    orientation="h",
                    color="university",
                    color_discrete_map=color_map,
                    labels={"installment_share": "درصد", "university": "دانشگاه"},
                    text=inst_df["installment_share"].map(lambda v: f"<b>{v:.1f}%</b>"),
                )
                fig.update_traces(
                    textposition="auto",
                    insidetextfont=dict(size=12, color="#FFFFFF", family="Vazirmatn, Tahoma", weight="bold"),
                    outsidetextfont=dict(size=12, color="#0F172A", family="Vazirmatn, Tahoma", weight="bold"),
                )
                fig.update_layout(
                    title=dict(
                        text="سهم تقسیط از کل مطالبات (٪)",
                        font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold"),
                    ),
                    showlegend=False,
                    bargap=0.35,
                    xaxis=dict(range=[0, 100], title="درصد"),
                    yaxis=dict(title="دانشگاه"),
                    margin=dict(l=25, r=140, t=70, b=55),
                )
                st.plotly_chart(
                    style_figure(fig, max(440, 65 * len(inst_df) + 160)),
                    use_container_width=True,
                )

        with a2:
            contact_df = selected_data.dropna(subset=["contact_rate"]).copy()
            contact_df = contact_df.sort_values("contact_rate")

            if not contact_df.empty:
                contact_min = float(contact_df["contact_rate"].min())
                contact_max = float(contact_df["contact_rate"].max())

                x_min = min(0, contact_min) - 20
                x_max = max(100, contact_max) + 20

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    y=contact_df["university"],
                    x=contact_df["contact_rate"],
                    orientation="h",
                    marker=dict(
                        color=[color_map.get(u, "#3B82F6") for u in contact_df["university"]],
                        line=dict(width=0),
                    ),
                    text=[f"<b>{v:.1f}%</b>" for v in contact_df["contact_rate"]],
                    textposition="auto",
                    insidetextfont=dict(size=14, family="Vazirmatn, Tahoma", color="#FFFFFF", weight="bold"),
                    outsidetextfont=dict(size=14, family="Vazirmatn, Tahoma", color="#0F172A", weight="bold"),
                    hovertemplate="<b>%{y}</b><br>نرخ مراجعه: %{x:.1f}%<extra></extra>",
                ))

                fig.add_vline(x=0, line=dict(color="#64748B", width=1.2, dash="dash"))
                fig.add_vline(x=100, line=dict(color="#94A3B8", width=1, dash="dot"))

                fig.update_layout(
                    title=dict(
                        text="نرخ مراجعه بدهکاران (٪)",
                        font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold"),
                    ),
                    showlegend=False,
                    bargap=0.45,
                    xaxis=dict(
                        title="درصد",
                        range=[x_min, x_max],
                        tickfont=dict(size=12, weight="bold"),
                        zeroline=False,
                        showticklabels=True,
                    ),
                    yaxis=dict(
                        title="دانشگاه",
                        tickfont=dict(size=14, family="Vazirmatn", weight="bold"),
                        automargin=True,
                    ),
                    margin=dict(l=25, r=140, t=70, b=55),
                )
                st.plotly_chart(
                    style_figure(fig, max(460, 70 * len(contact_df) + 180)),
                    use_container_width=True,
                )

        st.markdown(
            '<div class="section-header">📋 جدول تفصیلی مالی</div>',
            unsafe_allow_html=True,
        )
        fin_table = pd.DataFrame({"دانشگاه": selected_data["university"]})

        def safe_col(col):
            return selected_data[col] if col in selected_data.columns \
                else pd.Series([np.nan] * len(selected_data))

        fin_table["مانده بدهی (ریال)"] = safe_col("debt").map(fmt_rial)
        fin_table["تقسیط (ریال)"] = safe_col("installment").map(fmt_rial)
        fin_table["تعداد بدهکار"] = safe_col("debtor_count").map(fmt_int)
        fin_table["عدم مراجعه"] = safe_col("not_referred").map(fmt_int)
        fin_table["بدهی سرانه (ریال)"] = safe_col("debt_per_student").map(fmt_rial)
        fin_table["سهم تقسیط از مطالبات"] = safe_col("installment_share").map(
            lambda v: f"{v:.1f}%" if pd.notna(v) else "—"
        )
        fin_table["نرخ مراجعه بدهکاران"] = safe_col("contact_rate").map(
            lambda v: f"{v:.1f}%" if pd.notna(v) else "—"
        )
        render_pretty_table(fin_table)


with tab_compare:
    st.markdown(
        '<div class="section-header">📊 پراکندگی دانشجویان و مانده بدهی (مقایسه تفصیلی)</div>',
        unsafe_allow_html=True,
    )

    if "debt" in selected_data.columns:
        scatter = selected_data.dropna(subset=["students_latest", "debt"]).copy()

        if not scatter.empty:
            fig = px.scatter(
                scatter,
                x="students_latest",
                y="debt",
                color="university",
                text="university",
                labels={
                    "students_latest": "تعداد دانشجویان فعال",
                    "debt": "مانده بدهی (ریال)",
                    "university": "دانشگاه",
                },
                color_discrete_map=color_map,
            )
            fig.update_traces(
                textposition="top center",
                textfont=dict(size=13, family="Vazirmatn, Tahoma", color="#0F172A", weight="bold"),
                marker=dict(size=14, line=dict(width=2, color="#FFFFFF")),
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "دانشجو: %{x:,.0f}<br>"
                    "بدهی: %{y:,.0f} ریال<extra></extra>"
                ),
            )
            fig.update_layout(
                title=dict(
                    text="رابطه تعداد دانشجو و مانده بدهی",
                    font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold"),
                ),
                showlegend=True,
                margin=dict(l=25, r=25, t=60, b=55),
                xaxis_title="تعداد دانشجویان فعال",
                yaxis_title="مانده بدهی (ریال)",
            )
            st.plotly_chart(style_figure(fig, 500), use_container_width=True)

    st.markdown(
        '<div class="section-header">📋 جدول یکپارچه (دانشجو + مالی)</div>',
        unsafe_allow_html=True,
    )

    first_students_total = selected_data["students_first"].sum(min_count=1) \
        if "students_first" in selected_data.columns else np.nan
    latest_students_total = selected_data["students_latest"].sum(min_count=1)

    debt_per_student_first = np.nan
    debt_per_student_latest = np.nan

    if "debt" in selected_data.columns and pd.notna(total_debt):
        if pd.notna(first_students_total) and first_students_total > 0:
            debt_per_student_first = total_debt / first_students_total
        if pd.notna(latest_students_total) and latest_students_total > 0:
            debt_per_student_latest = total_debt / latest_students_total

    unified_rows = [
        {
            "تعداد دانشجویان": fmt_int(latest_students_total),
            "مانده بدهی (ریال)": fmt_rial(total_debt),
            "تقسیط (ریال)": fmt_rial(total_installment),
            "تعداد بدهکار": fmt_int(total_debtors),
            "عدم مراجعه": fmt_int(total_not_referred),
            f"بدهی سرانه (ریال) - نیمسال {first_sem}": fmt_rial(debt_per_student_first),
            f"بدهی سرانه (ریال) - نیمسال {latest_sem}": fmt_rial(debt_per_student_latest),
        }
    ]

    unified_table = pd.DataFrame(unified_rows)
    render_pretty_table(unified_table)

    st.markdown(
        '<div class="section-header">📥 خروجی گزارش</div>',
        unsafe_allow_html=True,
    )

    excel_content = make_excel({
        "خلاصه یکپارچه": unified_table,
        "روند دانشجویان": student_long.pivot_table(
            index="university",
            columns="semester_code",
            values="students",
            aggfunc="sum",
        ).reset_index(),
        "داده مالی": financial_df,
    })

    col_dl1, _ = st.columns([1, 3])
    with col_dl1:
        st.download_button(
            "📥 دانلود گزارش Excel",
            data=excel_content,
            file_name="university_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


with tab_fin_perf:
    if selected_university != "بندرترکمن":
        st.markdown(
            center_notice(
                "📍",
                "این بخش در حال حاضر فقط برای مرکز <b>بندرترکمن</b> قابل محاسبه و نمایش است.<br>"
                "لطفاً از منوی کناری، دانشگاه بندرترکمن را انتخاب کنید."
            ),
            unsafe_allow_html=True,
        )
    elif not (perf_sheets and perf_sheet):
        st.info(
            "فایل اطلاعات عملکرد مالی (uni-proj4.xlsx) یافت نشد یا شیت آن انتخاب نشده است. "
            "لطفاً آن را در کنار فایل اصلی قرار دهید یا از منوی کناری آپلود و انتخاب کنید."
        )
    else:
        perf_data = extract_perf_data(perf_sheets[perf_sheet])
        
        if perf_data:
            st.markdown(
                '<div class="section-header">📈 خلاصه عملکرد مالی و پیش‌بینی وضعیت</div>',
                unsafe_allow_html=True,
            )

            # ---------- بخش اول: نمودارهای درآمد و هزینه (عملکرد 1405-1404) ----------
            st.markdown(sub_header("📊 عملکرد 1405-1404"), unsafe_allow_html=True)
            
            col_inc_hist, col_exp_hist = st.columns(2)
            
            with col_inc_hist:
                inc_labels = [
                    perf_data["in_tuition"]["title"],
                    perf_data["in_outsourcing"]["title"],
                    perf_data["in_workshop"]["title"],
                    perf_data["in_total"]["title"],
                ]
                inc_vals = [
                    perf_data["in_tuition"]["hist"],
                    perf_data["in_outsourcing"]["hist"],
                    perf_data["in_workshop"]["hist"],
                    perf_data["in_total"]["hist"],
                ]
                x_ticks = ["۱", "۲", "۳", "۴"]
                
                fig_inc_hist = go.Figure(go.Bar(
                    x=inc_vals,
                    y=x_ticks,
                    orientation="h",
                    text=inc_vals,
                    texttemplate="%{text:,.0f}",
                    textposition="outside",
                    textfont=dict(size=14, color="#0F172A", family="Vazirmatn", weight="bold"),
                    marker_color="#1E40AF",
                    cliponaxis=False
                ))
                fig_inc_hist.update_layout(
                    title=dict(
                        text="نمودار درآمدها (ریال) - عملکرد 1405-1404",
                        font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")
                    ),
                    xaxis=dict(title="ریال", tickformat=","),
                    yaxis=dict(title="ردیف", type="category", autorange="reversed"),
                    showlegend=False,
                    margin=dict(l=60, r=80, t=60, b=40)
                )
                st.plotly_chart(style_figure(fig_inc_hist, 400), use_container_width=True)
                
                guide_html = "<div style='font-size:13px; color:#475569; direction:rtl; margin-top:-15px; line-height:1.6;'>"
                guide_html += "<b>راهنما:</b> "
                guide_html += " | ".join([f"<b>{i+1}</b>: {label}" for i, label in enumerate(inc_labels)])
                guide_html += "</div>"
                st.markdown(guide_html, unsafe_allow_html=True)

            with col_exp_hist:
                exp_labels = [
                    perf_data["ex_faculty"]["title"],
                    perf_data["ex_official"]["title"],
                    perf_data["ex_corporate"]["title"],
                    perf_data["ex_guest"]["title"],
                    perf_data["ex_rent"]["title"],
                    perf_data["ex_other"]["title"],
                    perf_data["ex_total"]["title"],
                ]
                exp_vals = [
                    perf_data["ex_faculty"]["hist"],
                    perf_data["ex_official"]["hist"],
                    perf_data["ex_corporate"]["hist"],
                    perf_data["ex_guest"]["hist"],
                    perf_data["ex_rent"]["hist"],
                    perf_data["ex_other"]["hist"],
                    perf_data["ex_total"]["hist"],
                ]
                x_ticks_exp = ["۱", "۲", "۳", "۴", "۵", "۶", "۷"]
                
                fig_exp_hist = go.Figure(go.Bar(
                    x=exp_vals,
                    y=x_ticks_exp,
                    orientation="h",
                    text=exp_vals,
                    texttemplate="%{text:,.0f}",
                    textposition="outside",
                    textfont=dict(size=14, color="#0F172A", family="Vazirmatn", weight="bold"),
                    marker_color="#DC2626",
                    cliponaxis=False
                ))
                fig_exp_hist.update_layout(
                    title=dict(
                        text="نمودار هزینه‌ها (ریال) - عملکرد 1405-1404",
                        font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")
                    ),
                    xaxis=dict(title="ریال", tickformat=","),
                    yaxis=dict(title="ردیف", type="category", autorange="reversed"),
                    showlegend=False,
                    margin=dict(l=60, r=80, t=60, b=40)
                )
                st.plotly_chart(style_figure(fig_exp_hist, 450), use_container_width=True)
                
                guide_html_exp = "<div style='font-size:13px; color:#475569; direction:rtl; margin-top:-15px; line-height:1.6;'>"
                guide_html_exp += "<b>راهنما:</b> "
                guide_html_exp += " | ".join([f"<b>{i+1}</b>: {label}" for i, label in enumerate(exp_labels)])
                guide_html_exp += "</div>"
                st.markdown(guide_html_exp, unsafe_allow_html=True)

            # ---------- بخش دوم: نمودارهای درآمد و هزینه (وضعیت فعلی 1406-1405) ----------
            st.markdown(sub_header("📊 وضعیت فعلی 1406-1405"), unsafe_allow_html=True)
            
            col_inc_curr, col_exp_curr = st.columns(2)
            
            with col_inc_curr:
                inc_curr_vals = [
                    perf_data["in_tuition"]["curr"],
                    perf_data["in_outsourcing"]["curr"],
                    perf_data["in_workshop"]["curr"],
                    perf_data["in_total"]["curr"],
                ]
                
                fig_inc_curr = go.Figure(go.Bar(
                    x=inc_curr_vals,
                    y=x_ticks,
                    orientation="h",
                    text=inc_curr_vals,
                    texttemplate="%{text:,.0f}",
                    textposition="outside",
                    textfont=dict(size=14, color="#0F172A", family="Vazirmatn", weight="bold"),
                    marker_color="#0E7490",
                    cliponaxis=False
                ))
                fig_inc_curr.update_layout(
                    title=dict(
                        text="نمودار درآمدها (ریال) - وضعیت فعلی 1406-1405",
                        font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")
                    ),
                    xaxis=dict(title="ریال", tickformat=","),
                    yaxis=dict(title="ردیف", type="category", autorange="reversed"),
                    showlegend=False,
                    margin=dict(l=60, r=80, t=60, b=40)
                )
                st.plotly_chart(style_figure(fig_inc_curr, 400), use_container_width=True)
                
                guide_html_curr = "<div style='font-size:13px; color:#475569; direction:rtl; margin-top:-15px; line-height:1.6;'>"
                guide_html_curr += "<b>راهنما:</b> "
                guide_html_curr += " | ".join([f"<b>{i+1}</b>: {label}" for i, label in enumerate(inc_labels)])
                guide_html_curr += "</div>"
                st.markdown(guide_html_curr, unsafe_allow_html=True)

            with col_exp_curr:
                exp_curr_vals = [
                    perf_data["ex_faculty"]["curr"],
                    perf_data["ex_official"]["curr"],
                    perf_data["ex_corporate"]["curr"],
                    perf_data["ex_guest"]["curr"],
                    perf_data["ex_rent"]["curr"],
                    perf_data["ex_other"]["curr"],
                    perf_data["ex_total"]["curr"],
                ]
                
                fig_exp_curr = go.Figure(go.Bar(
                    x=exp_curr_vals,
                    y=x_ticks_exp,
                    orientation="h",
                    text=exp_curr_vals,
                    texttemplate="%{text:,.0f}",
                    textposition="outside",
                    textfont=dict(size=14, color="#0F172A", family="Vazirmatn", weight="bold"),
                    marker_color="#D97706",
                    cliponaxis=False
                ))
                fig_exp_curr.update_layout(
                    title=dict(
                        text="نمودار هزینه‌ها (ریال) - وضعیت فعلی 1406-1405",
                        font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")
                    ),
                    xaxis=dict(title="ریال", tickformat=","),
                    yaxis=dict(title="ردیف", type="category", autorange="reversed"),
                    showlegend=False,
                    margin=dict(l=60, r=80, t=60, b=40)
                )
                st.plotly_chart(style_figure(fig_exp_curr, 450), use_container_width=True)
                
                guide_html_exp_curr = "<div style='font-size:13px; color:#475569; direction:rtl; margin-top:-15px; line-height:1.6;'>"
                guide_html_exp_curr += "<b>راهنما:</b> "
                guide_html_exp_curr += " | ".join([f"<b>{i+1}</b>: {label}" for i, label in enumerate(exp_labels)])
                guide_html_exp_curr += "</div>"
                st.markdown(guide_html_exp_curr, unsafe_allow_html=True)

            # ---------- بخش سوم: جدول پیش‌بینی با رگرسیون و محاسبه وضعیت ----------
            st.markdown(
                '<div class="section-header">📋 جدول پیش‌بینی و وضعیت</div>',
                unsafe_allow_html=True,
            )
            
            pred_col_name = f"پیش‌بینی {selected_prediction_sem}"
            rows = []
            for key in ["in_tuition", "in_outsourcing", "in_workshop", "in_total", 
                        "ex_faculty", "ex_official", "ex_corporate", "ex_guest", "ex_rent", "ex_other", "ex_total"]:
                title = perf_data[key]["title"]
                hist = perf_data[key]["hist"]
                curr = perf_data[key]["curr"]
                
                # الگوریتم رگرسیون: چون فقط یک نقطه تاریخی (hist) داریم، پیش‌بینی = hist
                pred = hist
                
                error = curr - pred
                
                if curr == 0:
                    status_str = '<span style="color:#7C3AED; font-weight:800;">—</span>'
                elif abs(error) / curr < 0.05:
                    status_str = '<span style="color:#7C3AED; font-weight:800;">مطابق پیش‌بینی</span>'
                elif error > 0:
                    status_str = f'<span style="color:#7C3AED; font-weight:800;">بیشتر از پیش‌بینی ({error:+,.0f})</span>'
                else:
                    status_str = f'<span style="color:#7C3AED; font-weight:800;">کمتر از پیش‌بینی ({error:+,.0f})</span>'

                pred_str = f'<span style="color:#7C3AED; font-weight:800;">{pred:,.0f}</span>'

                if "مجموع درآمد" in title:
                    title_display = f'<span style="color:#1E40AF; font-weight:800;">{title}</span>'
                elif "مجموع هزینه" in title:
                    title_display = f'<span style="color:#DC2626; font-weight:800;">{title}</span>'
                else:
                    title_display = title

                rows.append({
                    "شرح": title_display,
                    "عملکرد 1405-1404": fmt_rial(hist),
                    "وضعیت فعلی 1406-1405": fmt_rial(curr),
                    pred_col_name: pred_str,
                    "وضعیت فعلی نسبت به پیش‌بینی": status_str
                })
                
            pred_df = pd.DataFrame(rows)
            render_pretty_table(pred_df)

            # ---------- بخش چهارم: نمودار سود و زیان ----------
            st.markdown(
                '<div class="section-header">📊 نمودار سود و زیان</div>',
                unsafe_allow_html=True,
            )
            
            pl_labels = ["عملکرد 1405-1404", "وضعیت فعلی 1406-1405"]
            pl_vals = [
                perf_data["profit"]["hist"],
                perf_data["profit"]["curr"],
            ]
            
            fig_pl = go.Figure(go.Bar(
                x=pl_vals,
                y=pl_labels,
                orientation="h",
                text=pl_vals,
                texttemplate="%{text:,.0f}",
                textposition="outside",
                textfont=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold"),
                marker_color="#3B82F6",
                cliponaxis=False
            ))
            
            fig_pl.update_layout(
                title=dict(
                    text="مقایسه سود و زیان (ریال)",
                    font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")
                ),
                xaxis=dict(title="ریال", tickformat=","),
                yaxis=dict(title="بازه زمانی", type="category", autorange="reversed"),
                showlegend=False,
                margin=dict(l=120, r=80, t=60, b=40)
            )
            st.plotly_chart(style_figure(fig_pl, 250), use_container_width=True)


st.divider()
st.caption(
    "داشبورد مدیریتی هوشمند دانشگاه‌های زیرنظر واحد گرگان — "
    "داده‌ها از فایل‌های اکسل انتخاب‌شده استخراج می‌شوند."
)