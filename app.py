import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# --- 0. 페이지 설정 ---
st.set_page_config(page_title="청년 경제 데이터 분석", layout="wide")

# --- 1. 데이터베이스 연결 함수 ---
@st.cache_data
def load_data_from_db():
    # DB 파일 연결 (파일명이 'economics'라면 확장자 확인 필요)
    # 파일명이 'economics'이고 확장자가 없다면 아래 그대로 유지, 있다면 'economics.db'로 수정
    conn = sqlite3.connect('economics.db')
    
    try:
        # 테이블 이름에 특수문자나 한글이 포함된 경우 따옴표(")로 감싸야 안전합니다.
        df_econ_status = pd.read_sql_query('SELECT * FROM "경제활동현황"', conn)
        df_inactive = pd.read_sql_query('SELECT * FROM "비경제활동인구"', conn)
        df_ind_wage = pd.read_sql_query('SELECT * FROM "산업별_임금_및_근로시간"', conn)
        df_ind_worker = pd.read_sql_query('SELECT * FROM "산업별_취업자"', conn)
        df_reason = pd.read_sql_query('SELECT * FROM "쉬었음_주된_이유"', conn)
    finally:
        conn.close()
        
    return df_econ_status, df_inactive, df_ind_wage, df_ind_worker, df_reason

# 데이터 로드 실행
try:
    df_econ, df_inact, df_wage, df_worker, df_reason = load_data_from_db()
except Exception as e:
    st.error(f"⚠️ 데이터베이스 연결 오류: {e}")
    st.info("💡 팁: 'economics.db' 파일이 app.py와 같은 폴더에 있는지, 테이블 이름이 정확한지 확인해 주세요.")
    st.stop()

# --- 2. 데이터 전처리 ---
# 실업률 컬럼 숫자 변환 및 시점 정렬
if '실업률' in df_econ.columns:
    df_econ['실업률'] = pd.to_numeric(df_econ['실업률'].astype(str).str.replace('%', ''), errors='coerce')
available_months = sorted(df_econ['시점'].unique())

# --- 3. 사이드바 컨트롤러 ---
st.sidebar.header("📍 분석 컨트롤러")
selected_month = st.sidebar.select_slider("분석 시점 선택", options=available_months)

# --- 4. 대시보드 레이아웃 ---
st.title("📊 청년층 경제활동 통합 인사이트")

# 상단 지표
m_col1, m_col2, m_col3 = st.columns(3)
with m_col1:
    avg_unempl = df_econ[df_econ['시점'] == selected_month]['실업률'].mean()
    st.metric("평균 실업률", f"{avg_unempl:.1f}%")
with m_col2:
    inact_count = df_inact[df_inact['시점'] == selected_month]['비경제활동인구'].sum()
    st.metric("비경제활동인구", f"{inact_count:,}명")
with m_col3:
    reason_data = df_reason[df_reason['시점'] == selected_month].drop(columns=['시점'])
    if not reason_data.empty:
        top_reason = reason_data.idxmax(axis=1).values[0]
        st.metric("주요 '쉬었음' 사유", top_reason)

st.divider()

# 그래프 영역
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🗓️ 실업률 변화 추이")
    fig_line = px.line(df_econ, x='시점', y='실업률', color='성별', markers=True)
    st.plotly_chart(fig_line, use_container_width=True)

with col_right:
    st.subheader("❓ '쉬었음' 세부 사유 비중")
    if not reason_data.empty:
        pie_df = reason_data.T.reset_index()
        pie_df.columns = ['사유', '인원']
        fig_pie = px.pie(pie_df, values='인원', names='사유', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# 산업별 분석
st.subheader("🔍 산업별 노동시장 미스매치 (임금 vs 취업자)")
# 테이블 병합
df_merged = pd.merge(df_wage, df_worker, on=['산업별', '시점'])
df_merged['시간당임금'] = df_merged['전체임금총액'] / df_merged['전체근로시간']

fig_scatter = px.scatter(
    df_merged[df_merged['시점'] == selected_month],
    x='전체근로시간', y='전체임금총액', size='취업자수', color='산업별',
    hover_name='산업별', text='산업별', size_max=60
)
st.plotly_chart(fig_scatter, use_container_width=True)
