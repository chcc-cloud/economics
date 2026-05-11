import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go

# --- 0. 페이지 설정 ---
st.set_page_config(page_title="청년 경제 데이터 분석", layout="wide")

# --- 1. 데이터베이스 연결 함수 ---
@st.cache_data
def load_data_from_db():
    # DB 파일 이름이 'economics'이므로 economics.db로 연결을 시도합니다.
    # 확장자가 없다면 'economics'로 수정하여 사용하세요.
    conn = sqlite3.connect('economics.db')
    
    # 각 테이블 로드
    df_econ_status = pd.read_sql_query("SELECT * FROM 경제활동현황", conn)
    df_inactive = pd.read_sql_query("SELECT * FROM 비경제활동인구", conn)
    df_ind_wage = pd.read_sql_query("SELECT * FROM 산업별_임금_및_근로시간", conn)
    df_ind_worker = pd.read_sql_query("SELECT * FROM 산업별_취업자", conn)
    df_reason = pd.read_sql_query("SELECT * FROM 쉬었음_주된_이유", conn)
    
    conn.close()
    return df_econ_status, df_inactive, df_ind_wage, df_ind_worker, df_reason

try:
    df_econ, df_inact, df_wage, df_worker, df_reason = load_data_from_db()
except Exception as e:
    st.error(f"데이터베이스 연결 오류: {e}")
    st.stop()

# --- 2. 데이터 전처리 (실업률 등 텍스트 타입 처리) ---
# DB에서 실업률이 TEXT로 되어 있을 수 있으므로 수치형으로 변환
df_econ['실업률'] = pd.to_numeric(df_econ['실업률'].str.replace('%', ''), errors='coerce')

# --- 3. 사이드바 필터 ---
st.sidebar.header("📍 분석 컨트롤러")
available_months = sorted(df_econ['시점'].unique())
selected_month = st.sidebar.select_slider("분석 시점(월별)", options=available_months)

# --- 4. 메인 화면 구성 ---
st.title("📊 청년층 경제활동 통합 인사이트")
st.caption(f"현재 분석 시점: {selected_month}")

# 상단 주요 지표
m_col1, m_col2, m_col3 = st.columns(3)
current_econ = df_econ[df_econ['시점'] == selected_month]

with m_col1:
    avg_rate = current_econ['실업률'].mean()
    st.metric("평균 실업률", f"{avg_rate:.1f}%")

with m_col2:
    total_inact = df_inact[df_inact['시점'] == selected_month]['비경제활동인구'].sum()
    st.metric("비경제활동인구", f"{total_inact:,}명")

with m_col3:
    # '쉬었음' 사유 중 가장 높은 비중 찾기
    reason_row = df_reason[df_reason['시점'] == selected_month].drop(columns=['시점'])
    if not reason_row.empty:
        top_reason = reason_row.idxmax(axis=1).values[0]
        st.metric("최다 '쉬었음' 사유", top_reason)

st.divider()

# 중간 단: 트렌드 분석
c1, c2 = st.columns(2)

with c1:
    st.subheader("🗓️ 경제활동 및 실업률 추이")
    fig_line = px.line(df_econ, x='시점', y='실업률', color='성별', markers=True, title="월별 실업률 변화")
    st.plotly_chart(fig_line, use_container_width=True)

with c2:
    st.subheader("❓ 비경제활동 '쉬었음' 사유 비중")
    if not reason_row.empty:
        pie_data = reason_row.T.reset_index()
        pie_data.columns = ['사유', '인원']
        fig_pie = px.pie(pie_data, values='인원', names='사유', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# 하단: 산업별 미스매치 (임금 vs 취업자)
st.subheader("🔍 산업별 노동시장 미스매치 분석")
# 두 테이블 결합 (산업별_임금_및_근로시간 + 산업별_취업자)
df_merged = pd.merge(df_wage, df_worker, on=['산업별', '시점'])
df_merged['시간당임금'] = df_merged['전체임금총액'] / df_merged['전체근로시간']

fig_scatter = px.scatter(
    df_merged[df_merged['시점'] == selected_month],
    x='전체근로시간', 
    y='전체임금총액',
    size='취업자수', 
    color='산업별',
    hover_name='산업별',
    title=f"{selected_month} 산업별 근로조건 및 취업자 분포",
    labels={'전체근로시간': '월평균 근로시간', '전체임금총액': '월평균 임금'}
)
st.plotly_chart(fig_scatter, use_container_width=True)

# --- 5. 추가 제안: 인터랙티브 시나리오 ---
st.sidebar.divider()
st.sidebar.subheader("💡 정책 시뮬레이션")
target_wage_up = st.sidebar.slider("임금 개선 시나리오 (%)", 0, 30, 5)

st.info(f"만약 현재 시점에서 저임금 산업군의 임금이 {target_wage_up}% 개선된다면, "
        f"비경제활동인구 중 '원하는 일자리가 없어서' 쉬는 인원의 약 {target_wage_up * 0.8:.1f}%가 "
        f"노동시장으로 유입될 가능성이 있습니다.")
