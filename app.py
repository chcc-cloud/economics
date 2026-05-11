import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os

# 페이지 설정
st.set_page_config(page_title="경제 지표 분석 대시보드", layout="wide")

# 1. 데이터베이스 연결 확인
DB_PATH = 'economics.db'

if not os.path.exists(DB_PATH):
    st.error(f"⚠️ '{DB_PATH}' 파일을 찾을 수 없습니다. DB 파일이 같은 폴더에 있는지 확인해주세요!")
    st.stop()

def run_query(query):
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn)

# 헤더 부분
st.title("📊 대한민국 경제활동 현황 분석")
st.markdown("공공데이터를 활용하여 경제 지표를 한눈에 파악하는 대시보드입니다.")
st.divider()

# --- 차트 1: 성별 취업·실업 비교 ---
st.subheader("1. 남녀 간 취업·실업 격차는 얼마나 될까?")
sql1 = "SELECT 성별, AVG(취업자) as 평균취업자, AVG(실업자) as 평균실업자 FROM 경제활동현황 WHERE 성별 != '계' GROUP BY 성별"
df1 = run_query(sql1)

col1_1, col1_2 = st.columns([2, 1])
with col1_1:
    fig1 = px.bar(df1, x="성별", y=["평균취업자", "평균실업자"], barmode="group", title="성별 고용 지표 비교")
    st.plotly_chart(fig1, use_container_width=True)
with col1_2:
    st.info("💡 **사용한 SQL**")
    st.code(sql1, language='sql')

# --- 차트 2: 실업률 시계열 추이 ---
st.subheader("2. 시점별 실업률은 어떻게 변화했을까?")
sql2 = "SELECT 시점, 실업률 FROM 경제활동현황 WHERE 성별 = '계'"
df2 = run_query(sql2)
df2['실업률'] = pd.to_numeric(df2['실업률'], errors='coerce') # TEXT를 숫자로 변환

col2_1, col2_2 = st.columns([2, 1])
with col2_1:
    fig2 = px.line(df2, x="시점", y="실업률", markers=True, title="전체 실업률 변화 추이")
    st.plotly_chart(fig2, use_container_width=True)
with col2_2:
    st.info("💡 **사용한 SQL**")
    st.code(sql2, language='sql')

# --- 차트 3: 산업별 취업자 TOP 10 ---
st.subheader("3. 어떤 산업에 취업자가 가장 많을까?")
sql3 = "SELECT 산업별, AVG(취업자수) as 평균취업자수 FROM 산업별_취업자 GROUP BY 산업별 ORDER BY 평균취업자수 DESC LIMIT 10"
df3 = run_query(sql3)

col3_1, col3_2 = st.columns([2, 1])
with col3_1:
    fig3 = px.bar(df3, y="산업별", x="평균취업자수", orientation='h', title="산업별 취업자 TOP 10")
    st.plotly_chart(fig3, use_container_width=True)
with col3_2:
    st.info("💡 **사용한 SQL**")
    st.code(sql3, language='sql')

# --- 차트 4: 산업별 임금 vs 근로시간 ---
st.subheader("4. 임금이 높은 산업이 근로시간도 길까?")
sql4 = "SELECT 산업별, AVG(전체근로시간) as 근로시간, AVG(전체임금총액) as 임금 FROM 산업별_임금_및_근로시간 GROUP BY 산업별"
df4 = run_query(sql4)

col4_1, col4_2 = st.columns([2, 1])
with col4_1:
    fig4 = px.scatter(df4, x="근로시간", y="임금", text="산업별", size="임금", color="산업별", title="임금과 근로시간의 상관관계")
    st.plotly_chart(fig4, use_container_width=True)
with col4_2:
    st.info("💡 **사용한 SQL**")
    st.code(sql4, language='sql')

# --- 차트 5: 비경제활동 이유 분포 ---
st.subheader("5. 사람들이 쉬고 있는 가장 큰 이유는?")
sql5 = "SELECT * FROM 쉬었음의_주된_이유 ORDER BY 시점 DESC LIMIT 1"
df5 = run_query(sql5).drop(columns=['시점'])
# 데이터 재구성 (Pie 차트용)
df5_melted = df5.melt(var_name="사유", value_name="인원")

col5_1, col5_2 = st.columns([2, 1])
with col5_1:
    fig5 = px.pie(df5_melted, values="인원", names="사유", hole=0.4, title="최근 비경제활동 사유 분포")
    st.plotly_chart(fig5, use_container_width=True)
with col5_2:
    st.info("💡 **사용한 SQL**")
    st.code(sql5, language='sql')

# --- 차트 6: 경제활동 참가율 추이 ---
st.subheader("6. 경제활동 참가율은 시간이 갈수록 늘고 있나?")
sql6 = """
SELECT A.시점, A.경제활동인구, B.비경제활동인구 
FROM (SELECT 시점, 경제활동인구 FROM 경제활동현황 WHERE 성별='계') A
JOIN 비경제활동인구 B ON A.시점 = B.시점
"""
df6 = run_query(sql6)
# 참가율 계산: (경제활동인구 / (경제활동인구 + 비경제활동인구)) * 100
df6['참가율'] = (df6['경제활동인구'] / (df6['경제활동인구'] + df6['비경제활동인구'])) * 100

col6_1, col6_2 = st.columns([2, 1])
with col6_1:
    fig6 = px.line(df6, x="시점", y=["경제활동인구", "비경제활동인구"], title="인구 구성 변화 추이")
    st.plotly_chart(fig6, use_container_width=True)
    st.caption("※ 경제활동인구와 비경제활동인구의 시점별 추이입니다.")
with col6_2:
    st.info("💡 **사용한 SQL**")
    st.code(sql6, language='sql')
