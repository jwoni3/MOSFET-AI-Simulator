import streamlit as st
import numpy as np
import plotly.graph_objects as go
import google.generativeai as genai

# 1. 페이지 설정
st.set_page_config(page_title="MOSFET AI 시뮬레이터", layout="wide", initial_sidebar_state="expanded")

# UI 최적화 CSS
st.markdown("""
    <style>
        [data-testid="stSidebar"] { background-color: #f1f5f9; border-right: 1px solid #e2e8f0; }
        .block-container { padding-top: 1.5rem; padding-bottom: 1rem; max-width: 98%; }
        .header-text { font-size: 20px; font-weight: 700; color: #1e293b; margin-bottom: 10px; margin-top: 5px; }
    </style>
""", unsafe_allow_html=True)

# 메인 타이틀
st.markdown("<h2 style='text-align: center; color: #1e293b; margin-bottom: 20px;'>🔌 MOSFET 물리 시뮬레이터</h2>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. 좌측 사이드바: 제어 및 입력 패널
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### **🎛️ 제어 및 입력 패널**")
    
    # API 키 로드 (금고에서 가져오거나 직접 입력)
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Gemini API Key", type="password")
    
    st.markdown("---")
    mos_type = st.selectbox("소자 타입 선택", ["NMOS", "PMOS"])
    
    # 전압 슬라이더 설정
    if mos_type == "NMOS":
        v_th = st.slider("문턱 전압 (V_TH) [V]", 0.5, 2.0, 1.0, 0.1)
        v_gs = st.slider("게이트 전압 (V_GS) [V]", 0.0, 5.0, 3.0, 0.1)
        v_ds = st.slider("드레인 전압 (V_DS) [V]", 0.0, 5.0, 1.6, 0.1)
    else:
        v_th = st.slider("문턱 전압 (V_TH) [V]", -2.0, -0.5, -1.0, 0.1)
        v_gs = st.slider("게이트 전압 (V_GS) [V]", -5.0, 0.0, -3.0, 0.1)
        v_ds = st.slider("드레인 전압 (V_DS) [V]", -5.0, 0.0, -1.6, 0.1)

    st.markdown("---")
    st.markdown("### **💬 AI에게 질문하기**")
    user_query = st.text_area("질문 입력:", "현재 전압 상태를 물리적으로 설명해줘.", height=70)
    ask_ai_btn = st.button("🤖 AI 실시간 해설 받기", use_container_width=True)

# ---------------------------------------------------------
# 3. 물리 계산 로직
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
# 4. 메인 대시보드 (3단 구성)
# ---------------------------------------------------------
col1, col2, col3 = st.columns([1, 1.2, 1.2], gap="medium")

# --- [Column 1] 소자 상태 및 구조 ---
with col1:
    st.markdown("<div class='header-text'>📊 실시간 소자 상태</div>", unsafe_allow_html=True)
    
    # 동작 영역 박스 디자인
    box_color = "#e6f7ff" if "포화" in op_region else "#f6ffed" if "선형" in op_region else "#fff1f0"
    st.markdown(f"""<div style='background-color:{box_color}; padding:10px; border-radius:8px; border:1px solid #ddd; text-align:center;'>
        <span style='font-size:18px; font-weight:700;'>{op_region}</span></div>""", unsafe_allow_html=True)
    
    m1, m2 = st.columns(2)
    m1.metric("인가 전압 (|V_DS|)", f"{abs_vds:.2f} V")
    m2.metric("드레인 전류 (|I_D|)", f"{i_d:.2f} mA")
    
    st.markdown("<div class='header-text'>🧱 MOSFET 구조 시각화</div>", unsafe_allow_html=True)
    
    # MOSFET 구조 디자인 (PMOS 색상 대응)
    fig_struct = go.Figure()
    
    # NMOS/PMOS 색상 변수 설정
    if mos_type == "NMOS":
        sub_color, sd_color, ch_color = "#e0f2fe", "#4ade80", "#ef4444" # 연파랑 기판, 초록 S/D, 빨간 채널
        sub_text = "p-Substrate"
        sd_label = "n+"
    else:
        sub_color, sd_color, ch_color = "#ffedd5", "#a78bfa", "#3b82f6" # 연주황 기판, 보라 S/D, 파란 채널
        sub_text = "n-Substrate"
        sd_label = "p+"

    # (1) 기판
    fig_struct.add_shape(type="rect", x0=0, y0=0, x1=10, y1=4, fillcolor=sub_color, line=dict(width=0))
    # (2) 산화막 & 게이트
    fig_struct.add_shape(type="rect", x0=3, y0=4, x1=7, y1=4.15, fillcolor="#cbd5e1", line=dict(width=0))
    fig_struct.add_shape(type="rect", x0=3, y0=4.15, x1=7, y1=5.0, fillcolor="#1e293b", line=dict(width=0))
    # (3) 소스 & 드레인
    fig_struct.add_shape(type="rect", x0=1, y0=2.5, x1=3, y1=4, fillcolor=sd_color, line=dict(width=0))
    fig_struct.add_shape(type="rect", x0=7, y0=2.5, x1=9, y1=4, fillcolor=sd_color, line=dict(width=0))
    
    # (4) 채널 & 핀치오프
    if op_region != "차단 영역 (Cutoff)":
        if op_region == "선형 영역 (Linear)":
            t_d = 4.0 - 0.2 * (1 - abs_vds / max(v_ov, 0.001))
            fig_struct.add_shape(type="path", path=f"M 3 4 L 7 4 L 7 {t_d} L 3 3.85 Z", fillcolor=ch_color, line=dict(width=0), opacity=0.8)
        else: # Saturation
            p_p = max(4.0, 7 - (abs_vds - v_ov) * 0.8)
            fig_struct.add_shape(type="path", path=f"M 3 4 L {p_p} 4 L 3 3.85 Z", fillcolor=ch_color, line=dict(width=0), opacity=0.8)
            # Pinch-off 점선
            fig_struct.add_shape(type="line", x0=p_p, y0=0, x1=p_p, y1=5.5, line=dict(color="#ef4444", width=2, dash="dash"))
            fig_struct.add_annotation(x=p_p, y=5.7, text="Pinch-off", font=dict(color="#ef4444", size=10), showarrow=False)

    # 텍스트 라벨링
    fig_struct.add_annotation(x=2, y=3.25, text=f"<b>S</b><br><small>{sd_label}</small>", font=dict(color="white", size=14), showarrow=False)
    fig_struct.add_annotation(x=8, y=3.25, text=f"<b>D</b><br><small>{sd_label}</small>", font=dict(color="white", size=14), showarrow=False)
    fig_struct.add_annotation(x=5, y=4.55, text="Gate (G)", font=dict(color="white", size=12), showarrow=False)
    fig_struct.add_annotation(x=5, y=0.5, text=sub_text, font=dict(color="#475569", size=12), showarrow=False)

    fig_struct.update_layout(height=230, margin=dict(l=0, r=0, t=10, b=0), xaxis=dict(visible=False, range=[0, 10]), yaxis=dict(visible=False, range=[0, 6]), plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_struct, use_container_width=True)

# --- [Column 2] I-V 특성 곡선 ---
with col2:
    st.markdown("<div class='header-text'>📈 전류-전압 특성 곡선</div>", unsafe_allow_html=True)
    
    v_ax = np.linspace(0, 5, 200)
    v_b = np.linspace(0, 4, 100)
    i_b = 0.5 * k_n * (v_b**2)

    fig_iv = go.Figure()
    fig_iv.add_trace(go.Scatter(x=v_b, y=i_b, mode='lines', line=dict(color='#cbd5e1', dash='dash', width=1.5), name="Boundary"))
    
    i_ax = [0 if abs_vgs < abs_vth else (k_n*(v_ov*v - 0.5*v**2) if v < v_ov else 0.5*k_n*v_ov**2*(1+0.02*(v-v_ov))) for v in v_ax]
    fig_iv.add_trace(go.Scatter(x=v_ax, y=i_ax, mode='lines', line=dict(color='#3b82f6', width=3), name="I-V Curve"))
    fig_iv.add_trace(go.Scatter(x=[abs_vds], y=[i_d], mode='markers', marker=dict(color='#ef4444', size=12, line=dict(color='white', width=1.5)), name="Point"))
    
    fig_iv.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0), xaxis_title="V_DS (V)", yaxis_title="I_D (mA)", showlegend=False, plot_bgcolor='white')
    fig_iv.update_xaxes(showgrid=True, gridcolor='#f1f5f9')
    fig_iv.update_yaxes(showgrid=True, gridcolor='#f1f5f9')
    st.plotly_chart(fig_iv, use_container_width=True)

# --- [Column 3] AI 실시간 해설 ---
with col3:
    st.markdown("<div class='header-text'>🤖 AI 해설</div>", unsafe_allow_html=True)
    
    if ask_ai_btn:
        if not api_key:
            st.error("⚠️ 사이드바에 API Key를 입력해주세요.")
        else:
            with st.spinner("AI 교수님이 분석 중입니다..."):
                try:
                    # AI 모델 호출 안정화 (404 에러 방지)
                    genai.configure(api_key=api_key)
                    # 모델명을 가장 안정적인 기본형으로 명시
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    prompt = f"""
                    너는 반도체 공학 전문가 교수님이야. 아래 정보를 바탕으로 현재 MOSFET의 물리적 상태와 작동 원리를 친절하게 설명해줘.
                    - 소자 타입: {mos_type}
                    - 입력 전압: V_GS={v_gs}V, V_DS={v_ds}V, V_TH={v_th}V
                    - 현재 상태: {op_region}
                    - 계산된 전류: {i_d:.2f}mA
                    - 사용자 질문: {user_query}
                    
                    * 마크다운 불릿 포인트를 사용하여 가독성 있게 설명해줘.
                    """
                    
                    response = model.generate_content(prompt)
                    st.success("해설이 도착했습니다!")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"⚠️ AI 응답 생성 중 오류가 발생했습니다.\n\n상세 정보: {e}")
    else:
        st.info("👈 왼쪽 패널에서 설정을 마치고 [🤖 AI 실시간 해설 받기]를 눌러보세요.")