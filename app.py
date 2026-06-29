import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="BJT 물리 시뮬레이터", layout="wide")

st.markdown("<h2 style='text-align: center;'>🔬 BJT(NPN) 동작 모드 및 밴드 다이어그램</h2>", unsafe_allow_html=True)

# 1. 사이드바: 전압 입력
with st.sidebar:
    st.markdown("### 🎛️ BJT 바이어스 설정")
    v_be = st.slider("Base-Emitter 전압 (V_BE) [V]", -1.0, 1.0, 0.0, 0.1)
    v_bc = st.slider("Base-Collector 전압 (V_BC) [V]", -1.0, 1.0, 0.0, 0.1)
    
    # 바이어스 판별
    be_state = "순방향" if v_be >= 0.5 else "역방향"
    bc_state = "순방향" if v_bc >= 0.5 else "역방향"
    
    # 동작 모드 결정
    if v_be < 0.5 and v_bc < 0.5: mode = "차단 (Cutoff)"
    elif v_be >= 0.5 and v_bc < 0.5: mode = "순방향 활성 (Forward Active)"
    elif v_be >= 0.5 and v_bc >= 0.5: mode = "포화 (Saturation)"
    else: mode = "역방향 활성 (Reverse Active)"

# 2. 메인 화면
col1, col2 = st.columns([1, 1])

with col1:
    st.info(f"### 현재 동작 모드: {mode}")
    st.metric("B-E 접합 상태", be_state)
    st.metric("B-C 접합 상태", bc_state)

# 3. 에너지 밴드 다이어그램 및 전위 장벽 시각화
with col2:
    st.markdown("### ⚡ 에너지 밴드 및 캐리어 이동")
    
    # 물리적 밴드 높이 계산 (전압에 따른 장벽 감소 효과)
    x = np.linspace(0, 10, 100)
    barrier_be = 2.0 - v_be * 1.5
    barrier_bc = 2.0 - v_bc * 1.5
    
    fig = go.Figure()
    # 밴드 벤딩 묘사
    y_band = [barrier_be if val < 5 else barrier_bc for val in x]
    
    fig.add_trace(go.Scatter(x=x, y=y_band, mode='lines', line=dict(width=3, color='orange')))
    fig.add_annotation(x=2.5, y=barrier_be+0.5, text="E-B Barrier", showarrow=False)
    fig.add_annotation(x=7.5, y=barrier_bc+0.5, text="B-C Barrier", showarrow=False)
    
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=20, b=0), 
                      xaxis=dict(visible=False), yaxis=dict(title="Energy (eV)"))
    st.plotly_chart(fig, use_container_width=True)

# 4. 특징 설명
st.markdown("""
---
### 💡 물리적 해설
- **순방향 바이어스 (Forward Bias):** 전위 장벽이 낮아져 캐리어(전자/정공)가 접합부를 쉽게 넘습니다.
- **역방향 바이어스 (Reverse Bias):** 전위 장벽이 높아져 전류의 흐름을 차단합니다.
- **Active 모드:** E-B는 열리고 B-C는 닫혀있어, 베이스에서 주입된 전자들이 컬렉터로 빠르게 확산됩니다.
""")