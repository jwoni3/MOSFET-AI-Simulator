import streamlit as st
import plotly.graph_objects as go
import numpy as np

st.set_page_config(layout="wide", page_title="BJT 시뮬레이터")

st.markdown("""
<style>
[data-testid="stSidebar"] {
    background: #1a1f36;
    min-width: 260px;
    max-width: 260px;
}
[data-testid="stSidebar"] * { color: #e0e0e0 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #ffffff !important; font-size: 0.95rem !important; }
[data-testid="stSidebar"] .stRadio label { font-size: 0.82rem !important; }
[data-testid="stSidebar"] .stSlider { margin-top: -10px; margin-bottom: 0px; }
[data-testid="stSidebar"] .stSlider label { font-size: 0.80rem !important; margin-bottom: -4px; }
[data-testid="stSidebar"] .stSlider [data-testid="stMarkdownContainer"] p { font-size: 0.78rem !important; }
[data-testid="stSidebar"] .stNumberInput label { font-size: 0.78rem !important; }
[data-testid="stSidebar"] .stNumberInput input { font-size: 0.78rem !important; height: 28px; padding: 2px 6px; }
[data-testid="stSidebar"] .stTextArea label { font-size: 0.80rem !important; }
[data-testid="stSidebar"] .stTextArea textarea { font-size: 0.78rem !important; }
[data-testid="stSidebar"] hr { margin: 6px 0 !important; border-color: #3a4060 !important; }
[data-testid="stSidebar"] .stRadio > div { gap: 4px !important; }
[data-testid="stSidebar"] .stButton > button {
    background: #2d3561; border: 1px solid #4a5290;
    color: #ffffff !important; font-size: 0.82rem !important;
    padding: 4px 10px; width: 100%; border-radius: 6px; margin-top: 4px;
}
[data-testid="stSidebar"] .stButton > button:hover { background: #3d4671; }
div[data-testid="stRadio"] > div { flex-direction: row !important; gap: 8px !important; }
div[data-testid="stRadio"] label {
    background: #2d3561; border: 1px solid #4a5290;
    border-radius: 8px; padding: 4px 14px !important;
    font-size: 0.85rem !important; cursor: pointer;
}
div[data-testid="stRadio"] label:has(input:checked) {
    background: #4f6ef7; border-color: #7a9fff;
}
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
    st.markdown(f"<span style='font-size:0.80rem'>{label_be}</span>", unsafe_allow_html=True)
    V_be = st.slider(label_be, min_value=-1.0, max_value=1.5, step=0.05,
                     key="v_be_val", on_change=update_be_num, label_visibility="collapsed")
    st.number_input(label_be, min_value=-1.0, max_value=1.5, step=0.05,
                    key="be_num", on_change=update_be_slider,
                    value=st.session_state.v_be_val, label_visibility="collapsed")

    label_bc = "V_BC (V)" if bjt_type == "NPN" else "V_CB (V)"
    st.markdown(f"<span style='font-size:0.80rem'>{label_bc}</span>", unsafe_allow_html=True)
    V_bc = st.slider(label_bc, min_value=-5.0, max_value=5.0, step=0.1,
                     key="v_bc_val", on_change=update_bc_num, label_visibility="collapsed")
    st.number_input(label_bc, min_value=-5.0, max_value=5.0, step=0.1,
                    key="bc_num", on_change=update_bc_slider,
                    value=st.session_state.v_bc_val, label_visibility="collapsed")

    st.markdown("---")
    st.markdown("**💬 AI 질문**")
    user_question = st.text_area("질문 입력", height=68, label_visibility="collapsed",
                                 value="현재 바이어스 상태가 증폭기로서 왜 적합한지 밴드 다이어그램 관점에서 설명해줘.",
                                 placeholder="e.g. 현재 바이어스 상태를 물리적으로 설명해줘.")
    ai_btn = st.button("🚀 Gemini 분석 요청")

V_CC   = 5.0
R_C    = 800.0
beta   = 150
V_AF   = 100.0
early_k = 1.0 / V_AF

be_fwd = V_be > 0
bc_fwd = V_bc > 0

if be_fwd and not bc_fwd:
    mode      = "순방향 활성 모드"
    mode_en   = "Forward Active"
    mode_color = "#27ae60"
elif be_fwd and bc_fwd:
    mode      = "포화 모드"
    mode_en   = "Saturation"
    mode_color = "#8e44ad"
else:
    mode      = "차단 모드"
    mode_en   = "Cut-off"
    mode_color = "#e74c3c"

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

st.markdown(f"<h2 style='margin-bottom:4px'>📟 BJT 물리 & 특성 시뮬레이터</h2>", unsafe_allow_html=True)
st.markdown("<hr style='margin:4px 0 10px 0'>", unsafe_allow_html=True)

stat_col, main_col = st.columns([0.32, 0.68])

with stat_col:
    st.markdown(f"""
    <div style='background:#f8f9fa; border-radius:12px; padding:16px 18px; border:1px solid #e0e0e0; margin-bottom:12px'>
        <div style='font-size:0.78rem; color:#888; margin-bottom:4px'>Operating Region</div>
        <div style='font-size:1.7rem; font-weight:800; color:{mode_color}; line-height:1.2'>{mode}</div>
        <div style='font-size:1.0rem; font-weight:600; color:{mode_color}; margin-bottom:12px'>({mode_en})</div>
        <hr style='margin:8px 0; border-color:#e0e0e0'>
        <div style='display:flex; gap:16px; flex-wrap:wrap'>
            <div>
                <div style='font-size:0.72rem; color:#888'>V_CE</div>
                <div style='font-size:1.25rem; font-weight:700; color:#222'>{V_be - V_bc:.2f} V</div>
            </div>
            <div>
                <div style='font-size:0.72rem; color:#888'>I_C</div>
                <div style='font-size:1.25rem; font-weight:700; color:#222'>{q_ic_mA:.2f} mA</div>
            </div>
            <div>
                <div style='font-size:0.72rem; color:#888'>I_B</div>
                <div style='font-size:1.25rem; font-weight:700; color:#222'>{I_B_A*1e6:.1f} μA</div>
            </div>
            <div>
                <div style='font-size:0.72rem; color:#888'>Q점 V_CEQ</div>
                <div style='font-size:1.25rem; font-weight:700; color:#222'>{q_vce:.2f} V</div>
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
            with st.spinner("분석 중..."):
                try:
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    resp  = model.generate_content(system_instruction)
                    st.markdown(resp.text)
                except Exception as e:
                    st.error(f"오류: {e}")
        else:
            st.error("GEMINI_API_KEY가 Secrets에 없습니다.")

with main_col:
    tab1, tab2 = st.tabs(["🔋 에너지 밴드 다이어그램", "📈 I_C–V_CE 특성 곡선"])

    with tab1:
        fig_band = go.Figure()

        E_g    = 1.12
        phi_bi = 0.7

        x_e = np.linspace(0,   2.8, 60)
        x_b = np.linspace(2.8, 5.2, 50)
        x_c = np.linspace(5.2, 8.0, 60)
        x_all = np.concatenate([x_e, x_b, x_c])

        E_c_E_eq = 2.3
        E_c_B_eq = 1.5
        E_c_C_eq = 1.9
        E_F_eq   = E_c_B_eq - E_g + 0.2

        v_be_c = float(np.clip(V_be, -1.0, 0.7))
        v_bc_c = float(np.clip(V_bc, -4.0, 0.7))

        E_c_E = E_c_E_eq
        E_c_B = E_c_B_eq + v_be_c * 0.70
        E_c_C = E_c_C_eq - v_bc_c * 0.60

        be_barrier = max(0.0, phi_bi - v_be_c)
        bc_barrier = max(0.0, phi_bi - v_bc_c)
        be_peak_h  = min(be_barrier * 0.18, 0.25)
        bc_peak_h  = min(bc_barrier * 0.18, 0.35)

        ec_e = np.full_like(x_e, E_c_E)

        n_b    = len(x_b)
        half_b = n_b // 2
        peak_BE = max(E_c_E, E_c_B) + be_peak_h
        t_l  = np.linspace(0, np.pi, half_b)
        t_r  = np.linspace(0, np.pi, n_b - half_b)
        ec_b = np.concatenate([
            E_c_E + (peak_BE - E_c_E) * (1 - np.cos(t_l)) / 2,
            peak_BE + (E_c_B - peak_BE) * (1 - np.cos(t_r)) / 2
        ])

        n_c    = len(x_c)
        half_c = n_c // 2
        peak_BC = max(E_c_B, E_c_C) + bc_peak_h
        t_l2 = np.linspace(0, np.pi, half_c)
        t_r2 = np.linspace(0, np.pi, n_c - half_c)
        ec_c = np.concatenate([
            E_c_B + (peak_BC - E_c_B) * (1 - np.cos(t_l2)) / 2,
            peak_BC + (E_c_C - peak_BC) * (1 - np.cos(t_r2)) / 2
        ])

        ec_all = np.concatenate([ec_e, ec_b, ec_c])
        ev_all = ec_all - E_g
        ev_c   = ec_c - E_g

        E_F_B_base = E_c_B - E_g + 0.18

        if mode_en == "Cut-off":
            E_F_E_val = E_F_eq
            E_F_B_val = E_F_eq
            E_F_C_val = E_F_eq
        else:
            E_F_E_val = E_F_B_base + v_be_c * 0.75
            E_F_B_val = E_F_B_base
            E_F_C_val = E_F_B_base + v_bc_c * 0.60

        fig_band.add_vrect(x0=0,   x1=2.8, fillcolor="rgba(173,216,230,0.25)", line_width=0)
        fig_band.add_vrect(x0=2.8, x1=5.2, fillcolor="rgba(255,182,193,0.25)", line_width=0)
        fig_band.add_vrect(x0=5.2, x1=8.0, fillcolor="rgba(144,238,144,0.25)", line_width=0)

        fig_band.add_trace(go.Scatter(x=x_all, y=ec_all, mode='lines',
                                       line=dict(color='black', width=2.5), name='E_c'))
        fig_band.add_trace(go.Scatter(x=x_all, y=ev_all, mode='lines',
                                       line=dict(color='black', width=2.5), name='E_v'))

        for xarr, earr, show in [
            (x_e, np.full_like(x_e, E_F_E_val), True),
            (x_b, np.full_like(x_b, E_F_B_val), False),
            (x_c, np.full_like(x_c, E_F_C_val), False)
        ]:
            fig_band.add_trace(go.Scatter(
                x=xarr, y=earr, mode='lines',
                line=dict(color='blue', width=2, dash='dash'),
                name='E_F (준페르미)' if show else None, showlegend=show))

        fig_band.add_annotation(x=8.15, y=ec_c[-1]+0.05, text="<b>E_C</b>",
                                 showarrow=False, font=dict(size=12, color='black'))
        fig_band.add_annotation(x=8.15, y=ev_c[-1]-0.05, text="<b>E_V</b>",
                                 showarrow=False, font=dict(size=12, color='black'))

        for x_pos, ef_val in [(1.4, E_F_E_val), (4.0, E_F_B_val), (6.6, E_F_C_val)]:
            fig_band.add_annotation(x=x_pos, y=ef_val+0.12, text="<b>E_F</b>",
                                     showarrow=False, font=dict(size=10, color='blue'))

        e_lbl = "EMITTER (N⁺)" if bjt_type=="NPN" else "EMITTER (P⁺)"
        b_lbl = "BASE (P)"     if bjt_type=="NPN" else "BASE (N)"
        c_lbl = "COLLECTOR (N)"if bjt_type=="NPN" else "COLLECTOR (P)"

        fig_band.add_annotation(x=1.4, y=ec_e[0]+0.55, text=f"<b>{e_lbl}</b>",
                                 showarrow=False, font=dict(size=11, color='#1565C0'))
        fig_band.add_annotation(x=4.0, y=E_c_B+0.55, text=f"<b>{b_lbl}</b>",
                                 showarrow=False, font=dict(size=11, color='#B71C1C'))
        fig_band.add_annotation(x=6.6, y=ec_c[-1]+0.55, text=f"<b>{c_lbl}</b>",
                                 showarrow=False, font=dict(size=11, color='#1B5E20'))

        np.random.seed(7)
        if bjt_type == "NPN":
            fig_band.add_trace(go.Scatter(
                x=np.random.uniform(0.2, 2.6, 16),
                y=ec_e[0] + np.random.uniform(0.05, 0.22, 16),
                mode='markers', marker=dict(color='#1565C0', size=9,
                line=dict(color='#0D47A1', width=1.5)), name='전자 (e⁻)'))
            fig_band.add_trace(go.Scatter(
                x=np.random.uniform(3.0, 5.0, 10),
                y=(E_c_B - E_g) + np.random.uniform(0.02, 0.18, 10),
                mode='markers', marker=dict(color='#C62828', size=10,
                line=dict(color='#7B1818', width=1.5)), name='정공 (h⁺)'))
            fig_band.add_trace(go.Scatter(
                x=np.random.uniform(5.4, 7.8, 12),
                y=ec_c[-1] + np.random.uniform(0.05, 0.22, 12),
                mode='markers', marker=dict(color='#1565C0', size=9,
                line=dict(color='#0D47A1', width=1.5)), showlegend=False))
        else:
            fig_band.add_trace(go.Scatter(
                x=np.random.uniform(0.2, 2.6, 16),
                y=(ec_e[0] - E_g) + np.random.uniform(0.02, 0.18, 16),
                mode='markers', marker=dict(color='#C62828', size=10,
                line=dict(color='#7B1818', width=1.5)), name='정공 (h⁺)'))
            fig_band.add_trace(go.Scatter(
                x=np.random.uniform(3.0, 5.0, 10),
                y=E_c_B + np.random.uniform(0.05, 0.22, 10),
                mode='markers', marker=dict(color='#1565C0', size=9,
                line=dict(color='#0D47A1', width=1.5)), name='전자 (e⁻)'))
            fig_band.add_trace(go.Scatter(
                x=np.random.uniform(5.4, 7.8, 12),
                y=(ec_c[-1] - E_g) + np.random.uniform(0.02, 0.18, 12),
                mode='markers', marker=dict(color='#C62828', size=10,
                line=dict(color='#7B1818', width=1.5)), showlegend=False))

        if mode_en == "Forward Active":
            fig_band.add_annotation(x=2.8, y=peak_BE+0.22, text="<b>↓BE 장벽</b>",
                                     showarrow=False, font=dict(color='#E65100', size=10))
            fig_band.add_annotation(x=5.2, y=peak_BC+0.22, text="<b>↑BC 장벽</b>",
                                     showarrow=False, font=dict(color='#1A237E', size=10))
            fig_band.add_annotation(x=4.0, y=E_c_B+0.85, text="① 확산 → ② 표류 → 컬렉터",
                                     showarrow=False, font=dict(color='#FF6F00', size=10))
        elif mode_en == "Saturation":
            fig_band.add_annotation(x=4.0, y=E_c_B+0.85, text="⚡ 양쪽 장벽↓ → 닫힌 스위치",
                                     showarrow=False, font=dict(color='purple', size=10))
        else:
            fig_band.add_annotation(x=4.0, y=E_c_B+0.85, text="⛔ 양쪽 장벽↑ → 개방 스위치",
                                     showarrow=False, font=dict(color='gray', size=10))

        fig_band.add_vline(x=2.8, line=dict(color='gray', width=1, dash='dot'))
        fig_band.add_vline(x=5.2, line=dict(color='gray', width=1, dash='dot'))

        y_bot = min(ev_all.min(), E_F_C_val, E_F_E_val) - 0.4
        y_top = max(ec_all.max(), E_F_E_val) + 0.8

        fig_band.update_layout(
            xaxis=dict(visible=False, range=[-0.2, 8.6]),
            yaxis=dict(visible=False, range=[y_bot, y_top]),
            height=360, margin=dict(l=10, r=10, t=20, b=10),
            showlegend=True,
            legend=dict(x=0.01, y=0.02, bgcolor='rgba(255,255,255,0.85)',
                        bordercolor='lightgray', borderwidth=1,
                        font=dict(size=10), orientation='h'),
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
                x=[sign * v for v in v_arr],
                y=[sign * ic for ic in ic_curve],
                mode='lines', line=dict(color=color, width=2.2), showlegend=False))

            ic_end = sign * ic_sat * (1 + early_k * v_max)
            fig_iv.add_annotation(
                x=sign * v_max + sign * 0.1, y=ic_end,
                text=f"I_B={ib_uA}μA", showarrow=False,
                font=dict(size=9, color='gray'),
                xanchor='left' if bjt_type=="NPN" else 'right')

        sat_ic_mag = (V_CC / R_C) * 1000
        fig_iv.add_trace(go.Scatter(
            x=[0.0, sign * V_CC], y=[sign * sat_ic_mag, 0.0],
            mode='lines', line=dict(color='black', width=2.8),
            name='직류 부하선'))

        fig_iv.add_annotation(x=sign*0.15, y=sign*(sat_ic_mag+0.3), text="<b>포화점</b>",
                               showarrow=True, ax=sign*0.6, ay=sign*(sat_ic_mag-0.5),
                               arrowhead=2, arrowcolor='black', font=dict(size=11))
        fig_iv.add_annotation(x=sign*(V_CC-0.1), y=sign*0.4, text="<b>차단점</b>",
                               showarrow=True, ax=sign*(V_CC-0.8), ay=sign*1.0,
                               arrowhead=2, arrowcolor='black', font=dict(size=11))
        fig_iv.add_vline(x=sign*0.2, line=dict(color='purple', width=1.2, dash='dot'))
        fig_iv.add_annotation(x=sign*0.22, y=sign*sat_ic_mag*0.55, text="V_CE,sat",
                               showarrow=False, font=dict(size=9, color='purple'), textangle=-90)

        q_x, q_y = sign * q_vce, sign * q_ic_mA
        fig_iv.add_trace(go.Scatter(
            x=[q_x], y=[q_y], mode='markers',
            marker=dict(color='red', size=14, symbol='circle',
                        line=dict(color='white', width=2)), name="Q점"))
        fig_iv.add_annotation(x=q_x, y=q_y + sign*0.5,
                               text=f"<b>Q ({q_x:.2f}V, {q_y:.2f}mA)</b>",
                               showarrow=False, font=dict(color='red', size=11))
        fig_iv.add_shape(type='line', x0=q_x, x1=q_x, y0=0, y1=q_y,
                         line=dict(color='red', width=1, dash='dash'))
        fig_iv.add_shape(type='line', x0=0, x1=q_x, y0=q_y, y1=q_y,
                         line=dict(color='red', width=1, dash='dash'))
        fig_iv.add_annotation(x=sign*(-0.08), y=q_y, text="I_CQ",
                               showarrow=False, font=dict(size=9, color='red'),
                               xanchor='right' if bjt_type=="NPN" else 'left')
        fig_iv.add_annotation(x=q_x, y=sign*(-0.28), text="V_CEQ",
                               showarrow=False, font=dict(size=9, color='red'))

        x_range = [-0.15, V_CC+1.3] if bjt_type=="NPN" else [-(V_CC+1.3), 0.15]
        y_range = [-0.4, sat_ic_mag+1.5] if bjt_type=="NPN" else [-(sat_ic_mag+1.5), 0.4]

        fig_iv.update_layout(
            xaxis_title="V_CE [V]", yaxis_title="I_C [mA]",
            xaxis=dict(range=x_range, showgrid=True, gridcolor='#EEEEEE',
                       zeroline=True, zerolinecolor='black', zerolinewidth=1.5),
            yaxis=dict(range=y_range, showgrid=True, gridcolor='#EEEEEE',
                       zeroline=True, zerolinecolor='black', zerolinewidth=1.5),
            height=360, margin=dict(l=10, r=10, t=20, b=10),
            showlegend=True,
            legend=dict(x=0.55 if bjt_type=="NPN" else 0.01,
                        y=0.98 if bjt_type=="NPN" else 0.15,
                        bgcolor='rgba(255,255,255,0.85)',
                        bordercolor='lightgray', borderwidth=1, font=dict(size=10)),
            plot_bgcolor='white'
        )
        st.plotly_chart(fig_iv, use_container_width=True)