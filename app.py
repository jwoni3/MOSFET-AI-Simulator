import streamlit as st
import numpy as np
import plotly.graph_objects as go
import google.generativeai as genai

# 페이지 기본 설정 (가로로 넓게 사용)
st.set_page_config(page_title="MOSFET 물리 시뮬레이터 & AI 해설", layout="wide")

# UI/UX 개선을 위한 커스텀 CSS 주입
st.markdown("""
<style>
/* 좌측 제어 패널(첫 번째 컬럼) 배경색 및 스타일 지정 */
div[data-testid="column"]:nth-of-type(1) {
    background-color: #f4f7f6;
    padding: 25px 20px;
    border-radius: 15px;
    box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
}
</style>
""", unsafe_allow_html=True)

# 레이아웃 구성: 좌(제어), 중(시각화), 우(AI)
col_left, col_center, col_right = st.columns([1.2, 2.0, 1.2], gap="large")

# ---------------------------------------------------------
# 1. 좌측 화면: 제어 및 입력 패널
# ---------------------------------------------------------
with col_left:
    st.subheader("🎛️ 제어 및 입력 패널")
    
    # API 키 자동 로드 설정 (메시지 제거)
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Google Gemini API Key", type="password", help="API 키를 찾을 수 없습니다. 직접 입력하세요.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    mos_type = st.selectbox("소자 타입 선택", ["NMOS", "PMOS"])
    
    # NMOS, PMOS에 따른 슬라이더 범위 및 부호 조정
    if mos_type == "NMOS":
        v_th = st.slider("문턱 전압 (V_TH) [V]", 0.5, 2.0, 1.0, 0.1)
        v_gs = st.slider("게이트-소스 전압 (V_GS) [V]", 0.0, 5.0, 2.5, 0.1)
        v_ds = st.slider("드레인-소스 전압 (V_DS) [V]", 0.0, 5.0, 3.0, 0.1)
    else:
        v_th = st.slider("문턱 전압 (V_TH) [V]", -2.0, -0.5, -1.0, 0.1)
        v_gs = st.slider("게이트-소스 전압 (V_GS) [V]", -5.0, 0.0, -2.5, 0.1)
        v_ds = st.slider("드레인-소스 전압 (V_DS) [V]", -5.0, 0.0, -3.0, 0.1)

    st.markdown("---")
    st.subheader("💬 AI에게 해설 요청")
    user_query = st.text_area("궁금한 점을 입력하세요:", "현재 전압 상태와 물리적 현상에 대해 설명해줘.")
    ask_ai_btn = st.button("🤖 AI 실시간 해설 받기", use_container_width=True)

# ---------------------------------------------------------
# 2. 물리적 수치 및 동작 영역 계산 로직 (NMOS 기준 절대값 변환)
# ---------------------------------------------------------
k_n = 1.0 # Transconductance parameter (mA/V^2) 가정
abs_vgs = abs(v_gs)
abs_vds = abs(v_ds)
abs_vth = abs(v_th)

v_ov = abs_vgs - abs_vth # Overdrive voltage

# 동작 영역 판별 및 계산 (그래프 점과 완벽히 일치하도록 채널 길이 변조 0.02 반영)
if abs_vgs < abs_vth:
    op_region = "차단 영역 (Cutoff)"
    i_d = 0.0
elif abs_vds < v_ov:
    op_region = "선형 영역 (Linear/Triode)"
    i_d = k_n * ((v_ov) * abs_vds - 0.5 * (abs_vds ** 2))
else:
    op_region = "포화 영역 (Saturation)"
    i_d = 0.5 * k_n * (v_ov ** 2) * (1 + 0.02 * abs_vds)

# ---------------------------------------------------------
# 3. 중앙 화면: 메인 시각화 (동작 상태, 구조, I-V 곡선)
# ---------------------------------------------------------
with col_center:
    st.subheader("📊 실시간 소자 상태 및 시각화")
    
    # 동작 영역에 따른 강조 박스 색상 다르게 설정
    if "포화" in op_region:
        box_bg, box_border, text_color = "#e6f7ff", "#91d5ff", "#0050b3"
    elif "선형" in op_region:
        box_bg, box_border, text_color = "#f6ffed", "#b7eb8f", "#389e0d"
    else:
        box_bg, box_border, text_color = "#fff1f0", "#ffa39e", "#cf1322"
        
    st.markdown(f"""
    <div style="background-color: {box_bg}; padding: 15px; border-radius: 10px; border: 2px solid {box_border}; text-align: center; margin-bottom: 20px;">
        <h3 style="color: {text_color}; margin: 0;">현재 동작 영역 : <span style="font-weight: 800;">{op_region}</span></h3>
    </div>
    """, unsafe_allow_html=True)
    
    col_c1, col_c2 = st.columns(2)
    col_c1.metric(label="드레인 전류 (I_D)", value=f"{i_d:.2f} mA")
    col_c2.metric(label="오버드라이브 전압 (V_OV)", value=f"{max(0, v_ov):.2f} V")
    
    st.markdown("---")
    
    # 3-1. I-V 특성 곡선 (Plotly)
    st.markdown("**📉 I-V 특성 곡선 (I_D - V_DS)**")
    
    vds_array = np.linspace(0, 5, 100)
    id_array = np.zeros_like(vds_array)
    
    for i, v in enumerate(vds_array):
        if abs_vgs < abs_vth:
            id_array[i] = 0
        elif v < v_ov:
            id_array[i] = k_n * ((v_ov) * v - 0.5 * (v ** 2))
        else:
            id_array[i] = 0.5 * k_n * (v_ov ** 2) * (1 + 0.02 * v)

    fig_iv = go.Figure()
    
    # I-V 전체 곡선
    fig_iv.add_trace(go.Scatter(x=vds_array, y=id_array, mode='lines', name=f'{mos_type} Curve',
                                line=dict(color='blue', width=3),
                                hovertemplate='V_DS: %{x:.2f}V<br>I_D: %{y:.2f}mA<extra></extra>'))
    
    # 현재 동작점 (Red Dot)
    fig_iv.add_trace(go.Scatter(x=[abs_vds], y=[i_d], mode='markers', name='동작점 (Operating Point)',
                                marker=dict(color='red', size=12, symbol='circle'),
                                hovertemplate='<b>현재 위치</b><br>V_DS: %{x:.2f}V<br>I_D: %{y:.2f}mA<extra></extra>'))
    
    fig_iv.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0),
                         xaxis_title="|V_DS| (V)", yaxis_title="|I_D| (mA)",
                         hovermode="x unified")
    st.plotly_chart(fig_iv, use_container_width=True)

    # 3-2. MOSFET 구조 단순 시각화 (Plotly 도형 활용)
    st.markdown("**🧱 MOSFET 구조 시각화 (Pinch-off 모사)**")
    fig_struct = go.Figure()
    
    # Substrate
    fig_struct.add_shape(type="rect", x0=0, y0=0, x1=10, y1=4, fillcolor="#e0e0e0", line=dict(color="black"))
    fig_struct.add_annotation(x=5, y=1, text="P-Substrate" if mos_type=="NMOS" else "N-Substrate", showarrow=False)
    
    # Source & Drain (n+ or p+)
    sd_color = "#ff9999" if mos_type=="NMOS" else "#9999ff"
    sd_text = "n+" if mos_type=="NMOS" else "p+"
    fig_struct.add_shape(type="rect", x0=0.5, y0=2.5, x1=2.5, y1=4, fillcolor=sd_color, line=dict(color="black"))
    fig_struct.add_shape(type="rect", x0=7.5, y0=2.5, x1=9.5, y1=4, fillcolor=sd_color, line=dict(color="black"))
    fig_struct.add_annotation(x=1.5, y=3.25, text=f"Source ({sd_text})", showarrow=False)
    fig_struct.add_annotation(x=8.5, y=3.25, text=f"Drain ({sd_text})", showarrow=False)
    
    # Gate Oxide & Gate
    fig_struct.add_shape(type="rect", x0=2.5, y0=4, x1=7.5, y1=4.3, fillcolor="#ffd700", line=dict(color="black"))
    fig_struct.add_shape(type="rect", x0=2.5, y0=4.3, x1=7.5, y1=5.3, fillcolor="#555555", line=dict(color="black"))
    fig_struct.add_annotation(x=5, y=4.8, text="Gate", font=dict(color="white"), showarrow=False)
    
    # Channel Visualization (에러 원인이었던 부분 수정 완료: line=dict(width=0))
    if op_region != "차단 영역 (Cutoff)":
        channel_color = "rgba(255, 0, 0, 0.5)" if mos_type=="NMOS" else "rgba(0, 0, 255, 0.5)"
        if op_region == "선형 영역 (Linear/Triode)":
            fig_struct.add_trace(go.Scatter(x=[2.5, 7.5, 7.5, 2.5], y=[3.8, 3.8, 4.0, 4.0], 
                                            fill='toself', fillcolor=channel_color, line=dict(width=0),
                                            mode='none', showlegend=False, hoverinfo='skip'))
        elif op_region == "포화 영역 (Saturation)":
            pinch_point = 7.5 - (0.5 * (abs_vds - v_ov)) 
            pinch_point = max(3.0, pinch_point)
            fig_struct.add_trace(go.Scatter(x=[2.5, pinch_point, 7.5, 2.5], y=[3.7, 4.0, 4.0, 4.0], 
                                            fill='toself', fillcolor=channel_color, line=dict(width=0),
                                            mode='none', showlegend=False, hoverinfo='skip'))
            fig_struct.add_annotation(x=pinch_point, y=3.7, text="Pinch-off", showarrow=True, arrowhead=2, ax=0, ay=-30)

    fig_struct.update_layout(height=250, margin=dict(l=0, r=0, t=0, b=0),
                             xaxis=dict(visible=False, range=[0, 10]), 
                             yaxis=dict(visible=False, range=[0, 6]))
    st.plotly_chart(fig_struct, use_container_width=True)

# ---------------------------------------------------------
# 4. 우측 화면: AI 실시간 바이브 해설 (Gemini API)
# ---------------------------------------------------------
with col_right:
    st.subheader("🤖 AI 실시간 바이브 해설")
    
    if ask_ai_btn:
        if not api_key:
            st.error("좌측 패널에 Gemini API Key를 입력하거나 Secrets에 설정해주세요.")
        else:
            with st.spinner("AI가 물리 현상을 분석 중입니다..."):
                try:
                    # Gemini API 설정
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # AI에게 전달할 시스템/상태 프롬프트 구성
                    context_prompt = f"""
                    너는 반도체 공학 전문가이자 친절한 교수님이야. 사용자가 질문한 내용에 대해 다음의 현재 소자 상태를 바탕으로 물리적 원리(에너지 밴드, 핀치오프, 캐리어 움직임 등)를 명확하고 전문적으로 설명해줘.
                    
                    [현재 상태 정보]
                    - 소자: {mos_type}
                    - V_GS: {v_gs}V, V_DS: {v_ds}V, V_TH: {v_th}V
                    - 현재 동작 영역: {op_region}
                    - 계산된 I_D: {i_d:.2f}mA
                    - V_OV (Overdrive): {v_ov:.2f}V
                    
                    사용자 질문: {user_query}
                    
                    답변 작성 지침:
                    1. 지나치게 길지 않게 핵심만 가독성 좋게 작성해 (마크다운 활용).
                    2. 현재 설정된 전압 수치들을 직접 언급하며 왜 '{op_region}'에 도달했는지 물리적 이유(예: 채널 형성, 강반전, 핀치오프 등)를 연관지어 설명해.
                    """
                    
                    response = model.generate_content(context_prompt)
                    
                    st.success("해설이 도착했습니다!")
                    st.markdown(response.text)
                    
                except Exception as e:
                    st.error(f"AI 응답 생성 중 오류가 발생했습니다: {e}")
    else:
        st.info("왼쪽 패널에서 전압 설정을 마치고 **[AI 실시간 해설 받기]** 버튼을 누르면 이 영역에 물리적 원리 기반 해설이 생성됩니다.")