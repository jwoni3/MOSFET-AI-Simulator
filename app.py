import streamlit as st
import numpy as np
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(page_title="BJT 물리 시뮬레이터", layout="wide")

# UI 스타일
st.markdown("""
    <style>
        .block-container { padding-top: 1.5rem; max-width: 98%; }
        .header-text { font-size: 20px; font-weight: 700; color: #1e293b; margin-bottom: 10px; }
        [data-testid="stVerticalBlockBorderWrapper"] { 
            background-color: #f1f5f9; border-radius: 12px; padding: 15px; 
            resize: both; overflow: auto; min-height: 300px; 
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center;'>🔬 BJT 물리 시뮬레이터</h2>", unsafe_allow_html=True)

# 1. 사이드바 제어 패널
with st.sidebar:
    st.markdown("### **🎛️ BJT 제어 및 바이어스**")
    bjt_type = st.selectbox("BJT 타입 선택", ["NPN", "PNP"])
    v_be = st.slider("V_BE (Base-Emitter) [V]", -1.0, 1.0, 0.0, 0.1)
    v_bc = st.slider("V_BC (Base-Collector) [V]", -1.0, 1.0, 0.0, 0.1)
    st.markdown("---")
    user_query = st.text_area("🤖 AI에게 질문하기", "현재 동작 모드의 물리적 의미를 설명해줘.", height=100)
    ask_ai_btn = st.button("질문 전송 (AI 해설)", type="primary", use_container_width=True)

# 2. 로직: 동작 모드 판별
# PNP는 전압 극성이 반대이므로 절대값 로직 적용
v_be_eff = v_be if bjt_type == "NPN" else -v_be
v_bc_eff = v_bc if bjt_type == "NPN" else -v_bc

if v_be_eff < 0.3 and v_bc_eff < 0.3: 
    mode, box_color = "차단 (Cutoff)", "#fff1f0"
elif v_be_eff >= 0.3 and v_bc_eff < 0.3: 
    mode, box_color = "순방향 활성 (Forward Active)", "#f6ffed"
elif v_be_eff >= 0.3 and v_bc_eff >= 0.3: 
    mode, box_color = "포화 (Saturation)", "#e6f7ff"
else: 
    mode, box_color = "역방향 활성 (Reverse Active)", "#fffbe6"

# 3. 레이아웃
col1, col2, col3 = st.columns([1, 1.5, 1.2])

with col1:
    st.markdown("<div class='header-text'>📊 동작 상태</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='background-color:{box_color}; padding:15px; border-radius:8px; border:1px solid #ddd; text-align:center;'>
        <span style='font-size:18px; font-weight:700;'>{bjt_type} {mode}</span>
    </div>
    """, unsafe_allow_html=True)
    st.write(f"- B-E 접합: {'순방향' if v_be_eff >= 0.3 else '역방향'}")
    st.write(f"- B-C 접합: {'순방향' if v_bc_eff >= 0.3 else '역방향'}")

with col2:
    st.markdown("<div class='header-text'>⚡ 에너지 밴드 다이어그램 시뮬레이션</div>", unsafe_allow_html=True)
    
    x = np.linspace(0, 10, 200)
    # PNP는 밴드 구조가 반대 (Ec, Ev가 뒤집힘)
    sign = 1 if bjt_type == "NPN" else -1
    h_eb, h_bc = (2.0 - v_be_eff * 1.2) * sign, (2.0 - v_bc_eff * 1.2) * sign
    
    ec = sign * (1.5 + 0.5 * (np.tanh(x - 2.5) + np.tanh(x - 7.5)))
    ev = ec - (2.0 * sign)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=ec, line=dict(width=3, color='#3b82f6'), name="Ec"))
    fig.add_trace(go.Scatter(x=x, y=ev, line=dict(width=3, color='#ef4444'), name="Ev"))
    fig.add_trace(go.Scatter(x=x, y=np.zeros_like(x)+0.5*sign, line=dict(dash='dash', color='black'), name="Ef"))
    
    # 캐리어 배치 (NPN은 전자 중심, PNP는 정공 중심)
    fig.add_trace(go.Scatter(x=np.linspace(1, 9, 20), y=np.interp(np.linspace(1, 9, 20), x, ec)+0.2, 
                             mode='markers', marker=dict(size=8, color='black'), name="다수 캐리어"))

    fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10), 
                      xaxis=dict(visible=False), yaxis=dict(title="Energy (eV)"),
                      plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col3:
    with st.container(border=True):
        st.markdown("<div class='header-text' style='text-align: center; color: #3b82f6;'>🤖 AI 응답</div>", unsafe_allow_html=True)
        if ask_ai_btn:
            st.info("선택하신 BJT 타입과 동작 모드에 따른 물리 분석 결과가 출력됩니다.")
        else:
            st.info("바이어스를 설정하고 질문을 입력하세요.")