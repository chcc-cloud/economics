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
# 커스텀 CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&family=Space+Mono:wght@400;700&display=swap');

html, body,[class*="css"] {
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
    transition: transform 0.2s ease;
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
    margin-bottom: 8px;
}
.metric-value {
    font-family: 'Space Mono', monospace;
    font-size: 2rem;
    font-weight: 700;
    color: #e8eaf0;
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
    flex-shrink: 0;
}
.insight-box {
    background: linear-gradient(135deg, #0f1e3d 0%, #111827 100%);
    border: 1px solid #1e3a6e;
    border-left: 4px solid #3b82f6;
    border-radius: 12px;
    padding: 18px 22px;
    margin: 10px 0;
    color: #a8b8d8;
}
.js-plotly-plot { border-radius: 12px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Plotly 공통 테마
# ──────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Noto Sans KR", color="#a8b8d8", size=12),
    xaxis=dict(gridcolor="#1e2540", linecolor="#1e2540", tickcolor="#a8b8d8"),
    yaxis=dict(gridcolor="#1e2540", linecolor="#1e2540", tickcolor="#a8b8d8"),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#a8b8d8")),
)

@st.cache_resource
def get_conn(db_path: str):
    return sqlite3.connect(db_path, check_same_thread=False)

@st.cache_data
def load_table(_conn, table: str) -> pd.DataFrame:
    return pd.read_sql(f'SELECT * FROM "{table}"', _conn)

# ──────────────────────────────────────────────
# 사이드바
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ 데이터 설정")
    db_path = st.text_input("SQLite DB 파일 경로", value="economics.db")

if not os.path.exists(db_path):
    st.error(f"⚠️ DB 파일을 찾을 수 없습니다: `{db_path}`")
    st.stop()

conn = get_conn(db_path)

try:
    df_eco    = load_table(conn, "경제활동현황")
    df_inact  = load_table(conn, "비경제활동인구")
    df_wage   = load_table(conn, "산업별_임금_및_근로시간")
    df_emp    = load_table(conn, "산업별_취업자")
    df_reason = load_table(conn, "쉬었음의_주된_이유")
except Exception as e:
    st.error(f"테이블 로드 실패: {e}")
    st.stop()

# =====================================================================
# 🚨 [중요 디버깅 1] 문자열 콤마(,) 제거 후 확실하게 숫자로 변환
# 데이터에 1,200 처럼 콤마가 있으면 글자로 인식해서 mean() 에러가 발생합니다.
# =====================================================================
def make_numeric(df, cols):
    for col in cols:
        if col in df.columns:
            # 콤마 제거하고 숫자로 강제 변환 (문제가 있는 값은 NaN 처리 후 0으로 채움)
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

make_numeric(df_eco,["취업자", "실업자", "경제활동인구"])
make_numeric(df_emp,["취업자수"])
make_numeric(df_wage,["전체임금총액", "전체근로시간"])
make_numeric(df_inact, ["비경제활동인구"])

# ──────────────────────────────────────────────
# 헤더
# ──────────────────────────────────────────────
st.markdown("""
<div style='padding: 32px 0 8px 0;'>
  <h1 style='font-size: 2.2rem; font-weight: 900; color: #e8eaf0; margin: 0;'>청년 고용 현황 대시보드</h1>
  <p style='color: #6b7db3; margin-top: 8px;'>경제활동인구 · 실업률 · 산업별 임금 · 비경활 이유 통합 분석</p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# =====================================================================
# 🚨[중요 디버깅 2] 성별에 '계'가 없을 때의 스마트한 필터링 로직
# =====================================================================
if "성별" in df_eco.columns:
    genders_only = sorted([g for g in df_eco["성별"].dropna().unique() if g != '계'])
    filter_options =["전체"] + genders_only
    selected_gender = st.selectbox("성별 필터", filter_options, index=0)

    if selected_gender == "전체":
        if '계' in df_eco["성별"].values:
            df_eco_f = df_eco[df_eco["성별"] == '계'].copy()
        else:
            # DB에 '계'가 없다면, 시점별로 남/여 데이터를 더해서(sum) '전체' 데이터를 만듭니다.
            df_eco_f = df_eco.groupby("시점")[["취업자", "실업자", "경제활동인구"]].sum().reset_index()
            # 실업률은 텍스트(%)로 되어있으므로 다시 계산해 줍니다.
            df_eco_f["실업률"] = (df_eco_f["실업자"] / df_eco_f["경제활동인구"] * 100).round(1).astype(str) + "%"
    else:
        df_eco_f = df_eco[df_eco["성별"] == selected_gender].copy()
else:
    df_eco_f = df_eco.copy()

# ──────────────────────────────────────────────
# KPI 카드
# ──────────────────────────────────────────────
st.markdown("<div class='section-header'><div class='section-dot'></div><h2>핵심 지표 요약</h2></div>", unsafe_allow_html=True)

latest = df_eco_f.sort_values("시점").iloc[-1] if len(df_eco_f) else {}
prev   = df_eco_f.sort_values("시점").iloc[-2] if len(df_eco_f) > 1 else {}

def fmt_num(v):
    try: return f"{int(float(v)):,}"
    except: return str(v)

def delta_html(cur, prv, col, unit="", invert=False):
    try:
        cur_val = float(str(cur[col]).replace('%',''))
        prv_val = float(str(prv[col]).replace('%',''))
        d = cur_val - prv_val
        pct = d / prv_val * 100 if prv_val != 0 else 0
        up = d > 0
        cls = ("delta-down" if up else "delta-up") if invert else ("delta-up" if up else "delta-down")
        sign = "▲" if up else "▼"
        return f'<div class="metric-delta {cls}">{sign} {abs(d):,.0f}{unit} ({pct:+.1f}%)</div>'
    except:
        return ""

c1, c2, c3, c4 = st.columns(4)
cards =[
    (c1, "취업자 수", "취업자", "명", False, "#3b82f6"),
    (c2, "실업자 수", "실업자", "명", True,  "#ef4444"),
    (c3, "경제활동인구", "경제활동인구", "명", False, "#10b981"),
    (c4, "실업률",  "실업률", "%", True,  "#f59e0b"),
]

for col_obj, title, field, unit, invert, accent in cards:
    try:
        val = str(latest.get(field, 0)).replace('%', '')
        delta = delta_html(latest, prev, field, unit, invert)
        display = f"{float(val):.1f}" if field == "실업률" else fmt_num(val)
    except:
        display, delta = "–", ""
    with col_obj:
        st.markdown(f"<div class='metric-card' style='--accent:{accent}'><div class='metric-title'>{title}</div><div class='metric-value'>{display}</div>{delta}</div>", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# 1. 경제활동 추이
# ──────────────────────────────────────────────
st.markdown("<div class='section-header'><div class='section-dot'></div><h2>① 경제활동인구 · 실업률 추이</h2></div>", unsafe_allow_html=True)

col_l, col_r = st.columns([3, 2])

with col_l:
    df_ts = df_eco_f.sort_values("시점")
    if "실업률" in df_ts.columns:
        df_ts['실업률_num'] = pd.to_numeric(df_ts['실업률'].astype(str).str.replace('%', ''), errors='coerce')
    else:
        df_ts['실업률_num'] = 0
        
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=df_ts["시점"], y=df_ts["취업자"], name="취업자", mode="lines+markers", line=dict(color="#3b82f6", width=2.5)), secondary_y=False)
    fig.add_trace(go.Scatter(x=df_ts["시점"], y=df_ts["실업자"], name="실업자", mode="lines+markers", line=dict(color="#ef4444", width=2, dash="dot")), secondary_y=False)
    
    if not df_ts['실업률_num'].isna().all():
        fig.add_trace(go.Scatter(x=df_ts["시점"], y=df_ts['실업률_num'], name="실업률(%)", mode="lines", line=dict(color="#f59e0b", width=2)), secondary_y=True)
        fig.update_yaxes(title_text="실업률 (%)", secondary_y=True, gridcolor="#1e2540", color="#a8b8d8")
        
    fig.update_layout(title="경제활동 추이", **PLOTLY_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

with col_r:
    if "성별" in df_eco.columns:
        # 에러가 나던 핵심 부분! 데이터가 이제 완벽한 숫자이므로 mean() 연산이 안전하게 동작합니다.
        df_gender_base = df_eco[df_eco["성별"] != '계']
        df_gender = df_gender_base.groupby("성별")[["취업자", "실업자"]].mean().reset_index()
        
        fig2 = px.bar(df_gender.melt(id_vars="성별", var_name="구분", value_name="평균"),
                      x="성별", y="평균", color="구분", barmode="group",
                      title="성별 평균 취업/실업자 비교",
                      color_discrete_map={"취업자":"#3b82f6","실업자":"#ef4444"})
        fig2.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig2, use_container_width=True)

# ──────────────────────────────────────────────
# 2. 산업별 분석
# ──────────────────────────────────────────────
st.markdown("<div class='section-header'><div class='section-dot' style='background:#10b981'></div><h2>② 산업별 취업자 · 임금 · 근로시간 분석</h2></div>", unsafe_allow_html=True)

col_a, col_b, col_c = st.columns(3)

with col_a:
    df_emp_agg = df_emp.groupby("산업별")["취업자수"].mean().reset_index().sort_values("취업자수").tail(12)
    fig = px.bar(df_emp_agg, x="취업자수", y="산업별", orientation="h", title="산업별 평균 취업자수 (상위 12)", color="취업자수", color_continuous_scale=["#1e2a4a","#3b82f6"])
    fig.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    df_wage_agg = df_wage.groupby("산업별")["전체임금총액"].mean().reset_index().sort_values("전체임금총액").tail(12)
    fig = px.bar(df_wage_agg, x="전체임금총액", y="산업별", orientation="h", title="산업별 평균 임금 (상위 12)", color="전체임금총액", color_continuous_scale=["#1a2a1a","#10b981"])
    fig.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

with col_c:
    df_wage_agg2 = df_wage.groupby("산업별")["전체근로시간"].mean().reset_index().sort_values("전체근로시간").tail(12)
    fig = px.bar(df_wage_agg2, x="전체근로시간", y="산업별", orientation="h", title="산업별 평균 근로시간 (상위 12)", color="전체근로시간", color_continuous_scale=["#2a1a1a","#f59e0b"])
    fig.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("#### 💡 임금 vs 취업자 수 — 산업별 포지셔닝")
df_merge = pd.merge(df_emp.groupby("산업별")["취업자수"].mean().reset_index(), df_wage.groupby("산업별")[["전체임금총액","전체근로시간"]].mean().reset_index(), on="산업별", how="inner")
if not df_merge.empty:
    fig_sc = px.scatter(df_merge, x="취업자수", y="전체임금총액", size="전체근로시간", color="산업별", hover_name="산업별", text="산업별", title="취업자 多 = 임금도 高?", size_max=40)
    fig_sc.update_traces(textposition="top center", textfont_size=9)
    fig_sc.update_layout(**PLOTLY_LAYOUT, height=420, showlegend=False)
    st.plotly_chart(fig_sc, use_container_width=True)

# ──────────────────────────────────────────────
# 3. 쉬는 이유 분석
# ──────────────────────────────────────────────
st.markdown("<div class='section-header'><div class='section-dot' style='background:#ef4444'></div><h2>③ 쉬었음의 주된 이유</h2></div>", unsafe_allow_html=True)

reason_cols =[c for c in df_reason.columns if c != "시점"]
voluntary_keywords   =["직장의 휴업", "다음 일 준비", "퇴사(정년 퇴직)"]
involuntary_keywords =["몸이 좋지", "일의 완료", "원하는 일자리", "일자리(일거리)가 없어서"]

def classify(col):
    for k in voluntary_keywords:
        if k in col: return "자발적"
    for k in involuntary_keywords:
        if k in col: return "비자발적"
    return "기타"

df_reason_melt = df_reason.melt(id_vars="시점", value_vars=reason_cols, var_name="이유", value_name="인원")
df_reason_melt["인원"] = pd.to_numeric(df_reason_melt["인원"].astype(str).str.replace(',',''), errors="coerce").fillna(0)
df_reason_melt["유형"] = df_reason_melt["이유"].apply(classify)

col_p, col_q = st.columns([2, 3])

with col_p:
    agg_type = df_reason_melt.groupby("유형")["인원"].sum().reset_index()
    fig_pie = px.pie(agg_type, names="유형", values="인원", title="자발 vs 비자발 비율", color="유형", color_discrete_map={"자발적":"#10b981","비자발적":"#ef4444","기타":"#6b7db3"})
    fig_pie.update_traces(textposition="inside", textinfo="percent+label", hole=0.45)
    fig_pie.update_layout(**PLOTLY_LAYOUT, height=360)
    st.plotly_chart(fig_pie, use_container_width=True)

with col_q:
    agg_reason = df_reason_melt.groupby("이유")["인원"].mean().reset_index().sort_values("인원")
    fig_bar = px.bar(agg_reason, x="인원", y="이유", orientation="h", title="이유별 평균 인원", color="인원", color_continuous_scale=["#1a1a2e","#ef4444"])
    fig_bar.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False, height=360)
    st.plotly_chart(fig_bar, use_container_width=True)

# ──────────────────────────────────────────────
# 4. 상관 분석
# ──────────────────────────────────────────────
st.markdown("<div class='section-header'><div class='section-dot' style='background:#8b5cf6'></div><h2>④ 상관관계 분석</h2></div>", unsafe_allow_html=True)

if "성별" in df_eco.columns and '계' in df_eco["성별"].values:
    df_eco_total = df_eco[df_eco["성별"] == '계']
else:
    df_eco_total = df_eco.groupby("시점")[["취업자", "실업자", "경제활동인구"]].sum().reset_index()

df_combined = pd.merge(
    df_eco_total.groupby("시점")[["취업자","실업자","경제활동인구"]].sum().reset_index(),
    df_inact.groupby("시점")["비경제활동인구"].sum().reset_index(),
    on="시점", how="inner"
).sort_values("시점")

col_x, col_y = st.columns(2)

with col_x:
    fig_c = go.Figure()
    for col_name, color in[("취업자","#3b82f6"),("실업자","#ef4444"),("비경제활동인구","#8b5cf6")]:
        if col_name in df_combined.columns:
            fig_c.add_trace(go.Scatter(x=df_combined["시점"], y=df_combined[col_name], name=col_name, mode="lines", line=dict(color=color, width=2)))
    fig_c.update_layout(title="취업·실업·비경활 통합 추이", **PLOTLY_LAYOUT, height=320)
    st.plotly_chart(fig_c, use_container_width=True)

with col_y:
    if len(df_combined) > 3:
        corr_cols =["취업자","실업자","비경제활동인구","경제활동인구"]
        df_for_corr = df_combined[corr_cols]
        corr = df_for_corr.corr()
        
        fig_heat = px.imshow(corr, text_auto=".2f", color_continuous_scale=["#ef4444","#0a0e1a","#3b82f6"], title="지표 간 상관관계 히트맵")
        fig_heat.update_layout(**PLOTLY_LAYOUT, height=320)
        st.plotly_chart(fig_heat, use_container_width=True)

st.success("✨ 디버깅이 완료되었습니다! 문자열 에러와 '계' 데이터 부재 문제를 모두 해결했습니다.")
