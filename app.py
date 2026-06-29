import streamlit as st
import plotly.graph_objects as go
import numpy as np

st.set_page_config(layout="wide")
st.title("📟 AI 반도체 소자 직관 보조 툴: BJT 전자/물리 구조 매퍼")

if "GEMINI_API_KEY" in st.secrets:
    import google.generativeai as genai
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.sidebar.warning("🔑 Gemini API 키가 Secrets에 등록되지 않아 AI 인사이트 기능이 제한됩니다.")

st.sidebar.header("🎛️ BJT 소자 및 바이어스 조절")
bjt_type = st.sidebar.radio("소자 타입 선택", ["NPN", "PNP"])

st.sidebar.markdown("---")
st.sidebar.subheader("🔌 접합 전압 인가 (Bias)")

if "v_be_val" not in st.session_state: st.session_state.v_be_val = 0.75
if "v_bc_val" not in st.session_state: st.session_state.v_bc_val = -2.0

def update_be_slider(): st.session_state.v_be_val = st.session_state.be_num
def update_be_num():    st.session_state.be_num   = st.session_state.v_be_val
def update_bc_slider(): st.session_state.v_bc_val = st.session_state.bc_num
def update_bc_num():    st.session_state.bc_num   = st.session_state.v_bc_val

label_be = "V_BE [V]" if bjt_type == "NPN" else "V_EB [V]"
st.sidebar.number_input(label_be, min_value=-1.0, max_value=1.5, step=0.05,
                        key="be_num", on_change=update_be_slider,
                        value=st.session_state.v_be_val)
V_be = st.sidebar.slider(label_be, min_value=-1.0, max_value=1.5, step=0.05,
                         key="v_be_val", on_change=update_be_num,
                         label_visibility="collapsed")

label_bc = "V_BC [V]" if bjt_type == "NPN" else "V_CB [V]"
st.sidebar.number_input(label_bc, min_value=-5.0, max_value=5.0, step=0.1,
                        key="bc_num", on_change=update_bc_slider,
                        value=st.session_state.v_bc_val)
V_bc = st.sidebar.slider(label_bc, min_value=-5.0, max_value=5.0, step=0.1,
                         key="v_bc_val", on_change=update_bc_num,
                         label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.header("💬 AI에게 질문하기")
user_question = st.sidebar.text_area(
    "궁금한 점을 입력하세요:",
    value="현재 바이어스 상태가 증폭기로서 왜 적합한지 밴드 다이어그램 관점에서 설명해줘.",
    height=100)

V_CC  = 5.0
R_C   = 800.0
beta  = 150
V_AF  = 100.0
early_k = 1.0 / V_AF

be_fwd = V_be > 0
bc_fwd = V_bc > 0

if be_fwd and not bc_fwd:
    mode = "순방향 활성 모드 (Forward Active)"
elif be_fwd and bc_fwd:
    mode = "포화 모드 (Saturation)"
else:
    mode = "차단 모드 (Cut-off)"

R_B_eff = 30000.0

if be_fwd:
    I_B_A = max(0.0, V_be / R_B_eff)
else:
    I_B_A = 0.0

if mode == "순방향 활성 모드 (Forward Active)":
    I_C_ideal = beta * I_B_A
    I_C_max   = (V_CC - 0.2) / R_C
    q_ic_A    = min(I_C_ideal, I_C_max)
    q_ic_A    = max(0.0, q_ic_A)
    q_vce     = max(0.2, V_CC - q_ic_A * R_C)
elif mode == "포화 모드 (Saturation)":
    q_vce  = 0.2
    q_ic_A = (V_CC - q_vce) / R_C
else:
    q_vce  = V_CC
    q_ic_A = 0.0

q_ic_mA = q_ic_A * 1000

col1, col2 = st.columns([1.1, 0.9])

with col1:
    st.subheader("📊 실시간 BJT 물리 상태 시각화")
    st.info(
        f"**판정 모드:** {bjt_type} {mode}  \n"
        f"**V_CE = {V_be - V_bc:.2f}V**   "
        f"**I_B = {I_B_A*1e6:.2f} μA**   "
        f"**I_C = {q_ic_mA:.2f} mA**   "
        f"**Q점: ({q_vce:.2f} V, {q_ic_mA:.2f} mA)**"
    )

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

    E_F_eq = E_c_B_eq - E_g + 0.2

    v_be_c = float(np.clip(V_be, -1.0,  0.7))
    v_bc_c = float(np.clip(V_bc, -4.0,  0.7))

    E_c_E = E_c_E_eq
    E_c_B = E_c_B_eq + v_be_c * 0.70
    E_c_C = E_c_C_eq - v_bc_c * 0.60

    be_barrier = max(0.0, phi_bi - v_be_c)
    bc_barrier = max(0.0, phi_bi - v_bc_c)
    be_peak_h  = min(be_barrier * 0.18, 0.25)
    bc_peak_h  = min(bc_barrier * 0.18, 0.35)

    ec_e = np.full_like(x_e, E_c_E)

    n_b = len(x_b)
    half_b = n_b // 2
    peak_BE = max(E_c_E, E_c_B) + be_peak_h
    t_left  = np.linspace(0, np.pi, half_b)
    ec_b_left  = E_c_E + (peak_BE - E_c_E) * (1 - np.cos(t_left)) / 2
    t_right = np.linspace(0, np.pi, n_b - half_b)
    ec_b_right = peak_BE + (E_c_B - peak_BE) * (1 - np.cos(t_right)) / 2
    ec_b = np.concatenate([ec_b_left, ec_b_right])

    n_c = len(x_c)
    half_c = n_c // 2
    peak_BC = max(E_c_B, E_c_C) + bc_peak_h
    t_left2  = np.linspace(0, np.pi, half_c)
    ec_c_left  = E_c_B + (peak_BC - E_c_B) * (1 - np.cos(t_left2)) / 2
    t_right2 = np.linspace(0, np.pi, n_c - half_c)
    ec_c_right = peak_BC + (E_c_C - peak_BC) * (1 - np.cos(t_right2)) / 2
    ec_c = np.concatenate([ec_c_left, ec_c_right])

    ec_all = np.concatenate([ec_e, ec_b, ec_c])
    ev_all = ec_all - E_g
    ev_e = ec_e - E_g
    ev_b = ec_b - E_g
    ev_c = ec_c - E_g

    E_F_B_base = E_c_B - E_g + 0.18

    if mode == "차단 모드 (Cut-off)":
        E_F_E_val = E_F_eq
        E_F_B_val = E_F_eq
        E_F_C_val = E_F_eq
    elif mode == "순방향 활성 모드 (Forward Active)":
        E_F_E_val = E_F_B_base + v_be_c * 0.75
        E_F_B_val = E_F_B_base
        E_F_C_val = E_F_B_base + v_bc_c * 0.60
    else:
        E_F_E_val = E_F_B_base + v_be_c * 0.75
        E_F_B_val = E_F_B_base
        E_F_C_val = E_F_B_base + v_bc_c * 0.60

    ef_e = np.full_like(x_e, E_F_E_val)
    ef_b = np.full_like(x_b, E_F_B_val)
    ef_c = np.full_like(x_c, E_F_C_val)

    fig_band.add_vrect(x0=0,   x1=2.8, fillcolor="rgba(173,216,230,0.25)", line_width=0)
    fig_band.add_vrect(x0=2.8, x1=5.2, fillcolor="rgba(255,182,193,0.25)", line_width=0)
    fig_band.add_vrect(x0=5.2, x1=8.0, fillcolor="rgba(144,238,144,0.25)", line_width=0)

    fig_band.add_trace(go.Scatter(
        x=x_all, y=ec_all, mode='lines',
        line=dict(color='black', width=2.5), name='E_c'))
    fig_band.add_trace(go.Scatter(
        x=x_all, y=ev_all, mode='lines',
        line=dict(color='black', width=2.5), name='E_v'))

    for xarr, earr, show in [(x_e, ef_e, True), (x_b, ef_b, False), (x_c, ef_c, False)]:
        fig_band.add_trace(go.Scatter(
            x=xarr, y=earr, mode='lines',
            line=dict(color='blue', width=2, dash='dash'),
            name='E_F (준페르미)' if show else None,
            showlegend=show))

    fig_band.add_annotation(x=8.15, y=ec_c[-1]+0.05, text="<b>E_C</b>",
                             showarrow=False, font=dict(size=12, color='black'))
    fig_band.add_annotation(x=8.15, y=ev_c[-1]-0.05, text="<b>E_V</b>",
                             showarrow=False, font=dict(size=12, color='black'))

    for x_pos, ef_val in [(1.4, E_F_E_val), (4.0, E_F_B_val), (6.6, E_F_C_val)]:
        fig_band.add_annotation(x=x_pos, y=ef_val+0.12, text="<b>E_F</b>",
                                 showarrow=False, font=dict(size=10, color='blue'))

    e_label = "EMITTER (N⁺)" if bjt_type=="NPN" else "EMITTER (P⁺)"
    b_label = "BASE (P)"     if bjt_type=="NPN" else "BASE (N)"
    c_label = "COLLECTOR (N)"if bjt_type=="NPN" else "COLLECTOR (P)"

    fig_band.add_annotation(x=1.4, y=ec_e[0]+0.55, text=f"<b>{e_label}</b>",
                             showarrow=False, font=dict(size=11, color='#1565C0'))
    fig_band.add_annotation(x=4.0, y=E_c_B+0.55,   text=f"<b>{b_label}</b>",
                             showarrow=False, font=dict(size=11, color='#B71C1C'))
    fig_band.add_annotation(x=6.6, y=ec_c[-1]+0.55, text=f"<b>{c_label}</b>",
                             showarrow=False, font=dict(size=11, color='#1B5E20'))

    np.random.seed(7)

    if bjt_type == "NPN":
        fig_band.add_trace(go.Scatter(
            x=np.random.uniform(0.2, 2.6, 16),
            y=ec_e[0] + np.random.uniform(0.05, 0.22, 16),
            mode='markers', marker=dict(color='#1565C0', size=9,
            line=dict(color='#0D47A1', width=1.5)), name='전자 (e⁻)'))

        base_ev = E_c_B - E_g
        fig_band.add_trace(go.Scatter(
            x=np.random.uniform(3.0, 5.0, 10),
            y=base_ev + np.random.uniform(0.02, 0.18, 10),
            mode='markers', marker=dict(color='#C62828', size=10,
            line=dict(color='#7B1818', width=1.5)), name='정공 (h⁺)'))

        fig_band.add_trace(go.Scatter(
            x=np.random.uniform(5.4, 7.8, 12),
            y=ec_c[-1] + np.random.uniform(0.05, 0.22, 12),
            mode='markers', marker=dict(color='#1565C0', size=9,
            line=dict(color='#0D47A1', width=1.5)), showlegend=False))

        if mode == "순방향 활성 모드 (Forward Active)":
            fig_band.add_annotation(x=2.8, y=peak_BE+0.22, text="<b>↓BE 장벽</b>",
                                     showarrow=False, font=dict(color='#E65100', size=10))
            fig_band.add_annotation(x=5.2, y=peak_BC+0.22, text="<b>↑BC 장벽</b>",
                                     showarrow=False, font=dict(color='#1A237E', size=10))
            fig_band.add_annotation(x=4.0, y=E_c_B+0.85,
                                     text="① 확산 → ② 표류 → 컬렉터",
                                     showarrow=False, font=dict(color='#FF6F00', size=10))
        elif mode == "포화 모드 (Saturation)":
            fig_band.add_annotation(x=4.0, y=E_c_B+0.85,
                                     text="⚡ 양쪽 장벽↓ → 닫힌 스위치",
                                     showarrow=False, font=dict(color='purple', size=10))
        else:
            fig_band.add_annotation(x=4.0, y=E_c_B+0.85,
                                     text="⛔ 양쪽 장벽↑ → 개방 스위치 (전류 없음)",
                                     showarrow=False, font=dict(color='gray', size=10))
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

        if mode == "순방향 활성 모드 (Forward Active)":
            fig_band.add_annotation(x=4.0, y=E_c_B+0.85,
                                     text="← 정공 확산 / ← 정공 표류",
                                     showarrow=False, font=dict(color='#FF6F00', size=10))
        elif mode == "포화 모드 (Saturation)":
            fig_band.add_annotation(x=4.0, y=E_c_B+0.85,
                                     text="⚡ 양쪽 장벽↓ → 닫힌 스위치",
                                     showarrow=False, font=dict(color='purple', size=10))
        else:
            fig_band.add_annotation(x=4.0, y=E_c_B+0.85,
                                     text="⛔ 양쪽 장벽↑ → 개방 스위치",
                                     showarrow=False, font=dict(color='gray', size=10))

    fig_band.add_vline(x=2.8, line=dict(color='gray', width=1, dash='dot'))
    fig_band.add_vline(x=5.2, line=dict(color='gray', width=1, dash='dot'))

    y_bot = min(ev_all.min(), E_F_C_val, E_F_E_val) - 0.4
    y_top = max(ec_all.max(), E_F_E_val) + 0.8

    fig_band.update_layout(
        title="<b>🔋 에너지 밴드 다이어그램 (6주차 교안 기준)</b>",
        xaxis=dict(visible=False, range=[-0.2, 8.6]),
        yaxis=dict(visible=False, range=[y_bot, y_top]),
        height=360,
        margin=dict(l=10, r=10, t=45, b=10),
        showlegend=True,
        legend=dict(x=0.01, y=0.02, bgcolor='rgba(255,255,255,0.85)',
                    bordercolor='lightgray', borderwidth=1,
                    font=dict(size=10), orientation='h'),
        plot_bgcolor='white'
    )
    st.plotly_chart(fig_band, use_container_width=True)

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

        ic_curve = []
        for v in v_arr:
            sat_factor   = np.tanh(v / 0.12)
            early_factor = 1 + early_k * v
            ic = ic_sat * sat_factor * early_factor
            ic_curve.append(max(0.0, ic))

        x_plot = [sign * v  for v in v_arr]
        y_plot = [sign * ic for ic in ic_curve]

        fig_iv.add_trace(go.Scatter(
            x=x_plot, y=y_plot, mode='lines',
            line=dict(color=color, width=2.2), showlegend=False))

        ic_end  = sign * ic_sat * (1 + early_k * v_max)
        label_x = sign * v_max + sign * 0.1
        fig_iv.add_annotation(
            x=label_x, y=ic_end,
            text=f"I_B={ib_uA}μA",
            showarrow=False, font=dict(size=9, color='gray'),
            xanchor='left' if bjt_type=="NPN" else 'right')

    sat_ic_mag = (V_CC / R_C) * 1000
    v_load = np.array([0.0, sign * V_CC])
    i_load = np.array([sign * sat_ic_mag, 0.0])

    fig_iv.add_trace(go.Scatter(
        x=v_load, y=i_load, mode='lines',
        line=dict(color='black', width=2.8),
        name='직류 부하선', showlegend=True))

    fig_iv.add_annotation(x=sign*0.15, y=sign*(sat_ic_mag+0.3),
                           text="<b>포화점</b>", showarrow=True,
                           ax=sign*0.6, ay=sign*(sat_ic_mag-0.5),
                           arrowhead=2, arrowcolor='black', font=dict(size=11))
    fig_iv.add_annotation(x=sign*(V_CC-0.1), y=sign*0.4,
                           text="<b>차단점</b>", showarrow=True,
                           ax=sign*(V_CC-0.8), ay=sign*1.0,
                           arrowhead=2, arrowcolor='black', font=dict(size=11))

    fig_iv.add_vline(x=sign*0.2, line=dict(color='purple', width=1.2, dash='dot'))
    fig_iv.add_annotation(x=sign*0.22, y=sign*sat_ic_mag*0.55,
                           text="V_CE,sat", showarrow=False,
                           font=dict(size=9, color='purple'), textangle=-90)

    q_x = sign * q_vce
    q_y = sign * q_ic_mA

    fig_iv.add_trace(go.Scatter(
        x=[q_x], y=[q_y], mode='markers',
        marker=dict(color='red', size=14, symbol='circle',
                    line=dict(color='white', width=2)),
        name="Q점"))

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
        title="<b>📈 I_C–V_CE 특성 곡선 & 직류 부하선 (7주차 교안 기준)</b>",
        xaxis_title="V_CE [V]",
        yaxis_title="I_C [mA]",
        xaxis=dict(range=x_range, showgrid=True, gridcolor='#EEEEEE',
                   zeroline=True, zerolinecolor='black', zerolinewidth=1.5),
        yaxis=dict(range=y_range, showgrid=True, gridcolor='#EEEEEE',
                   zeroline=True, zerolinecolor='black', zerolinewidth=1.5),
        height=360,
        margin=dict(l=10, r=10, t=45, b=10),
        showlegend=True,
        legend=dict(x=0.55 if bjt_type=="NPN" else 0.01,
                    y=0.98 if bjt_type=="NPN" else 0.15,
                    bgcolor='rgba(255,255,255,0.85)',
                    bordercolor='lightgray', borderwidth=1,
                    font=dict(size=10)),
        plot_bgcolor='white'
    )
    st.plotly_chart(fig_iv, use_container_width=True)

with col2:
    st.subheader("🤖 AI 반도체 엔지니어 아키텍트 분석")
    st.caption(f"상태: {bjt_type} / {mode}")

    system_instruction = f"""
당신은 반도체 소자 물리학 및 증폭 회로 설계 전문가입니다.
[규칙] 인삿말 없이 바로 수치 분석부터 시작하세요.

현재 설정 조건:
- BJT 종류: {bjt_type}
- V_BE = {V_be:.2f}V, V_BC = {V_bc:.2f}V
- 판정 모드: {mode}
- I_B = {I_B_A*1e6:.2f} μA, I_C = {q_ic_mA:.2f} mA, Q점: V_CE = {q_vce:.2f}V

[미션]
6주차 에너지 밴드 교안(열적 평형, 순방향 장벽 하강, 캐리어 확산/표류)과
7주차 바이어스 교안(직류 부하선, Q점 설계 마진, 왜곡 방지)을 연결하여
사용자 질문에 수치적/물리적으로 명확한 한국어 마크다운 답변을 하세요.

사용자 질문: "{user_question}"
"""

    if st.button("🚀 Gemini 교수님께 분석 요청"):
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