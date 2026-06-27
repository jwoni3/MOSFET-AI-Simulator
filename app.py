import streamlit as st
import numpy as np
import plotly.graph_objects as go
import google.generativeai as genai

# 1. 페이지 설정: 사이드바 확장 및 전체 화면 레이아웃
st.set_page_config(page_title="MOSFET 물리 시뮬레이터", layout="wide", initial_sidebar_state="expanded")

# 2. 사이드바(제어 패널): 배경색 및 컴팩트한 디자인
with st.sidebar:
    st.title("🎛️ MOSFET 소자 및 전압 조절")
    
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Gemini API Key", type="password")
    
    st.markdown("---")
    mos_type = st.radio("소자 타입 선택", ["NMOS", "PMOS"], horizontal=True)
    
    if mos_type == "NMOS":
        v_th = st.slider("문턱 전압 (V_TH) [V]", 0.5, 2.0, 1.0, 0.1)
        v_gs = st.slider("게이트 전압 (V_GS) [V]", 0.0, 5.0, 2.5, 0.1)
        v_ds = st.slider("드레인 전압 (V_DS) [V]", 0.0, 5.0, 3.0, 0.1)
    else:
        v_th = st.slider("문턱 전압 (V_TH) [V]", -2.0, -0.5, -1.0, 0.1)
        v_gs = st.slider("게이트 전압 (V_GS) [V]", -5.0, 0.0, -2.5, 0.1)
        v_ds = st.slider("드레인 전압 (V_DS) [V]", -5.0, 0.0, -3.0, 0.1)

    st.markdown("---")
    st.subheader("💬 AI에게 질문하기")
    user_query = st.text_area("궁금한 점을 입력하세요:", "현재 전압 상태와 물리적 현상에 대해 설명해줘.", height=100)
    ask_ai_btn = st.button("🤖 AI 실시간 해설 받기", use_container_width=True)

# 3. 물리 계산 로직 (연속성 확보)
k_n = 1.0
abs_vgs, abs_vds, abs_vth = abs(v_gs), abs(v_ds), abs(v_th)
v_ov = abs_vgs - abs_vth

if abs_vgs < abs_vth:
    op_region, i_d = "차단 영역 (Cutoff)", 0.0
elif abs_vds < v_ov:
    op_region, i_d = "선형 영역 (Linear)", k_n * (v_ov * abs_vds - 0.5 * (abs_vds ** 2))
else:
    op_region, i_d = "포화 영역 (Saturation)", 0.5 * k_n * (v_ov ** 2) * (1 + 0.02 * (abs_vds - v_ov))

# 4. 메인 대시보드 레이아웃
col_vis, col_ai = st.columns([1.5, 1.1], gap="medium")

with col_vis:
    # 4-1. 동작 영역 강조 (컴팩트 박스)
    bg_color = "#e6f7ff" if "포화" in op_region else "#f6ffed" if "선형" in op_region else "#fff1f0"
    st.markdown(f"""<div style="background-color: {bg_color}; padding: 10px; border-radius: 8px; border: 1px solid #ddd; text-align: center; margin-bottom: 10px;">
        <h4 style="margin: 0; color: #333;">동작 영역 : <b>{op_region}</b></h4></div>""", unsafe_allow_html=True)
    
    m1, m2 = st.columns(2)
    m1.metric("드레인 전압 (V_DS)", f"{abs_vds:.2f} V")
    m2.metric("드레인 전류 (I_D)", f"{i_d:.2f} mA")

    # 4-2. I-V 특성 곡선 (경계선 추가)
    v_axis = np.linspace(0, 5, 200)
    # 경계선 (Saturation Boundary locus: 0.5 * k_n * V_DS^2)
    v_boundary = np.linspace(0, 4, 100)
    i_boundary = 0.5 * k_n * (v_boundary**2)

    fig_iv = go.Figure()
    # 경계 점선 추가
    fig_iv.add_trace(go.Scatter(x=v_boundary, y=i_boundary, mode='lines', name='영역 경계선', line=dict(color='gray', dash='dash', width=1)))
    # 현재 V_GS에 대한 곡선
    i_axis = [0 if abs_vgs < abs_vth else (k_n*(v_ov*v - 0.5*v**2) if v < v_ov else 0.5*k_n*v_ov**2*(1+0.02*(v-v_ov))) for v in v_axis]
    fig_iv.add_trace(go.Scatter(x=v_axis, y=i_axis, mode='lines', name='I-V 곡선', line=dict(color='blue', width=3)))
    fig_iv.add_trace(go.Scatter(x=[abs_vds], y=[i_d], mode='markers', name='동작점', marker=dict(color='red', size=12)))
    
    fig_iv.update_layout(height=230, margin=dict(l=0, r=0, t=10, b=0), xaxis_title="V_DS (V)", yaxis_title="I_D (mA)", showlegend=False)
    st.plotly_chart(fig_iv, use_container_width=True)

    # 4-3. MOSFET 구조 시각화 (높이 축소)
    fig_struct = go.Figure()
    fig_struct.add_shape(type="rect", x0=0, y0=0, x1=10, y1=4, fillcolor="#f0f0f0", line=dict(color="black")) # Substrate
    fig_struct.add_shape(type="rect", x0=0.5, y0=2.5, x1=2.5, y1=4, fillcolor="#ff9999", line=dict(color="black")) # Source
    fig_struct.add_shape(type="rect", x0=7.5, y0=2.5, x1=9.5, y1=4, fillcolor="#ff9999", line=dict(color="black")) # Drain
    fig_struct.add_shape(type="rect", x0=2.5, y0=4, x1=7.5, y1=4.2, fillcolor="gold") # Oxide
    fig_struct.add_shape(type="rect", x0=2.5, y0=4.2, x1=7.5, y1=5, fillcolor="#444") # Gate
    
    if op_region != "차단 영역 (Cutoff)":
        c_color = "rgba(255, 0, 0, 0.6)"
        if op_region == "선형 영역 (Linear)":
            fig_struct.add_trace(go.Scatter(x=[2.5, 7.5, 7.5, 2.5], y=[3.8, 3.8, 4.0, 4.0], fill='toself', fillcolor=c_color, line=dict(width=0), mode='none', showlegend=False))
        else:
            p_point = max(3.0, 7.5 - (abs_vds - v_ov))
            fig_struct.add_trace(go.Scatter(x=[2.5, p_point, 7.5, 2.5], y=[3.7, 4.0, 4.0, 4.0], fill='toself', fillcolor=c_color, line=dict(width=0), mode='none', showlegend=False))
            
    fig_struct.update_layout(height=180, margin=dict(l=0, r=0, t=0, b=0), xaxis=dict(visible=False), yaxis=dict(visible=False, range=[0, 6]))
    st.plotly_chart(fig_struct, use_container_width=True)

with col_ai:
    st.subheader("🤖 AI 실시간 해설")
    if ask_ai_btn:
        if not api_key: st.error("API Key를 입력해주세요.")
        else:
            with st.spinner("AI 분석 중..."):
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash') # 안정적인 모델명으로 고정
                    prompt = f"소자:{mos_type}, V_GS:{v_gs}V, V_DS:{v_ds}V, V_TH:{v_th}V, 영역:{op_region}. 질문:{user_query}"
                    response = model.generate_content(prompt)
                    st.success("해설 완료!")
                    st.markdown(response.text)
                except Exception as e: st.error(f"오류: {e}")
    else: st.info("사이드바에서 질문 후 버튼을 클릭하세요.")