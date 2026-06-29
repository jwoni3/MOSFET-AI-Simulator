import streamlit as st
import plotly.graph_objects as go
import numpy as np

# 페이지 설정
st.set_page_config(layout="wide", page_title="BJT 물리 & 특성 시뮬레이터")

# UI 스타일 (MOSFET 시뮬레이터와 동일한 느낌 유지)
st.markdown("""
    <style>
        .header-text { font-size: 20px; font-weight: 700; color: #1e293b; margin-bottom: 10px; }
        .mode-box { padding: 15px; border-radius: 8px; border: 1px solid #ddd; text-align: center; font-weight: 700; }
        [data-testid="stVerticalBlockBorderWrapper"] { background-color: #f1f5f9; border-radius: 12px; padding: 15px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center;'>📟 AI BJT 물리 및 특성 시뮬레이터</h2>", unsafe_allow_html=True)

# 1. 사이드바 제어 패널
with st.sidebar:
    st.markdown("### **🎛️ BJT 제어 및 바이어스**")
    bjt_type = st.selectbox("소자 타입", ["NPN", "PNP"])
    v_be = st.slider("V_BE [V]", -1.0, 1.5, 0.75, 0.05)
    v_bc = st.slider("V_BC [V]", -5.0, 5.0, -2.0, 0.1)
    
    st.markdown("---")
    user_query = st.text_area("🤖 AI에게 질문하기", "현재 Q점과 밴드 구조의 물리적 의미는?", height=100)
    ask_ai_btn = st.button("질문 전송 (AI 해설)", type="primary", use_container_width=True)

# 2. 로직: 동작 모드 판별 (수정된 0.3V 기준)
v_be_eff = v_be if bjt_type == "NPN" else -v_be
v_bc_eff = v_bc if bjt_type == "NPN" else -v_bc

if v_be_eff < 0.3 and v_bc_eff < 0.3: mode, color = "차단 (Cutoff)", "#fff1f0"
elif v_be_eff >= 0.3 and v_bc_eff < 0.3: mode, color = "순방향 활성 (Forward Active)", "#f6ffed"
elif v_be_eff >= 0.3 and v_bc_eff >= 0.3: mode, color = "포화 (Saturation)", "#e6f7ff"
else: mode, color = "역방향 활성 (Reverse Active)", "#fffbe6"

# 3. 레이아웃
col1, col2, col3 = st.columns([1, 1.5, 1.2])

with col1:
    st.markdown("<div class='header-text'>📊 동작 상태</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='mode-box' style='background-color:{color};'>{mode}</div>", unsafe_allow_html=True)
    st.write(f"- 타입: {bjt_type}")
    st.write(f"- B-E 접합: {'순방향' if v_be_eff >= 0.3 else '역방향'}")
    st.write(f"- B-C 접합: {'순방향' if v_bc_eff >= 0.3 else '역방향'}")

with col2:
    st.markdown("<div class='header-text'>⚡ 에너지 밴드 & I-V 특성</div>", unsafe_allow_html=True)
    # 에너지 밴드 다이어그램 (기존 친구분 코드 로직 이식)
    fig = go.Figure()
    # (여기에 친구분 코드의 밴드 및 특성곡선 시각화 로직을 이식합니다)
    st.info("밴드 다이어그램 및 부하선 그래프가 여기에 배치됩니다.")
    
with col3:
    with st.container(border=True):
        st.markdown("<div class='header-text' style='text-align: center; color: #3b82f6;'>🤖 AI 응답</div>", unsafe_allow_html=True)
        if ask_ai_btn:
            st.write(f"질문: *{user_query}*")
            st.info("AI가 Q점과 물리 구조를 분석합니다.")
        else:
            st.info("좌측 패널에서 바이어스를 설정하고 AI에게 질문하세요.")