import streamlit as st

st.set_page_config(page_title="BJT 물리 시뮬레이터", layout="wide")

# UI 스타일
st.markdown("""
    <style>
        .header-text { font-size: 20px; font-weight: 700; color: #1e293b; margin-bottom: 10px; }
        .mode-box { padding: 15px; border-radius: 8px; border: 1px solid #ddd; text-align: center; font-weight: 700; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center;'>🔬 BJT(NPN) 물리 시뮬레이터</h2>", unsafe_allow_html=True)

# 1. 사이드바 제어
with st.sidebar:
    st.markdown("### **🎛️ BJT 바이어스 설정**")
    v_be = st.slider("V_BE [V]", -1.0, 1.0, 0.0, 0.1)
    v_bc = st.slider("V_BC [V]", -1.0, 1.0, 0.0, 0.1)
    ask_ai_btn = st.button("AI 해설 받기", type="primary", use_container_width=True)

# 2. 로직: 모드 판별 및 해당 이미지 매칭
if v_be < 0.5 and v_bc < 0.5: 
    mode, color = "차단 모드 (Cutoff)", "#fff1f0"
    img_path = "https://raw.githubusercontent.com/your-repo/images/main/cutoff_band.jpg" # 실제 이미지 경로로 수정 필요
elif v_be >= 0.5 and v_bc < 0.5: 
    mode, color = "순방향 활성 모드 (Forward Active)", "#f6ffed"
    img_path = "https://raw.githubusercontent.com/your-repo/images/main/active_band.jpg"
else: 
    mode, color = "포화 모드 (Saturation)", "#e6f7ff"
    img_path = "https://raw.githubusercontent.com/your-repo/images/main/saturation_band.jpg"

# 3. 레이아웃
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.markdown("<div class='header-text'>📊 동작 모드</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='mode-box' style='background-color:{color};'>{mode}</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='header-text'>⚡ 에너지 밴드 다이어그램</div>", unsafe_allow_html=True)
    # 각 모드에 맞는 이미지 호출 (이미지 파일이 프로젝트 폴더 내부에 있어야 함)
    try:
        st.image(f"images/{mode.split('(')[0].strip().lower()}.jpg", use_container_width=True)
    except:
        st.warning("해당 모드의 에너지 밴드 이미지를 'images' 폴더에 넣어주세요.")

with col3:
    with st.container(border=True):
        st.markdown("<div class='header-text'>🤖 AI 해설</div>", unsafe_allow_html=True)
        if ask_ai_btn: st.write("분석 중입니다...")
        else: st.info("바이어스 설정 후 해설을 요청하세요.")