import streamlit as st
import plotly.graph_objects as go
import numpy as np

st.set_page_config(layout="wide", page_title="BJT 시뮬레이터")

# 최소한의 깔끔한 스타일만 남긴 CSS
st.markdown("""
<style>
    /* 메인 대시보드 카드 스타일 */
    .stat-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #eaeaea;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.04);
        margin-bottom: 12px;
    }
    .stat-title { font-size: 0.85rem; color: #7f8c8d; font-weight: 600; text-transform: uppercase; margin-bottom: 4px; }
    .stat-label { font-size: 0.75rem; color: #95a5a6; font-weight: 600; }
    .stat-value { font-size: 1.3rem; font-weight: 700; color: #2c3e50; }
    
    /* 사이드바 라디오 버튼 디자인 개선 */
    div[data-testid="stRadio"] > div { flex-direction: row !important; gap: 8px !important; }
</style>
""", unsafe_allow_html=True)

if "GEMINI_API_KEY" in st.secrets:
    import google.generativeai as genai
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

with st.sidebar:
    st.markdown("### 🔌 BJT 시뮬레이터")
    st.markdown("**소자 타입 선택**")
    bjt_type = st.radio("소자 타입", ["NPN", "PNP"], horizontal=True, label_visibility="collapsed")

    st.markdown("---")
    st.markdown("**접합 전압 인가**")

    if "v_be_val" not in st.session_state: st.session_state.v_be_val = 0.75
    if "v_bc_val" not in st.session_state: st.session_state.v_bc_val = -2.0

    def update_be_slider(): st.session_state.v_be_val = st.session_state.be_num
    def update_be_num():    st.session_state.be_num   = st.session_state.v_be_val
    def update_bc_slider(): st.session_state.v_bc_val = st.session_state.bc_num
    def update_bc_num():    st.session_state.bc_num   = st.session_state.v_bc_val

    label_be = "V_BE (V)" if bjt_type == "NPN" else "V_EB (V)"
    st.markdown(f"<span style='font-size:0.85rem; font-weight:600;'>{label_be}</span>", unsafe_allow_html=True)
    V_be = st.slider(label_be, min_value=-2.0, max_value=1.0, step=0.05,
                     key="v_be_val", on_change=update_be_num, label_visibility="collapsed")
    st.number_input(label_be, min_value=-2.0, max_value=1.0, step=0.05,
                    key="be_num", on_change=update_be_slider,
                    value=st.session_state.v_be_val, label_visibility="collapsed")

    label_bc = "V_BC (V)" if bjt_type == "NPN" else "V_CB (V)"
    st.markdown(f"<span style='font-size:0.85rem; font-weight:600; margin-top:10px; display:block;'>{label_bc}</span>", unsafe_allow_html=True)
    V_bc = st.slider(label_bc, min_value=-5.0, max_value=5.0, step=0.1,
                     key="v_bc_val", on_change=update_bc_num, label_visibility="collapsed")
    st.number_input(label_bc, min_value=-5.0, max_value=5.0, step=0.1,
                    key="bc_num", on_change=update_bc_slider,
                    value=st.session_state.v_bc_val, label_visibility="collapsed")

    st.markdown("---")
    st.markdown("**💬 AI 질문**")
    user_question = st.text_area("질문 입력", height=80, label_visibility="collapsed",
                                 value="현재 바이어스 상태가 증폭기로서 왜 적합한지 밴드 다이어그램 관점에서 설명해줘.",
                                 placeholder="e.g. 현재 바이어스 상태를 물리적으로 설명해줘.")
    ai_btn = st.button("🚀 Gemini 분석 요청", use_container_width=True)

V_CC   = 5.0
R_C    = 800.0
beta   = 150
V_AF   = 100.0
early_k = 1.0 / V_AF

be_fwd = V_be > 0
bc_fwd = V_bc > 0

# 스크린샷과 동일한 색상 및 텍스트 적용
if be_fwd and not bc_fwd:
    mode      = "순방향 활성 영역"
    mode_en   = "Forward Active"
    mode_color = "#f39c12" # 노랑/주황색 (선형 영역 색상 차용)
elif be_fwd and bc_fwd:
    mode      = "포화 영역"
    mode_en   = "Saturation"
    mode_color = "#28a745" # 초록색
else:
    mode      = "차단 영역"
    mode_en   = "Cutoff"
    mode_color = "#dc3545" # 빨간색

mode_full = f"{mode} ({mode_en})"

R_B_eff = 30000.0
I_B_A = max(0.0, V_be / R_B_eff) if be_fwd else 0.0

if mode_en == "Forward Active":
    I_C_ideal = beta * I_B_A
    I_C_max   = (V_CC - 0.2) / R_C
    q_ic_A    = max(0.0, min(I_C_ideal, I_C_max))
    q_vce     = max(0.2, V_CC - q_ic_A * R_C)
elif mode_en == "Saturation":
    q_vce  = 0.2
    q_ic_A = (V_CC - q_vce) / R_C
else:
    q_vce  = V_CC
    q_ic_A = 0.0

q_ic_mA = q_ic_A * 1000

st.markdown(f"<h2 style='margin-bottom:4px;'>📟 BJT 물리 & 특성 시뮬레이터</h2>", unsafe_allow_html=True)
st.markdown("<hr style='margin:4px 0 15px 0;'>", unsafe_allow_html=True)

stat_col, main_col = st.columns([0.3, 0.7])

with stat_col:
    # 스크린샷과 완벽하게 일치하는 한 줄 텍스트 및 폰트 레이아웃 적용
    st.markdown(f"""
    <div class='stat-card'>
        <div class='stat-title'>Operating Region</div>
        <div style='font-size:1.8rem; font-weight:800; color:{mode_color}; margin-bottom:20px;'>
            {mode} <span style='font-weight:600;'>({mode_en})</span>
        </div>
        <div style='display:grid; grid-template-columns: 1fr 1fr; gap:20px;'>
            <div>
                <div class='stat-label'>인가전압 |V_CE|</div>
                <div class='stat-value'>{V_be - V_bc:.2f} V</div>
            </div>
            <div>
                <div class='stat-label'>컬렉터전류 |I_C|</div>
                <div class='stat-value'>{q_ic_mA:.2f} mA</div>
            </div>
            <div>
                <div class='stat-label'>베이스전류 |I_B|</div>
                <div class='stat-value'>{I_B_A*1e6:.1f} μA</div>
            </div>
            <div>
                <div class='stat-label'>Q점 V_CEQ</div>
                <div class='stat-value'>{q_vce:.2f} V</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if ai_btn:
        system_instruction = f"""
당신은 반도체 소자 물리학 및 증폭 회로 설계 전문가입니다.
인삿말 없이 바로 수치 분석부터 시작하세요.
현재 설정: BJT={bjt_type}, V_BE={V_be:.2f}V, V_BC={V_bc:.2f}V
모드={mode_full}, I_B={I_B_A*1e6:.2f}μA, I_C={q_ic_mA:.2f}mA, Q점 V_CE={q_vce:.2f}V
6주차 에너지 밴드 교안과 7주차 바이어스 교안을 연결하여 한국어 마크다운으로 답변하세요.
질문: "{user_question}"
"""
        if "GEMINI_API_KEY" in st.secrets:
            with st.spinner("Gemini가 물리적 특성을 분석하고 있습니다..."):
                try:
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    resp  = model.generate_content(system_instruction)
                    st.markdown(f"<div style='background:#f4f6f9; padding:15px; border-radius:10px; font-size:0.9rem;'>{resp.text}</div>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"오류 발생: {e}")
        else:
            st.error("GEMINI_API_KEY가 Secrets에 설정되지 않았습니다.")

with main_col:
    tab1, tab2 = st.tabs(["🔋 에너지 밴드 다이어그램", "📈 I_C–V_CE 특성 곡선"])

    with tab1:
        fig_band = go.Figure()

        E_g = 1.12
        x_all = np.linspace(0, 8.0, 400)
        ec_all = np.zeros_like(x_all)
        
        v_be_eff = float(np.clip(V_be, -5.0, 0.75))
        v_bc_eff = float(np.clip(V_bc, -5.0, 0.75))

        if bjt_type == "NPN":
            E_F_Base = 0.0
            E_V_Base = -0.1
            E_C_Base = E_V_Base + E_g
            
            E_F_Emitter = E_F_Base + v_be_eff
            E_F_Collector = E_F_Base + v_bc_eff
            
            E_C_Emitter = E_F_Emitter - 0.05
            E_C_Collector = E_F_Collector - 0.15
        else: # PNP
            E_F_Base = 0.0
            E_C_Base = 0.1
            E_V_Base = E_C_Base - E_g
            
            E_F_Emitter = E_F_Base - v_be_eff
            E_F_Collector = E_F_Base - v_bc_eff
            
            E_V_Emitter = E_F_Emitter + 0.05
            E_V_Collector = E_F_Collector + 0.15
            E_C_Emitter = E_V_Emitter + E_g
            E_C_Collector = E_V_Collector + E_g

        for i, x in enumerate(x_all):
            if x <= 2.4:
                ec_all[i] = E_C_Emitter
            elif x >= 5.6:
                ec_all[i] = E_C_Collector
            elif 3.2 <= x <= 4.8:
                ec_all[i] = E_C_Base
            elif 2.4 < x < 3.2: 
                t = (x - 2.4) / 0.8 * np.pi
                ec_all[i] = E_C_Emitter + (E_C_Base - E_C_Emitter) * (1 - np.cos(t)) / 2
            elif 4.8 < x < 5.6: 
                t = (x - 4.8) / 0.8 * np.pi
                ec_all[i] = E_C_Base + (E_C_Collector - E_C_Base) * (1 - np.cos(t)) / 2
                
        ev_all = ec_all - E_g

        fig_band.add_vrect(x0=0,   x1=2.8, fillcolor="rgba(173,216,230,0.25)", line_width=0)
        fig_band.add_vrect(x0=2.8, x1=5.2, fillcolor="rgba(255,182,193,0.25)", line_width=0)
        fig_band.add_vrect(x0=5.2, x1=8.0, fillcolor="rgba(144,238,144,0.25)", line_width=0)

        fig_band.add_trace(go.Scatter(x=x_all, y=ec_all, mode='lines', line=dict(color='black', width=2.5), name='E_c'))
        fig_band.add_trace(go.Scatter(x=x_all, y=ev_all, mode='lines', line=dict(color='black', width=2.5), name='E_v'))

        fig_band.add_trace(go.Scatter(x=[0, 2.4], y=[E_F_Emitter, E_F_Emitter], mode='lines', line=dict(color='blue', width=2, dash='dash'), name='E_F (Emitter)'))
        fig_band.add_trace(go.Scatter(x=[3.2, 4.8], y=[E_F_Base, E_F_Base], mode='lines', line=dict(color='blue', width=2, dash='dash'), name='E_F (Base)'))
        fig_band.add_trace(go.Scatter(x=[5.6, 8.0], y=[E_F_Collector, E_F_Collector], mode='lines', line=dict(color='blue', width=2, dash='dash'), name='E_F (Collector)'))

        fig_band.add_annotation(x=8.15, y=ec_all[-1]+0.05, text="<b>E_C</b>", showarrow=False, font=dict(size=12, color='black'))
        fig_band.add_annotation(x=8.15, y=ev_all[-1]-0.05, text="<b>E_V</b>", showarrow=False, font=dict(size=12, color='black'))

        e_lbl = "EMITTER (N⁺)" if bjt_type=="NPN" else "EMITTER (P⁺)"
        b_lbl = "BASE (P)"     if bjt_type=="NPN" else "BASE (N)"
        c_lbl = "COLLECTOR (N)"if bjt_type=="NPN" else "COLLECTOR (P)"

        fig_band.add_annotation(x=1.4, y=max(ec_all)+0.55, text=f"<b>{e_lbl}</b>", showarrow=False, font=dict(size=11, color='#1565C0'))
        fig_band.add_annotation(x=4.0, y=max(ec_all)+0.55, text=f"<b>{b_lbl}</b>", showarrow=False, font=dict(size=11, color='#B71C1C'))
        fig_band.add_annotation(x=6.6, y=max(ec_all)+0.55, text=f"<b>{c_lbl}</b>", showarrow=False, font=dict(size=11, color='#1B5E20'))

        np.random.seed(42)
        if bjt_type == "NPN":
            fig_band.add_trace(go.Scatter(
                x=np.random.uniform(0.2, 2.2, 16), y=E_C_Emitter + np.random.uniform(0.02, 0.15, 16),
                mode='markers', marker=dict(color='#1565C0', size=9, line=dict(color='#0D47A1', width=1.5)), name='전자 (e⁻)'))
            fig_band.add_trace(go.Scatter(
                x=np.random.uniform(3.4, 4.6, 10), y=E_V_Base - np.random.uniform(0.02, 0.15, 10),
                mode='markers', marker=dict(color='#C62828', size=10, line=dict(color='#7B1818', width=1.5)), name='정공 (h⁺)'))
            fig_band.add_trace(go.Scatter(
                x=np.random.uniform(5.8, 7.8, 12), y=E_C_Collector + np.random.uniform(0.02, 0.15, 12),
                mode='markers', marker=dict(color='#1565C0', size=9, line=dict(color='#0D47A1', width=1.5)), showlegend=False))
        else:
            fig_band.add_trace(go.Scatter(
                x=np.random.uniform(0.2, 2.2, 16), y=E_V_Emitter - np.random.uniform(0.02, 0.15, 16),
                mode='markers', marker=dict(color='#C62828', size=10, line=dict(color='#7B1818', width=1.5)), name='정공 (h⁺)'))
            fig_band.add_trace(go.Scatter(
                x=np.random.uniform(3.4, 4.6, 10), y=E_C_Base + np.random.uniform(0.02, 0.15, 10),
                mode='markers', marker=dict(color='#1565C0', size=9, line=dict(color='#0D47A1', width=1.5)), name='전자 (e⁻)'))
            fig_band.add_trace(go.Scatter(
                x=np.random.uniform(5.8, 7.8, 12), y=E_V_Collector - np.random.uniform(0.02, 0.15, 12),
                mode='markers', marker=dict(color='#C62828', size=10, line=dict(color='#7B1818', width=1.5)), showlegend=False))

        if mode_en == "Forward Active":
            fig_band.add_annotation(x=2.8, y=max(E_C_Emitter, E_C_Base)+0.22, text="<b>↓BE 장벽 낮아짐</b>", showarrow=False, font=dict(color='#E65100', size=10))
            fig_band.add_annotation(x=4.0, y=max(ec_all)+0.85, text="순방향 활성: 캐리어 확산 및 표류 발생", showarrow=False, font=dict(color='#FF6F00', size=11))
        elif mode_en == "Saturation":
            fig_band.add_annotation(x=4.0, y=max(ec_all)+0.85, text="⚡ 포화: 양쪽 장벽 모두 낮아짐 (스위치 ON)", showarrow=False, font=dict(color='purple', size=11))
        else:
            fig_band.add_annotation(x=4.0, y=max(ec_all)+0.85, text="⛔ 차단: 장벽에 막혀 전류 흐르지 못함 (스위치 OFF)", showarrow=False, font=dict(color='gray', size=11))

        fig_band.add_vline(x=2.8, line=dict(color='gray', width=1, dash='dot'))
        fig_band.add_vline(x=5.2, line=dict(color='gray', width=1, dash='dot'))

        y_bot = min(ev_all) - 0.4
        y_top = max(ec_all) + 0.9

        fig_band.update_layout(
            xaxis=dict(visible=False, range=[-0.2, 8.6]),
            yaxis=dict(visible=False, range=[y_bot, y_top]),
            height=420, margin=dict(l=10, r=10, t=20, b=10),
            showlegend=True,
            legend=dict(x=0.01, y=0.02, bgcolor='rgba(255,255,255,0.85)', bordercolor='lightgray', borderwidth=1, font=dict(size=10), orientation='h'),
            plot_bgcolor='white'
        )
        st.plotly_chart(fig_band, use_container_width=True)

    with tab2:
        fig_iv = go.Figure()

        sign    = 1 if bjt_type == "NPN" else -1
        v_max   = V_CC + 0.8
        v_arr   = np.linspace(0, v_max, 300)
        ib_list = [10, 20, 30, 40, 50]
        base_color = (255, 127, 14) if bjt_type == "NPN" else (148, 103, 189)

        for idx, ib_uA in enumerate(ib_list):
            ib_A   = ib_uA * 1e-6
            ic_sat = beta * ib_A * 1000
            alpha  = 0.4 + 0.12 * idx
            color  = f"rgba({base_color[0]},{base_color[1]},{base_color[2]},{alpha:.2f})"

            ic_curve = [max(0.0, ic_sat * np.tanh(v / 0.12) * (1 + early_k * v)) for v in v_arr]

            fig_iv.add_trace(go.Scatter(
                x=[sign * v for v in v_arr], y=[sign * ic for ic in ic_curve],
                mode='lines', line=dict(color=color, width=2.2), showlegend=False))

            ic_end = sign * ic_sat * (1 + early_k * v_max)
            fig_iv.add_annotation(
                x=sign * v_max + sign * 0.1, y=ic_end, text=f"I_B={ib_uA}μA", showarrow=False, font=dict(size=9, color='gray'),
                xanchor='left' if bjt_type=="NPN" else 'right')

        sat_ic_mag = (V_CC / R_C) * 1000
        fig_iv.add_trace(go.Scatter(
            x=[0.0, sign * V_CC], y=[sign * sat_ic_mag, 0.0],
            mode='lines', line=dict(color='black', width=2.8), name='직류 부하선'))

        fig_iv.add_annotation(x=sign*0.15, y=sign*(sat_ic_mag+0.3), text="<b>포화점</b>", showarrow=True, ax=sign*0.6, ay=sign*(sat_ic_mag-0.5), arrowhead=2, arrowcolor='black', font=dict(size=11))
        fig_iv.add_annotation(x=sign*(V_CC-0.1), y=sign*0.4, text="<b>차단점</b>", showarrow=True, ax=sign*(V_CC-0.8), ay=sign*1.0, arrowhead=2, arrowcolor='black', font=dict(size=11))
        fig_iv.add_vline(x=sign*0.2, line=dict(color='purple', width=1.2, dash='dot'))
        fig_iv.add_annotation(x=sign*0.22, y=sign*sat_ic_mag*0.55, text="V_CE,sat", showarrow=False, font=dict(size=9, color='purple'), textangle=-90)

        q_x, q_y = sign * q_vce, sign * q_ic_mA
        fig_iv.add_trace(go.Scatter(
            x=[q_x], y=[q_y], mode='markers', marker=dict(color='red', size=14, symbol='circle', line=dict(color='white', width=2)), name="Q점"))
        fig_iv.add_annotation(x=q_x, y=q_y + sign*0.5, text=f"<b>Q ({q_x:.2f}V, {q_y:.2f}mA)</b>", showarrow=False, font=dict(color='red', size=11))
        fig_iv.add_shape(type='line', x0=q_x, x1=q_x, y0=0, y1=q_y, line=dict(color='red', width=1, dash='dash'))
        fig_iv.add_shape(type='line', x0=0, x1=q_x, y0=q_y, y1=q_y, line=dict(color='red', width=1, dash='dash'))

        x_range = [-0.15, V_CC+1.3] if bjt_type=="NPN" else [-(V_CC+1.3), 0.15]
        y_range = [-0.4, sat_ic_mag+1.5] if bjt_type=="NPN" else [-(sat_ic_mag+1.5), 0.4]

        fig_iv.update_layout(
            xaxis_title="V_CE [V]", yaxis_title="I_C [mA]",
            xaxis=dict(range=x_range, showgrid=True, gridcolor='#EEEEEE', zeroline=True, zerolinecolor='black', zerolinewidth=1.5),
            yaxis=dict(range=y_range, showgrid=True, gridcolor='#EEEEEE', zeroline=True, zerolinecolor='black', zerolinewidth=1.5),
            height=420, margin=dict(l=10, r=10, t=20, b=10), showlegend=True,
            legend=dict(x=0.55 if bjt_type=="NPN" else 0.01, y=0.98 if bjt_type=="NPN" else 0.15, bgcolor='rgba(255,255,255,0.85)', bordercolor='lightgray', borderwidth=1, font=dict(size=10)),
            plot_bgcolor='white'
        )
        st.plotly_chart(fig_iv, use_container_width=True)