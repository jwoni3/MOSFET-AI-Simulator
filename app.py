import streamlit as st
import plotly.graph_objects as go
import numpy as np

# 페이지 설정
st.set_page_config(layout="wide", page_title="BJT AI 물리 시뮬레이터")

st.title("📟 AI 반도체 소자 직관 보조 툴: BJT 전자/물리 구조 매퍼")

# 사이드바 입력
st.sidebar.header("🎛️ 제어 및 바이어스")
bjt_type = st.sidebar.radio("타입 선택", ["NPN", "PNP"])
v_be = st.sidebar.slider("V_BE [V]", -1.0, 1.5, 0.75, 0.05)
v_bc = st.sidebar.slider("V_BC [V]", -5.0, 5.0, -2.0, 0.1)

# 로직 및 Q점 계산
mode = "활성" if v_be >= 0.5 else ("포화" if v_be >= 0.5 and v_bc >= 0.5 else "차단")
ic_q = (5.0 - (v_be - v_bc)) / 1.0 # 예시 Q점 계산

# 레이아웃 구성
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### ⚡ 에너지 밴드 다이어그램")
    fig_band = go.Figure()
    
    # 밴드 벤딩 및 캐리어 배치 (질문자님 요청대로 전자/정공 포함)
    x = np.linspace(0, 9, 200)
    ec = 1.5 - (v_be * 0.2 * np.tanh(x - 3)) - (v_bc * 0.2 * np.tanh(x - 6))
    ev = ec - 1.2
    
    fig_band.add_trace(go.Scatter(x=x, y=ec, line=dict(width=3, color='black'), name="Ec"))
    fig_band.add_trace(go.Scatter(x=x, y=ev, line=dict(width=3, color='black'), name="Ev"))
    
    # 전자(●) 및 정공(○) 배치
    fig_band.add_trace(go.Scatter(x=np.linspace(0.5, 8.5, 20), y=np.interp(np.linspace(0.5, 8.5, 20), x, ec)+0.2, 
                                 mode='markers', marker=dict(size=8, color='#1f77b4'), name="전자"))
    fig_band.add_trace(go.Scatter(x=np.linspace(0.5, 8.5, 20), y=np.interp(np.linspace(0.5, 8.5, 20), x, ev)-0.2, 
                                 mode='markers', marker=dict(size=8, color='#d62728', symbol='circle-open'), name="정공"))
    
    fig_band.update_layout(height=350, margin=dict(l=10, r=10, t=20, b=20), plot_bgcolor='rgba(240,240,240,0.5)')
    st.plotly_chart(fig_band, use_container_width=True)

with col2:
    st.markdown("### 📈 I-V 특성 및 부하선")
    fig_iv = go.Figure()
    
    # 직류 부하선 및 Q점
    fig_iv.add_trace(go.Scatter(x=[0, 5], y=[5, 0], line=dict(width=3, color='black'), name="부하선"))
    fig_iv.add_trace(go.Scatter(x=[2.5], y=[ic_q], mode='markers', marker=dict(size=15, color='red'), name="Q점"))
    
    fig_iv.update_layout(height=350, margin=dict(l=10, r=10, t=20, b=20), xaxis_title="V_CE [V]", yaxis_title="I_C [mA]")
    st.plotly_chart(fig_iv, use_container_width=True)

# AI 응답 섹션
st.markdown("---")
user_question = st.text_area("🤖 AI에게 질문하기", "이 동작 모드에서 전자들이 어떻게 이동해?", height=80)
if st.button("질문 전송 (AI 해설)"):
    st.info("AI가 해당 동작 모드와 물리 구조를 분석합니다.")