import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="BJT 물리 및 특성 시뮬레이터", layout="wide")

st.markdown("<h2 style='text-align: center;'>🔬 BJT(NPN) 통합 시뮬레이터</h2>", unsafe_allow_html=True)

# 1. 사이드바 제어
with st.sidebar:
    st.markdown("### **🎛️ 바이어스 & 회로 파라미터**")
    v_be = st.slider("V_BE [V]", 0.0, 1.0, 0.7, 0.05)
    v_ce = st.slider("V_CE [V]", 0.0, 6.0, 2.5, 0.1)
    rc = st.slider("부하 저항 Rc [kΩ]", 0.5, 2.0, 1.0, 0.1)
    st.markdown("---")
    ask_ai_btn = st.button("AI 해설 받기", type="primary", use_container_width=True)

# 2. 로직: BJT 특성 계산
ic = (5.0 - v_ce) / rc  # 5V Vcc 가정
# 친구분 그래프 스타일 반영
mode = "포화" if v_ce < 0.2 else "활성"

col1, col2 = st.columns([1, 1])

# 3. 에너지 밴드 다이어그램 (상단 영역 반영)
with col1:
    st.markdown("<div class='header-text'>⚡ 에너지 밴드 다이어그램</div>", unsafe_allow_html=True)
    fig_band = go.Figure()
    # 영역별 배경색 구분 (Emitter/Base/Collector)
    x = np.linspace(0, 9, 300)
    # 밴드 벤딩 묘사 (친구분 이미지처럼 분리된 Fermi level)
    fig_band.add_trace(go.Scatter(x=[0,3,3,6,6,9], y=[1,1,0.5,0.5,1,1], line=dict(width=3, color='black'), name="Ec"))
    fig_band.update_layout(height=250, plot_bgcolor='rgba(240,240,240,0.5)')
    st.plotly_chart(fig_band, use_container_width=True)

# 4. I-V 특성 및 부하선 (하단 영역 반영)
with col2:
    st.markdown("<div class='header-text'>📈 특성 곡선 & 부하선</div>", unsafe_allow_html=True)
    fig_iv = go.Figure()
    
    # 여러 IB 곡선 (10uA ~ 50uA)
    for ib in [10, 20, 30, 40, 50]:
        v = np.linspace(0, 6, 100)
        i = (ib/10) * (1 - np.exp(-v))
        fig_iv.add_trace(go.Scatter(x=v, y=i, mode='lines', name=f"IB={ib}uA", line=dict(width=2)))
    
    # 직류 부하선 (친구분의 굵은 검은색 직선)
    fig_iv.add_trace(go.Scatter(x=[0, 5], y=[5/rc, 0], mode='lines', line=dict(width=4, color='black'), name="부하선"))
    # 동작점 Q
    fig_iv.add_trace(go.Scatter(x=[v_ce], y=[ic], mode='markers', marker=dict(size=15, color='red'), name="동작점 Q"))
    
    fig_iv.update_layout(height=300, xaxis_title="V_CE [V]", yaxis_title="I_C [mA]")
    st.plotly_chart(fig_iv, use_container_width=True)

st.info("친구분의 구현 방식처럼 에너지 밴드와 I-V 특성을 한눈에 비교할 수 있습니다.")