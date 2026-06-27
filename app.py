import streamlit as st
import numpy as np
import plotly.graph_objects as go
import google.generativeai as genai

# 페이지 기본 설정 (가로로 넓게 사용)
st.set_page_config(page_title="MOSFET 물리 시뮬레이터 & AI 해설", layout="wide", initial_sidebar_state="expanded")

# ---------------------------------------------------------
# 1. 좌측 화면: 터미널 스타일의 사이드바 (제어 및 입력 패널)
# ---------------------------------------------------------
with st.sidebar:
    st.title("🎛️ 제어 및 입력 패널")
    st.markdown("반도체 소자의 전압을 조절해 보세요.")
    
    # API 키 로드 (성공 메시지 등 불필요한 텍스트 모두 제거)
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Google Gemini API Key", type="password")
    
    st.markdown("---")
    
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
    st.subheader("💬 AI에게 질문하기")
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

# 동작 영역 판별 및 계산 (채널 길이 변조가 부드럽게 이어지도록 수식 개선)
if abs_vgs < abs_vth:
    op_region = "차단 영역 (Cutoff)"
    i_d = 0.0
elif abs_vds < v_ov:
    op_region = "선형 영역 (Linear/Triode)"
    i_d = k_n * (v_ov * abs_vds - 0.5 * (abs_vds ** 2))
else:
    op_region = "포화 영역 (Saturation)"
    # 곡선이 찌그러지지 않도록 포화 영역 진입점(v_ov) 이후부터 기울기 적용
    id_sat = 0.5 * k_n * (v_ov ** 2)
    i_d = id_sat * (1 + 0.02 * (abs_vds - v_ov))

# 메인 화면 레이아웃 분할 (좌측 시각화, 우측 AI 해설)
col_main_left, col_main_right = st.columns([1.5, 1.2], gap="large")

# ---------------------------------------------------------
# 3. 중앙 화면: 메인 시각화 (동작 상태, 구조, I-V 곡선)
# ---------------------------------------------------------
with col_main_left:
    st.header("📊 실시간 소자 상태 및 시각화")
    
    # 동작 영역에 따른 강조 박스 디자인
    if "포화" in op_region:
        box_bg, box_border, text_color = "#e6f7ff", "#91d5ff", "#0050b3"
    elif "선형" in op_region:
        box_bg, box_border, text_color = "#f6ffed", "#b7eb8f", "#389e0d"
    else:
        box_bg, box_border, text_color = "#fff1f0", "#ffa39e", "#cf1322"
        
    st.markdown(f"""
    <div style="background-color: {box_bg}; padding: 20px; border-radius: 12px; border: 2px solid {box_border}; text-align: center; margin-bottom: 25px;">
        <h3 style="color: {text_color}; margin: 0; font-size: 28px;">현재 동작 영역 : <span style="font-weight: 800;">{op_region}</span></h3>
    </div>
    """, unsafe_allow_html=True)
    
    # 요청하신 대로 드레인 전압과 드레인 전류만 표시
    col_c1, col_c2 = st.columns(2)
    col_c1.metric(label="드레인 전압 (|V_DS|)", value=f"{abs_vds:.2f} V")
    col_c2.metric(label="드레인 전류 (|I_D|)", value=f"{i_d:.2f} mA")
    
    st.markdown("---")
    
    # 3-1. I-V 특성 곡선 (Plotly)
    st.markdown("#### 📉 I-V 특성 곡선 (I_D - V_DS)")
    
    # 그래프를 찌그러짐 없이 매끄럽게 그리기 위해 해상도 증가
    vds_array = np.linspace(0, 5, 200)
    id_array = np.zeros_like(vds_array)
    
    for i, v in enumerate(vds_array):
        if abs_vgs < abs_vth:
            id_array[i] = 0
        elif v < v_ov:
            id_array[i] = k_n * (v_ov * v - 0.5 * (v ** 2))
        else:
            id_sat_calc = 0.5 * k_n * (v_ov ** 2)
            id_array[i] = id_sat_calc * (1 + 0.02 * (v - v_ov)) # 꺾임 방지

    fig_iv = go.Figure()
    
    fig_iv.add_trace(go.Scatter(x=vds_array, y=id_array, mode='lines', name=f'{mos_type} Curve',
                                line=dict(color='#2563eb', width=4),
                                hovertemplate='V_DS: %{x:.2f}V<br>I_D: %{y:.2f}mA<extra></extra>'))
    
    fig_iv.add_trace(go.Scatter(x=[abs_vds], y=[i_d], mode='markers', name='동작점',
                                marker=dict(color='#ef4444', size=14, symbol='circle', line=dict(color='white', width=2)),
                                hovertemplate='<b>현재 위치</b><br>V_DS: %{x:.2f}V<br>I_D: %{y:.2f}mA<extra></extra>'))
    
    fig_iv.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0),
                         xaxis_title="|V_DS| (V)", yaxis_title="|I_D| (mA)",
                         hovermode="x unified", plot_bgcolor='rgba(0,0,0,0)')
    fig_iv.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#e5e7eb')
    fig_iv.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#e5e7eb')
    st.plotly_chart(fig_iv, use_container_width=True)

    # 3-2. MOSFET 구조 시각화
    st.markdown("#### 🧱 MOSFET 구조 시각화 (채널 형성 및 Pinch-off 모사)")
    fig_struct = go.Figure()
    
    # Substrate
    fig_struct.add_shape(type="rect", x0=0, y0=0, x1=10, y1=4, fillcolor="#e2e8f0", line=dict(color="#64748b", width=2))
    fig_struct.add_annotation(x=5, y=1, text="P-Substrate" if mos_type=="NMOS" else "N-Substrate", showarrow=False, font=dict(color="#475569"))
    
    # Source & Drain
    sd_color = "#fca5a5" if mos_type=="NMOS" else "#93c5fd"
    sd_text = "n+" if mos_type=="NMOS" else "p+"
    fig_struct.add_shape(type="rect", x0=0.5, y0=2.5, x1=2.5, y1=4, fillcolor=sd_color, line=dict(color="#64748b", width=2))
    fig_struct.add_shape(type="rect", x0=7.5, y0=2.5, x1=9.5, y1=4, fillcolor=sd_color, line=dict(color="#64748b", width=2))
    fig_struct.add_annotation(x=1.5, y=3.25, text=f"Source ({sd_text})", showarrow=False)
    fig_struct.add_annotation(x=8.5, y=3.25, text=f"Drain ({sd_text})", showarrow=False)
    
    # Gate Oxide & Gate
    fig_struct.add_shape(type="rect", x0=2.5, y0=4, x1=7.5, y1=4.3, fillcolor="#fef08a", line=dict(color="#64748b", width=2))
    fig_struct.add_shape(type="rect", x0=2.5, y0=4.3, x1=7.5, y1=5.3, fillcolor="#334155", line=dict(color="#64748b", width=2))
    fig_struct.add_annotation(x=5, y=4.8, text="Gate", font=dict(color="white", size=14), showarrow=False)
    
    # Channel Visualization (에러 해결: 확실하게 보이도록 opacity 추가 및 색상 변경)
    if op_region != "차단 영역 (Cutoff)":
        channel_color = "#ef4444" if mos_type=="NMOS" else "#3b82f6"
        if op_region == "선형 영역 (Linear/Triode)":
            fig_struct.add_trace(go.Scatter(x=[2.5, 7.5, 7.5, 2.5], y=[3.8, 3.8, 4.0, 4.0], 
                                            fill='toself', fillcolor=channel_color, opacity=0.8,
                                            line=dict(width=0), mode='lines', hoverinfo='skip', showlegend=False))
        elif op_region == "포화 영역 (Saturation)":
            pinch_point = 7.5 - (0.5 * (abs_vds - v_ov)) 
            pinch_point = max(3.0, pinch_point)
            fig_struct.add_trace(go.Scatter(x=[2.5, pinch_point, 7.5, 2.5], y=[3.7, 4.0, 4.0, 4.0], 
                                            fill='toself', fillcolor=channel_color, opacity=0.8,
                                            line=dict(width=0), mode='lines', hoverinfo='skip', showlegend=False))
            fig_struct.add_annotation(x=pinch_point, y=3.7, text="Pinch-off", showarrow=True, arrowhead=2, ax=0, ay=-40, font=dict(color="#ef4444", size=13))

    fig_struct.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0),
                             xaxis=dict(visible=False, range=[0, 10]), 
                             yaxis=dict(visible=False, range=[0, 6]), plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_struct, use_container_width=True)

# ---------------------------------------------------------
# 4. 우측 화면: AI 실시간 해설 (Gemini API)
# ---------------------------------------------------------
with col_main_right:
    st.header("🤖 AI 실시간 해설")
    
    if ask_ai_btn:
        if not api_key:
            st.error("좌측 패널에 Gemini API Key를 입력하거나 Secrets에 설정해주세요.")
        else:
            with st.spinner("AI가 물리 현상을 분석 중입니다..."):
                try:
                    # Gemini API 설정 (404 에러를 방지하기 위해 가장 안정적인 latest 태그 사용)
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash-latest')
                    
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
                    2. 현재 설정된 전압 수치들을 직접 언급하며 왜 '{op_region}'에 도달했는지 물리적 이유(예: 채널 형성, 핀치오프 등)를 연관지어 설명해.
                    """
                    
                    response = model.generate_content(context_prompt)
                    
                    st.success("해설이 도착했습니다!")
                    st.markdown(response.text)
                    
                except Exception as e:
                    st.error(f"AI 응답 생성 중 오류가 발생했습니다. API 키가 정확한지 확인해 주세요.\n\n에러 상세: {e}")
    else:
        st.info("👈 좌측 패널에서 전압 설정을 마치고 **[🤖 AI 실시간 해설 받기]** 버튼을 누르면 이 영역에 해설이 나타납니다.")