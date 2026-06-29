import streamlit as st
import numpy as np
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(page_title="BJT 물리 시뮬레이터", layout="wide")

# UI 스타일
st.markdown("""
    <style>
        .header-text { font-size: 20px; font-weight: 700; color: #1e293b; margin-bottom: 10px; }
        .mode-box { padding: 15px; border-radius: 8px; border: 1px solid #ddd; text-align: center; font-weight: 700; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center;'>🔬 BJT(NPN) 물리 시뮬레이터</h2>", unsafe_allow_html=True)

# 1. 사이드바 제어
with st.sidebar:
    st.markdown("### **🎛️ BJT 제어 패널**")
    v_be = st.slider("V_BE (Base-Emitter) [V]", -1.0, 1.0, 0.0, 0.1)
    v_bc = st.slider("V_BC (Base-Collector) [V]", -1.0, 1.0, 0.0, 0.1)
    
    st.markdown("---")
    user_query = st.text_area("🤖 AI에게 질문하기", "이 동작 모드에서 전자들이 어떻게 이동해?", height=100)
    ask_ai_btn = st.button("질문 전송 (AI 해설)", type="primary", use_container_width=True)

# 2. 로직: 동작 모드
if v_be < 0.5 and v_bc < 0.5: mode, color = "차단 (Cutoff)", "#fff1f0"
elif v_be >= 0.5 and v_bc < 0.5: mode, color = "순방향 활성 (Forward Active)", "#f6ffed"
elif v_be >= 0.5 and v_bc >= 0.5: mode, color = "포화 (Saturation)", "#e6f7ff"
else: mode, color = "역방향 활성 (Reverse Active)", "#fffbe6"

# 3. 메인 레이아웃
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.markdown("<div class='header-text'>📊 동작 상태</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='mode-box' style='background-color:{color};'>{mode}</div>", unsafe_allow_html=True)
    st.write(f"- B-E 접합: {'순방향' if v_be >= 0.5 else '역방향'}")
    st.write(f"- B-C 접합: {'순방향' if v_bc >= 0.5 else '역방향'}")

with col2:
    st.markdown("<div class='header-text'>⚡ 에너지 밴드 다이어그램 시뮬레이션</div>", unsafe_allow_html=True)
    
    # 그래프 데이터 생성 (전압에 따른 장벽 변화)
    x = np.linspace(0, 10, 200)
    ec = 1.5 - (v_be * 0.4 * np.tanh(x - 2.5)) - (v_bc * 0.4 * np.tanh(x - 7.5))
    ev = ec - 2.0
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=ec, line=dict(width=4, color='#3b82f6'), name="Ec"))
    fig.add_trace(go.Scatter(x=x, y=ev, line=dict(width=4, color='#ef4444'), name="Ev"))
    fig.add_trace(go.Scatter(x=x, y=np.zeros_like(x)+0.5, line=dict(dash='dash', color='black'), name="Ef"))
    
    # 전자/정공 표현
    fig.add_trace(go.Scatter(x=np.linspace(1, 9, 20), y=np.interp(np.linspace(1, 9, 20), x, ec)+0.2, 
                             mode='markers', marker=dict(size=8, color='black'), name="전자"))
    fig.add_trace(go.Scatter(x=np.linspace(1, 9, 20), y=np.interp(np.linspace(1, 9, 20), x, ev)-0.2, 
                             mode='markers', marker=dict(size=8, color='black', symbol='circle-open'), name="정공"))

    fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10), 
                      xaxis=dict(visible=False), yaxis=dict(title="Energy (eV)", range=[-2, 3]),
                      plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col3:
    st.markdown("<div class='header-text'>🤖 AI 응답</div>", unsafe_allow_html=True)
    if ask_ai_btn:
        st.write(f"질문하신 내용: *{user_query}*")
        st.info("여기에 AI가 분석한 물리적 해설이 출력됩니다.")
    else:
        st.info("질문을 입력하고 '질문 전송'을 눌러주세요.")