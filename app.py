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
# 커스텀 CSS (화사한 Light Theme로 전면 개편)
# ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&family=Space+Mono:wght@400;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}
.stApp {
    background: #f8fafc; /* 아주 연한 회파랑색 배경 */
    color: #1e293b; /* 진한 회갈색 텍스트 */
}
section[data-testid="stSidebar"] {
    background: #ffffff !important; /* 사이드바는 완전 흰색 */
    border-right: 1px solid #e2e8f0;
}
.metric-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 24px;
    t
