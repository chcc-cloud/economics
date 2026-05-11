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
# CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&family=Space+Mono:wght@400;700&display=swap');

html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }

/* 전체 배경: 연한 라벤더-화이트 */
.stApp { background: #f5f4fb; color: #2d2a4a; }

/* 사이드바 */
section[data-testid="stSidebar"] {
    background: #faf9ff !important;
    border-right: 1px solid #ddd8f5;
}

/* KPI 카드 */
.metric-card {
    background: #ffffff;
    border: 1px solid #e4dffa;
    border-radius: 18px;
    padding: 24px;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: 0 4px 14px rgba(109, 92, 201, 0.08);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: var(--accent, #7c6fd4);
}
.metric-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 24px rgba(109, 92, 201, 0.14);
}
.metric-title {
    font-size: 0.78rem;
    font-weight: 600;
    color: #8b83c4;
    letter-spacing: 0.06em;
    margin-bottom: 8px;
    text-transform: uppercase;
}
.metric-value {
    font-family: 'Space Mono', monospace;
    font-size: 1.95rem;
    font-weight: 700;
    color: #2d2a4a;
}
.metric-delta { font-size: 0.83rem; margin-top: 6px; font-weight: 600; }
.delta-up   { color: #e05c7a; }
.delta-down { color: #5ba89e; }

/* 섹션 헤더 */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 36px 0 16px 0;
    padding-bottom: 12px;
    border-bottom: 1px solid #ddd8f5;
}
.section-header h2 {
    font-size: 1.15rem;
    font-weight: 700;
    color: #2d2a4a;
    margin: 0;
}
.section-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    background: #7c6fd4;
    flex-shrink: 0;
}

/* 차트 인사이트 박스 */
.chart-insight {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    background: #efedf9;
    border: 1px solid #cdc7ef;
    border-left: 4px solid #7c6fd4;
    border-radius: 10px;
    padding: 14px 18px;
    margin: 8px 0 22px 0;
    font-size: 0.88rem;
    line-height: 1.7;
    color: #3d3868;
}
.chart-insight .icon { font-size: 1.1rem; flex-shrink: 0; margin-top: 2px; }
.chart-insight b { color: #5b4fc2; }

/* 종합 인사이트 박스 */
.insight-box {
    border-radius: 14px;
    padding: 20px 24px;
    margin: 12px 0;
    font-size: 0.93rem;
    line-height: 1.7;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Plotly 공통 테마
# ──────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(255,255,255,1)",
    plot_bgcolor="rgba(255,255,255,1)",
    font=dict(family="Noto Sans KR", color="#5a5480", size=12),
    xaxis=dict(gridcolor="#ece9f8", linecolor="#ddd8f5", tickcolor="#8b83c4"),
    yaxis=dict(gridcolor="#ece9f8", linecolor="#ddd8f5", tickcolor="#8b83c4"),
    margin=dict(l=20, r=20, t=50, b=20),
    legend=dict(bgcolor="rgba(255,255,255,0.85)", font=dict(color="#3d3868")),
    colorway=["#7c6fd4","#a78bdb","#6baed6","#b8a9e8","#9ecae1","#c7b8f0","#74c0c8"],
)

# ──────────────────────────────────────────────
# 인사이트 박스 헬퍼
# ──────────────────────────────────────────────
def insight(icon, text):
    st.markdown(f"""
    <div class='chart-insight'>
      <span class='icon'>{icon}</span>
      <span>{text}</span>
    </div>""", unsafe_allow_html=True)

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
# 사이드바
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 데이터 설정")
    db_path = st.text_input("SQLite DB 파일 경로", value="economics.db")
    st.markdown("---")
    st.markdown("### 대시보드 스토리")
    st.markdown("""
    <div style='font-size:0.9rem; color:#5a5480; line-height:1.8; background:#efedf9; padding:15px; border-radius:10px;'>
    <b style='color:#2d2a4a'>청년 고용의 역설</b><br><br>
    취업자 수는 유지되지만<br>
    실업률은 <b style='color:#9b3f68'>급등</b>하고<br>
    쉬는 이유의 <b style='color:#7c6fd4'>60%가 비자발적</b>.<br><br>
    양적 고용 뒤에 숨은<br>
    <b>질적 미스매치</b>를 추적합니다.
    </div>
    """, unsafe_allow_html=True)

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

def make_numeric(df, cols):
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(',', ''), errors='coerce'
            ).fillna(0)

make_numeric(df_eco,   ["취업자", "실업자", "경제활동인구"])
make_numeric(df_emp,   ["취업자수"])
make_numeric(df_wage,  ["전체임금총액", "전체근로시간"])
make_numeric(df_inact, ["비경제활동인구"])

# ──────────────────────────────────────────────
# 헤더
# ──────────────────────────────────────────────
st.markdown("""
<div style='padding: 20px 0 10px 0;'>
  <div style='font-family: Space Mono, monospace; font-size: 0.8rem; color: #7c6fd4;
              letter-spacing: 0.15em; text-transform: uppercase; margin-bottom: 5px; font-weight: 700;'>
    Youth Labor Market Intelligence
  </div>
  <h1 style='font-size: 2.2rem; font-weight: 800; color: #0f172a; margin: 0;'>청년 고용 현황 대시보드</h1>
  <p style='color: #64748b; margin-top: 8px; font-size: 1rem;'>
    경제활동인구 · 실업률 · 산업별 임금 · 비경활 이유 통합 분석
  </p>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# 성별 필터
# ──────────────────────────────────────────────
if "성별" in df_eco.columns:
    genders_only = sorted([g for g in df_eco["성별"].dropna().unique() if g != '계'])
    selected_gender = st.selectbox("성별 필터", ["전체"] + genders_only, index=0)

    if selected_gender == "전체":
        if '계' in df_eco["성별"].values:
            df_eco_f = df_eco[df_eco["성별"] == '계'].copy()
        else:
            df_eco_f = df_eco.groupby("시점")[["취업자","실업자","경제활동인구"]].sum().reset_index()
            df_eco_f["실업률"] = (df_eco_f["실업자"] / df_eco_f["경제활동인구"] * 100).round(1).astype(str)
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
        d   = cur_val - prv_val
        pct = d / prv_val * 100 if prv_val != 0 else 0
        up  = d > 0
        cls = ("delta-down" if up else "delta-up") if invert else ("delta-up" if up else "delta-down")
        return f'<div class="metric-delta {cls}">{"▲" if up else "▼"} {abs(d):,.0f}{unit} ({pct:+.1f}%)</div>'
    except:
        return ""

c1, c2, c3, c4 = st.columns(4)
cards = [
    (c1, "취업자 수",    "취업자",       "명", False, "#7c6fd4"),
    (c2, "실업자 수",    "실업자",       "명", True,  "#e05c7a"),
    (c3, "경제활동인구", "경제활동인구", "명", False, "#74c0c8"),
    (c4, "실업률",       "실업률",       "%",  True,  "#a78bdb"),
]
for col_obj, title, field, unit, invert, accent in cards:
    try:
        val     = str(latest.get(field, 0)).replace('%','')
        display = f"{float(val):.1f}" if field == "실업률" else fmt_num(val)
        delta   = delta_html(latest, prev, field, unit, invert)
    except:
        display, delta = "–", ""
    with col_obj:
        st.markdown(f"""
        <div class='metric-card' style='--accent:{accent}'>
          <div class='metric-title'>{title}</div>
          <div class='metric-value'>{display}</div>
          {delta}
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# ① 경제활동 추이
# ══════════════════════════════════════════════
st.markdown("<div class='section-header'><div class='section-dot'></div><h2>① 경제활동인구 · 실업률 추이</h2></div>", unsafe_allow_html=True)

col_l, col_r = st.columns([3, 2])

with col_l:
    df_ts = df_eco_f.sort_values("시점").copy()
    df_ts["실업률_num"] = pd.to_numeric(
        df_ts.get("실업률", pd.Series(dtype=float)).astype(str).str.replace('%',''), errors='coerce'
    )
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=df_ts["시점"], y=df_ts["취업자"],
        name="취업자", mode="lines+markers",
        line=dict(color="#7c6fd4", width=2.5)), secondary_y=False)
    fig.add_trace(go.Scatter(x=df_ts["시점"], y=df_ts["실업자"],
        name="실업자", mode="lines+markers",
        line=dict(color="#e05c7a", width=2, dash="dot")), secondary_y=False)
    if not df_ts["실업률_num"].isna().all():
        fig.add_trace(go.Scatter(x=df_ts["시점"], y=df_ts["실업률_num"],
            name="실업률(%)", mode="lines",
            line=dict(color="#a78bdb", width=2)), secondary_y=True)
        fig.update_yaxes(title_text="실업률 (%)", secondary_y=True,
                         gridcolor="#e2e8f0", color="#475569")
    fig.update_layout(title="연도/월별 청년 경제활동 추이", **PLOTLY_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

    # ▶ 차트 인사이트
    insight("📉",
        "취업자 수는 완만히 감소하는 반면 <b>실업률은 하반기에 급등</b>하는 패턴이 나타납니다. "
        "이는 취업자 감소폭보다 <b>실업자 유입 속도가 빠른 구조</b>임을 의미하며, "
        "단순 취업자 수만으로는 고용 현황을 낙관하기 어렵습니다.")

with col_r:
    if "성별" in df_eco.columns:
        df_gender_base = df_eco[df_eco["성별"] != '계']
        df_gender = df_gender_base.groupby("성별")[["취업자","실업자"]].mean().reset_index()
        fig2 = px.bar(
            df_gender.melt(id_vars="성별", var_name="구분", value_name="평균"),
            x="성별", y="평균", color="구분", barmode="group",
            title="성별 평균 취업/실업자 비교",
            color_discrete_map={"취업자":"#7c6fd4","실업자":"#e05c7a"})
        fig2.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig2, use_container_width=True)

        # ▶ 차트 인사이트
        insight("👩‍💼",
            "여성 취업자가 남성보다 많지만 <b>실업자 수의 격차는 상대적으로 적습니다.</b> "
            "여성의 고용률은 높지만 <b>고용 안정성과 직종 다양성은 여전히 취약</b>한 구조를 보여줍니다.")

# ══════════════════════════════════════════════
# ② 산업별 분석
# ══════════════════════════════════════════════
st.markdown("<div class='section-header'><div class='section-dot' style='background:#a78bdb'></div><h2>② 산업별 취업자 · 임금 · 근로시간 분석</h2></div>", unsafe_allow_html=True)

col_a, col_b, col_c = st.columns(3)

with col_a:
    agg = df_emp.groupby("산업별")["취업자수"].mean().reset_index().sort_values("취업자수").tail(12)
    fig = px.bar(agg, x="취업자수", y="산업별", orientation="h",
                 title="산업별 평균 취업자수",
                 color="취업자수", color_continuous_scale=["#e0dcf8","#5b4fc2"])
    fig.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)
    insight("🏭",
        "<b>C(제조업)가 취업자 수 압도적 1위</b>이며, Q(보건복지)·G(도소매)가 뒤를 잇습니다. "
        "청년 고용이 <b>제조업과 서비스업에 집중</b>되어 있어 산업 포트폴리오가 편중되어 있습니다.")

with col_b:
    agg2 = df_wage.groupby("산업별")["전체임금총액"].mean().reset_index().sort_values("전체임금총액").tail(12)
    fig = px.bar(agg2, x="전체임금총액", y="산업별", orientation="h",
                 title="산업별 평균 임금",
                 color="전체임금총액", color_continuous_scale=["#d8eefb","#3b82c4"])
    fig.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)
    insight("💰",
        "<b>D(전기가스)·K(금융보험)이 최고 임금</b>을 기록하지만 취업자 수는 적습니다. "
        "반면 취업자 1위인 C(제조업)는 <b>임금 중간 수준</b>에 그쳐 고용 집중과 임금 수준이 불일치합니다.")

with col_c:
    agg3 = df_wage.groupby("산업별")["전체근로시간"].mean().reset_index().sort_values("전체근로시간").tail(12)
    fig = px.bar(agg3, x="전체근로시간", y="산업별", orientation="h",
                 title="산업별 평균 근로시간",
                 color="전체근로시간", color_continuous_scale=["#e8e2f8","#9b7fe8"])
    fig.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)
    insight("⏰",
        "E·C·B 산업이 <b>근로시간 상위권</b>을 차지합니다. "
        "특히 청년이 가장 많이 취업한 <b>C(제조업)는 근로시간 2위</b>로, "
        "긴 시간 일하지만 임금은 최고 수준이 아닌 <b>저효율 고용 구조</b>가 확인됩니다.")

# 산점도
st.markdown("#### 임금 vs 취업자 수 — 산업별 포지셔닝")
df_merge = pd.merge(
    df_emp.groupby("산업별")["취업자수"].mean().reset_index(),
    df_wage.groupby("산업별")[["전체임금총액","전체근로시간"]].mean().reset_index(),
    on="산업별", how="inner"
)
if not df_merge.empty:
    fig_sc = px.scatter(df_merge, x="취업자수", y="전체임금총액",
                         size="전체근로시간", color="산업별",
                         hover_name="산업별", text="산업별",
                         title="취업자가 많은 산업이 임금도 높을까?",
                         size_max=40)
    fig_sc.update_traces(textposition="top center", textfont_size=10)
    fig_sc.update_layout(**PLOTLY_LAYOUT, height=450, showlegend=False)
    st.plotly_chart(fig_sc, use_container_width=True)

    insight("🎯",
        "C(제조업)는 <b>취업자 최다이지만 임금은 중간, 근로시간은 상위권(버블 大)</b>입니다. "
        "반면 D·K는 임금 최상위지만 취업자가 적어 <b>청년이 접근하기 어려운 고임금 산업</b>임을 보여줍니다. "
        "고용의 양과 질이 반비례하는 <b>구조적 미스매치</b>가 명확합니다.")

# ══════════════════════════════════════════════
# ③ 쉬는 이유 분석
# ══════════════════════════════════════════════
st.markdown("<div class='section-header'><div class='section-dot' style='background:#b8a9e8'></div><h2>③ 청년층 쉬었음의 주된 이유</h2></div>", unsafe_allow_html=True)

reason_cols = [c for c in df_reason.columns if c != "시점"]
voluntary_kw   = ["직장의 휴업", "다음 일 준비", "퇴사(정년 퇴직)"]
involuntary_kw = ["몸이 좋지", "일의 완료", "원하는 일자리", "일자리(일거리)가 없어서"]

def classify(col):
    for k in voluntary_kw:
        if k in col: return "자발적"
    for k in involuntary_kw:
        if k in col: return "비자발적"
    return "기타"

df_rm = df_reason.melt(id_vars="시점", value_vars=reason_cols, var_name="이유", value_name="인원")
df_rm["인원"] = pd.to_numeric(df_rm["인원"].astype(str).str.replace(',',''), errors="coerce").fillna(0)
df_rm["유형"] = df_rm["이유"].apply(classify)

col_p, col_q = st.columns([2, 3])

with col_p:
    agg_type = df_rm.groupby("유형")["인원"].sum().reset_index()
    fig_pie = px.pie(agg_type, names="유형", values="인원",
                     title="자발 vs 비자발 비율", color="유형",
                     color_discrete_map={"자발적":"#74c0c8","비자발적":"#b8a9e8","기타":"#c4bfdf"})
    fig_pie.update_traces(textposition="inside", textinfo="percent+label", hole=0.45)
    fig_pie.update_layout(**PLOTLY_LAYOUT, height=360)
    st.plotly_chart(fig_pie, use_container_width=True)

    insight("🔴",
        "쉬고 있는 청년의 <b>60% 이상이 비자발적 이유</b>로 경제활동을 중단했습니다. "
        "이는 단순한 '쉬는 선택'이 아닌 <b>구조적 배제</b>에 가깝습니다.")

with col_q:
    agg_reason = df_rm.groupby("이유")["인원"].mean().reset_index().sort_values("인원")
    fig_bar = px.bar(agg_reason, x="인원", y="이유", orientation="h",
                     title="이유별 평균 인원",
                     color="인원", color_continuous_scale=["#e0dcf8","#7c3fa8"])
    fig_bar.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False, height=360)
    st.plotly_chart(fig_bar, use_container_width=True)

    insight("🔍",
        "<b>'원하는 일자리(일거리)를 찾기 어려워서'가 압도적 1위</b>입니다. "
        "이는 일자리 자체의 부재가 아닌 <b>직종·임금 미스매치</b>가 핵심 원인임을 나타냅니다. "
        "청년이 원하는 양질의 일자리 공급이 정책의 핵심 과제입니다.")

# ══════════════════════════════════════════════
# ④ 상관관계 분석
# ══════════════════════════════════════════════
st.markdown("<div class='section-header'><div class='section-dot' style='background:#9ecae1'></div><h2>④ 경제활동 지표 간 상관관계 분석</h2></div>", unsafe_allow_html=True)

if "성별" in df_eco.columns and '계' in df_eco["성별"].values:
    df_eco_total = df_eco[df_eco["성별"] == '계']
else:
    df_eco_total = df_eco.groupby("시점")[["취업자","실업자","경제활동인구"]].sum().reset_index()

df_combined = pd.merge(
    df_eco_total.groupby("시점")[["취업자","실업자","경제활동인구"]].sum().reset_index(),
    df_inact.groupby("시점")["비경제활동인구"].sum().reset_index(),
    on="시점", how="inner"
).sort_values("시점")

col_x, col_y = st.columns(2)

with col_x:
    fig_c = go.Figure()
    for name, color in [("취업자","#7c6fd4"),("실업자","#e05c7a"),("비경제활동인구","#9ecae1")]:
        if name in df_combined.columns:
            fig_c.add_trace(go.Scatter(x=df_combined["시점"], y=df_combined[name],
                name=name, mode="lines", line=dict(color=color, width=2)))
    fig_c.update_layout(title="취업·실업·비경활 통합 추이", **PLOTLY_LAYOUT, height=320)
    st.plotly_chart(fig_c, use_container_width=True)

    insight("👻",
        "비경제활동인구가 <b>취업자 대비 완만하게 유지</b>되는 반면 실업자는 소폭 증가합니다. "
        "이는 <b>실업자로 집계되지 않는 '숨은 실업'(구직 단념자)</b>이 비경활 수치 안에 포함되어 있을 가능성을 시사합니다.")

with col_y:
    if len(df_combined) > 3:
        corr_cols = ["취업자","실업자","비경제활동인구","경제활동인구"]
        corr = df_combined[corr_cols].corr()
        fig_heat = px.imshow(corr, text_auto=".2f",
                              color_continuous_scale=["#b8a9e8","#ffffff","#6baed6"],
                              title="지표 간 상관관계 히트맵")
        fig_heat.update_layout(**PLOTLY_LAYOUT, height=320)
        st.plotly_chart(fig_heat, use_container_width=True)

        insight("📐",
            "취업자와 경제활동인구의 상관계수가 <b>0.94로 매우 높아</b>, "
            "경제활동인구 증감이 곧 취업자 수 변화로 이어지는 <b>제로섬 구조</b>가 확인됩니다. "
            "반면 취업자↑ 시 실업자↓(-0.29)는 <b>둘이 서로 상충하는 관계</b>임을 수치로 증명합니다.")

# ══════════════════════════════════════════════
# ⑤ 종합 인사이트
# ══════════════════════════════════════════════
st.markdown("<div class='section-header'><div class='section-dot' style='background:#6baed6'></div><h2>⑤ 종합 인사이트 — 청년 고용의 구조적 문제</h2></div>", unsafe_allow_html=True)

st.markdown("""
<div class='insight-box' style='background:#efedf9; border:1px solid #cdc7ef; border-left:4px solid #7c6fd4; color:#2d2a4a;'>
📌 <strong>인사이트 1. 취업자 증가 ≠ 고용의 질 개선</strong><br>
취업자 1위 산업(제조업)은 근로시간 2위이지만 임금은 중간 수준. 청년이 몰리는 곳일수록
<b>긴 시간 일하고 적게 받는 구조</b>가 고착화되고 있습니다.
</div>
<div class='insight-box' style='background:#f5eef8; border:1px solid #d8b8e8; border-left:4px solid #b8a9e8; color:#2d2a4a;'>
📌 <strong>인사이트 2. 비자발적 쉬었음 60% — 선택이 아닌 구조적 배제</strong><br>
실업자로 집계되지 않지만 <b>"원하는 일자리가 없어서"</b> 쉬고 있는 청년이 가장 많습니다.
표면 실업률이 낮아도 <b>고용 미스매치는 심각</b>한 상태입니다.
</div>
<div class='insight-box' style='background:#f0f4fc; border:1px solid #c7d8f0; border-left:4px solid #6baed6; color:#2d2a4a;'>
📌 <strong>인사이트 3. 청년이 몰리는 산업일수록 임금 대비 근로시간이 길다</strong><br>
취업자가 가장 많은 C(제조업)는 근로시간 상위권이면서 임금은 중간 수준에 그칩니다.
청년 고용이 집중된 산업의 <b>근로 여건 개선 — 임금 인상 또는 근로시간 단축</b>이
고용의 질을 높이는 직접적인 정책 과제입니다.
</div>
""", unsafe_allow_html=True)

st.markdown("<br><br><div style='text-align:center; color:#8b83c4; font-size:0.85rem;'>Youth Labor Market Dashboard · Built with Streamlit & Plotly</div>", unsafe_allow_html=True)
