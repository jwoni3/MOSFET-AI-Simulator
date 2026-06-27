import streamlit as st
import numpy as np
import plotly.graph_objects as go
import google.generativeai as genai

# 1. 페이지 설정
st.set_page_config(page_title="MOSFET AI 시뮬레이터", layout="wide", initial_sidebar_state="expanded")

# UI 최적화 CSS
st.markdown("""
    <style>
        [data-testid="stSidebar"] { background-color: #f8fafc; border-right: 1px solid #e2e8f0; }
        .block-container { padding-top: 1.5rem; padding-bottom: 1rem; max-width: 98%; }
        .header-text { font-size: 22px; font-weight: 700; color: #1e293b; margin-bottom: 10px; margin-top: 5px; }
    </style>
""", unsafe_allow_html=True)

# 메인 타이틀
st.markdown("<h2 style='text-align: center; color: #1e293b; margin-bottom: 20px;'>🔌 MOSFET 물리 시뮬레이터</h2>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. 좌측 사이드바: 제어 및 입력 패널
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### **🎛️ 제어 및 입력 패널**")
    
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Gemini API Key", type="password")
    
    st.markdown("---")
    mos_type = st.selectbox("소자 타입 선택", ["NMOS", "PMOS"])
    
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
    
    box_color = "#e6f7ff" if "포화" in op_region else "#f6ffed" if "선형" in op_region else "#fff1f0"
    st.markdown(f"""<div style='background-color:{box_color}; padding:10px; border-radius:8px; border:1px solid #ddd; text-align:center;'>
        <span style='font-size:18px; font-weight:700;'>{op_region}</span></div>""", unsafe_allow_html=True)
    
    m1, m2 = st.columns(2)
    m1.metric("드레인 전압", f"{abs_vds:.2f} V")
    m2.metric("드레인 전류", f"{i_d:.2f} mA")
    
    st.markdown("<div class='header-text'>🧱 MOSFET 구조 시각화</div>", unsafe_allow_html=True)
    
    fig_struct = go.Figure()
    
    # 레퍼런스 이미지 스타일 적용 (기판: 연파랑, 전극: 초록색, 산화막: 옅은 회색)
    fig_struct.add_shape(type="rect", x0=0, y0=0, x1=10, y1=4, fillcolor="#e0f2fe", line=dict(width=0)) # 기판
    fig_struct.add_shape(type="rect", x0=3, y0=4, x1=7, y1=4.2, fillcolor="#e2e8f0", line=dict(width=0)) # SiO2
    fig_struct.add_shape(type="rect", x0=3, y0=4.2, x1=7, y1=5.2, fillcolor="#334155", line=dict(width=0)) # Gate
    
    sd_c = "#4ade80" # 초록색 S/D
    fig_struct.add_shape(type="rect", x0=1, y0=2.5, x1=3, y1=4, fillcolor=sd_c, line=dict(width=0))
    fig_struct.add_shape(type="rect", x0=7, y0=2.5, x1=9, y1=4, fillcolor=sd_c, line=dict(width=0))
    
    # 채널 (레퍼런스와 동일한 붉은색 쐐기 형태)
    if op_region != "차단 영역 (Cutoff)":
        ch_c = "#fc8181" 
        if op_region == "선형 영역 (Linear)":
            t_d = 4.0 - 0.2 * (1 - abs_vds / max(v_ov, 0.001))
            fig_struct.add_shape(type="path", path=f"M 3 4 L 7 4 L 7 {t_d} L 3 3.8 Z", fillcolor=ch_c, line=dict(width=0))
        else: # Saturation
            p_p = max(4.0, 7 - (abs_vds - v_ov) * 0.8)
            fig_struct.add_shape(type="path", path=f"M 3 4 L {p_p} 4 L 3 3.8 Z", fillcolor=ch_c, line=dict(width=0))
            # 붉은색 점선 Pinch-off 표시
            fig_struct.add_shape(type="line", x0=p_p, y0=0, x1=p_p, y1=5.5, line=dict(color="#b91c1c", width=2, dash="dash"))
            fig_struct.add_annotation(x=p_p, y=3.2, text="<b>Pinch-off<br>Point</b>", font=dict(color="#b91c1c", size=11), showarrow=False, align="center")
            
    # Depletion Region 점선 모사
    fig_struct.add_shape(type="line", x0=1, y0=2.2, x1=9, y1=2.2, line=dict(color="#94a3b8", width=1, dash="dot"))
    fig_struct.add_annotation(x=5, y=2.4, text="Depletion Region", font=dict(color="#94a3b8", size=10, style="italic"), showarrow=False)

    # 텍스트 디자인 강화
    sd_t = "n+" if mos_type=="NMOS" else "p+"
    fig_struct.add_annotation(x=2, y=3.5, text="<b>S</b>", font=dict(color="white", size=20), showarrow=False)
    fig_struct.add_annotation(x=2, y=3.0, text=f"<i>{sd_t}</i>", font=dict(color="white", size=14), showarrow=False)
    fig_struct.add_annotation(x=8, y=3.5, text="<b>D</b>", font=dict(color="white", size=20), showarrow=False)
    fig_struct.add_annotation(x=8, y=3.0, text=f"<i>{sd_t}</i>", font=dict(color="white", size=14), showarrow=False)
    fig_struct.add_annotation(x=5, y=4.7, text="<b>Gate (G)</b>", font=dict(color="white", size=14), showarrow=False)
    fig_struct.add_annotation(x=7.5, y=4.4, text="<i>SiO₂</i>", font=dict(color="purple", size=12), showarrow=False)
    fig_struct.add_annotation(x=5, y=0.5, text="<b>p-Substrate</b>" if mos_type=="NMOS" else "<b>n-Substrate</b>", font=dict(color="#475569", size=14), showarrow=False)

    # 에러 원인이었던 yaxes -> yaxis 수정 완료!!
    fig_struct.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0), xaxis=dict(visible=False, range=[0, 10]), yaxis=dict(visible=False, range=[0, 6]), plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_struct, use_container_width=True)

# --- [Column 2] I-V 특성 곡선 ---
with col2:
    st.markdown("<div class='header-text'>📈 전류-전압 특성 곡선</div>", unsafe_allow_html=True)
    
    v_ax = np.linspace(0, 5, 200)
    v_b = np.linspace(0, 4, 100)
    i_b = 0.5 * k_n * (v_b**2)

    fig_iv = go.Figure()
    fig_iv.add_trace(go.Scatter(x=v_b, y=i_b, mode='lines', line=dict(color='#94a3b8', dash='dash', width=1.5), name="Boundary"))
    
    i_ax = [0 if abs_vgs < abs_vth else (k_n*(v_ov*v - 0.5*v**2) if v < v_ov else 0.5*k_n*v_ov**2*(1+0.02*(v-v_ov))) for v in v_ax]
    fig_iv.add_trace(go.Scatter(x=v_ax, y=i_ax, mode='lines', line=dict(color='#2563eb', width=3), name="I-V Curve"))
    fig_iv.add_trace(go.Scatter(x=[abs_vds], y=[i_d], mode='markers', marker=dict(color='#dc2626', size=12, line=dict(color='white', width=1.5)), name="Point"))
    
    fig_iv.update_layout(height=360, margin=dict(l=0, r=0, t=10, b=0), xaxis_title="V_DS (V)", yaxis_title="I_D (mA)", showlegend=False, plot_bgcolor='white')
    fig_iv.update_xaxes(showgrid=True, gridcolor='#f1f5f9')
    fig_iv.update_yaxes(showgrid=True, gridcolor='#f1f5f9')
    st.plotly_chart(fig_iv, use_container_width=True)

# --- [Column 3] AI 실시간 해설 ---
with col3:
    st.markdown("<div class='header-text'>🤖 AI 실시간 바이브 해설</div>", unsafe_allow_html=True)
    
    if ask_ai_btn:
        if not api_key:
            st.error("API Key를 입력해주세요.")
        else:
            with st.spinner("AI 분석 중..."):
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"반도체 교수님 모드로 설명해줘. 소자:{mos_type}, V_GS:{v_gs}V, V_DS:{v_ds}V, V_TH:{v_th}V, 영역:{op_region}. 질문:{user_query}"
                    response = model.generate_content(prompt)
                    st.success("해설 완료!")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"에러: {e}")
    else:
        st.markdown("""<div style='background-color:#f0fdf4; padding:15px; border-radius:10px; border:1px solid #bbf7d0;'>
            <p style='margin:0; color:#166534; font-size:14px;'>👈 <b>왼쪽 패널</b>에서 전압을 조절하고 버튼을 누르면 교수님의 물리 해설이 등장합니다!</p>
            </div>""", unsafe_allow_html=True)