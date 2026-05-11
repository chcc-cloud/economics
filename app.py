import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# ──────────────────────────────────────────────
# 페이지 설정
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="청년 고용 현황 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# 커스텀 CSS (기존 스타일 유지)
# ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&family=Space+Mono:wght@400;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}

.stApp {
    background: #0a0e1a;
    color: #e8eaf0;
}

section[data-testid="stSidebar"] {
    background: #0f1422 !important;
    border-right: 1px solid #1e2540;
}

.metric-card {
    background: linear-gradient(135deg, #111827 0%, #1a2035 100%);
    border: 1px solid #1e2a4a;
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--accent, #3b82f6);
}
.metric-title {
    font-size: 0.75rem;
    font-weight: 500;
    color: #6b7db3;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.metric-value {
    font-family: 'Space Mono', monospace;
    font-size: 2rem;
    font-weight: 700;
    color: #e8eaf0;
    line-height: 1.1;
}
.metric-delta {
    font-size: 0.8rem;
    margin-top: 6px;
    font-weight: 500;
}
.delta-up   { color: #ef4444; }
.delta-down { color: #22c55e; }

.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 32px 0 16px 0;
    padding-bottom: 12px;
    border-bottom: 1px solid #1e2540;
}
.section-header h2 {
    font-size: 1.1rem;
    font-weight: 700;
    color: #c8d0e8;
    margin: 0;
}
.section-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #3b82f6;
}

.insight-box {
    background: linear-gradient(135deg, #0f1e3d 0%, #111827 100%);
    border: 1px solid #1e3a6e;
    border-left: 4px solid #3b82f6;
    border-radius: 12px;
    padding: 18px 22px;
    margin: 10px 0;
    font-size: 0.9rem;
    color: #a8b8d8;
}
</style>
""", unsafe_allow_html=True)

# Plotly 테마 설정
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Noto Sans KR", color="#a8b8d8", size=12),
    xaxis=dict(gridcolor="#1e2540", linecolor="#1e2540"),
    yaxis=dict(gridcolor="#1e2540", linecolor="#1e2540"),
    margin=dict(l=10, r=10, t=40, b=10),
)

# ──────────────────────────────────────────────
# 데이터 로드 및 전처리 (중요!)
# ──────────────────────────────────────────────
@st.cache_resource
def get_conn(db_path: str):
    return sqlite3.connect(db_path, check_same_thread=False)

def safe_to_numeric(df, cols):
    for col in cols:
        if col in df.columns:
            # 콤마, % 기호 제거 후 숫자로 변환 (NaN은 0으로 채움)
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.replace('%', ''), errors='coerce').fillna(0)
    return df

@st.cache_data
def load_and_preprocess_all(_conn):
    # 테이블 로드
    df_eco    = pd.read_sql('SELECT * FROM "경제활동현황"', _conn)
    df_inact  = pd.read_sql('SELECT * FROM "비경제활동인구"', _conn)
    df_wage   = pd.read_sql('SELECT * FROM "산업별_임금_및_근로시간"', _conn)
    df_emp    = pd.read_sql('SELECT * FROM "산업별_취업자"', _conn)
    df_reason = pd.read_sql('SELECT * FROM "쉬었음의_주된_이유
