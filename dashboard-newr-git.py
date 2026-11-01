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
import requests
import streamlit as st

st.set_page_config(
    page_title="داشبورد مدیریتی هوشمند مراکز آموزشی دانشگاه آزاد اسلامی استان گلستان",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
DIGIT_TRANSLATION = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
TOTAL_LABELS = {"مجموع", "جمع", "جمع کل", "کل", "کل مجموعه", "کلمجموعه", "مجموعه", "total"}
UNIVERSITY_COLORS = {
    "گرگان": "#1E40AF", "کردکوی": "#059669", "آق قلا": "#0E7490", "بندرترکمن": "#D97706",
    "گمیشان": "#7C3AED", "کلاله": "#DC2626", "گالیکش": "#DB2777", "مینودشت": "#0D9488",
}
KNOWN_UNIVERSITIES = list(UNIVERSITY_COLORS.keys())
FALLBACK_COLORS = ["#1E40AF", "#059669", "#0E7490", "#D97706", "#7C3AED", "#DC2626", "#DB2777", "#0D9488"]
FINANCIAL_SEMESTER_OPTIONS = ["4054061"]
PREDICTION_SEMESTER_OPTIONS = ["4054061", "4054062", "4054063"]
GITHUB_REPO_OWNER = "shidehsaraeian-ctrl"
GITHUB_REPO_NAME = "university-dashboard"
GITHUB_BRANCH = "main"

FALLBACK_LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.95"/><stop offset="100%" stop-color="#DBEAFE" stop-opacity="0.85"/></linearGradient></defs><circle cx="60" cy="60" r="52" fill="url(#g)" opacity="0.18"/><circle cx="60" cy="60" r="42" fill="none" stroke="white" stroke-width="2.5" opacity="0.85"/><path d="M35 55 L60 42 L85 55 L60 68 Z" fill="white" opacity="0.95"/><path d="M42 60 L42 74 Q60 84 78 74 L78 60" fill="none" stroke="white" stroke-width="2.5" stroke-linejoin="round"/><circle cx="60" cy="55" r="3" fill="#1E40AF"/><text x="60" y="98" font-family="Arial" font-size="12" font-weight="700" text-anchor="middle" fill="white" opacity="0.95">IAU</text></svg>"""

def get_logo_data_uri() -> str:
    for ext, mime in {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "svg": "image/svg+xml", "webp": "image/webp"}.items():
        path = BASE_DIR / f"azad-logo.{ext}"
        if path.exists():
            return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"
    return f"data:image/svg+xml;base64,{base64.b64encode(FALLBACK_LOGO_SVG.encode()).decode()}"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700;800;900&display=swap');
*{font-family:'Vazirmatn',Tahoma,Arial,sans-serif!important}
.stApp{background:linear-gradient(180deg,#EEF2F9 0%,#F7F9FC 100%)}
.block-container{padding-top:1.2rem;padding-bottom:2.5rem;max-width:1500px}
.main-header{background:linear-gradient(135deg,#1E3A8A 0%,#3B82F6 55%,#06B6D4 100%);border-radius:18px;padding:20px 28px;margin-bottom:22px;box-shadow:0 12px 32px rgba(30,58,138,0.18);direction:rtl;position:relative;overflow:hidden}
.main-header::before{content:'';position:absolute;top:-50%;right:-10%;width:420px;height:420px;background:radial-gradient(circle,rgba(255,255,255,0.14) 0%,transparent 70%);border-radius:50%}
.main-header::after{content:'';position:absolute;bottom:-60%;left:-5%;width:320px;height:320px;background:radial-gradient(circle,rgba(255,255,255,0.08) 0%,transparent 70%);border-radius:50%}
.header-inner{display:flex;align-items:center;justify-content:space-between;gap:18px;position:relative;z-index:2;direction:rtl}
.header-text{flex:1;text-align:right;min-width:0}
.header-text h1{color:#FFF;margin:0;font-size:clamp(0.9rem,1.5vw,1.3rem);font-weight:700;line-height:1.35;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.header-text p{color:rgba(255,255,255,0.9);margin:6px 0 0 0;font-size:0.85rem}
.header-logo{flex-shrink:0;width:80px;height:80px;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,0.10);border:1.5px solid rgba(255,255,255,0.25);border-radius:16px;padding:6px;backdrop-filter:blur(6px);box-shadow:0 6px 18px rgba(15,23,42,0.12)}
.header-logo img{width:100%;height:100%;object-fit:contain;display:block}
.kpi-card{background:#FFF;border-radius:16px;padding:18px 22px;box-shadow:0 4px 16px rgba(15,23,42,0.05);border:1px solid #E5E9F2;transition:all 0.25s ease;direction:rtl;min-height:130px;display:flex;flex-direction:column;justify-content:space-between}
.kpi-card:hover{transform:translateY(-3px);box-shadow:0 12px 26px rgba(15,23,42,0.10);border-color:#CBD5E1}
.kpi-label{color:#64748B;font-size:0.84rem;font-weight:500;margin-bottom:6px;line-height:1.4}
.kpi-value{color:#0F172A;font-size:1.5rem;font-weight:700;line-height:1.25;font-variant-numeric:tabular-nums;letter-spacing:-0.3px;word-break:break-word}
.kpi-unit{color:#94A3B8;font-size:0.78rem;font-weight:500;margin-top:4px}
.accent-blue{border-top:3px solid #2563EB}.accent-red{border-top:3px solid #DC2626}.accent-green{border-top:3px solid #059669}.accent-purple{border-top:3px solid #7C3AED}.accent-orange{border-top:3px solid #D97706}.accent-cyan{border-top:3px solid #0891B2}.accent-slate{border-top:3px solid #64748B}
.section-header{display:flex;align-items:center;gap:10px;margin:26px 0 14px 0;direction:rtl;font-size:1.1rem;font-weight:700;color:#0F172A;flex-wrap:wrap}
.section-header::before{content:'';width:4px;height:22px;background:linear-gradient(180deg,#2563EB,#06B6D4);border-radius:3px}
.sub-header-rtl{direction:rtl;text-align:right;font-size:1.02rem;font-weight:700;color:#0F172A;margin:20px 0 10px 0}
.badge{display:inline-block;padding:4px 12px;border-radius:20px;font-size:0.76rem;font-weight:600;background:#DBEAFE;color:#1E40AF}
.badge-orange{background:#FEF3C7;color:#92400E}
.explain-box{background:linear-gradient(135deg,#F0F9FF 0%,#EFF6FF 100%);border-right:3px solid #3B82F6;border-radius:8px;padding:8px 12px;margin:6px 0 10px 0;direction:rtl;text-align:right;color:#1E3A8A;font-size:0.78rem;line-height:1.65}
.explain-box b{color:#1E40AF}
.rtl-alert{direction:rtl;text-align:right;background:linear-gradient(135deg,#FEF3C7 0%,#FDE68A 100%);border-right:3px solid #D97706;border-radius:8px;padding:8px 12px;margin:6px 0 10px 0;color:#78350F;font-size:0.82rem;line-height:1.65}
.rtl-alert b{color:#92400E}
.gradient-divider{height:3px;background:linear-gradient(90deg,rgba(59,130,246,0) 0%,rgba(59,130,246,0.55) 20%,rgba(6,182,212,0.85) 50%,rgba(59,130,246,0.55) 80%,rgba(59,130,246,0) 100%);border:none;border-radius:3px;margin:28px 0 22px 0;box-shadow:0 2px 8px rgba(59,130,246,0.18)}
.vertical-divider{width:3px;height:100%;min-height:460px;background:linear-gradient(180deg,rgba(59,130,246,0) 0%,rgba(6,182,212,0.75) 50%,rgba(59,130,246,0) 100%);margin:20px auto 0 auto;box-shadow:0 0 14px rgba(6,182,212,0.4);border-radius:3px}
.chart-legend-strip{direction:rtl;display:flex;flex-wrap:wrap;justify-content:center;align-items:center;gap:2px 4px;font-size:0.72rem;color:#1E3A8A;padding:4px 8px;background:linear-gradient(135deg,#F0F9FF 0%,#EFF6FF 100%);border-radius:6px;margin:-4px 0 10px 0;border:1px solid #BFDBFE;font-weight:600;line-height:1.5}
.chart-legend-strip .legend-title{color:#1E40AF;font-weight:800;font-size:0.72rem;padding:0 2px}
.chart-legend-strip .legend-item{display:inline-flex;align-items:center;gap:3px;padding:1px 4px;color:#1E3A8A;white-space:nowrap}
.chart-legend-strip .legend-item b{color:#1E40AF;background:#DBEAFE;border-radius:3px;padding:0 4px;font-size:0.68rem;font-weight:800}
.chart-legend-strip .legend-sep{color:#CBD5E1;margin:0 1px;font-weight:400}
.welcome-box{background:#FFF;border-radius:18px;padding:46px 40px;text-align:center;direction:rtl;box-shadow:0 12px 32px rgba(15,23,42,0.08);border:1px solid #E5E9F2;margin-top:30px}
.welcome-box .welcome-icon{font-size:3rem;display:block;margin-bottom:14px}
.welcome-box .welcome-title{color:#1E3A8A;font-size:1.3rem;font-weight:700;margin-bottom:14px}
.welcome-box .welcome-text{color:#475569;font-size:0.98rem;line-height:2}
.welcome-box .welcome-hint{display:inline-block;margin-top:18px;background:#EFF6FF;color:#1E40AF;padding:10px 20px;border-radius:10px;font-size:0.9rem;font-weight:600}
.center-notice{display:flex;align-items:center;justify-content:center;min-height:260px;text-align:center;padding:30px}
.center-notice-inner{background:#FFF;border:1px solid #E5E9F2;border-radius:16px;padding:32px 40px;max-width:560px;box-shadow:0 6px 18px rgba(15,23,42,0.06);direction:rtl;color:#334155;font-size:0.95rem;line-height:2}
.center-notice-icon{font-size:2.2rem;margin-bottom:8px;display:block}
.pretty-table{width:100%;border-collapse:separate;border-spacing:0;border-radius:14px;overflow:hidden;direction:rtl;font-family:'Vazirmatn',Tahoma,Arial;font-size:13.5px;box-shadow:0 6px 22px rgba(15,23,42,0.07);background:#FFF;border:1px solid #E5E9F2;margin-top:6px}
.pretty-table thead th{background:linear-gradient(135deg,#1E3A8A 0%,#2563EB 60%,#3B82F6 100%);color:#FFF;font-weight:800;font-size:13.5px;text-align:right;padding:14px 16px;white-space:nowrap;letter-spacing:0.2px;border:none}
.pretty-table tbody td{text-align:right;padding:12px 16px;color:#1E293B;font-weight:600;font-variant-numeric:tabular-nums;border-bottom:1px solid #E8EDF5}
.pretty-table tbody tr:nth-child(even) td{background-color:#F8FAFC}
.pretty-table tbody tr:hover td{background-color:#EFF6FF}
.pretty-table tbody tr:last-child td{border-bottom:none}
.admin-grid-header{background:linear-gradient(135deg,#1E3A8A 0%,#2563EB 60%,#3B82F6 100%);color:#FFF!important;font-weight:800!important;font-size:13.5px!important;text-align:right;direction:rtl;padding:14px 16px;min-height:52px;display:flex;align-items:center;box-shadow:0 4px 12px rgba(30,58,138,0.14);border-radius:10px}
.admin-grid-cell{background:#FFF;color:#1E293B!important;font-weight:700!important;font-size:13.5px!important;text-align:right;direction:rtl;padding:12px 16px;min-height:52px;display:flex;align-items:center;font-variant-numeric:tabular-nums;border:1px solid #E5E9F2;border-radius:10px}
.admin-grid-cell:hover{background:#EFF6FF}
div[data-testid="stNumberInput"]{margin-bottom:0!important}
div[data-testid="stNumberInput"]>div{border:none!important;background:transparent!important}
div[data-testid="stNumberInput"] input{background:#FFF!important;color:#0F172A!important;font-weight:800!important;font-size:14px!important;padding:12px 16px!important;text-align:center!important;direction:ltr!important;border:1px solid #E5E9F2!important;border-radius:10px!important;min-height:52px!important;font-family:'Vazirmatn',Tahoma,Arial!important;font-variant-numeric:tabular-nums!important}
div[data-testid="stHorizontalBlock"]{gap:6px!important;margin-bottom:6px!important}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#F4F8FF 0%,#E6EEFB 60%,#DCE7F9 100%);border-right:1px solid #D6E2F5;box-shadow:2px 0 14px rgba(30,58,138,0.06)}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,[data-testid="stSidebar"] label{direction:rtl;text-align:right;color:#1E3A8A}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,[data-testid="stSidebar"] h4{direction:rtl!important;text-align:right!important;color:#1E40AF!important;font-weight:700!important}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"]{direction:rtl;text-align:right}
[data-testid="stSidebar"] hr{border-color:#D6E2F5}
[data-testid="stSidebar"] div[data-baseweb="select"]>div{background:rgba(255,255,255,0.85);border-color:#D6E2F5;direction:rtl}
[data-testid="stSidebar"] [data-testid="stCheckbox"]{background:transparent;border-radius:10px;padding:6px 10px;margin-bottom:4px;direction:rtl!important}
[data-testid="stSidebar"] [data-testid="stCheckbox"]:hover{background:rgba(255,255,255,0.35)}
[data-testid="stSidebar"] [data-testid="stCheckbox"] label{direction:rtl!important;display:flex!important;flex-direction:row-reverse!important;justify-content:flex-end!important;align-items:center!important;width:100%!important;gap:8px!important}
[data-testid="stSidebar"] [data-testid="stCheckbox"] label>div:first-child{margin-right:6px!important;margin-left:0!important}
[data-testid="stSidebar"] [data-testid="stCheckbox"] label>div:last-child{text-align:right!important;flex:1!important}
[data-testid="stSidebar"] [data-testid="stCheckbox"] label p{text-align:right!important;direction:rtl!important;width:100%!important;margin:0!important;font-weight:600!important;color:#1E3A8A!important}
/* دکمه‌های سایدبار - ظریف و شکیل */
[data-testid="stSidebar"] .stButton>button{background:#F8FAFC;color:#1E40AF;border:1.5px solid #CBD5E1;border-radius:10px;padding:9px 14px;font-weight:600;font-size:12.5px;transition:all 0.2s ease;box-shadow:0 1px 3px rgba(15,23,42,0.05)}
[data-testid="stSidebar"] .stButton>button:hover{background:#EFF6FF;border-color:#93C5FD;color:#1E3A8A;box-shadow:0 2px 6px rgba(30,64,175,0.10);transform:translateY(-1px)}
[data-testid="stSidebar"] .stButton>button:focus{outline:none!important;box-shadow:0 0 0 3px rgba(59,130,246,0.15)!important}
.file-chip{background:#ECFDF5;border:1px solid #A7F3D0;border-radius:10px;padding:9px 12px;color:#065F46;font-size:12.5px;margin-bottom:8px;direction:rtl;text-align:right;display:flex;align-items:center;gap:6px}
.file-chip b{color:#047857}
.file-label{color:#1E40AF;font-weight:700;font-size:12.5px;margin-bottom:4px;direction:rtl;text-align:right}
/* دکمه‌های آیکونی */
[data-testid="stSidebar"] .stButton>button[aria-label="✅"],
[data-testid="stSidebar"] .stButton>button[aria-label="❌"]{
    font-size:22px!important;
    padding:4px 6px!important;
    min-height:38px!important;
    line-height:1!important;
    border-radius:10px!important;
}
.stTabs [data-baseweb="tab-list"]{gap:6px;direction:rtl;border-bottom:2px solid #E5E9F2}
.stTabs [data-baseweb="tab"]{height:46px;padding:0 22px;background-color:transparent;border-radius:10px 10px 0 0;font-weight:600;color:#64748B}
.stTabs [aria-selected="true"]{background-color:#FFF;color:#1E40AF;border-bottom:3px solid #1E40AF}
.stDownloadButton>button{background:linear-gradient(135deg,#1E40AF,#3B82F6);color:white;border:none;border-radius:10px;padding:10px 24px;font-weight:600}
.stDownloadButton>button:hover{background:linear-gradient(135deg,#1E3A8A,#2563EB)}
div[data-testid="stMetric"]{display:none}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p,.stCaption,.stCaption p{direction:rtl!important;text-align:right!important}
</style>
""", unsafe_allow_html=True)


def normalize_text(value) -> str:
    if pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = text.replace("ي", "ی").replace("ك", "ک")
    text = text.replace("\u200c", " ").replace("\u200f", "").replace("\u200e", "")
    return re.sub(r"\s+", " ", text).strip()


def parse_number(value) -> float:
    if pd.isna(value):
        return np.nan
    if isinstance(value, (int, float, np.number)):
        r = float(value)
        return r if np.isfinite(r) else np.nan
    text = str(value).strip().translate(DIGIT_TRANSLATION)
    if text.lower() in {"", "-", "—", "nan", "none", "null"}:
        return np.nan
    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1]
    text = (text.replace("٬", "").replace(",", "").replace("٫", ".")
            .replace("−", "-").replace("\u200c", "")
            .replace("\u200e", "").replace("\u200f", "")
            .replace("ریال", "").replace("تومان", ""))
    text = re.sub(r"\s+", "", text)
    try:
        r = float(text)
    except (ValueError, TypeError):
        return np.nan
    if not np.isfinite(r):
        return np.nan
    return -abs(r) if negative else r


def is_total_label(value) -> bool:
    return normalize_text(value).replace(" ", "").lower() in {x.replace(" ", "").lower() for x in TOTAL_LABELS}


def fmt_int(v):
    return "—" if v is None or pd.isna(v) else f"{v:,.0f}"


def fmt_rial(v):
    return "—" if v is None or pd.isna(v) else f"{v:,.0f}"


def fmt_pct(v, d=1):
    if v is None or pd.isna(v):
        return "—"
    return f"{v:+.{d}f}%" if abs(v) < 1000 else f"{v:,.{d}f}%"


def kpi_card(label, value, unit="", accent="blue"):
    return f'<div class="kpi-card accent-{accent}"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-unit">{unit}</div></div>'


def explain_box(text):
    return f'<div class="explain-box">{text}</div>'


def rtl_alert(text):
    return f'<div class="rtl-alert">{text}</div>'


def sub_header(text):
    return f'<div class="sub-header-rtl">{text}</div>'


def gradient_divider():
    return '<div class="gradient-divider"></div>'


def two_cols_with_vdivider(min_height=460):
    c1, dc, c2 = st.columns([1, 0.04, 1])
    with dc:
        st.markdown(f'<div class="vertical-divider" style="min-height:{min_height}px;"></div>', unsafe_allow_html=True)
    return c1, c2


def add_below_legend(labels, title_prefix="📌 راهنما"):
    parts = [f'<span class="legend-title">{title_prefix}:</span>']
    for i, l in enumerate(labels):
        if i > 0:
            parts.append('<span class="legend-sep">│</span>')
        parts.append(f'<span class="legend-item"><b>{i+1}</b>{l}</span>')
    st.markdown(f'<div class="chart-legend-strip">{"".join(parts)}</div>', unsafe_allow_html=True)


def center_notice(icon, text):
    return f'<div class="center-notice"><div class="center-notice-inner"><span class="center-notice-icon">{icon}</span>{text}</div></div>'


def no_data_notice(u):
    return center_notice("📭", f"برای دانشگاه <b>{u}</b> داده‌ای در فایل‌های بارگذاری‌شده در دسترس نیست.<br>لطفاً فایل مناسب را بارگذاری نمایید یا دانشگاه دیگری انتخاب کنید.")


def perf_mismatch_notice(u):
    return center_notice("📭", f"داده‌ای برای دانشگاه <b>{u}</b> در دسترس نیست.<br>لطفاً فایل عملکرد مالی <b>{u}</b> را بارگذاری نمایید یا دانشگاه دیگری انتخاب کنید.")


def render_pretty_table(df):
    st.markdown(df.to_html(escape=False, index=False, classes="pretty-table", border=0, na_rep="—"), unsafe_allow_html=True)


@st.cache_data(show_spinner=False, max_entries=8)
def read_workbook(content: bytes) -> dict:
    sheets = pd.read_excel(io.BytesIO(content), sheet_name=None, engine="openpyxl")
    cleaned = {}
    for sn, frame in sheets.items():
        frame = frame.dropna(how="all").copy().dropna(axis=1, how="all")
        names, seen = [], {}
        for original in frame.columns:
            name = normalize_text(original) or "ستون_بدون_نام"
            seen[name] = seen.get(name, 0) + 1
            names.append(name + (f" [{seen[name]}]" if seen[name] > 1 else ""))
        frame.columns = names
        cleaned[sn] = frame.reset_index(drop=True)
    return cleaned


def pick_first_sheet(sheets):
    if not sheets:
        return None, pd.DataFrame()
    for name, frame in sheets.items():
        if not frame.empty:
            return name, frame
    first = list(sheets.keys())[0]
    return first, sheets[first]


def _uni_key(name):
    return normalize_text(name).replace(" ", "").replace("\u200c", "").lower()


def _known_uni_by_key(key):
    for u in KNOWN_UNIVERSITIES:
        if _uni_key(u) == key:
            return u
    return None


def detect_perf_university(df, sheet_name=None):
    if df is None or df.empty:
        return None
    if sheet_name:
        sn = normalize_text(sheet_name)
        direct = _known_uni_by_key(_uni_key(sn))
        if direct:
            return direct
        for u in KNOWN_UNIVERSITIES:
            uk = _uni_key(u)
            if uk and uk in _uni_key(sn):
                return u
    for col in df.columns:
        if any(k in normalize_text(col) for k in ("دانشگاه", "واحد", "مرکز", "شعبه")):
            for val in df[col].dropna().astype(str).head(30):
                vn = normalize_text(val)
                if not vn or len(vn) > 60:
                    continue
                direct = _known_uni_by_key(_uni_key(vn))
                if direct:
                    return direct
                for u in KNOWN_UNIVERSITIES:
                    uk = _uni_key(u)
                    if uk and uk in _uni_key(vn):
                        return u
    for col in df.columns:
        for val in df[col].dropna().astype(str).head(100):
            vn = normalize_text(val)
            if not vn or len(vn) > 60 or len(vn) < 3:
                continue
            direct = _known_uni_by_key(_uni_key(vn))
            if direct:
                return direct
            for u in KNOWN_UNIVERSITIES:
                uk = _uni_key(u)
                if uk and uk in _uni_key(vn):
                    return u
    return None


def style_figure(fig, height=430):
    fig.update_layout(template="plotly_white", height=height,
                      font=dict(family="Vazirmatn, Tahoma, Arial", size=13, color="#334155"),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(l=25, r=160, t=70, b=55),
                      title=dict(x=1, xanchor="right"),
                      legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02,
                                  font=dict(size=12, family="Vazirmatn", weight="bold"),
                                  bgcolor="rgba(255,255,255,0.9)", bordercolor="#E5E9F2", borderwidth=1),
                      hoverlabel=dict(bgcolor="#FFF", font_size=13, font_family="Vazirmatn, Tahoma", bordercolor="#CBD5E1"))
    fig.update_xaxes(showgrid=True, gridcolor="#E2E8F0", zeroline=False,
                     title_font=dict(size=14, color="#0F172A", family="Vazirmatn, Tahoma", weight="bold"),
                     tickfont=dict(size=11.5, color="#1E293B", family="Vazirmatn, Tahoma", weight="bold"))
    fig.update_yaxes(showgrid=False, zeroline=False,
                     title_font=dict(size=14, color="#0F172A", family="Vazirmatn, Tahoma", weight="bold"),
                     tickfont=dict(size=11.5, color="#1E293B", family="Vazirmatn, Tahoma", weight="bold"))
    return fig


def make_financial_bar_full(labels, values, color, title_text, height=680, color_list=None, x_axis_title="سرفصل"):
    x_vals = [str(i + 1) for i in range(len(labels))]
    pos = [v for v in values if v is not None and not pd.isna(v) and v > 0]
    neg = [v for v in values if v is not None and not pd.isna(v) and v < 0]
    max_pos = max(pos) if pos else 1
    max_neg = abs(min(neg)) if neg else 0
    y_top = max_pos * 2.3 if max_pos > 0 else 1
    y_bottom = -max_neg * 2.3 if max_neg > 0 else 0
    fig = go.Figure()
    fig.add_trace(go.Bar(x=x_vals, y=values,
                          text=[f"{v:,.0f}" if v is not None and not pd.isna(v) else "" for v in values],
                          textposition="outside", textangle=-90, cliponaxis=False,
                          textfont=dict(size=17, color="#0F172A", family="Vazirmatn, Tahoma", weight="bold"),
                          marker_color=color_list if color_list else color,
                          width=0.68, name="",
                          hovertemplate="%{x}<br>%{y:,.0f} ریال<extra></extra>"))
    fig.update_layout(template="plotly_white", height=height,
                      font=dict(family="Vazirmatn, Tahoma, Arial", size=13, color="#334155"),
                      title=dict(text=title_text, x=1, xanchor="right",
                                 font=dict(size=16, color="#0F172A", family="Vazirmatn", weight="bold")),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(l=110, r=60, t=210, b=100), showlegend=False, bargap=0.45,
                      xaxis=dict(title=x_axis_title, type="category",
                                 title_font=dict(size=14, color="#0F172A", family="Vazirmatn", weight="bold"),
                                 tickfont=dict(size=14, family="Vazirmatn", weight="bold"), showgrid=False),
                      yaxis=dict(title="ریال", tickformat=",.0f", exponentformat="none", showexponent="none",
                                 range=[y_bottom, y_top],
                                 tickfont=dict(size=12, family="Vazirmatn", weight="bold"),
                                 showgrid=True, gridcolor="#E2E8F0", zeroline=False),
                      hoverlabel=dict(bgcolor="#FFF", font_size=13, font_family="Vazirmatn, Tahoma", bordercolor="#CBD5E1"))
    return fig


def forecast_value(history, periods_ahead):
    if history is None:
        history = []
    clean = []
    for v in history:
        if v is None:
            continue
        try:
            fv = float(v)
            if np.isfinite(fv) and fv != 0:
                clean.append(fv)
        except (TypeError, ValueError):
            continue
    if not clean:
        return 0.0
    if len(clean) == 1:
        return clean[0] * (1.05 ** (periods_ahead + 1))
    x = np.arange(1, len(clean) + 1, dtype=float)
    y = np.array(clean, dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    x_target = float(len(clean) + periods_ahead + 1)
    return float(slope * x_target + intercept)


def apply_auto_bar_text(fig, inside_color="#FFFFFF", outside_color="#0F172A", size=11):
    fig.update_traces(textposition="auto", cliponaxis=False,
                      insidetextfont=dict(size=size, color=inside_color, family="Vazirmatn, Tahoma", weight="bold"),
                      outsidetextfont=dict(size=size, color=outside_color, family="Vazirmatn, Tahoma", weight="bold"))
    return fig


def excel_safe_frame(frame):
    result = frame.copy()
    def protect(v):
        if isinstance(v, str) and v.lstrip().startswith(("=", "+", "-", "@")):
            return "'" + v
        return v
    for col in result.select_dtypes(include=["object", "string"]).columns:
        result[col] = result[col].map(protect)
    return result


def make_excel(sheets):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for sn, frame in sheets.items():
            safe = sn[:31]
            excel_safe_frame(frame).to_excel(writer, sheet_name=safe, index=False)
            ws = writer.sheets[safe]
            ws.sheet_view.rightToLeft = True
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            for cells in ws.columns:
                letter = cells[0].column_letter
                ml = max((len(str(c.value)) if c.value is not None else 0) for c in cells)
                ws.column_dimensions[letter].width = min(max(ml + 2, 14), 45)
    return buf.getvalue()


def extract_student_long(frame):
    if frame.empty:
        return pd.DataFrame(columns=["university", "semester_code", "students"])
    semester_col = None
    for col in frame.columns:
        if any(k in col for k in ("نیمسال", "آمار کل", "ترم", "سال تحصیلی", "آمار ورودی")):
            semester_col = col
            break
    if semester_col is None:
        semester_col = frame.columns[-1]
    uni_cols = [c for c in frame.columns if c != semester_col and not is_total_label(c)]
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
                records.append({"university": normalize_text(uni), "semester_code": sem_code, "students": val})
    return pd.DataFrame(records)


def extract_financial(frame):
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


def extract_perf_data(df):
    if df is None or df.empty:
        return None
    try:
        df = df.copy()
        df.columns = [normalize_text(c) for c in df.columns]
        title_col = next((c for c in df.columns if "عنوان" in c), df.columns[-1])
        perf_cols_with_order = []
        for idx, col in enumerate(df.columns):
            if "عملکرد" in col and "وضعیت" not in col and "فعلی" not in col:
                years = re.findall(r"\d{2,4}", col)
                start_year = 0
                if years:
                    try:
                        y = years[0]
                        start_year = 1400 + int(y) if len(y) == 2 else int(y)
                    except (ValueError, TypeError):
                        start_year = 0
                perf_cols_with_order.append((start_year if start_year > 0 else 9999, idx, col))
        perf_cols_with_order.sort(key=lambda x: (x[0], x[1]))
        perf_cols = [c[2] for c in perf_cols_with_order]
        curr_col = next((c for c in df.columns if "وضعیت فعلی" in c), None)
        items_map = {
            "in_tuition": "درآمد شهریه ای", "in_outsourcing": "درآمد غیرشهریه ای (برون سپاری)",
            "in_workshop": "درآمد غیرشهریه ای (برگزاری کارگاه)", "ex_faculty": "هزینه پرسنلی هیات علمی",
            "ex_official": "هزینه پرسنلی رسمی و قراردادی", "ex_corporate": "هزینه پرسنلی شرکتی",
            "ex_guest": "هزینه حق التدریس اساتید مدعو", "ex_rent": "هزینه اجاره",
            "ex_other": "هزینه های جاری (سایر)",
        }
        data = {}
        for key, kw in items_map.items():
            mask = df[title_col].astype(str).str.contains(kw, regex=False, na=False)
            if mask.any():
                row = df[mask].iloc[0]
                history = [float(v) for pc in perf_cols if pd.notna(v := parse_number(row[pc]))]
                cv = parse_number(row[curr_col]) if curr_col else 0.0
                data[key] = {"title": kw, "curr": float(cv) if pd.notna(cv) else 0.0,
                             "hist": history[0] if history else 0.0, "history": history}
            else:
                data[key] = {"title": kw, "curr": 0.0, "hist": 0.0, "history": []}
        def _sum_h(keys_list):
            lists = [data[k]["history"] for k in keys_list if data[k]["history"]]
            if not lists:
                return []
            ml = min(len(l) for l in lists)
            return [sum(l[i] for l in lists) for i in range(ml)]
        in_tot_c = data["in_tuition"]["curr"] + data["in_outsourcing"]["curr"] + data["in_workshop"]["curr"]
        in_tot_h = data["in_tuition"]["hist"] + data["in_outsourcing"]["hist"] + data["in_workshop"]["hist"]
        in_tot_hist = _sum_h(["in_tuition", "in_outsourcing", "in_workshop"])
        ex_keys = ["ex_faculty", "ex_official", "ex_corporate", "ex_guest", "ex_rent", "ex_other"]
        ex_tot_c = sum(data[k]["curr"] for k in ex_keys)
        ex_tot_h = sum(data[k]["hist"] for k in ex_keys)
        ex_tot_hist = _sum_h(ex_keys)
        data["in_total"] = {"title": "مجموع درآمد", "curr": in_tot_c, "hist": in_tot_h, "history": in_tot_hist}
        data["ex_total"] = {"title": "مجموع هزینه‌ها", "curr": ex_tot_c, "hist": ex_tot_h, "history": ex_tot_hist}
        profit_hist = []
        if in_tot_hist and ex_tot_hist:
            ml = min(len(in_tot_hist), len(ex_tot_hist))
            profit_hist = [in_tot_hist[i] - ex_tot_hist[i] for i in range(ml)]
        data["profit"] = {"title": "سود یا زیان", "curr": in_tot_c - ex_tot_c, "hist": in_tot_h - ex_tot_h, "history": profit_hist}
        return data
    except Exception as e:
        st.error(f"خطا در خواندن فایل عملکرد مالی: {e}")
        return None


def perf_has_data(perf_data):
    if not perf_data:
        return False
    keys = ["in_tuition", "in_outsourcing", "in_workshop", "ex_faculty", "ex_official",
            "ex_corporate", "ex_guest", "ex_rent", "ex_other"]
    return any(abs(perf_data[k]["curr"]) > 0 or bool(perf_data[k]["history"]) for k in keys)


def get_file_bytes(uploaded, default_name):
    if uploaded is not None:
        return uploaded.getvalue()
    path = BASE_DIR / default_name
    return path.read_bytes() if path.exists() else None


@st.cache_data(ttl=300, show_spinner=False)
def list_github_files(owner: str, repo: str, branch: str = "main"):
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/?ref={branch}"
        r = requests.get(url, timeout=10, headers={"Accept": "application/vnd.github.v3+json"})
        if r.status_code == 200:
            files = r.json()
            return [f for f in files if f.get("type") == "file" and f.get("name", "").lower().endswith((".xlsx", ".xls", ".csv"))]
        return []
    except Exception:
        return []


def download_github_file(file_info):
    try:
        r = requests.get(file_info["download_url"], timeout=20)
        if r.status_code == 200:
            return r.content
        return None
    except Exception:
        return None


def github_file_picker(label: str, key: str):
    """فقط انتخاب فایل - بدون آپلود محلی"""
    active_content = st.session_state.get(f"gh_content_{key}")
    active_name = st.session_state.get(f"gh_name_{key}")

    if active_content:
        st.markdown(f'<div class="file-chip">✅ <b>{active_name}</b></div>', unsafe_allow_html=True)
        if st.button("🗑️ تغییر فایل", key=f"gh_clear_{key}", use_container_width=True):
            st.session_state.pop(f"gh_content_{key}", None)
            st.session_state.pop(f"gh_name_{key}", None)
            st.rerun()
        buf = io.BytesIO(active_content)
        buf.name = active_name or "file.xlsx"
        return buf

    if not st.session_state.get(f"gh_show_{key}", False):
        st.markdown(f'<div class="file-label">{label}</div>', unsafe_allow_html=True)
        if st.button("📂 انتخاب فایل", key=f"gh_open_{key}", use_container_width=True):
            st.session_state[f"gh_show_{key}"] = True
            st.rerun()
        return None

    with st.spinner("در حال دریافت لیست فایل‌ها..."):
        files = list_github_files(GITHUB_REPO_OWNER, GITHUB_REPO_NAME, GITHUB_BRANCH)

    if not files:
        st.warning("فایلی یافت نشد یا دسترسی به مخزن برقرار نیست.")
        if st.button("🔙 بازگشت", key=f"gh_back_{key}", use_container_width=True):
            st.session_state[f"gh_show_{key}"] = False
            st.rerun()
        return None

    names = [f["name"] for f in files]
    sel = st.selectbox("فایل مورد نظر:", options=names, key=f"gh_sel_{key}", index=None, placeholder="— انتخاب کنید —")

    # دکمه‌های آیکونی وسط‌چین
    _, c1, c2, _ = st.columns([1.5, 0.6, 0.6, 1.5])
    with c1:
        load_clicked = st.button("✅", key=f"gh_ok_{key}", use_container_width=True, disabled=not sel)
    with c2:
        cancel_clicked = st.button("❌", key=f"gh_cancel_{key}", use_container_width=True)

    if cancel_clicked:
        st.session_state[f"gh_show_{key}"] = False
        st.rerun()

    if load_clicked and sel:
        f_info = next((f for f in files if f["name"] == sel), None)
        if f_info:
            with st.spinner(f"در حال دانلود {sel}..."):
                content = download_github_file(f_info)
            if content:
                st.session_state[f"gh_content_{key}"] = content
                st.session_state[f"gh_name_{key}"] = sel
                st.session_state[f"gh_show_{key}"] = False
                st.rerun()
            else:
                st.error("دانلود فایل ناموفق بود.")

    return None


LOGO_URI = get_logo_data_uri()
st.markdown(f"""
<div class="main-header">
  <div class="header-inner">
    <div class="header-text">
      <h1>🎓 داشبورد مدیریتی هوشمند مراکز آموزشی دانشگاه آزاد اسلامی استان گلستان</h1>
      <p>روند دانشجویان فعال، تحلیل بدهی و تقسیط، مقایسه عملکرد دانشگاه‌ها به همراه پیش بینی</p>
    </div>
    <div class="header-logo"><img src="{LOGO_URI}" alt="لوگو"/></div>
  </div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🏛️ دانشگاه")
    selected_university = st.selectbox("دانشگاه خود را انتخاب کنید", options=KNOWN_UNIVERSITIES,
                                        index=0, key="main_university_selector",
                                        help="ابتدا دانشگاه خود را انتخاب نمایید.")
    st.divider()
    st.markdown("### ⚙️ منابع داده")
    student_upload = github_file_picker("📋 فایل دانشجویان فعال", "student")
    st.write("")
    financial_upload = github_file_picker("💰 فایل اطلاعات مالی", "financial")
    st.write("")
    proj3_upload = github_file_picker("📈 فایل آمار ورودی جدید", "proj3")
    st.write("")
    perf_upload = github_file_picker("📊 فایل عملکرد مالی", "perf")

if student_upload is None or financial_upload is None:
    st.markdown("""
    <div class="welcome-box">
      <span class="welcome-icon">📂</span>
      <div class="welcome-title">به داشبورد مدیریتی خوش آمدید</div>
      <div class="welcome-text">
        برای مشاهده تحلیل‌ها، لطفاً فایل‌های اکسل زیر را بارگذاری کنید:<br>
        • <b>فایل دانشجویان فعال</b><br>
        • <b>فایل اطلاعات مالی بر اساس بدهی و تقسیط</b><br>
        • <b>فایل آمار ورودی جدید</b><br>
        • <b>فایل عملکرد مالی بر اساس سود و زیان</b>
      </div>
      <div class="welcome-hint">⬅️ از منوی کناری فایل‌ها را انتخاب کنید</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

student_bytes = student_upload.getvalue()
financial_bytes = financial_upload.getvalue()
proj3_bytes = get_file_bytes(proj3_upload, "uni-proj3.xlsx")
perf_bytes = get_file_bytes(perf_upload, "uni-proj4.xlsx")

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
student_sheet, student_raw = pick_first_sheet(student_sheets)
financial_sheet, financial_raw = pick_first_sheet(financial_sheets)
proj3_sheet, _ = pick_first_sheet(proj3_sheets) if proj3_sheets else (None, pd.DataFrame())
perf_sheet, _ = pick_first_sheet(perf_sheets) if perf_sheets else (None, pd.DataFrame())

if student_raw.empty or financial_raw.empty:
    st.warning("یکی از فایل‌های اصلی (دانشجویان یا مالی) خالی است.")
    st.stop()

student_long = extract_student_long(student_raw)
financial_df = extract_financial(financial_raw)

if student_long.empty:
    st.error("داده دانشجویان قابل استخراج نبود.")
    st.stop()

if financial_df.empty:
    st.warning("داده مالی قابل استخراج نبود. ادامه با داده دانشجویان.")

semesters = sorted(student_long["semester_code"].unique())
first_sem, latest_sem = semesters[0], semesters[-1]

perf_university = None
perf_data = None
if perf_sheets and perf_sheet:
    perf_raw_df = perf_sheets[perf_sheet]
    perf_university = detect_perf_university(perf_raw_df, perf_sheet)
    perf_data = extract_perf_data(perf_raw_df)

latest_students = student_long[student_long["semester_code"] == latest_sem][["university", "students"]].rename(columns={"students": "students_latest"})
first_students = student_long[student_long["semester_code"] == first_sem][["university", "students"]].rename(columns={"students": "students_first"})
combined = latest_students.merge(financial_df, on="university", how="outer").merge(first_students, on="university", how="left")

if "debt" in combined.columns:
    combined["debt_per_student"] = combined["debt"] / combined["students_latest"].where(combined["students_latest"] > 0)
if "installment" in combined.columns and "debt" in combined.columns:
    tc = combined["debt"] + combined["installment"]
    combined["installment_share"] = combined["installment"] / tc.where(tc > 0) * 100
if "not_referred" in combined.columns and "debtor_count" in combined.columns:
    combined["contacted_count"] = combined["debtor_count"] - combined["not_referred"]
    combined["contact_rate"] = combined["contacted_count"] / combined["debtor_count"].where(combined["debtor_count"] > 0) * 100
if "students_first" in combined.columns:
    base = combined["students_first"].where(combined["students_first"] > 0)
    combined["growth_pct"] = (combined["students_latest"] - combined["students_first"]) / base * 100

combined = combined.sort_values("students_latest", ascending=False).reset_index(drop=True)
color_map = {u: UNIVERSITY_COLORS.get(u, FALLBACK_COLORS[i % len(FALLBACK_COLORS)]) for i, u in enumerate(KNOWN_UNIVERSITIES)}

with st.sidebar:
    st.divider()
    st.markdown("### 📊 مقایسه دانشگاه‌ها")
    st.caption("دو یا چند دانشگاه را انتخاب کنید")
    if "reset_key" not in st.session_state:
        st.session_state.reset_key = 0
    current_reset_key = st.session_state.reset_key
    compared_universities = []
    for uni in KNOWN_UNIVERSITIES:
        if st.checkbox(uni, value=False, key=f"cmp_{uni}_{current_reset_key}"):
            compared_universities.append(uni)
    if st.button("🔄 ریست انتخاب‌ها", use_container_width=True, key="reset_compare_btn"):
        st.session_state.reset_key += 1
        st.rerun()
    st.divider()
    st.markdown("### 📅 انتخاب نیمسال‌ها")
    selected_financial_sem = st.selectbox("نیمسال داده مالی", options=FINANCIAL_SEMESTER_OPTIONS, index=0, key="selected_financial_sem")
    selected_prediction_sem = st.selectbox("نیمسال هدف پیش‌بینی", options=PREDICTION_SEMESTER_OPTIONS, index=0, key="selected_prediction_sem")

prediction_offset = PREDICTION_SEMESTER_OPTIONS.index(selected_prediction_sem)

available_in_data = set(combined["university"].tolist())
valid_compared = [u for u in compared_universities if u in available_in_data]
missing_compared = [u for u in compared_universities if u not in available_in_data]
is_compare_requested = len(compared_universities) >= 2
is_compare_mode = is_compare_requested and len(valid_compared) >= 2

if is_compare_requested:
    if missing_compared:
        ms = "، ".join(f"<b>{u}</b>" for u in missing_compared)
        st.markdown(rtl_alert(f"⚠️ دانشگاه‌های زیر در فایل‌ها موجود نیستند و از مقایسه حذف شدند:<br>{ms}"), unsafe_allow_html=True)
    if len(valid_compared) < 2:
        st.markdown(center_notice("⚠️", f"برای مقایسه حداقل <b>دو دانشگاه</b> باید در فایل‌ها موجود باشند.<br>از {len(compared_universities)} انتخاب، تنها <b>{len(valid_compared)}</b> مورد یافت شد.<br>انتخاب‌ها را اصلاح کنید یا فایل‌ها را بارگذاری نمایید."), unsafe_allow_html=True)
        st.stop()

if is_compare_mode:
    st.markdown('<div class="section-header">📊 مقایسه تفصیلی دانشگاه‌های انتخاب‌شده</div>', unsafe_allow_html=True)
    comparison_data = combined[combined["university"].isin(valid_compared)].copy()
    st.markdown(sub_header("📊 مقایسه تعداد دانشجویان"), unsafe_allow_html=True)
    left, right = two_cols_with_vdivider(min_height=500)
    with left:
        chart_df = comparison_data.dropna(subset=["students_first", "students_latest"]).copy()
        if not chart_df.empty:
            overview_long = pd.concat([
                chart_df[["university", "students_first"]].rename(columns={"students_first": "students"}).assign(نیمسال=f"نیمسال {first_sem}"),
                chart_df[["university", "students_latest"]].rename(columns={"students_latest": "students"}).assign(نیمسال=f"نیمسال {latest_sem}"),
            ], ignore_index=True)
            fig = px.bar(overview_long, x="students", y="university", color="نیمسال", orientation="h", barmode="group", text="students",
                         color_discrete_map={f"نیمسال {first_sem}": "#60A5FA", f"نیمسال {latest_sem}": "#1E40AF"})
            apply_auto_bar_text(fig, size=11)
            fig.update_layout(title=dict(text=f"تعداد دانشجویان — نیمسال {first_sem} و {latest_sem}",
                                         font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")),
                              xaxis_title="تعداد دانشجو", yaxis_title="دانشگاه", bargap=0.25)
            st.plotly_chart(style_figure(fig, max(420, 65 * len(chart_df) + 140)), use_container_width=True)
    with right:
        pie_df = comparison_data.dropna(subset=["students_latest"]).copy()
        pie_df = pie_df[pie_df["students_latest"] > 0]
        if not pie_df.empty:
            fig = px.pie(pie_df, names="university", values="students_latest", hole=0.62, color="university", color_discrete_map=color_map)
            fig.update_traces(textposition="inside", textinfo="percent",
                              textfont=dict(size=14, color="#FFFFFF", family="Vazirmatn", weight="bold"),
                              hovertemplate="<b>%{label}</b><br>%{value:,.0f} نفر<br>%{percent}<extra></extra>")
            fig.update_layout(title=dict(text="سهم هر دانشگاه از دانشجویان انتخاب‌شده",
                                         font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")),
                              showlegend=True, margin=dict(l=25, r=25, t=60, b=40))
            st.plotly_chart(style_figure(fig, 480), use_container_width=True)

    if "debt" in comparison_data.columns:
        st.markdown('<div class="section-header">💰 مقایسه مالی دانشگاه‌های انتخاب‌شده</div>', unsafe_allow_html=True)
        m_left, m_right = two_cols_with_vdivider(min_height=440)
        with m_left:
            fin_df = comparison_data.dropna(subset=["debt"]).copy().sort_values("debt", ascending=True)
            if not fin_df.empty:
                fig = go.Figure()
                fig.add_bar(name="مانده بدهی", y=fin_df["university"], x=fin_df["debt"], orientation="h",
                            marker=dict(color="#DC2626", line=dict(width=0)),
                            text=fin_df["debt"].map(lambda v: f"{v:,.0f}"),
                            hovertemplate="<b>%{y}</b><br>بدهی: %{x:,.0f} ریال<extra></extra>")
                if "installment" in fin_df.columns:
                    fig.add_bar(name="مبلغ تقسیط‌شده", y=fin_df["university"], x=fin_df["installment"], orientation="h",
                                marker=dict(color="#059669", line=dict(width=0)),
                                text=fin_df["installment"].map(lambda v: f"{v:,.0f}"),
                                hovertemplate="<b>%{y}</b><br>تقسیط: %{x:,.0f} ریال<extra></extra>")
                apply_auto_bar_text(fig, size=11)
                fig.update_layout(title=dict(text="مقایسه بدهی و تقسیط (ریال)",
                                             font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")),
                                  barmode="group", xaxis_title="ریال", yaxis_title="دانشگاه",
                                  bargap=0.3, margin=dict(l=25, r=200, t=70, b=55),
                                  xaxis=dict(tickformat=",.0f", exponentformat="none"))
                st.plotly_chart(style_figure(fig, max(420, 65 * len(fin_df) + 160)), use_container_width=True)
        with m_right:
            per_capita = comparison_data.dropna(subset=["debt_per_student"]).copy().sort_values("debt_per_student")
            if not per_capita.empty:
                fig = px.bar(per_capita, x="debt_per_student", y="university", orientation="h",
                             labels={"x": "ریال به‌ازای هر دانشجو", "university": "دانشگاه"},
                             color="university", color_discrete_map=color_map,
                             text=per_capita["debt_per_student"].map(lambda v: f"{v:,.0f}"))
                apply_auto_bar_text(fig, size=11)
                fig.update_layout(title=dict(text="بدهی سرانه هر دانشجو (ریال)",
                                             font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")),
                                  showlegend=False, bargap=0.35, xaxis_title="ریال", yaxis_title="دانشگاه",
                                  margin=dict(l=25, r=140, t=70, b=55),
                                  xaxis=dict(tickformat=",.0f", exponentformat="none"))
                st.plotly_chart(style_figure(fig, max(420, 65 * len(per_capita) + 160)), use_container_width=True)

        st.markdown(gradient_divider(), unsafe_allow_html=True)
        n_left, n_right = two_cols_with_vdivider(min_height=440)
        with n_left:
            inst_df = comparison_data.dropna(subset=["installment_share"]).copy().sort_values("installment_share")
            if not inst_df.empty:
                fig = px.bar(inst_df, x="installment_share", y="university", orientation="h",
                             color="university", color_discrete_map=color_map,
                             labels={"installment_share": "درصد", "university": "دانشگاه"},
                             text=inst_df["installment_share"].map(lambda v: f"{v:.1f}%"))
                apply_auto_bar_text(fig, size=11)
                fig.update_layout(title=dict(text="سهم تقسیط از کل مطالبات (٪)",
                                             font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")),
                                  showlegend=False, bargap=0.35,
                                  xaxis=dict(range=[0, 100], title="درصد"),
                                  yaxis=dict(title="دانشگاه"), margin=dict(l=25, r=140, t=70, b=55))
                st.plotly_chart(style_figure(fig, max(420, 65 * len(inst_df) + 160)), use_container_width=True)
        with n_right:
            contact_df = comparison_data.dropna(subset=["contact_rate"]).copy().sort_values("contact_rate")
            if not contact_df.empty:
                cmin, cmax = float(contact_df["contact_rate"].min()), float(contact_df["contact_rate"].max())
                xmin, xmax = min(0, cmin) - 20, max(100, cmax) + 20
                fig = go.Figure()
                fig.add_trace(go.Bar(y=contact_df["university"], x=contact_df["contact_rate"], orientation="h",
                                     marker=dict(color=[color_map.get(u, "#3B82F6") for u in contact_df["university"]], line=dict(width=0)),
                                     text=[f"{v:.1f}%" for v in contact_df["contact_rate"]],
                                     hovertemplate="<b>%{y}</b><br>نرخ مراجعه: %{x:.1f}%<extra></extra>"))
                apply_auto_bar_text(fig, size=11)
                fig.add_vline(x=0, line=dict(color="#64748B", width=1.2, dash="dash"))
                fig.add_vline(x=100, line=dict(color="#94A3B8", width=1, dash="dot"))
                fig.update_layout(title=dict(text="نرخ مراجعه بدهکاران (٪)",
                                             font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")),
                                  showlegend=False, bargap=0.45,
                                  xaxis=dict(title="درصد", range=[xmin, xmax], tickfont=dict(size=12, weight="bold"), zeroline=False, showticklabels=True),
                                  yaxis=dict(title="دانشگاه", tickfont=dict(size=14, family="Vazirmatn", weight="bold"), automargin=True),
                                  margin=dict(l=25, r=140, t=70, b=55))
                st.plotly_chart(style_figure(fig, max(420, 70 * len(contact_df) + 180)), use_container_width=True)

    st.markdown('<div class="section-header">📋 جدول خلاصه مقایسه</div>', unsafe_allow_html=True)
    cmp_summary = pd.DataFrame({
        "دانشگاه": comparison_data["university"],
        f"دانشجو ({first_sem})": comparison_data.get("students_first", pd.Series([np.nan]*len(comparison_data))).map(fmt_int),
        f"دانشجو ({latest_sem})": comparison_data["students_latest"].map(fmt_int),
        "رشد/افت (%)": comparison_data.get("growth_pct", pd.Series([np.nan]*len(comparison_data))).map(lambda v: fmt_pct(v) if pd.notna(v) else "—"),
        "بدهی (ریال)": comparison_data.get("debt", pd.Series([np.nan]*len(comparison_data))).map(fmt_rial),
        "تقسیط (ریال)": comparison_data.get("installment", pd.Series([np.nan]*len(comparison_data))).map(fmt_rial),
        "بدهی سرانه (ریال)": comparison_data.get("debt_per_student", pd.Series([np.nan]*len(comparison_data))).map(fmt_rial),
        "تعداد بدهکار": comparison_data.get("debtor_count", pd.Series([np.nan]*len(comparison_data))).map(fmt_int),
        "عدم مراجعه": comparison_data.get("not_referred", pd.Series([np.nan]*len(comparison_data))).map(fmt_int),
        "سهم تقسیط": comparison_data.get("installment_share", pd.Series([np.nan]*len(comparison_data))).map(lambda v: f"{v:.1f}%" if pd.notna(v) else "—"),
        "نرخ مراجعه": comparison_data.get("contact_rate", pd.Series([np.nan]*len(comparison_data))).map(lambda v: f"{v:.1f}%" if pd.notna(v) else "—"),
    })
    render_pretty_table(cmp_summary)

    st.markdown('<div class="section-header">📥 خروجی گزارش مقایسه</div>', unsafe_allow_html=True)
    cmp_excel = make_excel({
        "خلاصه مقایسه": cmp_summary,
        "روند دانشجویان": student_long[student_long["university"].isin(valid_compared)].pivot_table(index="university", columns="semester_code", values="students", aggfunc="sum").reset_index(),
        "داده مالی": financial_df[financial_df["university"].isin(valid_compared)] if not financial_df.empty else pd.DataFrame(),
    })
    c_dl, _ = st.columns([1, 3])
    with c_dl:
        st.download_button("📥 دانلود گزارش مقایسه (Excel)", data=cmp_excel, file_name="comparison_report.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True, key="download_compare_excel")
    st.divider()
    st.stop()

selected_data = combined[combined["university"] == selected_university].copy()
has_selected_data = not selected_data.empty
st.markdown(f'<div class="section-header">📍 نمای مدیریتی: {selected_university}</div>', unsafe_allow_html=True)

if has_selected_data:
    row0 = selected_data.iloc[0]
    total_students = row0.get("students_latest", np.nan)
    total_debt = row0.get("debt", np.nan)
    total_installment = row0.get("installment", np.nan)
    total_not_referred = row0.get("not_referred", np.nan)
    total_debtors = row0.get("debtor_count", np.nan)
    debt_per_student = row0.get("debt_per_student", np.nan)
    first_students_val = row0.get("students_first", np.nan)
    growth_val = row0.get("growth_pct", np.nan)
else:
    total_students = total_debt = total_installment = np.nan
    total_not_referred = total_debtors = debt_per_student = np.nan
    first_students_val = growth_val = np.nan

all_students_total = combined["students_latest"].sum(min_count=1)
share_of_total = (total_students / all_students_total * 100) if pd.notna(all_students_total) and all_students_total > 0 and pd.notna(total_students) else np.nan

if not has_selected_data:
    st.markdown(no_data_notice(selected_university), unsafe_allow_html=True)
else:
    st.markdown('<div class="section-header">📊 شاخص‌های کلیدی</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(kpi_card(f"دانشجویان فعال — نیمسال {latest_sem}", fmt_int(total_students), "نفر", "blue"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card(f"مانده بدهی — نیمسال {selected_financial_sem}", fmt_rial(total_debt), "ریال", "red"), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card(f"مبلغ تقسیط‌شده — نیمسال {selected_financial_sem}", fmt_rial(total_installment), "ریال", "green"), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_card("بدهی سرانه", fmt_rial(debt_per_student), "ریال به‌ازای هر دانشجو", "purple"), unsafe_allow_html=True)
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        st.markdown(kpi_card("سهم از کل دانشجویان", fmt_pct(share_of_total) if pd.notna(share_of_total) else "—", "درصد", "cyan"), unsafe_allow_html=True)
    with c6:
        st.markdown(kpi_card(f"تعداد بدهکاران — نیمسال {selected_financial_sem}", fmt_int(total_debtors), "نفر", "orange"), unsafe_allow_html=True)
    with c7:
        st.markdown(kpi_card(f"عدم مراجعه — نیمسال {selected_financial_sem}", fmt_int(total_not_referred), "نفر", "slate"), unsafe_allow_html=True)
    with c8:
        st.markdown(kpi_card(f"رشد از نیمسال {first_sem} تا {latest_sem}", fmt_pct(growth_val) if pd.notna(growth_val) else "—", "درصد", "green"), unsafe_allow_html=True)
    st.markdown(explain_box(
        "<b>بدهی سرانه:</b> میانگین سهم هر دانشجوی فعال از کل مانده بدهی.<br>"
        "<b>فرمول:</b> مجموع مانده بدهی ÷ مجموع دانشجویان فعال<br>"
        "<b>سهم از کل دانشجویان:</b> نسبت دانشجویان این واحد به کل واحدها.<br>"
        "<b>فرمول:</b> دانشجویان این واحد ÷ دانشجویان کل واحدها × ۱۰۰"), unsafe_allow_html=True)

tab_trend, tab_financial, tab_fin_perf = st.tabs(["📈 روند دانشجویان", "💰 تحلیل مالی", "📈 خلاصه عملکرد مالی و پیش‌بینی وضعیت"])

with tab_trend:
    trend_scope = student_long[student_long["university"] == selected_university].copy()
    if not has_selected_data or trend_scope.empty:
        st.markdown(no_data_notice(selected_university), unsafe_allow_html=True)
    else:
        st.markdown('<div class="section-header">📈 روند تعداد دانشجویان — مهرماه و بهمن‌ماه</div>', unsafe_allow_html=True)
        trend_agg = trend_scope.groupby("semester_code", as_index=False)["students"].sum(min_count=1).sort_values("semester_code")
        mehr_data = trend_agg[trend_agg["semester_code"].str.endswith("1")]
        bahman_data = trend_agg[trend_agg["semester_code"].str.endswith("2")]
        if trend_agg.empty:
            st.markdown(no_data_notice(selected_university), unsafe_allow_html=True)
        else:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=mehr_data["semester_code"], y=mehr_data["students"], name="نیمسال‌های مهرماه",
                                      mode="lines+markers+text", text=mehr_data["students"].map(lambda v: f"<b>{v:,.0f}</b>"),
                                      textposition="top center", textfont=dict(size=11, color="#991B1B", family="Vazirmatn", weight="bold"),
                                      line=dict(color="#DC2626", width=3), marker=dict(size=12, line=dict(width=2, color="#FFFFFF")),
                                      hovertemplate="<b>%{x}</b><br>مهرماه: %{y:,.0f}<extra></extra>"))
            fig.add_trace(go.Scatter(x=bahman_data["semester_code"], y=bahman_data["students"], name="نیمسال‌های بهمن‌ماه",
                                      mode="lines+markers+text", text=bahman_data["students"].map(lambda v: f"<b>{v:,.0f}</b>"),
                                      textposition="bottom center", textfont=dict(size=11, color="#0E7490", family="Vazirmatn", weight="bold"),
                                      line=dict(color="#0891B2", width=3), marker=dict(size=12, line=dict(width=2, color="#FFFFFF")),
                                      hovertemplate="<b>%{x}</b><br>بهمن‌ماه: %{y:,.0f}<extra></extra>"))
            fig.update_layout(title=dict(text=f"روند دانشجویان فعال — {selected_university}",
                                          font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")),
                              hovermode="x unified",
                              xaxis=dict(title="کد نیمسال", type="category", categoryorder="array", categoryarray=list(trend_agg["semester_code"])),
                              yaxis_title="تعداد دانشجو")
            st.plotly_chart(style_figure(fig, 540), use_container_width=True)

            st.markdown('<div class="section-header">🔥 نقشه حرارتی</div>', unsafe_allow_html=True)
            heat_data = student_long.pivot_table(index="university", columns="semester_code", values="students", aggfunc="sum").reindex(columns=semesters)
            if selected_university in heat_data.index:
                heat_data = heat_data.loc[[selected_university]]
            if heat_data.empty or heat_data.isna().all().all():
                st.markdown(no_data_notice(selected_university), unsafe_allow_html=True)
            else:
                heat_height = max(320, 80 * len(heat_data) + 220)
                fig = px.imshow(heat_data, text_auto=".0f", aspect="auto",
                                color_continuous_scale=[[0.0, "#EFF6FF"], [0.25, "#BFDBFE"], [0.5, "#60A5FA"], [0.75, "#2563EB"], [1.0, "#1E3A8A"]],
                                labels=dict(x="کد نیمسال", y="دانشگاه", color="تعداد"))
                fig.update_traces(textfont=dict(size=14, family="Vazirmatn, Tahoma", color="#0F172A", weight="bold"), xgap=3, ygap=3)
                fig.update_layout(title=dict(text=f"توزیع تعداد دانشجو — {selected_university}",
                                              font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")),
                                  margin=dict(l=25, r=25, t=60, b=50),
                                  coloraxis_colorbar=dict(title=dict(text="تعداد", font=dict(size=12, weight="bold")),
                                                          thickness=14, len=0.75, tickfont=dict(size=11, weight="bold")))
                fig.update_xaxes(tickangle=0, tickfont=dict(size=12, family="Vazirmatn", weight="bold"), side="bottom")
                fig.update_yaxes(tickfont=dict(size=13, family="Vazirmatn", weight="bold"))
                st.plotly_chart(style_figure(fig, heat_height), use_container_width=True)

            st.markdown('<div class="section-header">📊 تحلیل رشد/افت</div>', unsafe_allow_html=True)
            def _color_growth(val):
                if pd.isna(val):
                    return "—"
                c = "#059669" if val > 0 else ("#DC2626" if val < 0 else "#64748B")
                return f'<span style="color:{c};font-weight:800;">{val:+.1f}%</span>'
            render_pretty_table(pd.DataFrame({
                "دانشگاه": [selected_university],
                f"نیمسال {first_sem}": [fmt_int(first_students_val)],
                f"نیمسال {latest_sem}": [fmt_int(total_students)],
                "رشد/افت (%)": [_color_growth(growth_val)],
            }))

            st.markdown(f'<div class="section-header">🔮 پیش‌بینی تعداد دانشجویان برای نیمسال {selected_prediction_sem}</div>', unsafe_allow_html=True)
            uni_series = student_long[student_long["university"] == selected_university].sort_values("semester_code")
            y = uni_series["students"].values.astype(float)
            if len(y) >= 2:
                x = np.arange(len(y))
                slope, intercept = np.polyfit(x, y, 1)
                predicted = slope * (len(y) + prediction_offset) + intercept
            else:
                predicted = np.nan
            pred_fig = go.Figure()
            pred_fig.add_trace(go.Scatter(x=uni_series["semester_code"].tolist(), y=uni_series["students"].tolist(),
                                           mode="lines+markers+text", name="واقعی",
                                           line=dict(color="#1E40AF", width=3), marker=dict(size=12),
                                           text=[f"{v:,.0f}" for v in uni_series["students"]], textposition="top center",
                                           textfont=dict(size=11, color="#1E40AF", family="Vazirmatn", weight="bold")))
            if pd.notna(predicted):
                pred_fig.add_trace(go.Scatter(x=[selected_prediction_sem], y=[predicted], mode="markers+text", name="پیش‌بینی",
                                               marker=dict(size=20, color="#DC2626", symbol="star"),
                                               text=[f"<b>{predicted:,.0f}</b>"], textposition="top center",
                                               textfont=dict(size=14, color="#DC2626", weight="bold")))
            pred_fig.update_layout(title=dict(text=f"پیش‌بینی تعداد دانشجویان {selected_university} برای نیمسال {selected_prediction_sem}",
                                               font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")),
                                    xaxis_title="نیمسال", yaxis_title="تعداد دانشجو", hovermode="x unified")
            st.plotly_chart(style_figure(pred_fig, 450), use_container_width=True)

            render_pretty_table(pd.DataFrame([{
                "دانشگاه": selected_university,
                "آخرین نیمسال موجود": latest_sem,
                "تعداد دانشجویان در حال حاضر": fmt_int(total_students),
                "نیمسال هدف برای پیش بینی": selected_prediction_sem,
                "تعداد دانشجویان پیش بینی شده": fmt_int(predicted) if pd.notna(predicted) else "—",
            }]))

            st.markdown('<div class="section-header">🎯 مقایسه وضعیت تعداد دانشجویان فعلی و تعداد دانشجویان پیش بینی شده</div>', unsafe_allow_html=True)
            headers = ["دانشگاه", f"تعداد دانشجویان پیش بینی شده در {selected_prediction_sem}", "واقعی (ادمین)"]
            hcols = st.columns([1.6, 1.6, 1.6], gap="small")
            for i, lb in enumerate(headers):
                with hcols[i]:
                    st.markdown(f'<div class="admin-grid-header">{lb}</div>', unsafe_allow_html=True)
            rcols = st.columns([1.6, 1.6, 1.6], gap="small")
            with rcols[0]:
                st.markdown(f'<div class="admin-grid-cell">{selected_university}</div>', unsafe_allow_html=True)
            with rcols[1]:
                st.markdown(f'<div class="admin-grid-cell">{fmt_int(predicted) if pd.notna(predicted) else "—"}</div>', unsafe_allow_html=True)
            with rcols[2]:
                actual_value = st.number_input(f"واقعی — {selected_university}", min_value=0, value=0, step=1,
                                                key=f"actual_{selected_university}_{selected_prediction_sem}",
                                                label_visibility="collapsed")
            def _closeness(actual, pred):
                if pd.isna(actual) or pd.isna(pred) or actual == 0:
                    return "—"
                r = abs(actual - pred) / actual
                if r <= 0.05:
                    return '<span style="color:#059669;font-weight:800;">بسیار نزدیک</span>'
                if r <= 0.15:
                    return '<span style="color:#D97706;font-weight:800;">نزدیک</span>'
                return '<span style="color:#DC2626;font-weight:800;">دور از پیش‌بینی</span>'
            if actual_value > 0:
                st.markdown(sub_header("📊 نتیجه مقایسه تعداد دانشجویان پیش‌بینی شده با تعداد واقعی دانشجویان"), unsafe_allow_html=True)
                render_pretty_table(pd.DataFrame([{
                    "دانشگاه": selected_university,
                    "تعداد دانشجویان پیش بینی شده": fmt_int(predicted) if pd.notna(predicted) else "—",
                    "تعداد دانشجویان فعلی": fmt_int(actual_value),
                    "وضعیت": _closeness(actual_value, predicted),
                }]))
            else:
                st.markdown(rtl_alert("برای محاسبه دقت پیش‌بینی، مقدار «واقعی» را در فیلد بالا وارد کنید."), unsafe_allow_html=True)

with tab_financial:
    if not has_selected_data:
        st.markdown(no_data_notice(selected_university), unsafe_allow_html=True)
    elif "debt" not in combined.columns:
        st.info("داده بدهی در فایل مالی شناسایی نشد.")
    else:
        st.markdown(f'<div class="section-header">💰 تحلیل مالی <span class="badge badge-orange">نیمسال {selected_financial_sem}</span></div>', unsafe_allow_html=True)
        left, right = two_cols_with_vdivider(min_height=460)
        with left:
            fin_df = selected_data.dropna(subset=["debt"]).copy().sort_values("debt", ascending=True)
            if fin_df.empty:
                st.markdown(no_data_notice(selected_university), unsafe_allow_html=True)
            else:
                fig = go.Figure()
                fig.add_bar(name="مانده بدهی", y=fin_df["university"], x=fin_df["debt"], orientation="h",
                            marker=dict(color="#DC2626", line=dict(width=0)),
                            text=fin_df["debt"].map(lambda v: f"{v:,.0f}"),
                            hovertemplate="<b>%{y}</b><br>بدهی: %{x:,.0f} ریال<extra></extra>")
                if "installment" in fin_df.columns:
                    fig.add_bar(name="مبلغ تقسیط‌شده", y=fin_df["university"], x=fin_df["installment"], orientation="h",
                                marker=dict(color="#059669", line=dict(width=0)),
                                text=fin_df["installment"].map(lambda v: f"{v:,.0f}"),
                                hovertemplate="<b>%{y}</b><br>تقسیط: %{x:,.0f} ریال<extra></extra>")
                apply_auto_bar_text(fig, size=12)
                fig.update_layout(title=dict(text="مقایسه بدهی و تقسیط (ریال)",
                                             font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")),
                                  barmode="group", xaxis_title="ریال", yaxis_title="دانشگاه",
                                  bargap=0.3, margin=dict(l=25, r=200, t=70, b=55),
                                  xaxis=dict(tickformat=",.0f", exponentformat="none"))
                st.plotly_chart(style_figure(fig, max(400, 70 * len(fin_df) + 180)), use_container_width=True)
        with right:
            per_capita = selected_data.dropna(subset=["debt_per_student"]).copy().sort_values("debt_per_student")
            if per_capita.empty:
                st.markdown(no_data_notice(selected_university), unsafe_allow_html=True)
            else:
                fig = px.bar(per_capita, x="debt_per_student", y="university", orientation="h",
                             labels={"x": "ریال به‌ازای هر دانشجو", "university": "دانشگاه"},
                             color="university", color_discrete_map=color_map,
                             text=per_capita["debt_per_student"].map(lambda v: f"{v:,.0f}"))
                apply_auto_bar_text(fig, size=12)
                fig.update_layout(title=dict(text="بدهی سرانه هر دانشجو (ریال)",
                                             font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")),
                                  showlegend=False, bargap=0.35, xaxis_title="ریال", yaxis_title="دانشگاه",
                                  margin=dict(l=25, r=140, t=70, b=55),
                                  xaxis=dict(tickformat=",.0f", exponentformat="none"))
                st.plotly_chart(style_figure(fig, max(400, 70 * len(per_capita) + 180)), use_container_width=True)

        st.markdown(gradient_divider(), unsafe_allow_html=True)
        st.markdown('<div class="section-header">📐 شاخص‌های تحلیلی مالی</div>', unsafe_allow_html=True)
        st.markdown(explain_box("<b>سهم تقسیط از مطالبات:</b> تقسیط ÷ (بدهی + تقسیط) × ۱۰۰<br>"
                                "<b>نرخ مراجعه بدهکاران:</b> (تعداد بدهکاران − عدم مراجعه) ÷ تعداد بدهکاران × ۱۰۰"),
                    unsafe_allow_html=True)

        a1, a2 = two_cols_with_vdivider(min_height=460)
        with a1:
            inst_df = selected_data.dropna(subset=["installment_share"]).copy().sort_values("installment_share")
            if inst_df.empty:
                st.markdown(no_data_notice(selected_university), unsafe_allow_html=True)
            else:
                fig = px.bar(inst_df, x="installment_share", y="university", orientation="h",
                             color="university", color_discrete_map=color_map,
                             labels={"installment_share": "درصد", "university": "دانشگاه"},
                             text=inst_df["installment_share"].map(lambda v: f"{v:.1f}%"))
                apply_auto_bar_text(fig, size=12)
                fig.update_layout(title=dict(text="سهم تقسیط از کل مطالبات (٪)",
                                             font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")),
                                  showlegend=False, bargap=0.35,
                                  xaxis=dict(range=[0, 100], title="درصد"),
                                  yaxis=dict(title="دانشگاه"), margin=dict(l=25, r=140, t=70, b=55))
                st.plotly_chart(style_figure(fig, max(400, 70 * len(inst_df) + 180)), use_container_width=True)
        with a2:
            contact_df = selected_data.dropna(subset=["contact_rate"]).copy().sort_values("contact_rate")
            if contact_df.empty:
                st.markdown(no_data_notice(selected_university), unsafe_allow_html=True)
            else:
                cmin, cmax = float(contact_df["contact_rate"].min()), float(contact_df["contact_rate"].max())
                xmin, xmax = min(0, cmin) - 20, max(100, cmax) + 20
                fig = go.Figure()
                fig.add_trace(go.Bar(y=contact_df["university"], x=contact_df["contact_rate"], orientation="h",
                                     marker=dict(color=[color_map.get(u, "#3B82F6") for u in contact_df["university"]], line=dict(width=0)),
                                     text=[f"{v:.1f}%" for v in contact_df["contact_rate"]],
                                     hovertemplate="<b>%{y}</b><br>نرخ مراجعه: %{x:.1f}%<extra></extra>"))
                apply_auto_bar_text(fig, size=12)
                fig.add_vline(x=0, line=dict(color="#64748B", width=1.2, dash="dash"))
                fig.add_vline(x=100, line=dict(color="#94A3B8", width=1, dash="dot"))
                fig.update_layout(title=dict(text="نرخ مراجعه بدهکاران (٪)",
                                             font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")),
                                  showlegend=False, bargap=0.45,
                                  xaxis=dict(title="درصد", range=[xmin, xmax], tickfont=dict(size=12, weight="bold"), zeroline=False, showticklabels=True),
                                  yaxis=dict(title="دانشگاه", tickfont=dict(size=14, family="Vazirmatn", weight="bold"), automargin=True),
                                  margin=dict(l=25, r=140, t=70, b=55))
                st.plotly_chart(style_figure(fig, max(400, 70 * len(contact_df) + 180)), use_container_width=True)

        st.markdown(gradient_divider(), unsafe_allow_html=True)
        st.markdown('<div class="section-header">📋 جدول تفصیلی مالی</div>', unsafe_allow_html=True)
        fin_table = pd.DataFrame({"دانشگاه": selected_data["university"]})
        def _safe(col):
            return selected_data[col] if col in selected_data.columns else pd.Series([np.nan]*len(selected_data))
        fin_table["مانده بدهی (ریال)"] = _safe("debt").map(fmt_rial)
        fin_table["تقسیط (ریال)"] = _safe("installment").map(fmt_rial)
        fin_table["تعداد بدهکار"] = _safe("debtor_count").map(fmt_int)
        fin_table["عدم مراجعه"] = _safe("not_referred").map(fmt_int)
        fin_table["بدهی سرانه (ریال)"] = _safe("debt_per_student").map(fmt_rial)
        fin_table["سهم تقسیط از مطالبات"] = _safe("installment_share").map(lambda v: f"{v:.1f}%" if pd.notna(v) else "—")
        fin_table["نرخ مراجعه بدهکاران"] = _safe("contact_rate").map(lambda v: f"{v:.1f}%" if pd.notna(v) else "—")
        render_pretty_table(fin_table)

with tab_fin_perf:
    perf_matches_selected = perf_university is not None and _uni_key(perf_university) == _uni_key(selected_university)
    if not has_selected_data:
        st.markdown(no_data_notice(selected_university), unsafe_allow_html=True)
    elif not (perf_sheets and perf_sheet):
        st.markdown(center_notice("📭", f"داده‌ای برای دانشگاه <b>{selected_university}</b> در دسترس نیست.<br>لطفاً فایل عملکرد مالی <b>{selected_university}</b> را بارگذاری نمایید یا دانشگاه دیگری انتخاب کنید."), unsafe_allow_html=True)
    elif not perf_matches_selected:
        st.markdown(perf_mismatch_notice(selected_university), unsafe_allow_html=True)
    elif not perf_data or not perf_has_data(perf_data):
        st.markdown(perf_mismatch_notice(selected_university), unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="section-header">📈 خلاصه عملکرد مالی و پیش‌بینی وضعیت — {selected_university}</div>', unsafe_allow_html=True)
        inc_labels = ["شهریه", "برون‌سپاری", "کارگاه", "مجموع درآمد"]
        inc_hist = [perf_data["in_tuition"]["hist"], perf_data["in_outsourcing"]["hist"], perf_data["in_workshop"]["hist"], perf_data["in_total"]["hist"]]
        exp_labels = ["هیات علمی", "رسمی/قراردادی", "شرکتی", "اساتید مدعو", "اجاره", "سایر", "مجموع هزینه"]
        exp_hist = [perf_data["ex_faculty"]["hist"], perf_data["ex_official"]["hist"], perf_data["ex_corporate"]["hist"],
                    perf_data["ex_guest"]["hist"], perf_data["ex_rent"]["hist"], perf_data["ex_other"]["hist"], perf_data["ex_total"]["hist"]]

        st.markdown(sub_header("📊 عملکرد 1405-1404"), unsafe_allow_html=True)
        st.plotly_chart(make_financial_bar_full(inc_labels, inc_hist, "#1E40AF", "درآمدها — عملکرد 1405-1404 (ریال)", height=680, x_axis_title="سرفصل درآمدی"), use_container_width=True)
        add_below_legend(inc_labels)
        st.plotly_chart(make_financial_bar_full(exp_labels, exp_hist, "#DC2626", "هزینه‌ها — عملکرد 1405-1404 (ریال)", height=740, x_axis_title="سرفصل هزینه‌ای"), use_container_width=True)
        add_below_legend(exp_labels)

        st.markdown(gradient_divider(), unsafe_allow_html=True)
        st.markdown(sub_header("📊 وضعیت فعلی 1406-1405"), unsafe_allow_html=True)
        inc_curr = [perf_data["in_tuition"]["curr"], perf_data["in_outsourcing"]["curr"], perf_data["in_workshop"]["curr"], perf_data["in_total"]["curr"]]
        exp_curr = [perf_data["ex_faculty"]["curr"], perf_data["ex_official"]["curr"], perf_data["ex_corporate"]["curr"],
                    perf_data["ex_guest"]["curr"], perf_data["ex_rent"]["curr"], perf_data["ex_other"]["curr"], perf_data["ex_total"]["curr"]]
        st.plotly_chart(make_financial_bar_full(inc_labels, inc_curr, "#0E7490", "درآمدها — وضعیت فعلی 1406-1405 (ریال)", height=680, x_axis_title="سرفصل درآمدی"), use_container_width=True)
        add_below_legend(inc_labels)
        st.plotly_chart(make_financial_bar_full(exp_labels, exp_curr, "#D97706", "هزینه‌ها — وضعیت فعلی 1406-1405 (ریال)", height=740, x_axis_title="سرفصل هزینه‌ای"), use_container_width=True)
        add_below_legend(exp_labels)

        st.markdown(gradient_divider(), unsafe_allow_html=True)
        st.markdown('<div class="section-header">📋 جدول پیش‌بینی و وضعیت</div>', unsafe_allow_html=True)

        pred_col_name = f"پیش‌بینی {selected_prediction_sem}"
        rows = []
        for key in ["in_tuition", "in_outsourcing", "in_workshop", "in_total",
                    "ex_faculty", "ex_official", "ex_corporate", "ex_guest", "ex_rent", "ex_other", "ex_total"]:
            title = perf_data[key]["title"]
            hist = perf_data[key]["hist"]
            curr = perf_data[key]["curr"]
            history = perf_data[key].get("history", [])
            pred = forecast_value(history, prediction_offset)

            if curr == 0 and pred == 0:
                status_str = '<span style="color:#7C3AED;font-weight:800;">—</span>'
            elif pred == 0:
                status_str = '<span style="color:#7C3AED;font-weight:800;">—</span>'
            elif abs(curr - pred) / abs(pred) < 0.05:
                status_str = '<span style="color:#7C3AED;font-weight:800;">مطابق پیش‌بینی</span>'
            elif curr > pred:
                status_str = f'<span style="color:#059669;font-weight:800;">بیشتر از پیش‌بینی ({curr - pred:+,.0f})</span>'
            else:
                status_str = f'<span style="color:#DC2626;font-weight:800;">کمتر از پیش‌بینی ({curr - pred:+,.0f})</span>'

            if "مجموع درآمد" in title:
                td = f'<span style="color:#1E40AF;font-weight:800;">{title}</span>'
            elif "مجموع هزینه" in title:
                td = f'<span style="color:#DC2626;font-weight:800;">{title}</span>'
            else:
                td = title

            rows.append({
                "شرح": td,
                "عملکرد 1405-1404": fmt_rial(hist),
                "وضعیت فعلی 1406-1405": fmt_rial(curr),
                pred_col_name: f'<span style="color:#7C3AED;font-weight:800;">{pred:,.0f}</span>',
                "وضعیت فعلی نسبت به پیش‌بینی": status_str,
            })
        render_pretty_table(pd.DataFrame(rows))

        st.markdown(gradient_divider(), unsafe_allow_html=True)
        st.markdown('<div class="section-header">📊 نمودار سود یا زیان</div>', unsafe_allow_html=True)
        pl_labels = ["عملکرد 1405-1404", "وضعیت فعلی 1406-1405"]
        pl_vals = [perf_data["profit"]["hist"], perf_data["profit"]["curr"]]
        st.plotly_chart(make_financial_bar_full(pl_labels, pl_vals, None, "نمودار سود یا زیان (ریال)", height=620, color_list=["#059669", "#3B82F6"], x_axis_title="بازه زمانی"), use_container_width=True)
        add_below_legend(pl_labels, title_prefix="📌 بازه زمانی")

st.divider()
st.caption("داشبورد مدیریتی هوشمند مراکز آموزشی دانشگاه آزاد اسلامی استان گلستان — داده‌ها از فایل‌های اکسل استخراج می‌شوند.")