import streamlit as st
import numpy as np
import plotly.graph_objects as go
import google.generativeai as genai

# 1. 페이지 설정: 와이드 레이아웃 적용
st.set_page_config(page_title="MOSFET 물리 시뮬레이터", layout="wide", initial_sidebar_state="expanded")

# 사이드바 및 메인 화면 간격 최적화 CSS
st.markdown("""
    <style>
        [data-testid="stSidebar"] { background-color: #f8fafc; border-right: 1px solid #e2e8f0; }
        .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 95%; }
        h3 { margin-bottom: 1rem !important; }
    </style>
""", unsafe_allow_html=True)

# 메인 타이틀
st.markdown("<h1 style='text-align: center; color: #1e293b; margin-bottom: 30px;'>🔌 NMOS/PMOS MOSFET 물리 시뮬레이터</h1>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. 좌측 사이드바: 제어 및 입력 패널
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("## 🎛️ **제어 및 입력 패널**")
    
    # API 키 로드 (성공 메시지 숨김 처리)
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Gemini API Key", type="password")
    
    st.markdown("---")
    mos_type = st.selectbox("소자 타입 선택", ["NMOS", "PMOS"])
    
    # 슬라이더 전압 설정
    if mos_type == "NMOS":
        v_th = st.slider("문턱 전압 (V_TH) [V]", 0.5, 2.0, 1.0, 0.1)
        v_gs = st.slider("게이트-소스 전압 (V_GS) [V]", 0.0, 5.0, 3.0, 0.1)
        v_ds = st.slider("드레인-소스 전압 (V_DS) [V]", 0.0, 5.0, 1.6, 0.1)
    else:
        v_th = st.slider("문턱 전압 (V_TH) [V]", -2.0, -0.5, -1.0, 0.1)
        v_gs = st.slider("게이트-소스 전압 (V_GS) [V]", -5.0, 0.0, -3.0, 0.1)
        v_ds = st.slider("드레인-소스 전압 (V_DS) [V]", -5.0, 0.0, -1.6, 0.1)

    st.markdown("---")
    st.markdown("### 💬 **AI에게 질문하기**")
    user_query = st.text_area("궁금한 점을 입력하세요:", "현재 전압 조건 상태에 대해 물리적으로 쉽게 설명해줘.", height=100)
    ask_ai_btn = st.button("🤖 AI 실시간 해설 받기", use_container_width=True)

# ---------------------------------------------------------
# 3. 물리 계산 로직 (수학적 모델링)
# ---------------------------------------------------------
k_n = 1.0
abs_vgs, abs_vds, abs_vth = abs(v_gs), abs(v_ds), abs(v_th)
v_ov = abs_vgs - abs_vth

# 동작 영역 및 드레인 전류 계산
if abs_vgs < abs_vth:
    op_region, i_d = "차단 영역 (Cutoff)", 0.0
elif abs_vds < v_ov:
    op_region, i_d = "선형 영역 (Linear / Triode)", k_n * (v_ov * abs_vds - 0.5 * (abs_vds ** 2))
else:
    op_region, i_d = "포화 영역 (Saturation)", 0.5 * k_n * (v_ov ** 2) * (1 + 0.02 * (abs_vds - v_ov))

# ---------------------------------------------------------
# 4. 메인 화면: 3단 분할 레이아웃 (상태&구조 | I-V 곡선 | AI 해설)
# ---------------------------------------------------------
col1, col2, col3 = st.columns([1, 1.2, 1.2], gap="large")

# ==========================================
# [Column 1] 실시간 소자 상태 및 구조 시각화
# ==========================================
with col1:
    st.markdown("### 📊 **실시간 소자 상태**")
    
    # 상태 텍스트
    st.markdown(f"<div style='font-size: 16px; color: #64748b;'>동작 영역</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size: 32px; font-weight: 700; color: #0f172a; margin-bottom: 15px;'>{op_region}</div>", unsafe_allow_html=True)
    
    m1, m2 = st.columns(2)
    m1.metric("포화 시작 전압 (|V_DS,sat|)", f"{max(0, v_ov):.2f} V")
    m2.metric("드레인 전류 (I_D)", f"{i_d:.2f} mA")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🧱 **모스펫 구조 시각화**")
    
    # 구조 시각화 (레이어 꼬임 방지를 위해 모두 add_shape로 통합)
    fig_struct = go.Figure()
    
    # 1. 기판, 산화막, 게이트, 소스/드레인 배치
    fig_struct.add_shape(type="rect", x0=0, y0=0, x1=10, y1=4, fillcolor="#e2e8f0", line=dict(color="#94a3b8", width=2)) # P-Substrate
    fig_struct.add_shape(type="rect", x0=2.5, y0=4, x1=7.5, y1=4.15, fillcolor="#fef08a", line=dict(color="#94a3b8")) # SiO2
    fig_struct.add_shape(type="rect", x0=2.5, y0=4.15, x1=7.5, y1=5.2, fillcolor="#334155", line=dict(color="#1e293b")) # Gate
    
    sd_color = "#f87171" if mos_type == "NMOS" else "#60a5fa"
    sd_txt = "n+" if mos_type == "NMOS" else "p+"
    fig_struct.add_shape(type="rect", x0=0.5, y0=2.5, x1=2.5, y1=4, fillcolor=sd_color, line=dict(color="#94a3b8", width=1)) # Source
    fig_struct.add_shape(type="rect", x0=7.5, y0=2.5, x1=9.5, y1=4, fillcolor=sd_color, line=dict(color="#94a3b8", width=1)) # Drain
    
    # 2. 채널 형성 (SVG 다각형 Path 적용 - 절대 숨지 않고 전압에 따라 형태 변형)
    if op_region != "차단 영역 (Cutoff)":
        ch_color = "#f59e0b" # 눈에 잘 띄는 짙은 주황색/금색
        if op_region == "선형 영역 (Linear / Triode)":
            # 드레인 쪽으로 갈수록 얇아지는 사다리꼴 형태
            t_drain = 4.0 - 0.15 * (1 - abs_vds / max(v_ov, 0.001))
            path = f"M 2.5 4.0 L 7.5 4.0 L 7.5 {t_drain:.3f} L 2.5 3.85 Z"
            fig_struct.add_shape(type="path", path=path, fillcolor=ch_color, line=dict(width=0))
        else:
            # 포화 영역: 핀치오프 발생 (삼각형 형태)
            p_point = max(3.0, 7.5 - (abs_vds - v_ov) * 0.8)
            path = f"M 2.5 4.0 L {p_point:.3f} 4.0 L 2.5 3.85 Z"
            fig_struct.add_shape(type="path", path=path, fillcolor=ch_color, line=dict(width=0))
            # 핀치오프 포인트 지시선 추가
            fig_struct.add_annotation(x=p_point, y=3.7, text="<b>Pinch-off Point</b>", font=dict(color="#dc2626", size=11), showarrow=True, arrowhead=2, ax=0, ay=-30)
            
    # 텍스트 라벨
    fig_struct.add_annotation(x=1.5, y=3.25, text=f"<b>Source</b><br>({sd_txt})", showarrow=False, font=dict(color="white"))
    fig_struct.add_annotation(x=8.5, y=3.25, text=f"<b>Drain</b><br>({sd_txt})", showarrow=False, font=dict(color="white"))
    fig_struct.add_annotation(x=5, y=4.67, text="<b>Gate (G)</b>", showarrow=False, font=dict(color="white", size=14))
    fig_struct.add_annotation(x=5, y=1, text="P-Substrate" if mos_type=="NMOS" else "N-Substrate", showarrow=False, font=dict(color="#64748b"))

    fig_struct.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0), xaxis=dict(visible=False, range=[0, 10]), yaxis=dict(visible=False, range=[0, 6]), plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_struct, use_container_width=True)

# ==========================================
# [Column 2] I-V 특성 곡선
# ==========================================
with col2:
    st.markdown("### 📈 **전류-전압 특성 곡선**")
    
    v_axis = np.linspace(0, 5, 200)
    v_bound = np.linspace(0, 4, 100)
    i_bound = 0.5 * k_n * (v_bound**2) # 포화 시작 경계선 점선

    fig_iv = go.Figure()
    
    # 1. 경계선
    fig_iv.add_trace(go.Scatter(x=v_bound, y=i_bound, mode='lines', line=dict(color='#94a3b8', dash='dash', width=2), name="Sat. Boundary"))
    
    # 2. 메인 곡선
    i_axis = [0 if abs_vgs < abs_vth else (k_n*(v_ov*v - 0.5*v**2) if v < v_ov else 0.5*k_n*v_ov**2*(1+0.02*(v-v_ov))) for v in v_axis]
    fig_iv.add_trace(go.Scatter(x=v_axis, y=i_axis, mode='lines', line=dict(color='#2563eb', width=3), name="I-V Curve"))
    
    # 3. 현재 동작점
    fig_iv.add_trace(go.Scatter(x=[abs_vds], y=[i_d], mode='markers', marker=dict(color='#dc2626', size=14, line=dict(color='white', width=2)), name="Operating Point"))
    
    fig_iv.update_layout(height=430, margin=dict(l=0, r=0, t=20, b=0), xaxis_title="V_DS (V)", yaxis_title="I_D (mA)", 
                         legend=dict(yanchor="top", y=0.95, xanchor="left", x=0.05, bgcolor="rgba(255,255,255,0.8)"), plot_bgcolor='white')
    fig_iv.update_xaxes(showgrid=True, gridcolor='#f1f5f9', zeroline=True, zerolinecolor='#cbd5e1')
    fig_iv.update_yaxes(showgrid=True, gridcolor='#f1f5f9', zeroline=True, zerolinecolor='#cbd5e1')
    
    st.plotly_chart(fig_iv, use_container_width=True)

# ==========================================
# [Column 3] AI 실시간 바이브 해설
# ==========================================
with col3:
    st.markdown("### 🤖 **AI 실시간 바이브 해설**")
    
    if ask_ai_btn:
        if not api_key:
            st.error("⚠️ 사이드바에 Gemini API Key를 입력해주세요.")
        else:
            with st.spinner("AI가 물리 법칙을 분석하고 있습니다..."):
                try:
                    # 404 에러 방지를 위해 가장 범용적인 기본 모델명 명시
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    prompt = f"""
                    너는 반도체 공학 교수님이야. 사용자가 질문한 내용에 대해 다음의 현재 소자 상태를 바탕으로 물리적 원리를 명확하게 설명해줘.
                    
                    [현재 상태 정보]
                    - 소자: {mos_type}
                    - V_GS: {v_gs}V, V_DS: {v_ds}V, V_TH: {v_th}V
                    - 현재 동작 영역: {op_region}
                    - 계산된 드레인 전류 I_D: {i_d:.2f}mA
                    - 포화 시작 전압 V_DS,sat: {v_ov:.2f}V
                    
                    사용자 질문: {user_query}
                    
                    답변 지침:
                    1. 지나치게 길지 않게 가독성 좋게 작성해 (마크다운 불릿 활용).
                    2. 현재 전압 수치들을 직접 언급하며 왜 '{op_region}'에 도달했는지 설명해.
                    """
                    
                    response = model.generate_content(prompt)
                    st.success("해설이 도착했습니다! 🎉")
                    st.markdown(response.text)
                    
                except Exception as e:
                    # 상세 에러 원인 출력
                    st.error(f"⚠️ AI 응답 생성 중 오류가 발생했습니다. API 키가 정확한지 확인해 주세요.\n\n상세 에러: {e}")
    else:
        # 안내 박스 디자인 개선
        st.markdown("""
        <div style="background-color: #f0fdf4; padding: 20px; border-radius: 10px; border: 1px solid #bbf7d0;">
            <p style="margin: 0; color: #166534; font-size: 16px;">
            👉 <b>왼쪽 패널</b>에서 전압 설정을 끝내고 <b>[🤖 AI 실시간 해설 받기]</b> 버튼을 누르면 교수님의 명품 물리 해설이 등장합니다!
            </p>
        </div>
        """, unsafe_allow_html=True)