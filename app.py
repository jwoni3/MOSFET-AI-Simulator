import streamlit as st
import numpy as np
import plotly.graph_objects as go
import google.generativeai as genai

# 1. 페이지 설정: 원스크린 뷰를 위해 컴팩트 레이아웃 적용
st.set_page_config(page_title="MOSFET AI 시뮬레이터", layout="wide", initial_sidebar_state="expanded")

# 사이드바 스타일링 (터미널 느낌의 배경색 분리)
st.markdown("""
    <style>
        [data-testid="stSidebar"] { background-color: #f1f3f6; border-right: 1px solid #d1d5db; }
        .stSlider { padding-top: 0rem; padding-bottom: 1rem; }
        .main .block-container { padding-top: 2rem; padding-bottom: 1rem; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. 좌측 사이드바: 제어 및 입력 패널
# ---------------------------------------------------------
with st.sidebar:
    st.title("🎛️ MOSFET 소자 제어")
    
    # API 키 로드 (성공 메시지 제거)
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
    st.subheader("💬 AI 해설 요청")
    user_query = st.text_area("질문 내용을 입력하세요:", "현재 상태에 대해 물리적으로 설명해줘.", height=80)
    ask_ai_btn = st.button("🤖 AI 실시간 해설 받기", use_container_width=True)

# ---------------------------------------------------------
# 3. 물리 계산 로직 (연속성 및 정확도 확보)
# ---------------------------------------------------------
k_n = 1.0
abs_vgs, abs_vds, abs_vth = abs(v_gs), abs(v_ds), abs(v_th)
v_ov = abs_vgs - abs_vth

if abs_vgs < abs_vth:
    op_region, i_d = "차단 영역 (Cutoff)", 0.0
elif abs_vds < v_ov:
    op_region, i_d = "선형 영역 (Linear)", k_n * (v_ov * abs_vds - 0.5 * (abs_vds ** 2))
else:
    op_region, i_d = "포화 영역 (Saturation)", 0.5 * k_n * (v_ov ** 2) * (1 + 0.02 * (abs_vds - v_ov))

# ---------------------------------------------------------
# 4. 메인 화면 구성
# ---------------------------------------------------------
col_vis, col_ai = st.columns([1.6, 1.0], gap="medium")

with col_vis:
    # 4-1. 동작 영역 강조 (박스 높이 축소)
    status_colors = {"포화": ("#e6f7ff", "#0050b3"), "선형": ("#f6ffed", "#389e0d"), "차단": ("#fff1f0", "#cf1322")}
    bg, txt = next((v for k, v in status_colors.items() if k in op_region), ("#f9f9f9", "#333"))
    
    st.markdown(f"""<div style="background-color:{bg}; padding:8px; border-radius:10px; border:1px solid #ddd; text-align:center; margin-bottom:10px;">
        <h4 style="margin:0; color:{txt};">동작 영역 : <b>{op_region}</b></h4></div>""", unsafe_allow_html=True)
    
    m1, m2 = st.columns(2)
    m1.metric("인가 전압 (V_DS)", f"{abs_vds:.2f} V")
    m2.metric("드레인 전류 (I_D)", f"{i_d:.2f} mA")

    # 4-2. MOSFET 구조 시각화 (채널 형성 강조)
    fig_struct = go.Figure()

    # (1) Substrate & Oxide & Gate (먼저 그려서 배경으로 만듦)
    fig_struct.add_shape(type="rect", x0=0, y0=0, x1=10, y1=4, fillcolor="#eef2f7", line=dict(color="#64748b")) # Substrate
    fig_struct.add_shape(type="rect", x0=2.5, y0=4, x1=7.5, y1=4.15, fillcolor="#fbbf24") # Oxide
    fig_struct.add_shape(type="rect", x0=2.5, y0=4.15, x1=7.5, y1=5, fillcolor="#334155") # Gate
    
    # (2) Source & Drain
    sd_color = "#f87171" if mos_type == "NMOS" else "#60a5fa"
    fig_struct.add_shape(type="rect", x0=0.5, y0=2.5, x1=2.5, y1=4, fillcolor=sd_color, line=dict(width=0))
    fig_struct.add_shape(type="rect", x0=7.5, y0=2.5, x1=9.5, y1=4, fillcolor=sd_color, line=dict(width=0))
    
    # (3) 채널 형성 시각화 (중요: 가장 나중에 그려서 위에 띄움)
    if op_region != "차단 영역 (Cutoff)":
        ch_color = "rgba(255, 165, 0, 0.8)" # 가시성 높은 주황색 채널
        if op_region == "선형 영역 (Linear)":
            fig_struct.add_trace(go.Scatter(x=[2.5, 7.5, 7.5, 2.5], y=[3.85, 3.85, 4.0, 4.0], fill='toself', 
                                            fillcolor=ch_color, line=dict(width=0), mode='lines', name="Channel"))
        else: # Saturation (Pinch-off 모사)
            p_point = max(3.5, 7.5 - (abs_vds - v_ov) * 0.8)
            fig_struct.add_trace(go.Scatter(x=[2.5, p_point, 7.5, 2.5], y=[3.8, 4.0, 4.0, 4.0], fill='toself', 
                                            fillcolor=ch_color, line=dict(width=0), mode='lines', name="Channel"))
            fig_struct.add_annotation(x=p_point, y=3.7, text="Pinch-off Point", font=dict(color="red", size=10), showarrow=True, arrowhead=1)

    # (4) 글자 라벨 표시
    fig_struct.add_annotation(x=1.5, y=3.25, text="<b>Source</b>", showarrow=False, font=dict(size=12))
    fig_struct.add_annotation(x=8.5, y=3.25, text="<b>Drain</b>", showarrow=False, font=dict(size=12))
    fig_struct.add_annotation(x=5, y=4.6, text="<b>GATE</b>", showarrow=False, font=dict(color="white", size=13))
    fig_struct.add_annotation(x=5, y=1, text="P-Substrate" if mos_type=="NMOS" else "N-Substrate", showarrow=False, font=dict(size=12, color="#64748b"))
    if op_region != "차단 영역 (Cutoff)":
        fig_struct.add_annotation(x=4, y=3.6, text="<b>Channel</b>", showarrow=False, font=dict(color="#d97706", size=11))

    fig_struct.update_layout(height=200, margin=dict(l=0, r=0, t=5, b=5), xaxis=dict(visible=False, range=[0, 10]), yaxis=dict(visible=False, range=[0, 6]))
    st.plotly_chart(fig_struct, use_container_width=True)

    # 4-3. I-V 특성 곡선
    v_axis = np.linspace(0, 5, 200)
    v_bound = np.linspace(0, 4, 100)
    i_bound = 0.5 * k_n * (v_bound**2) # Saturation boundary 궤적

    fig_iv = go.Figure()
    fig_iv.add_trace(go.Scatter(x=v_bound, y=i_bound, mode='lines', line=dict(color='silver', dash='dash', width=1), name="Boundary"))
    
    i_axis = [0 if abs_vgs < abs_vth else (k_n*(v_ov*v - 0.5*v**2) if v < v_ov else 0.5*k_n*v_ov**2*(1+0.02*(v-v_ov))) for v in v_axis]
    fig_iv.add_trace(go.Scatter(x=v_axis, y=i_axis, mode='lines', line=dict(color='#2563eb', width=3), name="I-V Curve"))
    fig_iv.add_trace(go.Scatter(x=[abs_vds], y=[i_d], mode='markers', marker=dict(color='red', size=12, line=dict(width=2, color='white')), name="Point"))
    
    fig_iv.update_layout(height=250, margin=dict(l=0, r=0, t=10, b=0), xaxis_title="V_DS (V)", yaxis_title="I_D (mA)", showlegend=False, plot_bgcolor='white')
    fig_iv.update_xaxes(showgrid=True, gridcolor='#f0f0f0')
    fig_iv.update_yaxes(showgrid=True, gridcolor='#f0f0f0')
    st.plotly_chart(fig_iv, use_container_width=True)

# ---------------------------------------------------------
# 5. 우측 화면: AI 실시간 해설
# ---------------------------------------------------------
with col_ai:
    st.subheader("🤖 AI 교수님의 실시간 해설")
    if ask_ai_btn:
        if not api_key: st.error("사이드바에 API Key를 입력해주세요.")
        else:
            with st.spinner("물리 현상 분석 중..."):
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash') 
                    prompt = f"너는 반도체 교수님이야. 소자:{mos_type}, V_GS:{v_gs}V, V_DS:{v_ds}V, V_TH:{v_th}V, 영역:{op_region}. 질문:{user_query}"
                    response = model.generate_content(prompt)
                    st.success("해설이 생성되었습니다.")
                    st.markdown(response.text)
                except Exception as e: st.error(f"AI 에러: {e}")
    else:
        st.info("👈 왼쪽 제어 패널에서 전압을 조절하고 버튼을 눌러보세요.")