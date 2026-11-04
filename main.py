from pathlib import Path
import json
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="NEON ARENA FPS", page_icon="🎮", layout="wide")
st.markdown("""
<style>
.stApp{background:#080d18;color:#eef5ff}
[data-testid="stSidebar"]{background:#101827}
h1,h2,h3,p,label{color:#eef5ff!important}
.hero small{color:#54efff;letter-spacing:3px;font-weight:800}
.hero h1{font-size:clamp(2.2rem,5vw,3.5rem);margin:0;font-weight:900}
.hero p{color:#a9b8d0!important}
div[data-testid="stTextInput"] input{background:#111c2e;color:#fff}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
<small>ONLINE MULTIPLAYER · 3D ARENA</small>
<h1>NEON ARENA <span style="color:#54efff">FPS</span></h1>
<p>친구와 함께 접속하는 브라우저 FPS 훈련장</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 접속 설정")
    server_url = st.text_input("게임 서버 주소", placeholder="https://your-server.onrender.com")
    nickname = st.text_input("닉네임", value="Player", max_chars=18)
    st.markdown("---")
    st.markdown("### 조작법")
    st.markdown("- **W A S D** 이동\n- **마우스** 조준\n- **마우스 왼쪽 클릭** 발사\n- **Space** 점프\n- **R** 재장전\n- **Esc** 마우스 잠금 해제")
    st.caption("최대 16명 · 팀 데스매치 프로토타입")
    if server_url and not server_url.startswith(("https://", "http://")):
        st.error("서버 주소는 https:// 또는 http:// 로 시작해야 합니다.")

if not server_url.strip():
    st.info("Render에 게임 서버를 배포한 뒤 서버 주소를 입력하세요. 주소가 비어 있으면 연습 모드로 실행됩니다.")

html_path = Path(__file__).parent / "game.html"
if not html_path.exists():
    st.error("game.html 파일을 main.py와 같은 폴더에 업로드해야 합니다.")
else:
    html = html_path.read_text(encoding="utf-8")
    html = html.replace("__SERVER_URL_JSON__", json.dumps(server_url.strip().rstrip("/")))
    html = html.replace("__NICKNAME_JSON__", json.dumps(nickname.strip() or "Player"))
    components.html(html, height=780, scrolling=False)

st.caption("학습용 프로토타입입니다. 공개 경쟁 서비스로 사용하기 전에는 보안·부하 테스트가 필요합니다.")
