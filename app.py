import streamlit as st
import numpy as np
import plotly.graph_objects as go
import google.generativeai as genai

# 1. 페이지 설정
st.set_page_config(page_title="BJT 물리 시뮬레이터", layout="wide")

# UI 스타일 CSS
st.markdown("""
    <style>
        .block-container { padding-top: 1.5rem; max-width: 98%; }
        .header-text { font-size: 20px; font-weight: 700; color: #1e293b; margin-bottom: 10px; }
        [data-testid="stVerticalBlockBorderWrapper"] { background-color: #f1f5f9; border-radius: 12px; padding: 15px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center;'>🔬 BJT(NPN) 물리 시뮬레이터</h2>", unsafe_allow_html=True)

# 2. 사이드바 제어 패널 (API Key 삭제)
with st.sidebar:
    st.markdown("### **🎛️ BJT 제어 및 바이어스**")
    v_be = st.slider("V_BE (Base-Emitter) [V]", -1.0, 1.0, 0.0, 0.1)
    v_bc = st.slider("V_BC (Base-Collector) [V]", -1.0, 1.0, 0.0, 0.1)
    
    st.markdown("---")
    user_query = st.text_area("AI 질문", "현재 동작 모드의 물리적 의미를 설명해줘.", height=60)
    ask_ai_btn = st.button("AI 실시간 해설 받기", type="primary", use_container_width=True)

# 3. 로직: 동작 모드 판별
if v_be < 0.5 and v_bc < 0.5: 
    mode, box_color = "차단 (Cutoff)", "#fff1f0"
elif v_be >= 0.5 and v_bc < 0.5: 
    mode, box_color = "순방향 활성 (Forward Active)", "#f6ffed"
elif v_be >= 0.5 and v_bc >= 0.5: 
    mode, box_color = "포화 (Saturation)", "#e6f7ff"
else: 
    mode, box_color = "역방향 활성 (Reverse Active)", "#fffbe6"

# 4. 레이아웃
col1, col2, col3 = st.columns([1, 1.5, 1.2])

with col1:
    st.markdown("<div class='header-text'>📊 동작 상태</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='background-color:{box_color}; padding:15px; border-radius:8px; border:1px solid #ddd; text-align:center;'>
        <div style='font-size:12px; color:#475569;'>현재 동작 모드</div>
        <span style='font-size:18px; font-weight:700;'>{mode}</span>
    </div>
    """, unsafe_allow_html=True)
    st.write(f"- B-E 접합: {'순방향' if v_be >= 0.5 else '역방향'}")
    st.write(f"- B-C 접합: {'순방향' if v_bc >= 0.5 else '역방향'}")

with col2:
    st.markdown("<div class='header-text'>⚡ 에너지 밴드 다이어그램</div>", unsafe_allow_html=True)
    x = np.linspace(0, 10, 100)
    # 에너지 밴드 벤딩 묘사
    y_band = [2.0 - v_be*0.8 if val < 5 else 2.0 - v_bc*0.8 for val in x]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y_band, line=dict(width=4, color='#3b82f6')))
    fig.update_layout(height=300, margin=dict(l=0,r=0,t=20,b=0), xaxis=dict(visible=False), yaxis=dict(title="Energy (eV)"))
    st.plotly_chart(fig, use_container_width=True)

with col3:
    with st.container(border=True):
        st.markdown("<h4 style='text-align: center; color: #3b82f6;'>🤖 AI 실시간 해설</h4>", unsafe_allow_html=True)
        if ask_ai_btn:
            st.write("분석 중입니다...") 
            # 여기에 Gemini API 호출 로직을 넣으시면 됩니다.
        else:
            st.info("왼쪽 패널에서 바이어스를 설정하고 해설을 받아보세요.")