import streamlit as st
import numpy as np
import plotly.graph_objects as go
import google.generativeai as genai

# 페이지 설정
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

# 1. 사이드바 제어 패널
with st.sidebar:
    st.markdown("### 🎛️ BJT 바이어스 입력")
    api_key = st.text_input("Gemini API Key", type="password")
    v_be = st.slider("V_BE (Base-Emitter) [V]", -1.0, 1.0, 0.0, 0.1)
    v_bc = st.slider("V_BC (Base-Collector) [V]", -1.0, 1.0, 0.0, 0.1)
    user_query = st.text_area("AI 질문", "현재 동작 상태를 물리적으로 설명해줘.", height=60)
    ask_ai_btn = st.button("AI 실시간 해설 받기", type="primary", use_container_width=True)

# 2. 로직: 동작 모드 판별
if v_be < 0.5 and v_bc < 0.5: mode = "차단 (Cutoff)"
elif v_be >= 0.5 and v_bc < 0.5: mode = "순방향 활성 (Forward Active)"
elif v_be >= 0.5 and v_bc >= 0.5: mode = "포화 (Saturation)"
else: mode = "역방향 활성 (Reverse Active)"

# 3. 레이아웃
col1, col2, col3 = st.columns([1, 1.5, 1.2])

with col1:
    st.markdown("<div class='header-text'>📊 동작 상태</div>", unsafe_allow_html=True)
    st.metric("동작 모드", mode)
    st.write(f"- B-E 접합: {'순방향' if v_be >= 0.5 else '역방향'}")
    st.write(f"- B-C 접합: {'순방향' if v_bc >= 0.5 else '역방향'}")

with col2:
    st.markdown("<div class='header-text'>⚡ 에너지 밴드 다이어그램</div>", unsafe_allow_html=True)
    x = np.linspace(0, 10, 100)
    # 전압에 따른 밴드 벤딩 묘사
    y_band = [2.0 - v_be*0.8 if val < 5 else 2.0 - v_bc*0.8 for val in x]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y_band, line=dict(width=4, color='#3b82f6')))
    fig.update_layout(height=300, margin=dict(l=0,r=0,t=20,b=0), xaxis=dict(visible=False), yaxis=dict(title="Energy (eV)"))
    st.plotly_chart(fig, use_container_width=True)

with col3:
    with st.container(border=True):
        st.markdown("<div class='header-text' style='text-align: center;'>🤖 AI 실시간 해설</div>", unsafe_allow_html=True)
        if ask_ai_btn:
            if not api_key: st.error("API Key를 입력하세요.")
            else:
                # 여기에 기존 MOSFET 코드의 AI 호출 로직을 BJT 버전으로 수정해서 넣으면 됩니다.
                st.write(f"현재 {mode} 상태에 대한 물성 분석 결과가 여기에 출력됩니다.")

# 
#