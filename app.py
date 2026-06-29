import streamlit as st
import plotly.graph_objects as go
import numpy as np
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="BJT 시뮬레이터")

st.markdown("""
<style>
    [data-testid="stSidebar"] { min-width: 250px; max-width: 250px; }
    [data-testid="stSidebar"] .element-container,
    [data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p { margin-bottom: 0.2rem !important; }
    [data-testid="stSidebar"] h3 { font-size: 0.95rem !important; margin-bottom: 5px !important; margin-top: 5px !important; }
    [data-testid="stSidebar"] hr { margin: 6px 0 !important; }
    [data-testid="stSidebar"] .stSlider { margin-top: -15px !important; margin-bottom: -5px !important; }
    [data-testid="stSidebar"] .stNumberInput div[data-baseweb="input"],
    [data-testid="stSidebar"] .stNumberInput div[data-baseweb="base-input"] { background-color: #ffffff !important; }
    [data-testid="stSidebar"] .stNumberInput input {
        height: 26px !important; padding: 1px 4px !important;
        font-size: 0.75rem !important; color: #2c3e50 !important; background-color: #ffffff !important;
    }
    [data-testid="stSidebar"] .stTextArea textarea { font-size: 0.78rem !important; padding: 5px !important; color: #2c3e50 !important; }
    div[data-testid="stRadio"] > div { flex-direction: row !important; gap: 4px !important; }

    .stat-card {
        background: #ffffff; border-radius: 12px; padding: 14px;
        border: 1px solid #eaeaea; box-shadow: 0px 4px 10px rgba(0,0,0,0.04); height: 100%;
    }
    .stat-title { font-size: 0.75rem; color: #7f8c8d; font-weight: 600; text-transform: uppercase; margin-bottom: 2px; }
    .stat-label { font-size: 0.68rem; color: #95a5a6; font-weight: 600; }
    .stat-value { font-size: 1.05rem; font-weight: 700; color: #2c3e50; }

    /* 탭 간격 줄이기 */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] { padding: 4px 12px; font-size: 0.82rem; }

    /* 플롯 여백 최소화 */
    .stPlotlyChart { margin: 0 !important; padding: 0 !important; }

    /* 전체 페이지 상단 여백 */
    .block-container { padding-top: 1rem !important; padding-bottom: 0.5rem !important; }
</style>
""", unsafe_allow_html=True)

if "GEMINI_API_KEY" in st.secrets:
    import google.generativeai as genai
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# ── 사이드바
with st.sidebar:
    st.markdown("### 🔌 BJT 시뮬레이터")
    bjt_type = st.radio("소자 타입", ["NPN", "PNP"], horizontal=True, label_visibility="collapsed")
    st.markdown("---")
    st.markdown("<span style='font-size:0.8rem; font-weight:700; color:#1e293b;'>접합 전압 인가</span>", unsafe_allow_html=True)

    if "v_be_val" not in st.session_state: st.session_state.v_be_val = 0.75
    if "v_bc_val" not in st.session_state: st.session_state.v_bc_val = -2.0

    def update_be_slider(): st.session_state.v_be_val = st.session_state.be_num
    def update_be_num():    st.session_state.be_num   = st.session_state.v_be_val
    def update_bc_slider(): st.session_state.v_bc_val = st.session_state.bc_num
    def update_bc_num():    st.session_state.bc_num   = st.session_state.v_bc_val

    label_be = "V_BE (V)" if bjt_type == "NPN" else "V_EB (V)"
    st.markdown(f"<span style='font-size:0.75rem;font-weight:700;color:#2c3e50;'>{label_be}</span>", unsafe_allow_html=True)
    V_be = st.slider(label_be, min_value=-1.0, max_value=1.0, step=0.05,
                     key="v_be_val", on_change=update_be_num, label_visibility="collapsed")
    st.number_input(label_be, min_value=-1.0, max_value=1.0, step=0.05,
                    key="be_num", on_change=update_be_slider,
                    value=st.session_state.v_be_val, label_visibility="collapsed")

    label_bc = "V_BC (V)" if bjt_type == "NPN" else "V_CB (V)"
    st.markdown(f"<span style='font-size:0.75rem;font-weight:700;color:#2c3e50;margin-top:2px;display:block;'>{label_bc}</span>", unsafe_allow_html=True)
    V_bc = st.slider(label_bc, min_value=-5.0, max_value=5.0, step=0.1,
                     key="v_bc_val", on_change=update_bc_num, label_visibility="collapsed")
    st.number_input(label_bc, min_value=-5.0, max_value=5.0, step=0.1,
                    key="bc_num", on_change=update_bc_slider,
                    value=st.session_state.v_bc_val, label_visibility="collapsed")

    st.markdown("---")
    st.markdown("<span style='font-size:0.8rem;font-weight:700;color:#1e293b;'>💬 AI 질문</span>", unsafe_allow_html=True)
    user_question = st.text_area("질문 입력", height=60, label_visibility="collapsed",
                                 value="현재 바이어스 상태가 증폭기로서 왜 적합한지 밴드 다이어그램 관점에서 설명해줘.",
                                 placeholder="e.g. 현재 바이어스 상태를 물리적으로 설명해줘.")
    ai_btn = st.button("🚀 Gemini 분석 요청", use_container_width=True)

# ── 물리량 계산
V_CC    = 5.0; R_C = 800.0; beta = 150; V_AF = 100.0
early_k = 1.0 / V_AF
be_fwd  = V_be > 0
bc_fwd  = V_bc > 0

if be_fwd and not bc_fwd:
    mode, mode_en, mode_color, anim_key = "순방향 활성 영역", "Forward Active", "#f39c12", "forward_active"
    mode_desc = "B-E 순방향 + B-C 역방향 → 전자 확산 후 포류 → 증폭기 동작"
elif be_fwd and bc_fwd:
    mode, mode_en, mode_color, anim_key = "포화 영역", "Saturation", "#28a745", "saturation"
    mode_desc = "양쪽 접합 순방향 → 장벽 소실 → 캐리어 범람 → V_CE≈0.2V"
elif not be_fwd and bc_fwd:
    mode, mode_en, mode_color, anim_key = "역방향 활성 영역", "Reverse Active", "#9b59b6", "reverse_active"
    mode_desc = "B-E 역방향 + B-C 순방향 → 흐름 역전 → 낮은 β"
else:
    mode, mode_en, mode_color, anim_key = "차단 영역", "Cutoff", "#dc3545", "cutoff"
    mode_desc = "양쪽 접합 역방향 → 장벽 최대 → 전류 차단 → OFF 상태"

mode_full = f"{mode} ({mode_en})"
R_B_eff   = 30000.0
I_B_A     = max(0.0, V_be / R_B_eff) if be_fwd else 0.0

if mode_en == "Forward Active":
    I_C_ideal = beta * I_B_A
    I_C_max   = (V_CC - 0.2) / R_C
    q_ic_A    = max(0.0, min(I_C_ideal, I_C_max))
    q_vce     = max(0.2, V_CC - q_ic_A * R_C)
elif mode_en == "Saturation":
    q_vce = 0.2; q_ic_A = (V_CC - q_vce) / R_C
else:
    q_vce = V_CC; q_ic_A = 0.0

q_ic_mA = q_ic_A * 1000

# ── BJT 구조 SVG (회로 기호 스타일)
def make_bjt_svg(bjt_type, V_be, V_bc):
    is_npn = bjt_type == "NPN"
    vbe_lbl = f"V_BE={V_be:.2f}V" if is_npn else f"V_EB={V_be:.2f}V"
    vbc_lbl = f"V_BC={V_bc:.2f}V" if is_npn else f"V_CB={V_bc:.2f}V"

    # 색상
    e_color = "#4a9eff" if is_npn else "#ff6b6b"
    c_color = "#4a9eff" if is_npn else "#ff6b6b"
    b_color = "#ff6b6b" if is_npn else "#4a9eff"

    # NPN: 이미터 화살표 밖으로, PNP: 이미터 화살표 안으로
    # 회로 기호 스타일 BJT
    arrow_e = """
      <!-- 이미터 화살표 (NPN: 밖으로) -->
      <defs>
        <marker id="arrowE" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto">
          <polygon points="0,0 8,4 0,8" fill="#4a9eff"/>
        </marker>
      </defs>
      <line x1="200" y1="110" x2="155" y2="140" stroke="#4a9eff" stroke-width="2.5" marker-end="url(#arrowE)"/>
    """ if is_npn else """
      <!-- 이미터 화살표 (PNP: 안으로) -->
      <defs>
        <marker id="arrowE" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto">
          <polygon points="8,0 0,4 8,8" fill="#ff6b6b"/>
        </marker>
      </defs>
      <line x1="155" y1="140" x2="200" y2="110" stroke="#ff6b6b" stroke-width="2.5" marker-end="url(#arrowE)"/>
    """

    svg = f"""
<svg width="340" height="200" viewBox="0 0 340 200" style="display:block; margin:auto;">
  <style>
    .bjt-label {{ font-family: monospace; font-weight: bold; }}
    .bjt-sub   {{ font-family: monospace; font-size: 10px; fill: #888; }}
    .pin-label {{ font-family: monospace; font-size: 13px; font-weight: bold; }}
  </style>

  <!-- 베이스 수직 막대 -->
  <rect x="195" y="60" width="10" height="80" rx="2"
        fill="{b_color}" opacity="0.9"/>

  <!-- 컬렉터 사선 (위) -->
  <line x1="200" y1="90" x2="255" y2="55" stroke="{c_color}" stroke-width="2.5"/>
  <!-- 이미터 사선 (아래) -->
  {arrow_e}

  <!-- 컬렉터 수직선 -->
  <line x1="255" y1="55" x2="255" y2="20" stroke="{c_color}" stroke-width="2.5"/>
  <!-- 이미터 수직선 -->
  <line x1="155" y1="140" x2="155" y2="175" stroke="{e_color}" stroke-width="2.5"/>

  <!-- 베이스 수평선 -->
  <line x1="115" y1="100" x2="195" y2="100" stroke="{b_color}" stroke-width="2.5"/>

  <!-- 단자 원 -->
  <circle cx="255" cy="18" r="5" fill="{c_color}" opacity="0.9"/>
  <circle cx="155" cy="177" r="5" fill="{e_color}" opacity="0.9"/>
  <circle cx="113" cy="100" r="5" fill="{b_color}" opacity="0.9"/>

  <!-- 단자 라벨 -->
  <text x="262" y="22" class="pin-label" fill="{c_color}">C</text>
  <text x="162" y="192" class="pin-label" fill="{e_color}">E</text>
  <text x="88"  y="104" class="pin-label" fill="{b_color}">B</text>

  <!-- 영역 블록 (반도체 영역 표시) -->
  <!-- Emitter -->
  <rect x="30" y="130" width="70" height="36" rx="5"
        fill="{'#1a3a5c' if is_npn else '#5c1a1a'}"
        stroke="{'#4a9eff' if is_npn else '#ff6b6b'}" stroke-width="1.5"/>
  <text x="65" y="146" text-anchor="middle" class="bjt-label"
        fill="{'#7ec8ff' if is_npn else '#ffaaaa'}" font-size="12">
        {'N⁺' if is_npn else 'P⁺'}</text>
  <text x="65" y="160" text-anchor="middle" class="bjt-sub">Emitter</text>

  <!-- Base -->
  <rect x="108" y="75" width="50" height="36" rx="5"
        fill="{'#4a1a3a' if is_npn else '#1a3a2a'}"
        stroke="{'#ff6b6b' if is_npn else '#4a9eff'}" stroke-width="1.5"/>
  <text x="133" y="91" text-anchor="middle" class="bjt-label"
        fill="{'#ffaaaa' if is_npn else '#7ec8ff'}" font-size="12">
        {'P' if is_npn else 'N'}</text>
  <text x="133" y="105" text-anchor="middle" class="bjt-sub">Base</text>

  <!-- Collector -->
  <rect x="230" y="28" width="70" height="36" rx="5"
        fill="{'#1a3a1a' if is_npn else '#3a2a1a'}"
        stroke="{'#4a9eff' if is_npn else '#ff6b6b'}" stroke-width="1.5"/>
  <text x="265" y="44" text-anchor="middle" class="bjt-label"
        fill="{'#7ec8ff' if is_npn else '#ffaa77'}" font-size="12">
        {'N' if is_npn else 'P'}</text>
  <text x="265" y="58" text-anchor="middle" class="bjt-sub">Collector</text>

  <!-- 전압 라벨 -->
  <text x="170" y="172" text-anchor="middle" font-family="monospace" font-size="9"
        fill="{'#7ac' if is_npn else '#ca7'}">{vbe_lbl}</text>
  <text x="248" y="100" text-anchor="middle" font-family="monospace" font-size="9"
        fill="{'#7ca' if is_npn else '#a7c'}">{vbc_lbl}</text>

  <!-- BJT 타입 라벨 -->
  <text x="310" y="100" text-anchor="middle" font-family="monospace" font-size="14"
        font-weight="bold" fill="#ccc">{bjt_type}</text>
  <text x="310" y="114" text-anchor="middle" font-family="monospace" font-size="10"
        fill="#777">BJT</text>
</svg>"""
    return svg

bjt_svg = make_bjt_svg(bjt_type, V_be, V_bc)

# ── 동작 설명 색상
desc_color_map = {
    "forward_active": "#f39c12", "saturation": "#28a745",
    "reverse_active": "#9b59b6", "cutoff": "#dc3545",
}
desc_color = desc_color_map[anim_key]

# ════════════════════════════════════════════════
# 레이아웃: 상단 3컬럼 (stat | BJT구조+애니 | AI)
# ════════════════════════════════════════════════
st.markdown("<h3 style='margin:0 0 6px 0; font-size:1.1rem;'>📟 BJT 물리 & 특성 시뮬레이터</h3>", unsafe_allow_html=True)

col_stat, col_anim, col_ai = st.columns([0.25, 0.42, 0.33])

# ── 왼쪽: 수치 카드 + 동작 모드
with col_stat:
    st.markdown(f"""
    <div class='stat-card'>
        <div class='stat-title'>Operating Region</div>
        <div style='font-size:1.2rem; font-weight:800; color:{mode_color}; line-height:1.2; margin-bottom:4px;'>
            {mode}
        </div>
        <div style='font-size:0.8rem; color:{mode_color}; margin-bottom:10px;'>({mode_en})</div>
        <div style='display:grid; grid-template-columns:1fr 1fr; gap:8px;'>
            <div>
                <div class='stat-label'>인가전압 |V_CE|</div>
                <div class='stat-value'>{abs(V_be - V_bc):.2f} V</div>
            </div>
            <div>
                <div class='stat-label'>컬렉터전류 I_C</div>
                <div class='stat-value'>{q_ic_mA:.2f} mA</div>
            </div>
            <div>
                <div class='stat-label'>베이스전류 I_B</div>
                <div class='stat-value'>{I_B_A*1e6:.1f} μA</div>
            </div>
            <div>
                <div class='stat-label'>Q점 V_CEQ</div>
                <div class='stat-value'>{q_vce:.2f} V</div>
            </div>
        </div>
        <div style='margin-top:10px; padding:8px 10px; background:#f8f9fa;
                    border-left:3px solid {desc_color}; border-radius:4px;
                    font-size:0.74rem; color:{desc_color}; line-height:1.45;'>
            {mode_desc}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── 가운데: BJT 구조 그림 + 캐리어 애니메이션
with col_anim:
    canvas_html = f"""
<div style="display:flex; flex-direction:column; align-items:center; gap:6px;">

  <!-- BJT 구조 그림 (회로 기호 스타일) -->
  <div style="background:#1e1e1e; border-radius:8px; padding:4px 8px; width:100%;">
    {bjt_svg}
  </div>

  <!-- 캐리어 거동 애니메이션 -->
  <canvas id="bjtCanvas" width="420" height="145"
          style="background:#2d2d2d; border-radius:8px; display:block;
                 box-shadow:0 4px 10px rgba(0,0,0,0.15); width:100%;"></canvas>

  <!-- 범례 -->
  <p style="color:#aaa; font-size:0.78rem; margin:0; font-family:sans-serif; text-align:center;">
      <span style="color:#00E6FF; font-weight:bold;">● 전자 (Electron)</span>
      &nbsp;&nbsp;&nbsp;
      <span style="color:#FF7043; font-weight:bold;">● 정공 (Hole)</span>
  </p>
</div>

<script>
(function() {{
    const canvas = document.getElementById('bjtCanvas');
    const ctx    = canvas.getContext('2d');
    const MODE     = '{anim_key}';
    const BJT_TYPE = '{bjt_type}';
    const W = canvas.width, H = canvas.height;

    const N_e = 35, N_h = 35;
    let particles = [];

    for (let i = 0; i < N_e; i++) {{
        particles.push({{ x: Math.random()*W, y: 35+Math.random()*75, r:3.5, type:'electron', dir:Math.random()<0.5?1:-1 }});
    }}
    for (let i = 0; i < N_h; i++) {{
        particles.push({{ x: Math.random()*W, y: 35+Math.random()*75, r:3.5, type:'hole', dir:Math.random()<0.5?1:-1 }});
    }}

    function draw() {{
        ctx.clearRect(0, 0, W, H);

        // 영역 배경
        ctx.fillStyle='rgba(74,158,255,0.08)';  ctx.fillRect(0,0,130,H);
        ctx.fillStyle='rgba(255,107,107,0.08)'; ctx.fillRect(130,0,160,H);
        ctx.fillStyle='rgba(74,158,255,0.08)';  ctx.fillRect(290,0,W-290,H);

        // 접합면
        [130, 290].forEach(x => {{
            ctx.strokeStyle='#555'; ctx.lineWidth=1.5;
            ctx.setLineDash([4,4]);
            ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,H); ctx.stroke();
            ctx.setLineDash([]);
        }});

        // 영역 라벨
        ctx.font='11px monospace';
        const labels = BJT_TYPE==='NPN'
            ? ['Emitter (N+)','Base (P)','Collector (N)']
            : ['Emitter (P+)','Base (N)','Collector (P)'];
        ctx.fillStyle='#7ec8ff'; ctx.fillText(labels[0], 8, 20);
        ctx.fillStyle='#ffaaaa'; ctx.fillText(labels[1], 138, 20);
        ctx.fillStyle='#7ec8ff'; ctx.fillText(labels[2], 298, 20);

        // 입자
        particles.forEach(p => {{
            ctx.fillStyle   = p.type==='electron' ? '#00E6FF' : '#FF7043';
            ctx.shadowBlur  = 5; ctx.shadowColor = ctx.fillStyle;
            ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI*2); ctx.fill();
            ctx.shadowBlur  = 0;

            let vx=0, scatterX=0.2;

            if (MODE==='forward_active') {{
                if (BJT_TYPE==='NPN') {{
                    if (p.type==='electron') {{ vx=3.2; if(p.x>W) p.x=0; }}
                    else                     {{ vx=-1.2; if(p.x<0) p.x=290; }}
                }} else {{
                    if (p.type==='hole')     {{ vx=3.2; if(p.x>W) p.x=0; }}
                    else                     {{ vx=-1.2; if(p.x<0) p.x=290; }}
                }}
            }} else if (MODE==='saturation') {{
                if (BJT_TYPE==='NPN') {{
                    if (p.type==='electron') {{
                        vx=p.dir*3.0;
                        if(vx>0 && p.x>W) p.x=0;
                        if(vx<0 && p.x<0) p.x=W;
                    }} else {{
                        vx=p.dir*1.5;
                        if(vx>0 && p.x>W) p.x=210;
                        if(vx<0 && p.x<0) p.x=210;
                    }}
                }} else {{
                    if (p.type==='hole') {{
                        vx=p.dir*3.0;
                        if(vx>0 && p.x>W) p.x=0;
                        if(vx<0 && p.x<0) p.x=W;
                    }} else {{
                        vx=p.dir*1.5;
                        if(vx>0 && p.x>W) p.x=210;
                        if(vx<0 && p.x<0) p.x=210;
                    }}
                }}
            }} else if (MODE==='reverse_active') {{
                if (BJT_TYPE==='NPN') {{
                    if (p.type==='electron') {{ vx=-3.2; if(p.x<0) p.x=W; }}
                    else                     {{ vx=1.2;  if(p.x>W) p.x=130; }}
                }} else {{
                    if (p.type==='hole')     {{ vx=-3.2; if(p.x<0) p.x=W; }}
                    else                     {{ vx=1.2;  if(p.x>W) p.x=130; }}
                }}
            }} else {{
                vx=0; scatterX=0.6;
            }}

            p.x += vx + (Math.random()-0.5)*scatterX;
            p.y += (Math.random()-0.5)*0.6;
            if (p.y<28)  p.y=H-10;
            if (p.y>H-5) p.y=28;
        }});

        requestAnimationFrame(draw);
    }}
    draw();
}})();
</script>
"""
    components.html(canvas_html, height=390)

# ── 오른쪽: AI 분석
with col_ai:
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
                    import google.generativeai as genai
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    resp  = model.generate_content(system_instruction)
                    st.markdown(f"""
                    <div style='background:#f8f9fa; padding:12px; border-radius:10px;
                                border:1px solid #eaeaea; font-size:0.78rem;
                                height:360px; overflow-y:auto; line-height:1.45;'>
                        <strong>💡 AI 물리적 해설</strong><br>{resp.text}
                    </div>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"오류: {e}")
        else:
            st.error("GEMINI_API_KEY 미설정")
    else:
        st.markdown(f"""
        <div style='background:#f8f9fa; padding:14px; border-radius:10px;
                    border:1px solid #eaeaea; font-size:0.82rem;
                    height:360px; color:#64748b;
                    display:flex; align-items:center; justify-content:center; text-align:center;'>
            사이드바 하단의<br>'🚀 Gemini 분석 요청' 버튼을<br>누르면 이 자리에<br>물리 밴드 관점의<br>상세 해설이 표시됩니다.
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════
# 하단: 에너지 밴드 다이어그램 | I_C-V_CE 특성 곡선  (나란히)
# ════════════════════════════════════════════════
col_band, col_iv = st.columns(2)

# ── 에너지 밴드 다이어그램
with col_band:
    st.markdown("<span style='font-size:0.85rem; font-weight:700; color:#334155;'>🔋 에너지 밴드 다이어그램</span>", unsafe_allow_html=True)
    fig_band = go.Figure()
    E_g = 1.12
    x_all = np.linspace(0, 8.0, 400)
    ec_all = np.zeros_like(x_all)

    v_be_eff = float(np.clip(V_be, -5.0, 0.75))
    v_bc_eff = float(np.clip(V_bc, -5.0, 0.75))

    if bjt_type == "NPN":
        E_F_Base = 0.0; E_V_Base = -0.1; E_C_Base = E_V_Base + E_g
        E_F_Emitter = E_F_Base + v_be_eff; E_F_Collector = E_F_Base + v_bc_eff
        E_C_Emitter = E_F_Emitter - 0.05;  E_C_Collector = E_F_Collector - 0.15
    else:
        E_F_Base = 0.0; E_C_Base = 0.1; E_V_Base = E_C_Base - E_g
        E_F_Emitter = E_F_Base - v_be_eff; E_F_Collector = E_F_Base - v_bc_eff
        E_V_Emitter = E_F_Emitter + 0.05;  E_V_Collector = E_F_Collector + 0.15
        E_C_Emitter = E_V_Emitter + E_g;   E_C_Collector = E_V_Collector + E_g

    for i, x in enumerate(x_all):
        if   x <= 2.4: ec_all[i] = E_C_Emitter
        elif x >= 5.6: ec_all[i] = E_C_Collector
        elif 3.2 <= x <= 4.8: ec_all[i] = E_C_Base
        elif 2.4 < x < 3.2:
            t = (x-2.4)/0.8*np.pi
            ec_all[i] = E_C_Emitter + (E_C_Base-E_C_Emitter)*(1-np.cos(t))/2
        elif 4.8 < x < 5.6:
            t = (x-4.8)/0.8*np.pi
            ec_all[i] = E_C_Base + (E_C_Collector-E_C_Base)*(1-np.cos(t))/2
    ev_all = ec_all - E_g

    fig_band.add_vrect(x0=0,   x1=2.8, fillcolor="rgba(173,216,230,0.25)", line_width=0)
    fig_band.add_vrect(x0=2.8, x1=5.2, fillcolor="rgba(255,182,193,0.25)", line_width=0)
    fig_band.add_vrect(x0=5.2, x1=8.0, fillcolor="rgba(144,238,144,0.25)", line_width=0)
    fig_band.add_trace(go.Scatter(x=x_all, y=ec_all, mode='lines', line=dict(color='black',width=2.5), name='E_c'))
    fig_band.add_trace(go.Scatter(x=x_all, y=ev_all, mode='lines', line=dict(color='black',width=2.5), name='E_v'))
    fig_band.add_trace(go.Scatter(x=[0,2.4],   y=[E_F_Emitter,E_F_Emitter],   mode='lines', line=dict(color='blue',width=2,dash='dash'), name='E_F(E)'))
    fig_band.add_trace(go.Scatter(x=[3.2,4.8], y=[E_F_Base,E_F_Base],         mode='lines', line=dict(color='blue',width=2,dash='dash'), name='E_F(B)'))
    fig_band.add_trace(go.Scatter(x=[5.6,8.0], y=[E_F_Collector,E_F_Collector],mode='lines', line=dict(color='blue',width=2,dash='dash'), name='E_F(C)'))
    fig_band.add_annotation(x=8.15, y=ec_all[-1]+0.05, text="<b>E_C</b>", showarrow=False, font=dict(size=11,color='black'))
    fig_band.add_annotation(x=8.15, y=ev_all[-1]-0.05, text="<b>E_V</b>", showarrow=False, font=dict(size=11,color='black'))

    e_lbl = "EMITTER (N⁺)" if bjt_type=="NPN" else "EMITTER (P⁺)"
    b_lbl = "BASE (P)"     if bjt_type=="NPN" else "BASE (N)"
    c_lbl = "COLLECTOR (N)"if bjt_type=="NPN" else "COLLECTOR (P)"
    fig_band.add_annotation(x=1.4, y=max(ec_all)+0.5, text=f"<b>{e_lbl}</b>", showarrow=False, font=dict(size=10,color='#1565C0'))
    fig_band.add_annotation(x=4.0, y=max(ec_all)+0.5, text=f"<b>{b_lbl}</b>", showarrow=False, font=dict(size=10,color='#B71C1C'))
    fig_band.add_annotation(x=6.6, y=max(ec_all)+0.5, text=f"<b>{c_lbl}</b>", showarrow=False, font=dict(size=10,color='#1B5E20'))

    np.random.seed(42)
    if bjt_type == "NPN":
        fig_band.add_trace(go.Scatter(x=np.random.uniform(0.2,2.2,16), y=E_C_Emitter+np.random.uniform(0.02,0.15,16),
            mode='markers', marker=dict(color='#1565C0',size=8,line=dict(color='#0D47A1',width=1.5)), name='전자(e⁻)'))
        fig_band.add_trace(go.Scatter(x=np.random.uniform(3.4,4.6,10), y=E_V_Base-np.random.uniform(0.02,0.15,10),
            mode='markers', marker=dict(color='#C62828',size=9,line=dict(color='#7B1818',width=1.5)), name='정공(h⁺)'))
        fig_band.add_trace(go.Scatter(x=np.random.uniform(5.8,7.8,12), y=E_C_Collector+np.random.uniform(0.02,0.15,12),
            mode='markers', marker=dict(color='#1565C0',size=8,line=dict(color='#0D47A1',width=1.5)), showlegend=False))
    else:
        fig_band.add_trace(go.Scatter(x=np.random.uniform(0.2,2.2,16), y=E_V_Emitter-np.random.uniform(0.02,0.15,16),
            mode='markers', marker=dict(color='#C62828',size=9,line=dict(color='#7B1818',width=1.5)), name='정공(h⁺)'))
        fig_band.add_trace(go.Scatter(x=np.random.uniform(3.4,4.6,10), y=E_C_Base+np.random.uniform(0.02,0.15,10),
            mode='markers', marker=dict(color='#1565C0',size=8,line=dict(color='#0D47A1',width=1.5)), name='전자(e⁻)'))
        fig_band.add_trace(go.Scatter(x=np.random.uniform(5.8,7.8,12), y=E_V_Collector-np.random.uniform(0.02,0.15,12),
            mode='markers', marker=dict(color='#C62828',size=9,line=dict(color='#7B1818',width=1.5)), showlegend=False))

    fig_band.add_vline(x=2.8, line=dict(color='gray',width=1,dash='dot'))
    fig_band.add_vline(x=5.2, line=dict(color='gray',width=1,dash='dot'))
    fig_band.update_layout(
        xaxis=dict(visible=False, range=[-0.2,8.6]),
        yaxis=dict(visible=False, range=[min(ev_all)-0.35, max(ec_all)+0.8]),
        height=300, margin=dict(l=5,r=10,t=5,b=5),
        showlegend=True,
        legend=dict(x=0.01,y=0.02,bgcolor='rgba(255,255,255,0.85)',bordercolor='lightgray',borderwidth=1,font=dict(size=9),orientation='h'),
        plot_bgcolor='white'
    )
    st.plotly_chart(fig_band, use_container_width=True)

# ── I_C–V_CE 특성 곡선
with col_iv:
    st.markdown("<span style='font-size:0.85rem; font-weight:700; color:#334155;'>📈 I_C–V_CE 특성 곡선 & 직류 부하선</span>", unsafe_allow_html=True)
    fig_iv = go.Figure()
    sign       = 1 if bjt_type=="NPN" else -1
    v_arr      = np.linspace(0, V_CC+0.8, 300)
    ib_list    = [10,20,30,40,50]
    base_color = (255,127,14) if bjt_type=="NPN" else (148,103,189)

    for idx, ib_uA in enumerate(ib_list):
        ib_A   = ib_uA*1e-6
        ic_sat = beta*ib_A*1000
        alpha  = 0.35 + 0.14*idx
        color  = f"rgba({base_color[0]},{base_color[1]},{base_color[2]},{alpha:.2f})"
        ic_curve = [max(0.0, ic_sat*np.tanh(v/0.12)*(1+early_k*v)) for v in v_arr]
        fig_iv.add_trace(go.Scatter(
            x=[sign*v for v in v_arr], y=[sign*ic for ic in ic_curve],
            mode='lines', line=dict(color=color,width=2.0),
            name=f"I_B={ib_uA}μA", showlegend=True))

    sat_ic_mag = (V_CC/R_C)*1000
    fig_iv.add_trace(go.Scatter(
        x=[0.0, sign*V_CC], y=[sign*sat_ic_mag, 0.0],
        mode='lines', line=dict(color='black',width=2.5), name='직류 부하선'))
    fig_iv.add_vline(x=sign*0.2, line=dict(color='purple',width=1.2,dash='dot'))

    q_x, q_y = sign*q_vce, sign*q_ic_mA
    fig_iv.add_trace(go.Scatter(
        x=[q_x], y=[q_y], mode='markers+text',
        marker=dict(color='red',size=12,symbol='circle',line=dict(color='white',width=2)),
        text=[f"Q ({q_vce:.2f}V, {q_ic_mA:.2f}mA)"],
        textposition="top right", textfont=dict(size=10,color='red'), name="Q점"))
    fig_iv.add_shape(type='line', x0=q_x,x1=q_x, y0=0,y1=q_y, line=dict(color='red',width=1,dash='dash'))
    fig_iv.add_shape(type='line', x0=0,x1=q_x,   y0=q_y,y1=q_y, line=dict(color='red',width=1,dash='dash'))

    # 포화점/차단점 라벨
    fig_iv.add_annotation(x=sign*0.2, y=sign*sat_ic_mag, text="포화점", showarrow=False,
                           xanchor='left', font=dict(size=9,color='purple'))
    fig_iv.add_annotation(x=sign*V_CC, y=0, text="차단점", showarrow=False,
                           xanchor='right', font=dict(size=9,color='purple'))

    x_range = [-0.1, V_CC+1.2] if bjt_type=="NPN" else [-(V_CC+1.2), 0.1]
    y_range = [-0.3, sat_ic_mag+1.2] if bjt_type=="NPN" else [-(sat_ic_mag+1.2), 0.3]
    fig_iv.update_layout(
        xaxis_title="V_CE [V]", yaxis_title="I_C [mA]",
        xaxis=dict(range=x_range,showgrid=True,gridcolor='#EEEEEE',zeroline=True,zerolinecolor='black',zerolinewidth=1.5),
        yaxis=dict(range=y_range,showgrid=True,gridcolor='#EEEEEE',zeroline=True,zerolinecolor='black',zerolinewidth=1.5),
        height=300, margin=dict(l=5,r=10,t=5,b=5), showlegend=True,
        legend=dict(x=0.6 if bjt_type=="NPN" else 0.01,
                    y=0.98 if bjt_type=="NPN" else 0.15,
                    bgcolor='rgba(255,255,255,0.85)',bordercolor='lightgray',borderwidth=1,font=dict(size=9)),
        plot_bgcolor='white'
    )
    st.plotly_chart(fig_iv, use_container_width=True)