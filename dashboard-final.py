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
    page_title="داشبورد مدیریتی هوشمند مراکز آموزشی دانشگاه آزاد اسلامی استان گلستان",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

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
ALL_UNIVERSITIES_LABEL = "🏛️ همه دانشگاه‌ها"

UNIVERSITY_ALIASES = {
    "مبنودشت": "مینودشت", "مینو دشت": "مینودشت",
    "بندر ترکمن": "بندرترکمن", "بندرتركمن": "بندرترکمن",
    "آق‌قلا": "آق قلا", "آق قلا": "آق قلا", "اق قلا": "آق قلا",
    "كردكوی": "کردکوی", "كردكوي": "کردکوی",
    "گميشان": "گمیشان", "كلاوه": "کلاله",
}

FALLBACK_LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.95"/><stop offset="100%" stop-color="#DBEAFE" stop-opacity="0.85"/></linearGradient></defs><circle cx="60" cy="60" r="52" fill="url(#g)" opacity="0.18"/><circle cx="60" cy="60" r="42" fill="none" stroke="white" stroke-width="2.5" opacity="0.85"/><path d="M35 55 L60 42 L85 55 L60 68 Z" fill="white" opacity="0.95"/><path d="M42 60 L42 74 Q60 84 78 74 L78 60" fill="none" stroke="white" stroke-width="2.5" stroke-linejoin="round"/><circle cx="60" cy="55" r="3" fill="#1E40AF"/><text x="60" y="98" font-family="Arial" font-size="12" font-weight="700" text-anchor="middle" fill="white" opacity="0.95">IAU</text></svg>"""


def get_logo_data_uri() -> str:
    for base in (BASE_DIR, DATA_DIR):
        for ext, mime in {"png":"image/png","jpg":"image/jpeg","jpeg":"image/jpeg","svg":"image/svg+xml","webp":"image/webp"}.items():
            path = base / f"azad-logo.{ext}"
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
[data-testid="stSidebar"] .stButton>button{background:linear-gradient(135deg,#DC2626,#EF4444);color:#FFF;border:none;border-radius:10px;padding:10px 16px;font-weight:700;font-size:14px;transition:all 0.2s ease;box-shadow:0 4px 12px rgba(220,38,38,0.25)}
[data-testid="stSidebar"] .stButton>button:hover{background:linear-gradient(135deg,#B91C1C,#DC2626);box-shadow:0 6px 16px rgba(220,38,38,0.35);transform:translateY(-1px)}
.stTabs [data-baseweb="tab-list"]{gap:6px;direction:rtl;border-bottom:2px solid #E5E9F2}
.stTabs [data-baseweb="tab"]{height:46px;padding:0 22px;background-color:transparent;border-radius:10px 10px 0 0;font-weight:600;color:#64748B}
.stTabs [aria-selected="true"]{background-color:#FFF;color:#1E40AF;border-bottom:3px solid #1E40AF}
.stDownloadButton>button{background:linear-gradient(135deg,#1E40AF,#3B82F6);color:white;border:none;border-radius:10px;padding:10px 24px;font-weight:600}
.stDownloadButton>button:hover{background:linear-gradient(135deg,#1E3A8A,#2563EB)}
div[data-testid="stMetric"]{display:none}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p,.stCaption,.stCaption p{direction:rtl!important;text-align:right!important}
</style>
""", unsafe_allow_html=True)


# ============================================================
# ابزارهای کمکی
# ============================================================
def normalize_text(value) -> str:
    if pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = text.replace("ي", "ی").replace("ك", "ک")
    text = text.replace("\u200c", " ").replace("\u200f", "").replace("\u200e", "")
    return re.sub(r"\s+", " ", text).strip()


def normalize_uni_name(name):
    if not name:
        return None
    n = normalize_text(name).replace(" ", "").replace("\u200c", "").lower()
    if not n:
        return None
    for alias, canonical in UNIVERSITY_ALIASES.items():
        if normalize_text(alias).replace(" ", "").lower() == n:
            return canonical
    for u in KNOWN_UNIVERSITIES:
        if normalize_text(u).replace(" ", "").lower() == n:
            return u
    return None


def parse_number(value) -> float:
    if pd.isna(value):
        return np.nan
    if isinstance(value, (int, float, np.number)):
        r = float(value)
        return r if np.isfinite(r) else np.nan
    text = unicodedata.normalize("NFKC", str(value)).strip()
    text = text.replace("ي", "ی").replace("ك", "ک")
    text = text.translate(DIGIT_TRANSLATION)
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
    """پیام یکدست برای داده‌های ناموجود"""
    return center_notice("📭", f"داده‌ای برای دانشگاه <b>{u}</b> در دسترس نیست و دانشگاه دیگری را انتخاب کنید.")


def all_data_missing_notice():
    return center_notice("📭", "داده‌ای برای هیچ دانشگاهی در دسترس نیست.")


def render_pretty_table(df):
    st.markdown(df.to_html(escape=False, index=False, classes="pretty-table", border=0, na_rep="—"), unsafe_allow_html=True)


# ============================================================
# خواندن اکسل
# ============================================================
@st.cache_data(show_spinner=False, max_entries=16)
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


def pick_first_sheet(sheets) -> tuple:
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
        for alias, canonical in UNIVERSITY_ALIASES.items():
            if _uni_key(alias) in _uni_key(sn):
                return canonical
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


# ============================================================
# استایل نمودارها
# ============================================================
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


# ============================================================
# استخراج داده‌ها
# ============================================================
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
        for uni_col in uni_cols:
            uni_canonical = normalize_uni_name(uni_col) or normalize_text(uni_col)
            val = parse_number(row[uni_col])
            if pd.notna(val):
                records.append({"university": uni_canonical, "semester_code": sem_code, "students": val})
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
        raw_uni = normalize_text(row[uni_col])
        if not raw_uni or is_total_label(raw_uni):
            continue
        uni_canonical = normalize_uni_name(raw_uni) or raw_uni
        rec = {"university": uni_canonical}
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
        if curr_col is None or df[curr_col].dropna().empty:
            curr_col = next((c for c in df.columns if "پیش بینی" in c), None)

        items_map = {
            "in_tuition": "درآمد شهریه ای", "in_outsourcing": "درآمد غیرشهریه ای (برون سپاری)",
            "in_workshop": "درآمد غیرشهریه ای (برگزاری کارگاه)", "ex_faculty": "هزینه پرسنلی هیات علمی",
            "ex_official": "هزینه پرسنلی رسمی و قراردادی", "ex_corporate": "هزینه پرسنلی شرکتی",
            "ex_guest": "هزینه حق التدریس اساتید مدعو", "ex_rent": "هزینه اجاره",
            "ex_other": "هزینه های جاری (سایر)",
        }
        alt_keywords = {
            "in_workshop": ["درآمد غیرشهریه ای (سایر)", "درآمد غیرشهریه‌ای (سایر)"],
        }
        data = {}
        for key, kw in items_map.items():
            mask = df[title_col].astype(str).str.contains(kw, regex=False, na=False)
            if not mask.any() and key in alt_keywords:
                for alt_kw in alt_keywords[key]:
                    mask = df[title_col].astype(str).str.contains(alt_kw, regex=False, na=False)
                    if mask.any():
                        break
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


def load_all_perf_data(sheets: dict) -> dict:
    result = {}
    if not sheets:
        return result
    for sheet_name, df in sheets.items():
        if df is None or df.empty:
            continue
        uni = detect_perf_university(df, sheet_name)
        if not uni:
            sn = normalize_text(sheet_name)
            for alias, canonical in UNIVERSITY_ALIASES.items():
                if normalize_text(alias) in sn:
                    uni = canonical
                    break
        if not uni or uni in result:
            continue
        data = extract_perf_data(df)
        if data and perf_has_data(data):
            result[uni] = data
    return result


def load_file_bytes(default_names):
    """فقط از پوشه‌های BASE_DIR و DATA_DIR روی سرور می‌خواند."""
    if isinstance(default_names, str):
        default_names = [default_names]
    for name in default_names:
        for base in (BASE_DIR, DATA_DIR):
            p = base / name
            if p.exists():
                return p.read_bytes()
    return None


# ============================================================
# HEADER
# ============================================================
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

# ============================================================
# SIDEBAR — انتخاب دانشگاه
# ============================================================
with st.sidebar:
    st.markdown("### 🏛️ دانشگاه")
    selector_options = [ALL_UNIVERSITIES_LABEL] + KNOWN_UNIVERSITIES
    selected_university_option = st.selectbox(
        "دانشگاه خود را انتخاب کنید",
        options=selector_options,
        index=0,
        key="main_university_selector",
        help="«همه دانشگاه‌ها» را برای مشاهده تمام واحدها در هر سه تب انتخاب کنید.",
    )
    is_all_mode = selected_university_option == ALL_UNIVERSITIES_LABEL
    selected_university = None if is_all_mode else selected_university_option

    st.divider()
    st.markdown("### ⚙️ منابع داده")
    st.caption("فایل‌های مورد نیاز به‌صورت خودکار از سرور خوانده می‌شوند.")

# ---------- بارگذاری فایل‌ها از سرور ----------
student_bytes = load_file_bytes(["uni-students.xlsx", "uni-proj.xlsx", "students.xlsx"])
financial_bytes = load_file_bytes(["uni-financial.xlsx", "uni-proj2.xlsx", "financial.xlsx"])
perf_bytes = load_file_bytes(["uni-proj4.xlsx", "perf.xlsx"])

if student_bytes is None or financial_bytes is None:
    st.markdown("""
    <div class="welcome-box">
      <span class="welcome-icon">📂</span>
      <div class="welcome-title">فایل‌های داده یافت نشد</div>
      <div class="welcome-text">
        لطفاً فایل‌های <b>uni-students.xlsx</b>، <b>uni-financial.xlsx</b> و (اختیاری) <b>uni-proj4.xlsx</b> را
        در پوشه <code>data/</code> روی سرور قرار دهید و صفحه را دوباره بارگذاری کنید.
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

try:
    student_sheets = read_workbook(student_bytes)
    financial_sheets = read_workbook(financial_bytes)
except Exception as exc:
    st.error("خواندن فایل اکسل ناموفق بود.")
    with st.expander("جزئیات خطا"):
        st.code(str(exc))
    st.stop()

student_sheet, student_raw = pick_first_sheet(student_sheets)
financial_sheet, financial_raw = pick_first_sheet(financial_sheets)

if student_raw.empty or financial_raw.empty:
    st.warning("یکی از فایل‌های اصلی (دانشجویان یا مالی) خالی است.")
    st.stop()

student_long = extract_student_long(student_raw)
financial_df = extract_financial(financial_raw)

if student_long.empty:
    st.error("داده دانشجویان قابل استخراج نبود.")
    st.stop()

semesters = sorted(student_long["semester_code"].unique())
first_sem, latest_sem = semesters[0], semesters[-1]

perf_sheets = read_workbook(perf_bytes) if perf_bytes else {}
perf_data_all = load_all_perf_data(perf_sheets)

# ============================================================
# جدول ترکیبی
# ============================================================
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

# ============================================================
# SIDEBAR — مقایسه و نیمسال‌ها
# ============================================================
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

# ============================================================
# اعتبارسنجی مقایسه
# ============================================================
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
        st.markdown(center_notice("⚠️", f"برای مقایسه حداقل <b>دو دانشگاه</b> باید در فایل‌ها موجود باشند.<br>از {len(compared_universities)} انتخاب، تنها <b>{len(valid_compared)}</b> مورد یافت شد."), unsafe_allow_html=True)
        st.stop()

# ============================================================
# مقایسه تفصیلی
# ============================================================
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
                fig.update_layout(title=dict(text="مقایسه بدهی و تقسیط",
                                             font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")),
                                  barmode="group", xaxis_title="مبلغ (ریال)", yaxis_title="دانشگاه",
                                  bargap=0.3, margin=dict(l=25, r=200, t=70, b=55),
                                  xaxis=dict(tickformat=",.0f", exponentformat="none"))
                st.plotly_chart(style_figure(fig, max(420, 65 * len(fin_df) + 160)), use_container_width=True)
        with m_right:
            per_capita = comparison_data.dropna(subset=["debt_per_student"]).copy().sort_values("debt_per_student")
            if not per_capita.empty:
                fig = px.bar(per_capita, x="debt_per_student", y="university", orientation="h",
                             color="university", color_discrete_map=color_map,
                             text=per_capita["debt_per_student"].map(lambda v: f"{v:,.0f}"))
                apply_auto_bar_text(fig, size=11)
                fig.update_layout(title=dict(text="بدهی سرانه هر دانشجو",
                                             font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")),
                                  showlegend=False, bargap=0.35,
                                  xaxis=dict(title="مبلغ (ریال به ازای هر دانشجو)", tickformat=",.0f", exponentformat="none"),
                                  yaxis=dict(title="دانشگاه"),
                                  margin=dict(l=25, r=140, t=70, b=55))
                st.plotly_chart(style_figure(fig, max(420, 65 * len(per_capita) + 160)), use_container_width=True)

        st.markdown(gradient_divider(), unsafe_allow_html=True)
        n_left, n_right = two_cols_with_vdivider(min_height=440)
        with n_left:
            inst_df = comparison_data.dropna(subset=["installment_share"]).copy().sort_values("installment_share")
            if not inst_df.empty:
                fig = px.bar(inst_df, x="installment_share", y="university", orientation="h",
                             color="university", color_discrete_map=color_map,
                             text=inst_df["installment_share"].map(lambda v: f"{v:.1f}%"))
                apply_auto_bar_text(fig, size=11)
                fig.update_layout(title=dict(text="سهم تقسیط از کل مطالبات",
                                             font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")),
                                  showlegend=False, bargap=0.35,
                                  xaxis=dict(title="درصد", range=[0, 100]),
                                  yaxis=dict(title="دانشگاه"),
                                  margin=dict(l=25, r=140, t=70, b=55))
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
                fig.update_layout(title=dict(text="نرخ مراجعه بدهکاران",
                                             font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")),
                                  showlegend=False, bargap=0.45,
                                  xaxis=dict(title="درصد", range=[xmin, xmax], tickfont=dict(size=12, weight="bold"), zeroline=False),
                                  yaxis=dict(title="دانشگاه", tickfont=dict(size=14, family="Vazirmatn", weight="bold"), automargin=True),
                                  margin=dict(l=25, r=140, t=70, b=55))
                st.plotly_chart(style_figure(fig, max(420, 70 * len(contact_df) + 180)), use_container_width=True)

    st.markdown('<div class="section-header">📋 جدول خلاصه مقایسه</div>', unsafe_allow_html=True)
    def _safe_series(df, col):
        return df[col] if col in df.columns else pd.Series([np.nan] * len(df))
    cmp_summary = pd.DataFrame({
        "دانشگاه": comparison_data["university"],
        f"دانشجو ({first_sem})": _safe_series(comparison_data, "students_first").map(fmt_int),
        f"دانشجو ({latest_sem})": _safe_series(comparison_data, "students_latest").map(fmt_int),
        "رشد/افت (%)": _safe_series(comparison_data, "growth_pct").map(lambda v: fmt_pct(v) if pd.notna(v) else "—"),
        "بدهی (ریال)": _safe_series(comparison_data, "debt").map(fmt_rial),
        "تقسیط (ریال)": _safe_series(comparison_data, "installment").map(fmt_rial),
        "بدهی سرانه (ریال)": _safe_series(comparison_data, "debt_per_student").map(fmt_rial),
        "تعداد بدهکار": _safe_series(comparison_data, "debtor_count").map(fmt_int),
        "عدم مراجعه": _safe_series(comparison_data, "not_referred").map(fmt_int),
        "سهم تقسیط": _safe_series(comparison_data, "installment_share").map(lambda v: f"{v:.1f}%" if pd.notna(v) else "—"),
        "نرخ مراجعه": _safe_series(comparison_data, "contact_rate").map(lambda v: f"{v:.1f}%" if pd.notna(v) else "—"),
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

# ============================================================
# حالت «همه دانشگاه‌ها»
# ============================================================
if is_all_mode:
    n_units = len(combined)
    st.markdown(f'<div class="section-header">📍 نمای کلی همه دانشگاه‌ها ({n_units} واحد)</div>', unsafe_allow_html=True)

    if combined.empty:
        st.markdown(all_data_missing_notice(), unsafe_allow_html=True)
        st.stop()

    all_students = combined["students_latest"].sum(min_count=1)
    all_first = combined["students_first"].sum(min_count=1) if "students_first" in combined.columns else np.nan
    all_debt = combined["debt"].sum(min_count=1) if "debt" in combined.columns else np.nan
    all_installment = combined["installment"].sum(min_count=1) if "installment" in combined.columns else np.nan
    all_debtors = combined["debtor_count"].sum(min_count=1) if "debtor_count" in combined.columns else np.nan
    all_not_referred = combined["not_referred"].sum(min_count=1) if "not_referred" in combined.columns else np.nan
    all_debt_per_student = (all_debt / all_students) if pd.notna(all_debt) and pd.notna(all_students) and all_students > 0 else np.nan
    all_growth = ((all_students - all_first) / all_first * 100) if pd.notna(all_first) and all_first > 0 else np.nan

    st.markdown('<div class="section-header">📊 شاخص‌های کلیدی کل استان</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(kpi_card(f"کل دانشجویان — {latest_sem}", fmt_int(all_students), "نفر", "blue"), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card(f"کل مانده بدهی — {selected_financial_sem}", fmt_rial(all_debt), "ریال", "red"), unsafe_allow_html=True)
    with c3: st.markdown(kpi_card(f"کل تقسیط — {selected_financial_sem}", fmt_rial(all_installment), "ریال", "green"), unsafe_allow_html=True)
    with c4: st.markdown(kpi_card("بدهی سرانه کل", fmt_rial(all_debt_per_student), "ریال/دانشجو", "purple"), unsafe_allow_html=True)
    c5, c6, c7, c8 = st.columns(4)
    with c5: st.markdown(kpi_card("کل بدهکاران", fmt_int(all_debtors), "نفر", "orange"), unsafe_allow_html=True)
    with c6: st.markdown(kpi_card("عدم مراجعه", fmt_int(all_not_referred), "نفر", "slate"), unsafe_allow_html=True)
    with c7: st.markdown(kpi_card("تعداد واحدها", fmt_int(n_units), "دانشگاه", "cyan"), unsafe_allow_html=True)
    with c8: st.markdown(kpi_card(f"رشد کل ({first_sem} → {latest_sem})", fmt_pct(all_growth) if pd.notna(all_growth) else "—", "درصد", "green"), unsafe_allow_html=True)

    st.markdown('<div class="section-header">📋 جدول شاخص‌های کلیدی هر دانشگاه</div>', unsafe_allow_html=True)
    def _safe_col(df, col):
        return df[col] if col in df.columns else pd.Series([np.nan] * len(df))
    overview_table = pd.DataFrame({
        "دانشگاه": combined["university"],
        f"دانشجو ({latest_sem})": _safe_col(combined, "students_latest").map(fmt_int),
        f"دانشجو ({first_sem})": _safe_col(combined, "students_first").map(fmt_int),
        "رشد/افت (%)": _safe_col(combined, "growth_pct").map(lambda v: fmt_pct(v) if pd.notna(v) else "—"),
        "بدهی (ریال)": _safe_col(combined, "debt").map(fmt_rial),
        "تقسیط (ریال)": _safe_col(combined, "installment").map(fmt_rial),
        "بدهی سرانه": _safe_col(combined, "debt_per_student").map(fmt_rial),
        "تعداد بدهکار": _safe_col(combined, "debtor_count").map(fmt_int),
        "عدم مراجعه": _safe_col(combined, "not_referred").map(fmt_int),
        "سهم تقسیط": _safe_col(combined, "installment_share").map(lambda v: f"{v:.1f}%" if pd.notna(v) else "—"),
        "نرخ مراجعه": _safe_col(combined, "contact_rate").map(lambda v: f"{v:.1f}%" if pd.notna(v) else "—"),
    })
    render_pretty_table(overview_table)

    tab_trend_all, tab_fin_all, tab_perf_all = st.tabs([
        "📈 روند دانشجویان (همه)", "💰 تحلیل مالی (همه)", "📈 عملکرد مالی (همه)",
    ])

    # ---------- تب روند همه ----------
    with tab_trend_all:
        st.markdown('<div class="section-header">📈 روند دانشجویان تمام دانشگاه‌ها</div>', unsafe_allow_html=True)
        trend_pivot = student_long.pivot_table(index="semester_code", columns="university", values="students", aggfunc="sum").sort_index()
        if trend_pivot.empty:
            st.markdown(all_data_missing_notice(), unsafe_allow_html=True)
        else:
            fig = go.Figure()
            for uni in trend_pivot.columns:
                fig.add_trace(go.Scatter(
                    x=trend_pivot.index.tolist(), y=trend_pivot[uni].tolist(),
                    name=uni, mode="lines+markers",
                    line=dict(color=color_map.get(uni, "#3B82F6"), width=2.5),
                    marker=dict(size=9, line=dict(width=1.5, color="#FFFFFF")),
                    hovertemplate=f"<b>{uni}</b><br>%{{x}}<br>%{{y:,.0f}} نفر<extra></extra>",
                ))
            fig.update_layout(title=dict(text="روند دانشجویان فعال — همه دانشگاه‌ها",
                                          font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")),
                              hovermode="x unified",
                              xaxis=dict(title="کد نیمسال", type="category"),
                              yaxis=dict(title="تعداد دانشجو"))
            st.plotly_chart(style_figure(fig, 580), use_container_width=True)

            st.markdown('<div class="section-header">🔥 نقشه حرارتی همه دانشگاه‌ها</div>', unsafe_allow_html=True)
            heat_data = student_long.pivot_table(index="university", columns="semester_code", values="students", aggfunc="sum").reindex(columns=semesters)
            heat_height = max(360, 55 * len(heat_data) + 220)
            fig = px.imshow(heat_data, text_auto=".0f", aspect="auto",
                            color_continuous_scale=[[0.0, "#EFF6FF"], [0.25, "#BFDBFE"], [0.5, "#60A5FA"], [0.75, "#2563EB"], [1.0, "#1E3A8A"]],
                            labels=dict(x="کد نیمسال", y="دانشگاه", color="تعداد"))
            fig.update_traces(textfont=dict(size=12, family="Vazirmatn, Tahoma", color="#0F172A", weight="bold"), xgap=2, ygap=2)
            fig.update_layout(title=dict(text="توزیع تعداد دانشجو — همه دانشگاه‌ها",
                                          font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")),
                              xaxis_title="کد نیمسال", yaxis_title="دانشگاه",
                              margin=dict(l=25, r=25, t=60, b=50))
            st.plotly_chart(style_figure(fig, heat_height), use_container_width=True)

            st.markdown(f'<div class="section-header">🔮 پیش‌بینی دانشجویان برای نیمسال {selected_prediction_sem}</div>', unsafe_allow_html=True)
            pred_rows = []
            for uni in student_long["university"].unique():
                s = student_long[student_long["university"] == uni].sort_values("semester_code")
                y = s["students"].values.astype(float)
                if len(y) >= 2:
                    x = np.arange(len(y))
                    slope, intercept = np.polyfit(x, y, 1)
                    pred = float(slope * (len(y) + prediction_offset) + intercept)
                elif len(y) == 1:
                    pred = float(y[0] * (1.05 ** (prediction_offset + 1)))
                else:
                    pred = np.nan
                pred_rows.append({
                    "دانشگاه": uni,
                    "آخرین نیمسال": s["semester_code"].iloc[-1] if not s.empty else "—",
                    "دانشجوی فعلی": fmt_int(y[-1]) if len(y) > 0 else "—",
                    f"پیش‌بینی {selected_prediction_sem}": fmt_int(pred) if pd.notna(pred) else "—",
                })
            render_pretty_table(pd.DataFrame(pred_rows))

    # ---------- تب مالی همه ----------
    with tab_fin_all:
        if "debt" not in combined.columns:
            st.markdown(all_data_missing_notice(), unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="section-header">💰 مقایسه مالی همه دانشگاه‌ها <span class="badge badge-orange">نیمسال {selected_financial_sem}</span></div>', unsafe_allow_html=True)
            left, right = two_cols_with_vdivider(min_height=460)
            with left:
                fin_df = combined.dropna(subset=["debt"]).copy().sort_values("debt", ascending=True)
                if fin_df.empty:
                    st.markdown(all_data_missing_notice(), unsafe_allow_html=True)
                else:
                    fig = go.Figure()
                    fig.add_bar(name="مانده بدهی", y=fin_df["university"], x=fin_df["debt"], orientation="h",
                                marker=dict(color="#DC2626"),
                                text=fin_df["debt"].map(lambda v: f"{v:,.0f}"),
                                hovertemplate="<b>%{y}</b><br>بدهی: %{x:,.0f} ریال<extra></extra>")
                    if "installment" in fin_df.columns:
                        fig.add_bar(name="مبلغ تقسیط", y=fin_df["university"], x=fin_df["installment"], orientation="h",
                                    marker=dict(color="#059669"),
                                    text=fin_df["installment"].map(lambda v: f"{v:,.0f}"),
                                    hovertemplate="<b>%{y}</b><br>تقسیط: %{x:,.0f} ریال<extra></extra>")
                    apply_auto_bar_text(fig, size=11)
                    fig.update_layout(title=dict(text="مقایسه بدهی و تقسیط همه دانشگاه‌ها",
                                                 font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")),
                                      barmode="group",
                                      xaxis=dict(title="مبلغ (ریال)", tickformat=",.0f", exponentformat="none"),
                                      yaxis=dict(title="دانشگاه"),
                                      bargap=0.3)
                    st.plotly_chart(style_figure(fig, max(420, 55 * len(fin_df) + 160)), use_container_width=True)
            with right:
                per_capita = combined.dropna(subset=["debt_per_student"]).copy().sort_values("debt_per_student")
                if per_capita.empty:
                    st.markdown(all_data_missing_notice(), unsafe_allow_html=True)
                else:
                    fig = px.bar(per_capita, x="debt_per_student", y="university", orientation="h",
                                 color="university", color_discrete_map=color_map,
                                 text=per_capita["debt_per_student"].map(lambda v: f"{v:,.0f}"))
                    apply_auto_bar_text(fig, size=11)
                    fig.update_layout(title=dict(text="بدهی سرانه هر دانشجو",
                                                 font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")),
                                      showlegend=False, bargap=0.35,
                                      xaxis=dict(title="مبلغ (ریال به ازای هر دانشجو)", tickformat=",.0f", exponentformat="none"),
                                      yaxis=dict(title="دانشگاه"))
                    st.plotly_chart(style_figure(fig, max(420, 55 * len(per_capita) + 160)), use_container_width=True)

            st.markdown(gradient_divider(), unsafe_allow_html=True)
            a1, a2 = two_cols_with_vdivider(min_height=460)
            with a1:
                inst_df = combined.dropna(subset=["installment_share"]).copy().sort_values("installment_share")
                if inst_df.empty:
                    st.markdown(all_data_missing_notice(), unsafe_allow_html=True)
                else:
                    fig = px.bar(inst_df, x="installment_share", y="university", orientation="h",
                                 color="university", color_discrete_map=color_map,
                                 text=inst_df["installment_share"].map(lambda v: f"{v:.1f}%"))
                    apply_auto_bar_text(fig, size=11)
                    fig.update_layout(title=dict(text="سهم تقسیط از مطالبات",
                                                 font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")),
                                      showlegend=False, bargap=0.35,
                                      xaxis=dict(title="درصد", range=[0, 100]),
                                      yaxis=dict(title="دانشگاه"))
                    st.plotly_chart(style_figure(fig, max(420, 55 * len(inst_df) + 160)), use_container_width=True)
            with a2:
                contact_df = combined.dropna(subset=["contact_rate"]).copy().sort_values("contact_rate")
                if contact_df.empty:
                    st.markdown(all_data_missing_notice(), unsafe_allow_html=True)
                else:
                    cmin, cmax = float(contact_df["contact_rate"].min()), float(contact_df["contact_rate"].max())
                    xmin, xmax = min(0, cmin) - 20, max(100, cmax) + 20
                    fig = go.Figure(go.Bar(y=contact_df["university"], x=contact_df["contact_rate"], orientation="h",
                                           marker=dict(color=[color_map.get(u, "#3B82F6") for u in contact_df["university"]]),
                                           text=[f"{v:.1f}%" for v in contact_df["contact_rate"]],
                                           hovertemplate="<b>%{y}</b><br>%{x:.1f}%<extra></extra>"))
                    apply_auto_bar_text(fig, size=11)
                    fig.add_vline(x=0, line=dict(color="#64748B", width=1.2, dash="dash"))
                    fig.add_vline(x=100, line=dict(color="#94A3B8", width=1, dash="dot"))
                    fig.update_layout(title=dict(text="نرخ مراجعه بدهکاران",
                                                 font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")),
                                      showlegend=False, bargap=0.45,
                                      xaxis=dict(title="درصد", range=[xmin, xmax]),
                                      yaxis=dict(title="دانشگاه"))
                    st.plotly_chart(style_figure(fig, max(420, 55 * len(contact_df) + 160)), use_container_width=True)

            st.markdown('<div class="section-header">📋 جدول تفصیلی مالی همه دانشگاه‌ها</div>', unsafe_allow_html=True)
            fin_table = pd.DataFrame({
                "دانشگاه": combined["university"],
                "مانده بدهی (ریال)": _safe_col(combined, "debt").map(fmt_rial),
                "تقسیط (ریال)": _safe_col(combined, "installment").map(fmt_rial),
                "تعداد بدهکار": _safe_col(combined, "debtor_count").map(fmt_int),
                "عدم مراجعه": _safe_col(combined, "not_referred").map(fmt_int),
                "بدهی سرانه": _safe_col(combined, "debt_per_student").map(fmt_rial),
                "سهم تقسیط": _safe_col(combined, "installment_share").map(lambda v: f"{v:.1f}%" if pd.notna(v) else "—"),
                "نرخ مراجعه": _safe_col(combined, "contact_rate").map(lambda v: f"{v:.1f}%" if pd.notna(v) else "—"),
            })
            render_pretty_table(fin_table)

    # ---------- تب عملکرد مالی همه ----------
    with tab_perf_all:
        st.markdown('<div class="section-header">📈 عملکرد مالی همه دانشگاه‌ها</div>', unsafe_allow_html=True)
        if not perf_data_all:
            st.markdown(center_notice("📭", "داده‌ای برای هیچ دانشگاهی در بخش عملکرد مالی در دسترس نیست."), unsafe_allow_html=True)
        else:
            summary_rows = []
            for uni, d in perf_data_all.items():
                summary_rows.append({
                    "دانشگاه": uni,
                    "درآمد ۱۴۰۵-۱۴۰۴": fmt_rial(d["in_total"]["hist"]),
                    "هزینه ۱۴۰۵-۱۴۰۴": fmt_rial(d["ex_total"]["hist"]),
                    "سود ۱۴۰۵-۱۴۰۴": fmt_rial(d["profit"]["hist"]),
                    "درآمد فعلی": fmt_rial(d["in_total"]["curr"]),
                    "هزینه فعلی": fmt_rial(d["ex_total"]["curr"]),
                    "سود فعلی": fmt_rial(d["profit"]["curr"]),
                })
            render_pretty_table(pd.DataFrame(summary_rows))

            st.markdown(sub_header("📊 مقایسه سود/زیان همه دانشگاه‌ها"), unsafe_allow_html=True)
            profit_df = pd.DataFrame({
                "دانشگاه": list(perf_data_all.keys()),
                "سود ۱۴۰۵-۱۴۰۴": [d["profit"]["hist"] for d in perf_data_all.values()],
                "سود فعلی": [d["profit"]["curr"] for d in perf_data_all.values()],
            })
            long_profit = pd.concat([
                profit_df[["دانشگاه", "سود ۱۴۰۵-۱۴۰۴"]].rename(columns={"سود ۱۴۰۵-۱۴۰۴": "سود"}).assign(دوره="۱۴۰۵-۱۴۰۴"),
                profit_df[["دانشگاه", "سود فعلی"]].rename(columns={"سود فعلی": "سود"}).assign(دوره="فعلی"),
            ], ignore_index=True)
            fig = px.bar(long_profit, x="دانشگاه", y="سود", color="دوره", barmode="group",
                         color_discrete_map={"۱۴۰۵-۱۴۰۴": "#059669", "فعلی": "#3B82F6"}, text="سود")
            apply_auto_bar_text(fig, size=10)
            fig.update_layout(title=dict(text="سود/زیان — همه دانشگاه‌ها",
                                         font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")),
                              xaxis=dict(title="دانشگاه"),
                              yaxis=dict(title="مبلغ (ریال)", tickformat=",.0f", exponentformat="none"))
            st.plotly_chart(style_figure(fig, 540), use_container_width=True)

            st.markdown('<div class="section-header">🔍 مشاهده جزئیات یک دانشگاه</div>', unsafe_allow_html=True)
            drill_uni = st.selectbox("دانشگاه مورد نظر برای جزئیات", options=list(perf_data_all.keys()), key="perf_drill_uni")
            d = perf_data_all[drill_uni]

            inc_labels = ["شهریه", "برون‌سپاری", "کارگاه", "مجموع درآمد"]
            exp_labels = ["هیات علمی", "رسمی/قراردادی", "شرکتی", "اساتید مدعو", "اجاره", "سایر", "مجموع هزینه"]
            inc_hist = [d["in_tuition"]["hist"], d["in_outsourcing"]["hist"], d["in_workshop"]["hist"], d["in_total"]["hist"]]
            inc_curr = [d["in_tuition"]["curr"], d["in_outsourcing"]["curr"], d["in_workshop"]["curr"], d["in_total"]["curr"]]
            exp_hist = [d["ex_faculty"]["hist"], d["ex_official"]["hist"], d["ex_corporate"]["hist"],
                        d["ex_guest"]["hist"], d["ex_rent"]["hist"], d["ex_other"]["hist"], d["ex_total"]["hist"]]
            exp_curr = [d["ex_faculty"]["curr"], d["ex_official"]["curr"], d["ex_corporate"]["curr"],
                        d["ex_guest"]["curr"], d["ex_rent"]["curr"], d["ex_other"]["curr"], d["ex_total"]["curr"]]

            st.markdown(sub_header(f"📊 عملکرد ۱۴۰۵-۱۴۰۴ — {drill_uni}"), unsafe_allow_html=True)
            st.plotly_chart(make_financial_bar_full(inc_labels, inc_hist, "#1E40AF", f"درآمدها — {drill_uni}", height=640, x_axis_title="سرفصل درآمدی"), use_container_width=True)
            add_below_legend(inc_labels)
            st.plotly_chart(make_financial_bar_full(exp_labels, exp_hist, "#DC2626", f"هزینه‌ها — {drill_uni}", height=700, x_axis_title="سرفصل هزینه‌ای"), use_container_width=True)
            add_below_legend(exp_labels)

            st.markdown(sub_header(f"📊 وضعیت فعلی ۱۴۰۶-۱۴۰۵ — {drill_uni}"), unsafe_allow_html=True)
            st.plotly_chart(make_financial_bar_full(inc_labels, inc_curr, "#0E7490", f"درآمدها — {drill_uni}", height=640, x_axis_title="سرفصل درآمدی"), use_container_width=True)
            add_below_legend(inc_labels)
            st.plotly_chart(make_financial_bar_full(exp_labels, exp_curr, "#D97706", f"هزینه‌ها — {drill_uni}", height=700, x_axis_title="سرفصل هزینه‌ای"), use_container_width=True)
            add_below_legend(exp_labels)

    st.divider()
    st.caption("داشبورد مدیریتی هوشمند مراکز آموزشی دانشگاه آزاد اسلامی استان گلستان — داده‌ها از فایل‌های اکسل سرور استخراج می‌شوند.")
    st.stop()

# ============================================================
# نمای مدیریتی (تک‌دانشگاهی)
# ============================================================
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
    with c1: st.markdown(kpi_card(f"دانشجویان فعال — {latest_sem}", fmt_int(total_students), "نفر", "blue"), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card(f"مانده بدهی — {selected_financial_sem}", fmt_rial(total_debt), "ریال", "red"), unsafe_allow_html=True)
    with c3: st.markdown(kpi_card(f"مبلغ تقسیط‌شده — {selected_financial_sem}", fmt_rial(total_installment), "ریال", "green"), unsafe_allow_html=True)
    with c4: st.markdown(kpi_card("بدهی سرانه", fmt_rial(debt_per_student), "ریال/دانشجو", "purple"), unsafe_allow_html=True)
    c5, c6, c7, c8 = st.columns(4)
    with c5: st.markdown(kpi_card("سهم از کل دانشجویان", fmt_pct(share_of_total) if pd.notna(share_of_total) else "—", "درصد", "cyan"), unsafe_allow_html=True)
    with c6: st.markdown(kpi_card(f"تعداد بدهکاران — {selected_financial_sem}", fmt_int(total_debtors), "نفر", "orange"), unsafe_allow_html=True)
    with c7: st.markdown(kpi_card(f"عدم مراجعه — {selected_financial_sem}", fmt_int(total_not_referred), "نفر", "slate"), unsafe_allow_html=True)
    with c8: st.markdown(kpi_card(f"رشد ({first_sem} → {latest_sem})", fmt_pct(growth_val) if pd.notna(growth_val) else "—", "درصد", "green"), unsafe_allow_html=True)

    st.markdown(explain_box(
        "<b>بدهی سرانه:</b> مجموع مانده بدهی ÷ مجموع دانشجویان فعال<br>"
        "<b>سهم از کل:</b> دانشجویان این واحد ÷ دانشجویان کل واحدها × ۱۰۰"), unsafe_allow_html=True)

# ============================================================
# TABS (تک‌دانشگاهی)
# ============================================================
tab_trend, tab_financial, tab_fin_perf = st.tabs([
    "📈 روند دانشجویان", "💰 تحلیل مالی", "📈 خلاصه عملکرد مالی و پیش‌بینی وضعیت",
])

# ---------- TAB 1: روند ----------
with tab_trend:
    if not has_selected_data:
        st.markdown(no_data_notice(selected_university), unsafe_allow_html=True)
    else:
        trend_scope = student_long[student_long["university"] == selected_university].copy()
        if trend_scope.empty:
            st.markdown(no_data_notice(selected_university), unsafe_allow_html=True)
        else:
            st.markdown('<div class="section-header">📈 روند تعداد دانشجویان — مهرماه و بهمن‌ماه</div>', unsafe_allow_html=True)
            trend_agg = trend_scope.groupby("semester_code", as_index=False)["students"].sum(min_count=1).sort_values("semester_code")
            mehr_data = trend_agg[trend_agg["semester_code"].str.endswith("1")]
            bahman_data = trend_agg[trend_agg["semester_code"].str.endswith("2")]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=mehr_data["semester_code"], y=mehr_data["students"], name="مهرماه",
                                      mode="lines+markers+text", text=mehr_data["students"].map(lambda v: f"<b>{v:,.0f}</b>"),
                                      textposition="top center", textfont=dict(size=11, color="#991B1B", family="Vazirmatn", weight="bold"),
                                      line=dict(color="#DC2626", width=3), marker=dict(size=12, line=dict(width=2, color="#FFFFFF")),
                                      hovertemplate="<b>%{x}</b><br>مهرماه: %{y:,.0f}<extra></extra>"))
            fig.add_trace(go.Scatter(x=bahman_data["semester_code"], y=bahman_data["students"], name="بهمن‌ماه",
                                      mode="lines+markers+text", text=bahman_data["students"].map(lambda v: f"<b>{v:,.0f}</b>"),
                                      textposition="bottom center", textfont=dict(size=11, color="#0E7490", family="Vazirmatn", weight="bold"),
                                      line=dict(color="#0891B2", width=3), marker=dict(size=12, line=dict(width=2, color="#FFFFFF")),
                                      hovertemplate="<b>%{x}</b><br>بهمن‌ماه: %{y:,.0f}<extra></extra>"))
            fig.update_layout(title=dict(text=f"روند دانشجویان فعال — {selected_university}",
                                          font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")),
                              hovermode="x unified",
                              xaxis=dict(title="کد نیمسال", type="category", categoryorder="array", categoryarray=list(trend_agg["semester_code"])),
                              yaxis=dict(title="تعداد دانشجو"))
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
                                  xaxis_title="کد نیمسال", yaxis_title="دانشگاه",
                                  margin=dict(l=25, r=25, t=60, b=50))
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

            st.markdown(f'<div class="section-header">🔮 پیش‌بینی برای نیمسال {selected_prediction_sem}</div>', unsafe_allow_html=True)
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
            pred_fig.update_layout(title=dict(text=f"پیش‌بینی — {selected_university} — {selected_prediction_sem}",
                                               font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")),
                                    xaxis=dict(title="نیمسال"),
                                    yaxis=dict(title="تعداد دانشجو"),
                                    hovermode="x unified")
            st.plotly_chart(style_figure(pred_fig, 450), use_container_width=True)

            render_pretty_table(pd.DataFrame([{
                "دانشگاه": selected_university,
                "آخرین نیمسال": latest_sem,
                "دانشجوی فعلی": fmt_int(total_students),
                "نیمسال هدف": selected_prediction_sem,
                "پیش‌بینی": fmt_int(predicted) if pd.notna(predicted) else "—",
            }]))

            st.markdown('<div class="section-header">🎯 مقایسه پیش‌بینی با واقعی</div>', unsafe_allow_html=True)
            headers = ["دانشگاه", f"پیش‌بینی {selected_prediction_sem}", "واقعی (ادمین)"]
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
                st.markdown(sub_header("📊 نتیجه مقایسه"), unsafe_allow_html=True)
                render_pretty_table(pd.DataFrame([{
                    "دانشگاه": selected_university,
                    "پیش‌بینی": fmt_int(predicted) if pd.notna(predicted) else "—",
                    "واقعی": fmt_int(actual_value),
                    "وضعیت": _closeness(actual_value, predicted),
                }]))
            else:
                st.markdown(rtl_alert("برای محاسبه دقت پیش‌بینی، مقدار «واقعی» را وارد کنید."), unsafe_allow_html=True)

# ---------- TAB 2: تحلیل مالی ----------
with tab_financial:
    if not has_selected_data:
        st.markdown(no_data_notice(selected_university), unsafe_allow_html=True)
    elif "debt" not in combined.columns or selected_data["debt"].dropna().empty:
        st.markdown(no_data_notice(selected_university), unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="section-header">💰 تحلیل مالی <span class="badge badge-orange">نیمسال {selected_financial_sem}</span></div>', unsafe_allow_html=True)

        # --- نمودار بدهی و تقسیط (محور X: مبلغ به ریال، محور Y: دانشگاه) ---
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
                fig.update_layout(title=dict(text="مقایسه بدهی و تقسیط",
                                             font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")),
                                  barmode="group", bargap=0.3,
                                  xaxis=dict(title="مبلغ (ریال)", tickformat=",.0f", exponentformat="none"),
                                  yaxis=dict(title="دانشگاه"),
                                  margin=dict(l=25, r=200, t=70, b=55))
                st.plotly_chart(style_figure(fig, max(400, 70 * len(fin_df) + 180)), use_container_width=True)
        with right:
            per_capita = selected_data.dropna(subset=["debt_per_student"]).copy().sort_values("debt_per_student")
            if per_capita.empty:
                st.markdown(no_data_notice(selected_university), unsafe_allow_html=True)
            else:
                fig = px.bar(per_capita, x="debt_per_student", y="university", orientation="h",
                             color="university", color_discrete_map=color_map,
                             text=per_capita["debt_per_student"].map(lambda v: f"{v:,.0f}"))
                apply_auto_bar_text(fig, size=12)
                fig.update_layout(title=dict(text="بدهی سرانه هر دانشجو",
                                             font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")),
                                  showlegend=False, bargap=0.35,
                                  xaxis=dict(title="مبلغ (ریال به ازای هر دانشجو)", tickformat=",.0f", exponentformat="none"),
                                  yaxis=dict(title="دانشگاه"),
                                  margin=dict(l=25, r=140, t=70, b=55))
                st.plotly_chart(style_figure(fig, max(400, 70 * len(per_capita) + 180)), use_container_width=True)

        st.markdown(gradient_divider(), unsafe_allow_html=True)
        st.markdown('<div class="section-header">📐 شاخص‌های تحلیلی مالی</div>', unsafe_allow_html=True)
        st.markdown(explain_box("<b>سهم تقسیط از مطالبات:</b> تقسیط ÷ (بدهی + تقسیط) × ۱۰۰<br>"
                                "<b>نرخ مراجعه بدهکاران:</b> (تعداد بدهکاران − عدم مراجعه) ÷ تعداد بدهکاران × ۱۰۰"),
                    unsafe_allow_html=True)

        # --- سهم تقسیط (محور X: درصد، محور Y: دانشگاه) ---
        a1, a2 = two_cols_with_vdivider(min_height=460)
        with a1:
            inst_df = selected_data.dropna(subset=["installment_share"]).copy().sort_values("installment_share")
            if inst_df.empty:
                st.markdown(no_data_notice(selected_university), unsafe_allow_html=True)
            else:
                fig = px.bar(inst_df, x="installment_share", y="university", orientation="h",
                             color="university", color_discrete_map=color_map,
                             text=inst_df["installment_share"].map(lambda v: f"{v:.1f}%"))
                apply_auto_bar_text(fig, size=12)
                fig.update_layout(title=dict(text="سهم تقسیط از کل مطالبات",
                                             font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")),
                                  showlegend=False, bargap=0.35,
                                  xaxis=dict(title="درصد", range=[0, 100]),
                                  yaxis=dict(title="دانشگاه"),
                                  margin=dict(l=25, r=140, t=70, b=55))
                st.plotly_chart(style_figure(fig, max(400, 70 * len(inst_df) + 180)), use_container_width=True)
        # --- نرخ مراجعه (محور X: درصد، محور Y: دانشگاه) ---
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
                fig.update_layout(title=dict(text="نرخ مراجعه بدهکاران",
                                             font=dict(size=15, color="#0F172A", family="Vazirmatn", weight="bold")),
                                  showlegend=False, bargap=0.45,
                                  xaxis=dict(title="درصد", range=[xmin, xmax], tickfont=dict(size=12, weight="bold"), zeroline=False),
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

# ---------- TAB 3: عملکرد مالی ----------
with tab_fin_perf:
    perf_data = perf_data_all.get(selected_university)
    if not has_selected_data:
        st.markdown(no_data_notice(selected_university), unsafe_allow_html=True)
    elif not perf_sheets:
        st.markdown(no_data_notice(selected_university), unsafe_allow_html=True)
    elif not perf_data or not perf_has_data(perf_data):
        st.markdown(no_data_notice(selected_university), unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="section-header">📈 خلاصه عملکرد مالی و پیش‌بینی وضعیت — {selected_university}</div>', unsafe_allow_html=True)

        inc_labels = ["شهریه", "برون‌سپاری", "کارگاه", "مجموع درآمد"]
        inc_hist = [perf_data["in_tuition"]["hist"], perf_data["in_outsourcing"]["hist"], perf_data["in_workshop"]["hist"], perf_data["in_total"]["hist"]]
        exp_labels = ["هیات علمی", "رسمی/قراردادی", "شرکتی", "اساتید مدعو", "اجاره", "سایر", "مجموع هزینه"]
        exp_hist = [perf_data["ex_faculty"]["hist"], perf_data["ex_official"]["hist"], perf_data["ex_corporate"]["hist"],
                    perf_data["ex_guest"]["hist"], perf_data["ex_rent"]["hist"], perf_data["ex_other"]["hist"], perf_data["ex_total"]["hist"]]

        st.markdown(sub_header("📊 عملکرد ۱۴۰۵-۱۴۰۴"), unsafe_allow_html=True)
        st.plotly_chart(make_financial_bar_full(inc_labels, inc_hist, "#1E40AF", "درآمدها — عملکرد ۱۴۰۵-۱۴۰۴", height=680, x_axis_title="سرفصل درآمدی"), use_container_width=True)
        add_below_legend(inc_labels)
        st.plotly_chart(make_financial_bar_full(exp_labels, exp_hist, "#DC2626", "هزینه‌ها — عملکرد ۱۴۰۵-۱۴۰۴", height=740, x_axis_title="سرفصل هزینه‌ای"), use_container_width=True)
        add_below_legend(exp_labels)

        st.markdown(gradient_divider(), unsafe_allow_html=True)
        st.markdown(sub_header("📊 وضعیت فعلی ۱۴۰۶-۱۴۰۵"), unsafe_allow_html=True)
        inc_curr = [perf_data["in_tuition"]["curr"], perf_data["in_outsourcing"]["curr"], perf_data["in_workshop"]["curr"], perf_data["in_total"]["curr"]]
        exp_curr = [perf_data["ex_faculty"]["curr"], perf_data["ex_official"]["curr"], perf_data["ex_corporate"]["curr"],
                    perf_data["ex_guest"]["curr"], perf_data["ex_rent"]["curr"], perf_data["ex_other"]["curr"], perf_data["ex_total"]["curr"]]
        st.plotly_chart(make_financial_bar_full(inc_labels, inc_curr, "#0E7490", "درآمدها — وضعیت فعلی ۱۴۰۶-۱۴۰۵", height=680, x_axis_title="سرفصل درآمدی"), use_container_width=True)
        add_below_legend(inc_labels)
        st.plotly_chart(make_financial_bar_full(exp_labels, exp_curr, "#D97706", "هزینه‌ها — وضعیت فعلی ۱۴۰۶-۱۴۰۵", height=740, x_axis_title="سرفصل هزینه‌ای"), use_container_width=True)
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
                status_str = f'<span style="color:#059669;font-weight:800;">بیشتر ({curr - pred:+,.0f})</span>'
            else:
                status_str = f'<span style="color:#DC2626;font-weight:800;">کمتر ({curr - pred:+,.0f})</span>'

            if "مجموع درآمد" in title:
                td = f'<span style="color:#1E40AF;font-weight:800;">{title}</span>'
            elif "مجموع هزینه" in title:
                td = f'<span style="color:#DC2626;font-weight:800;">{title}</span>'
            else:
                td = title

            rows.append({
                "شرح": td,
                "عملکرد ۱۴۰۵-۱۴۰۴": fmt_rial(hist),
                "وضعیت فعلی ۱۴۰۶-۱۴۰۵": fmt_rial(curr),
                pred_col_name: f'<span style="color:#7C3AED;font-weight:800;">{pred:,.0f}</span>',
                "وضعیت نسبت به پیش‌بینی": status_str,
            })
        render_pretty_table(pd.DataFrame(rows))

        st.markdown(gradient_divider(), unsafe_allow_html=True)
        st.markdown('<div class="section-header">📊 نمودار سود یا زیان</div>', unsafe_allow_html=True)
        pl_labels = ["عملکرد ۱۴۰۵-۱۴۰۴", "وضعیت فعلی ۱۴۰۶-۱۴۰۵"]
        pl_vals = [perf_data["profit"]["hist"], perf_data["profit"]["curr"]]
        st.plotly_chart(make_financial_bar_full(pl_labels, pl_vals, None, "نمودار سود یا زیان", height=620, color_list=["#059669", "#3B82F6"], x_axis_title="بازه زمانی"), use_container_width=True)
        add_below_legend(pl_labels, title_prefix="📌 بازه زمانی")

st.divider()
st.caption("داشبورد مدیریتی هوشمند مراکز آموزشی دانشگاه آزاد اسلامی استان گلستان — داده‌ها از فایل‌های اکسل سرور استخراج می‌شوند.")