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

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}

.stApp {
    background: #0a0e1a;
    color: #e8eaf0;
}

/* 사이드바 */
section[data-testid="stSidebar"] {
    background: #0f1422 !important;
    border-right: 1px solid #1e2540;
}

/* 메트릭 카드 */
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
.metric-card:hover { transform: translateY(-2px); }
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

/* 섹션 헤더 */
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
    letter-spacing: 0.02em;
}
.section-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #3b82f6;
    flex-shrink: 0;
}

/* 인사이트 박스 */
.insight-box {
    background: linear-gradient(135deg, #0f1e3d 0%, #111827 100%);
    border: 1px solid #1e3a6e;
    border-left: 4px solid #3b82f6;
    border-radius: 12px;
    padding: 18px 22px;
    margin: 10px 0;
    font-size: 0.9rem;
    line-height: 1.7;
    color: #a8b8d8;
}
.insight-box strong { color: #60a5fa; }

/* Plotly 차트 배경 오버라이드 */
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
    colorway=["#3b82f6","#f59e0b","#10b981","#ef4444","#8b5cf6","#ec4899","#06b6d4"],
)

ACCENT_COLORS = {
    "blue":   "#3b82f6",
    "amber":  "#f59e0b",
    "green":  "#10b981",
    "red":    "#ef4444",
    "purple": "#8b5cf6",
}

# ──────────────────────────────────────────────
# DB 연결
# ──────────────────────────────────────────────
@st.cache_resource
def get_conn(db_path: str):
    return sqlite3.connect(db_path, check_same_thread=False)

@st.cache_data
def load_table(_conn, table: str) -> pd.DataFrame:
    return pd.read_sql(f'SELECT * FROM "{table}"', _conn)

# ──────────────────────────────────────────────
# 사이드바: DB 파일 경로 입력
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ 데이터 설정")
    db_path = st.text_input(
        "SQLite DB 파일 경로",
        value="economics.db",
        help="청년 고용 데이터가 담긴 .db 파일 경로를 입력하세요"
    )
    st.markdown("---")
    st.markdown("### 📋 포함된 테이블")
    st.markdown("""
    - 경제활동동현황  
    - 비경제활동인구  
    - 산업별_임금_및_근로시간  
    - 산업별_취업자  
    - 쉬었음의_주된_이유  
    """)
    st.markdown("---")
    st.markdown("### 🎯 핵심 인사이트")
    st.markdown("""
    <div style='font-size:0.82rem; color:#6b7db3; line-height:1.8'>
    청년층 취업자 수는 증가하지만<br>
    <b style='color:#f59e0b'>임금·근로시간의 질적 격차</b>와<br>
    <b style='color:#ef4444'>비자발적 비경활 비율 증가</b>가<br>
    동시에 나타나는 구조적 문제를<br>
    시각화합니다.
    </div>
    """, unsafe_allow_html=True)

# ──────────────────────────────────────────────
# DB 로드
# ──────────────────────────────────────────────
if not os.path.exists(db_path):
    st.error(f"⚠️ DB 파일을 찾을 수 없습니다: `{db_path}`")
    st.info("사이드바에서 올바른 DB 파일 경로를 입력해주세요.")
    st.stop()

conn = get_conn(db_path)

try:
    df_eco    = load_table(conn, "경제활동동현황")
    df_inact  = load_table(conn, "비경제활동인구")
    df_wage   = load_table(conn, "산업별_임금_및_근로시간")
    df_emp    = load_table(conn, "산업별_취업자")
    df_reason = load_table(conn, "쉬었음의_주된_이유")
except Exception as e:
    st.error(f"테이블 로드 실패: {e}")
    st.stop()

# ──────────────────────────────────────────────
# 헤더
# ──────────────────────────────────────────────
st.markdown("""
<div style='padding: 32px 0 8px 0;'>
  <div style='font-family: Space Mono, monospace; font-size: 0.7rem; color: #3b82f6; letter-spacing: 0.2em; text-transform: uppercase; margin-bottom: 8px;'>
    Youth Labor Market Intelligence
  </div>
  <h1 style='font-size: 2.2rem; font-weight: 900; color: #e8eaf0; margin: 0; line-height: 1.15;'>
    청년 고용 현황 대시보드
  </h1>
  <p style='color: #6b7db3; margin-top: 8px; font-size: 0.95rem;'>
    경제활동인구 · 실업률 · 산업별 임금 · 비경활 이유 통합 분석
  </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ──────────────────────────────────────────────
# 성별 필터 (경제활동동현황에 성별 컬럼이 있는 경우)
# ──────────────────────────────────────────────
genders = ["전체"] + sorted(df_eco["성별"].dropna().unique().tolist()) if "성별" in df_eco.columns else ["전체"]
selected_gender = st.selectbox("성별 필터", genders, index=0)

df_eco_f = df_eco if selected_gender == "전체" else df_eco[df_eco["성별"] == selected_gender]

# ──────────────────────────────────────────────
# KPI 카드
# ──────────────────────────────────────────────
st.markdown("""
<div class='section-header'>
  <div class='section-dot'></div>
  <h2>핵심 지표 요약</h2>
</div>
""", unsafe_allow_html=True)

latest = df_eco_f.sort_values("시점").iloc[-1] if len(df_eco_f) else {}
prev   = df_eco_f.sort_values("시점").iloc[-2] if len(df_eco_f) > 1 else {}

def fmt_num(v):
    try:
        return f"{int(v):,}"
    except:
        return str(v)

def delta_html(cur, prv, col, unit="", invert=False):
    try:
        d = float(cur[col]) - float(prv[col])
        pct = d / float(prv[col]) * 100 if float(prv[col]) != 0 else 0
        up = d > 0
        cls = ("delta-down" if up else "delta-up") if invert else ("delta-up" if up else "delta-down")
        sign = "▲" if up else "▼"
        return f'<div class="metric-delta {cls}">{sign} {abs(d):,.0f}{unit} ({pct:+.1f}%)</div>'
    except:
        return ""

c1, c2, c3, c4 = st.columns(4)
cards = [
    (c1, "취업자 수", "취업자", "명", False, "#3b82f6"),
    (c2, "실업자 수", "실업자", "명", True,  "#ef4444"),
    (c3, "경제활동인구", "경제활동인구", "명", False, "#10b981"),
    (c4, "실업률",  "실업률", "%", True,  "#f59e0b"),
]

for col_obj, title, field, unit, invert, accent in cards:
    try:
        val = latest[field]
        delta = delta_html(latest, prev, field, unit, invert)
        display = f"{float(val):.1f}" if field == "실업률" else fmt_num(val)
    except:
        display, delta = "–", ""
    with col_obj:
        st.markdown(f"""
        <div class='metric-card' style='--accent:{accent}'>
          <div class='metric-title'>{title}</div>
          <div class='metric-value'>{display}</div>
          {delta}
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# 1. 경제활동 추이
# ──────────────────────────────────────────────
st.markdown("""
<div class='section-header'>
  <div class='section-dot'></div>
  <h2>① 경제활동인구 · 실업률 추이</h2>
</div>
""", unsafe_allow_html=True)

col_l, col_r = st.columns([3, 2])

with col_l:
    df_ts = df_eco_f.sort_values("시점")
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(
        x=df_ts["시점"], y=df_ts["취업자"],
        name="취업자", mode="lines+markers",
        line=dict(color="#3b82f6", width=2.5),
        marker=dict(size=5),
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=df_ts["시점"], y=df_ts["실업자"],
        name="실업자", mode="lines+markers",
        line=dict(color="#ef4444", width=2, dash="dot"),
        marker=dict(size=5),
    ), secondary_y=False)
    try:
        fig.add_trace(go.Scatter(
            x=df_ts["시점"], y=df_ts["실업률"].astype(float),
            name="실업률(%)", mode="lines",
            line=dict(color="#f59e0b", width=2),
        ), secondary_y=True)
        fig.update_yaxes(title_text="실업률 (%)", secondary_y=True,
                         gridcolor="#1e2540", color="#a8b8d8")
    except:
        pass
    fig.update_layout(title="경제활동 추이", **PLOTLY_LAYOUT)
    fig.update_yaxes(title_text="인구 (명)", secondary_y=False,
                     gridcolor="#1e2540", color="#a8b8d8")
    st.plotly_chart(fig, use_container_width=True)

with col_r:
    if "성별" in df_eco.columns:
        df_gender = df_eco.groupby("성별")[["취업자","실업자"]].mean().reset_index()
        fig2 = px.bar(df_gender.melt(id_vars="성별", var_name="구분", value_name="평균"),
                      x="성별", y="평균", color="구분", barmode="group",
                      title="성별 평균 취업/실업자",
                      color_discrete_map={"취업자":"#3b82f6","실업자":"#ef4444"})
        fig2.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        # 비경제활동인구 추이
        df_ia = df_inact.sort_values("시점")
        fig2 = go.Figure(go.Scatter(
            x=df_ia["시점"], y=df_ia["비경제활동인구"],
            fill="tozeroy", mode="lines",
            line=dict(color="#8b5cf6", width=2.5),
            fillcolor="rgba(139,92,246,0.15)"
        ))
        fig2.update_layout(title="비경제활동인구 추이", **PLOTLY_LAYOUT)
        st.plotly_chart(fig2, use_container_width=True)

# ──────────────────────────────────────────────
# 2. 산업별 분석
# ──────────────────────────────────────────────
st.markdown("""
<div class='section-header'>
  <div class='section-dot' style='background:#10b981'></div>
  <h2>② 산업별 취업자 · 임금 · 근로시간 분석</h2>
</div>
""", unsafe_allow_html=True)

col_a, col_b, col_c = st.columns(3)

with col_a:
    df_emp_agg = df_emp.groupby("산업별")["취업자수"].mean().reset_index().sort_values("취업자수", ascending=True).tail(12)
    fig = px.bar(df_emp_agg, x="취업자수", y="산업별", orientation="h",
                 title="산업별 평균 취업자수 (상위 12)",
                 color="취업자수", color_continuous_scale=["#1e2a4a","#3b82f6"])
    fig.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    df_wage_agg = df_wage.groupby("산업별")["전체임금총액"].mean().reset_index().sort_values("전체임금총액", ascending=True).tail(12)
    fig = px.bar(df_wage_agg, x="전체임금총액", y="산업별", orientation="h",
                 title="산업별 평균 임금총액 (상위 12)",
                 color="전체임금총액", color_continuous_scale=["#1a2a1a","#10b981"])
    fig.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

with col_c:
    df_wage_agg2 = df_wage.groupby("산업별")["전체근로시간"].mean().reset_index().sort_values("전체근로시간", ascending=True).tail(12)
    fig = px.bar(df_wage_agg2, x="전체근로시간", y="산업별", orientation="h",
                 title="산업별 평균 근로시간 (상위 12)",
                 color="전체근로시간", color_continuous_scale=["#2a1a1a","#f59e0b"])
    fig.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

# 임금 vs 취업자 산점도
st.markdown("#### 💡 임금 vs 취업자 수 — 산업별 포지셔닝")

df_merge = pd.merge(
    df_emp.groupby("산업별")["취업자수"].mean().reset_index(),
    df_wage.groupby("산업별")[["전체임금총액","전체근로시간"]].mean().reset_index(),
    on="산업별", how="inner"
)
if len(df_merge) > 0:
    fig_sc = px.scatter(
        df_merge, x="취업자수", y="전체임금총액",
        size="전체근로시간", color="산업별",
        hover_name="산업별", text="산업별",
        title="취업자 多 = 임금도 高? — 산업별 분포",
        size_max=40,
    )
    fig_sc.update_traces(textposition="top center", textfont_size=9)
    fig_sc.update_layout(**PLOTLY_LAYOUT, height=420,
                          showlegend=False)
    st.plotly_chart(fig_sc, use_container_width=True)

    st.markdown("""
    <div class='insight-box'>
    💡 <strong>버블 크기 = 근로시간</strong> | 오른쪽 위 = <strong>취업자 多 + 고임금</strong>이지만,
    근로시간이 긴 산업(버블 大)이 반드시 임금이 높지는 않습니다.
    <strong>취업자가 많지만 임금·시간이 낮은 산업</strong>은 청년 고용의 질적 리스크 신호입니다.
    </div>
    """, unsafe_allow_html=True)

# ──────────────────────────────────────────────
# 3. 쉬는 이유 분석
# ──────────────────────────────────────────────
st.markdown("""
<div class='section-header'>
  <div class='section-dot' style='background:#ef4444'></div>
  <h2>③ 쉬었음의 주된 이유 — 자발 vs 비자발 구조 분석</h2>
</div>
""", unsafe_allow_html=True)

reason_cols = [c for c in df_reason.columns if c != "시점"]

# 자발/비자발 분류
voluntary_keywords   = ["직장의 휴업", "다음 일 준비", "퇴사(정년 퇴직)"]
involuntary_keywords = ["몸이 좋지", "일의 완료", "원하는 일자리", "일자리(일거리)가 없어서"]

def classify(col):
    for k in voluntary_keywords:
        if k in col: return "자발적"
    for k in involuntary_keywords:
        if k in col: return "비자발적"
    return "기타"

df_reason_melt = df_reason.melt(id_vars="시점", value_vars=reason_cols,
                                 var_name="이유", value_name="인원")
df_reason_melt["인원"] = pd.to_numeric(df_reason_melt["인원"], errors="coerce")
df_reason_melt["유형"] = df_reason_melt["이유"].apply(classify)

col_p, col_q = st.columns([2, 3])

with col_p:
    agg_type = df_reason_melt.groupby("유형")["인원"].mean().reset_index()
    fig_pie = px.pie(agg_type, names="유형", values="인원",
                     title="자발 vs 비자발 비율",
                     color="유형",
                     color_discrete_map={"자발적":"#10b981","비자발적":"#ef4444","기타":"#6b7db3"})
    fig_pie.update_traces(textposition="inside", textinfo="percent+label",
                          hole=0.45,
                          marker=dict(line=dict(color="#0a0e1a", width=2)))
    fig_pie.update_layout(**PLOTLY_LAYOUT, height=360)
    st.plotly_chart(fig_pie, use_container_width=True)

with col_q:
    agg_reason = df_reason_melt.groupby("이유")["인원"].mean().reset_index().sort_values("인원", ascending=True)
    fig_bar = px.bar(agg_reason, x="인원", y="이유", orientation="h",
                     title="이유별 평균 인원",
                     color="인원", color_continuous_scale=["#1a1a2e","#ef4444"])
    fig_bar.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False, height=360)
    st.plotly_chart(fig_bar, use_container_width=True)

# 시계열 추이 (자발 vs 비자발)
st.markdown("#### 📈 비자발적 쉬었음 인원 시계열 추이")
df_type_ts = df_reason_melt.groupby(["시점","유형"])["인원"].sum().reset_index().sort_values("시점")
fig_ts = px.area(df_type_ts, x="시점", y="인원", color="유형",
                  color_discrete_map={"자발적":"#10b981","비자발적":"#ef4444","기타":"#6b7db3"})
fig_ts.update_layout(**PLOTLY_LAYOUT, height=320)
st.plotly_chart(fig_ts, use_container_width=True)

st.markdown("""
<div class='insight-box'>
💡 <strong>비자발적 쉬었음이 증가하는 시점</strong>은 청년 실업 악화의 선행 신호입니다.
<strong>"원하는 일자리를 찾기 어려워서"</strong>와 <strong>"몸이 좋지 않아서"</strong>의 비중 변화를
주목하면 고용 정책의 개입 시점을 포착할 수 있습니다.
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# 4. 비경제활동인구 연계 분석
# ──────────────────────────────────────────────
st.markdown("""
<div class='section-header'>
  <div class='section-dot' style='background:#8b5cf6'></div>
  <h2>④ 비경제활동인구 vs 경제활동 지표 상관 분석</h2>
</div>
""", unsafe_allow_html=True)

df_combined = pd.merge(
    df_eco_f.groupby("시점")[["취업자","실업자","경제활동인구"]].sum().reset_index(),
    df_inact.groupby("시점")["비경제활동인구"].sum().reset_index(),
    on="시점", how="inner"
).sort_values("시점")

col_x, col_y = st.columns(2)

with col_x:
    fig_c = go.Figure()
    for col_name, color in [("취업자","#3b82f6"),("실업자","#ef4444"),("비경제활동인구","#8b5cf6")]:
        if col_name in df_combined.columns:
            fig_c.add_trace(go.Scatter(
                x=df_combined["시점"], y=df_combined[col_name],
                name=col_name, mode="lines",
                line=dict(color=color, width=2),
            ))
    fig_c.update_layout(title="취업·실업·비경활 통합 추이", **PLOTLY_LAYOUT, height=320)
    st.plotly_chart(fig_c, use_container_width=True)

with col_y:
    if len(df_combined) > 3:
        corr = df_combined[["취업자","실업자","비경제활동인구","경제활동인구"]].corr()
        fig_heat = px.imshow(corr, text_auto=".2f",
                              color_continuous_scale=["#ef4444","#0a0e1a","#3b82f6"],
                              title="지표 간 상관관계 히트맵")
        fig_heat.update_layout(**PLOTLY_LAYOUT, height=320)
        st.plotly_chart(fig_heat, use_container_width=True)

# ──────────────────────────────────────────────
# 5. 종합 인사이트
# ──────────────────────────────────────────────
st.markdown("""
<div class='section-header'>
  <div class='section-dot' style='background:#f59e0b'></div>
  <h2>⑤ 종합 인사이트 — 청년 고용의 구조적 문제</h2>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class='insight-box' style='border-left-color:#3b82f6'>
📌 <strong>인사이트 1. 취업자 증가 ≠ 고용의 질 개선</strong><br>
취업자 수는 증가하지만, 임금 대비 근로시간이 높은 산업에 청년이 집중될 경우
고용의 <strong>양적 성장과 질적 정체</strong>가 동시에 나타납니다.
</div>
<div class='insight-box' style='border-left-color:#ef4444'>
📌 <strong>인사이트 2. 비자발적 쉬었음 비율 증가가 핵심 경보 신호</strong><br>
"원하는 일자리를 찾기 어렵다"는 이유가 증가하는 시점은 청년 <strong>구조적 실업의 전조</strong>입니다.
단순 실업률이 낮아도 이 지표가 악화된다면 고용 미스매치가 심화되고 있는 것입니다.
</div>
<div class='insight-box' style='border-left-color:#10b981'>
📌 <strong>인사이트 3. 산업별 임금·취업자 미스매치</strong><br>
취업자가 많은 산업이 반드시 고임금·적정근로시간을 보장하지 않습니다.
청년 유입이 많은 산업의 <strong>임금 경쟁력</strong>을 높이는 것이 고용 정책의 핵심 과제입니다.
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.markdown("""
<div style='text-align:center; color:#2d3a5a; font-size:0.8rem; padding: 12px 0;'>
  Youth Labor Market Dashboard · Built with Streamlit & Plotly
</div>
""", unsafe_allow_html=True)
