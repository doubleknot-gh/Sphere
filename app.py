
import streamlit as st
import requests
import time
import os
from PIL import Image

# --- 기본 설정 ---
# FastAPI 백엔드 주소
if "API_URL" in os.environ:
    API_URL = os.environ["API_URL"]
elif hasattr(st, "secrets") and "API_URL" in st.secrets:
    API_URL = st.secrets["API_URL"]
else:
    API_URL = "https://sphere-e317.onrender.com"

# 페이지 설정 (넓은 레이아웃, 제목, 아이콘 등)
logo_image = Image.open("logo.png")
st.set_page_config(page_title="디지털 회원증", layout="wide", page_icon=logo_image)

# --- CSS 스타일 ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 다크 모드 및 커스텀 스타일 적용
# (별도 CSS 파일 대신 직접 스타일 지정)
st.markdown("""
<style>
/* 1. 전체 배경색을 로고 바탕색과 일치 */
[data-testid="stAppViewContainer"] {
    background-color: #050A18 !important;
    background-image: radial-gradient(circle at 50% 50%, #0d1b3a 0%, #050A18 100%);
    color: #FFFFFF !important;
}

/* 2. '디지털 회원증 로그인' 제목을 로고 색상으로 더 밝게 */
h1 {
    color: #F5EFE0 !important; /* 로고의 밝은 아이보리 색상 */
    font-weight: 800 !important;
    text-shadow: 0px 0px 10px rgba(245, 239, 224, 0.3); /* 은은한 광채 효과 */
}

/* 3. 입력창 라벨(학번, 비밀번호) 글씨 밝게 */
.stTextInput label p {
    color: #F5EFE0 !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
}

/* 4. 입력창 내부의 안내 문구(Placeholder) 가독성 개선 */
input::placeholder {
    color: rgba(255, 255, 255, 0.5) !important;
}

/* 상단 헤더 숨기기 (선택 사항 - 더 깔끔해짐) */
[data-testid="stHeader"] {
    background: rgba(0,0,0,0);
}

/* 애니메이션 정의 (아래에서 위로 부드럽게 등장) */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translate3d(0, 30px, 0);
    }
    to {
        opacity: 1;
        transform: translate3d(0, 0, 0);
    }
}

/* 2. 디지털 회원증 카드 (단순화된 디자인) */
.membership-card {
    background: linear-gradient(120deg, #1a2a4a 0%, #0d1526 100%);
    border: 1px solid rgba(228, 212, 164, 0.4);
    border-radius: 16px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    width: 350px;
    margin: 40px auto;
    padding: 25px;
    box-sizing: border-box;
    color: white;
    animation: fadeInUp 0.8s cubic-bezier(0.2, 0.8, 0.2, 1);
}

/* 카드 내부 요소 스타일 */
.membership-card h2 {
    font-size: 1.8rem;
    color: #E4D4A4;
    margin: 20px 0 10px 0;
    text-align: center;
    letter-spacing: 1px;
}

.membership-card p {
    font-size: 1.1rem;
    text-align: center;
    margin: 5px 0;
    opacity: 0.9;
}

.membership-card .club {
    font-size: 1rem;
    color: #E4D4A4;
    font-weight: bold;
}

.membership-card .time {
    font-size: 0.8rem;
    color: #aaa;
    text-align: center;
    margin-top: 30px;
}


/* 로그인 폼 입력창 스타일 */
.stTextInput > div > div > input {
    background-color: rgba(10, 25, 47, 0.6) !important;
    color: #F5EFE0 !important;
    border: 1px solid rgba(228, 212, 164, 0.2) !important;
    border-radius: 12px !important;
    padding: 15px !important;
    font-size: 1rem !important;
    transition: all 0.3s ease;
}

.stTextInput > div > div > input:focus {
    border-color: #E4D4A4 !important;
    box-shadow: 0 0 15px rgba(228, 212, 164, 0.15) !important;
    background-color: rgba(10, 25, 47, 0.9) !important;
}

/* 로그인 폼 컨테이너 (Glassmorphism) */
[data-testid="stForm"] {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 24px;
    padding: 30px;
    box-shadow: 0 20px 50px rgba(0,0,0,0.5);
    backdrop-filter: blur(10px);
    animation: fadeInUp 0.6s ease-out;
}

/* 버튼 스타일 */
.stButton button {
    width: 100%;
    background-color: #E4D4A4 !important;
    color: #050A18 !important;
    border: none !important;
    font-weight: bold !important;
    border-radius: 12px !important;
    padding: 0.75rem !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease !important;
}

/* 5. 버튼 글자색을 배경과 대비되게 (어두운 배경엔 밝은 버튼) */
.stButton button p {
    color: #050A18 !important; /* 버튼 배경이 밝으므로 글씨는 어둡게 */
    font-weight: bold !important;
    font-size: 1.1rem !important;
}

.stButton button:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(228, 212, 164, 0.2);
}

/* --- 관리자 대시보드 스타일 (프리미엄 다크 테마) --- */

/* 탭 스타일 */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}
.stTabs [data-baseweb="tab"] {
    background-color: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    color: #aaa;
    border: none;
    padding: 8px 16px;
    transition: all 0.3s ease;
}
.stTabs [data-baseweb="tab"]:hover {
    background-color: rgba(255, 255, 255, 0.1);
    color: white;
}
.stTabs [aria-selected="true"] {
    background-color: #E4D4A4 !important;
    color: #050A18 !important;
    font-weight: bold;
    box-shadow: 0 0 10px rgba(228, 212, 164, 0.3);
}

/* 알림 박스 (st.info, st.success 등) */
[data-testid="stAlert"] {
    background-color: rgba(28, 33, 57, 0.8);
    border: 1px solid rgba(228, 212, 164, 0.3);
    color: #E4D4A4;
    border-radius: 12px;
}

/* 파일 업로더 */
[data-testid="stFileUploader"] section {
    background-color: rgba(255, 255, 255, 0.03);
    border: 1px dashed rgba(228, 212, 164, 0.3);
    border-radius: 12px;
}

/* 셀렉트박스 */
.stSelectbox div[data-baseweb="select"] > div {
    background-color: rgba(10, 25, 47, 0.6) !important;
    color: #F5EFE0 !important;
    border: 1px solid rgba(228, 212, 164, 0.2) !important;
    border-radius: 12px !important;
}
</style>
""", unsafe_allow_html=True)


# --- 세션 상태 초기화 ---
if 'token' not in st.session_state:
    st.session_state.token = None
if 'member_info' not in st.session_state:
    st.session_state.member_info = None

# --- 페이지 로직 ---

# 1. 로그인 페이지
def show_login_page():
    # 화면 중앙 정렬을 위한 컬럼 분할
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        # 로고 중앙 정렬
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.image(logo_image, use_container_width=True)
        
        st.markdown("<h1 style='text-align: center; margin-bottom: 40px;'>MEMBER LOGIN</h1>", unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=True):
            st.markdown("<h3 style='color: #E4D4A4; text-align: center; margin-bottom: 20px;'>환영합니다</h3>", unsafe_allow_html=True)
            student_id = st.text_input("학번", placeholder="학번을 입력해주세요")
            password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력해주세요")
            
            st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True) # 간격 추가
            submitted = st.form_submit_button("로그인")

            if submitted:
                try:
                    response = requests.post(
                        f"{API_URL}/token",
                        data={"username": student_id, "password": password}
                    )
                    if response.status_code == 200:
                        st.session_state.token = response.json()['access_token']
                        st.rerun() # 페이지를 다시 실행하여 회원증 페이지로 이동
                    else:
                        st.error("학번 또는 비밀번호가 일치하지 않습니다.")
                except requests.exceptions.ConnectionError:
                    st.error("백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")

# 1.5 관리자 대시보드 (신규 추가)
def show_admin_dashboard():
    st.title("🛡️ 관리자 대시보드")
    st.info(f"관리자: {st.session_state.member_info['name']}님 접속 중")
    
    # 탭으로 기능 분리
    tab1, tab2, tab3, tab4 = st.tabs(["👥 전체 회원 조회", "📂 명단 일괄 등록", "➕ 신규 회원 등록", "⚙️ 개별 회원 관리"])
    headers = {"Authorization": f"Bearer {st.session_state.token}"}

    with tab1:
        if st.button("회원 목록 새로고침"):
            try:
                res = requests.get(f"{API_URL}/admin/members", headers=headers)
                if res.status_code == 200:
                    st.dataframe(res.json())
                else:
                    st.error("데이터를 불러올 수 없습니다.")
            except:
                st.error("서버 연결 실패")

    with tab2:
        uploaded_file = st.file_uploader("CSV 파일 업로드 (학번, 이름, 소속동아리)", type="csv")
        if uploaded_file and st.button("업로드 시작"):
            files = {"file": (uploaded_file.name, uploaded_file, "text/csv")}
            try:
                res = requests.post(f"{API_URL}/admin/upload-csv", headers=headers, files=files)
                if res.status_code == 200:
                    st.success("업로드 성공!")
                else:
                    st.error(f"업로드 실패: {res.text}")
            except:
                st.error("서버 연결 실패")

    with tab3:
        st.subheader("신규 회원 직접 등록")
        with st.form("add_member_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                new_sid = st.text_input("학번", placeholder="예: 20241234")
            with col2:
                new_name = st.text_input("이름", placeholder="예: 홍길동")
            new_club = st.text_input("소속 동아리", placeholder="예: 총동아리연합회")
            
            if st.form_submit_button("회원 등록"):
                if new_sid and new_name and new_club:
                    try:
                        res = requests.post(f"{API_URL}/admin/members", headers=headers, json={"student_id": new_sid, "name": new_name, "club": new_club})
                        if res.status_code == 200:
                            st.success(f"✅ {new_name}({new_sid}) 등록 완료!")
                        else:
                            st.error(f"❌ 등록 실패: {res.json().get('detail')}")
                    except:
                        st.error("서버 오류 발생")
                else:
                    st.warning("모든 정보를 입력해주세요.")

    with tab4:
        target_id = st.text_input("관리할 대상 학번")
        col1, col2 = st.columns(2)
        with col1:
            new_status = st.selectbox("상태 선택", ["active", "inactive"])
            if st.button("상태 변경 적용"):
                res = requests.patch(f"{API_URL}/admin/members/{target_id}/status", 
                                     headers=headers, params={"status": new_status})
                if res.status_code == 200: st.success("변경 완료")
                else: st.error("변경 실패")
        with col2:
            if st.button("비밀번호 초기화 ('1234')"):
                if target_id:
                    res = requests.patch(f"{API_URL}/admin/members/{target_id}/reset-password", headers=headers)
                    if res.status_code == 200:
                        st.success(f"{target_id}의 비밀번호가 '1234'로 초기화되었습니다.")
                    else:
                        st.error(f"초기화 실패: {res.json().get('detail')}")
                else:
                    st.warning("초기화할 대상 학번을 입력해주세요.")

            if st.button("회원 영구 삭제", type="primary"):
                res = requests.delete(f"{API_URL}/admin/members/{target_id}", headers=headers)
                if res.status_code == 200: st.warning("삭제 완료")
                else: st.error("삭제 실패")

# 2. 디지털 회원증 페이지
def show_membership_card():
    # 토큰을 사용하여 회원 정보 가져오기
    if st.session_state.member_info is None:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        try:
            response = requests.get(f"{API_URL}/members/me", headers=headers)
            if response.status_code == 200:
                st.session_state.member_info = response.json()
            else: # 토큰이 만료되었거나 유효하지 않은 경우
                st.session_state.token = None
                st.session_state.member_info = None
                st.rerun()
                return
        except requests.exceptions.ConnectionError:
            st.error("백엔드 서버에 연결할 수 없습니다.")
            st.session_state.token = None # 연결 실패 시 로그아웃 처리
            st.session_state.member_info = None
            if st.button("다시 시도"):
                st.rerun()
            return
            
    info = st.session_state.member_info
    
    # 관리자 권한 확인 및 사이드바 메뉴 활성화
    if info.get("role") == "admin":
        with st.sidebar:
            st.header("관리자 메뉴")
            menu = st.radio("페이지 이동", ["디지털 회원증", "관리자 대시보드"])
        
        if menu == "관리자 대시보드":
            show_admin_dashboard()
            return
    
    # 로고 표시
    st.image(logo_image, width=150)
    
    # 회원증 카드 UI (단순화된 버전)
    st.markdown(f"""
        <div class="membership-card">
            <h2>{info['name']}</h2>
            <p>{info['student_id']}</p>
            <p class="club">{info.get('club', '소속 없음')}</p>
            <div class="time" id="real-time"></div>
        </div>
    """, unsafe_allow_html=True)

    # 실시간 시간 표시 스크립트
    st.components.v1.html("""
        <script>
            function updateTime() {
                const timeElement = parent.document.getElementById('real-time');
                if (timeElement) {
                    const now = new Date();
                    const timeString = now.toLocaleDateString('ko-KR') + ' ' + now.toLocaleTimeString('ko-KR');
                    timeElement.innerText = '실시간 서버 시간: ' + timeString;
                }
            }
            // 1초마다 시간 업데이트
            setInterval(updateTime, 1000);
            // 페이지 로드 시 즉시 시간 표시
            updateTime();
        </script>
    """, height=0)
    
    # 비밀번호 변경 기능
    with st.expander("비밀번호 변경"):
        with st.form("password_change_form", clear_on_submit=True):
            current_password = st.text_input("현재 비밀번호", type="password")
            new_password = st.text_input("새 비밀번호", type="password")
            confirm_password = st.text_input("새 비밀번호 확인", type="password")
            
            if st.form_submit_button("비밀번호 변경하기"):
                if new_password != confirm_password:
                    st.error("새 비밀번호가 일치하지 않습니다.")
                elif not current_password or not new_password:
                    st.warning("모든 필드를 입력해주세요.")
                else:
                    headers = {"Authorization": f"Bearer {st.session_state.token}"}
                    data = {"current_password": current_password, "new_password": new_password}
                    try:
                        res = requests.put(f"{API_URL}/members/me/password", headers=headers, json=data)
                        if res.status_code == 200:
                            st.success("비밀번호가 성공적으로 변경되었습니다.")
                        else:
                            st.error(f"비밀번호 변경 실패: {res.json().get('detail')}")
                    except:
                        st.error("서버 오류 발생")

    # 로그아웃 버튼
    if st.button("로그아웃"):
        st.session_state.token = None
        st.session_state.member_info = None
        st.rerun()


# --- 메인 실행 로직 ---
if st.session_state.token is None:
    show_login_page()
else:
    show_membership_card()
