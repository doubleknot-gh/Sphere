
import streamlit as st
import requests
import time
import base64
import os
import pandas as pd
from PIL import Image

# --- 기본 설정 ---
# FastAPI 백엔드 주소
API_URL = "http://127.0.0.1:8000"  # 로컬 개발용 기본값

if "API_URL" in os.environ: # Render 환경
    API_URL = os.environ["API_URL"]
else: # Streamlit Cloud 또는 로컬 환경
    try:
        if "API_URL" in st.secrets:
            API_URL = st.secrets["API_URL"]
    except st.errors.StreamlitAPIException:
        # 로컬에서 secrets.toml 파일이 없을 때 예외 발생, 기본값을 사용하므로 pass
        pass

# 페이지 설정 (넓은 레이아웃, 제목, 아이콘 등)
logo_image = Image.open("logo.png")
st.set_page_config(page_title="디지털 회원증", layout="wide", page_icon=logo_image)

# --- CSS 스타일 ---
def local_css(file_name):
    with open(file_name, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style.css")


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
        if 'admin_member_list' not in st.session_state:
            st.session_state.admin_member_list = []

        if st.button("회원 목록 새로고침"):
            try:
                res = requests.get(f"{API_URL}/admin/members", headers=headers)
                if res.status_code == 200:
                    st.session_state.admin_member_list = res.json()
                else:
                    st.error("데이터를 불러올 수 없습니다.")
            except requests.exceptions.RequestException:
                st.error("서버 연결 실패")
        
        if st.session_state.admin_member_list:
            # 데이터프레임 변환 및 선택 컬럼 추가
            df = pd.DataFrame(st.session_state.admin_member_list)
            df.insert(0, "선택", False)
            
            # 데이터 에디터로 출력 (체크박스 기능)
            edited_df = st.data_editor(
                df,
                column_config={
                    "선택": st.column_config.CheckboxColumn("선택", default=False)
                },
                disabled=["student_id", "name", "club", "status", "role"],
                hide_index=True,
                use_container_width=True,
                key="member_list_editor"
            )
            
            # 선택된 회원 필터링
            selected_rows = edited_df[edited_df["선택"]]
            
            if not selected_rows.empty:
                st.markdown("---")
                if st.button(f"선택한 {len(selected_rows)}명 삭제하기", type="primary", key="delete_selected_btn"):
                    st.session_state['delete_confirm_targets'] = selected_rows['student_id'].tolist()
            
            # 삭제 확인 및 처리
            if st.session_state.get('delete_confirm_targets'):
                targets = st.session_state['delete_confirm_targets']
                st.warning(f"정말 {len(targets)}명의 회원을 삭제하시겠습니까? (복구 불가)")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("✅ 예, 일괄 삭제", key="confirm_yes_bulk"):
                        success_cnt = 0
                        for tid in targets:
                            try:
                                requests.delete(f"{API_URL}/admin/members/{tid}", headers=headers)
                                success_cnt += 1
                            except: pass
                        
                        st.success(f"{success_cnt}명 삭제 완료.")
                        st.session_state.admin_member_list = [m for m in st.session_state.admin_member_list if m['student_id'] not in targets]
                        del st.session_state['delete_confirm_targets']
                        time.sleep(1)
                        st.rerun()
                with col_no:
                    if st.button("❌ 취소", key="confirm_no_bulk"):
                        del st.session_state['delete_confirm_targets']
                        st.rerun()

    with tab2:
        uploaded_file = st.file_uploader("CSV 또는 Excel 파일 업로드 (이름, 학번, 소속동아리)", type=["csv", "xlsx"])
        if uploaded_file and st.button("업로드 시작"):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            try:
                res = requests.post(f"{API_URL}/admin/upload-csv", headers=headers, files=files)
                if res.status_code == 200:
                    st.success("업로드 성공!")
                else:
                    try:
                        err_msg = res.json().get('detail')
                    except:
                        err_msg = res.text
                    st.error(f"업로드 실패: {err_msg}")
            except requests.exceptions.RequestException:
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
                    except requests.exceptions.RequestException:
                        st.error("서버 오류 발생")
                else:
                    st.warning("모든 정보를 입력해주세요.")

    with tab4:
        target_id = st.text_input("관리할 대상 학번")
        
        st.markdown("---")
        st.subheader("소속 동아리 변경")
        new_club_name = st.text_input("변경할 동아리 이름", placeholder="예: 테니스부, 축구부 (여러 개는 콤마로 구분)")
        if st.button("동아리 정보 업데이트"):
            if target_id and new_club_name:
                try:
                    res = requests.patch(f"{API_URL}/admin/members/{target_id}/club", 
                                         headers=headers, params={"club": new_club_name})
                    if res.status_code == 200:
                        st.success("소속 동아리가 변경되었습니다.")
                    else:
                        st.error(f"변경 실패: {res.json().get('detail')}")
                except requests.exceptions.RequestException:
                    st.error("서버 연결 실패")
            else:
                st.warning("학번과 변경할 동아리 이름을 모두 입력해주세요.")

        st.markdown("---")
        st.subheader("계정 상태 및 관리")
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
                if target_id:
                    st.session_state['delete_confirm_target_tab4'] = target_id
                else:
                    st.warning("삭제할 대상 학번을 입력해주세요.")
            
            if st.session_state.get('delete_confirm_target_tab4'):
                st.warning(f"정말 {st.session_state['delete_confirm_target_tab4']} 회원을 영구 삭제하시겠습니까?")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("✅ 예, 삭제합니다", key="confirm_yes_tab4"):
                        try:
                            res = requests.delete(f"{API_URL}/admin/members/{st.session_state['delete_confirm_target_tab4']}", headers=headers)
                            if res.status_code == 200: 
                                st.success("삭제 완료")
                                del st.session_state['delete_confirm_target_tab4']
                                time.sleep(0.5)
                                st.rerun()
                            else: 
                                st.error(f"삭제 실패: {res.json().get('detail')}")
                        except requests.exceptions.RequestException:
                            st.error("서버 연결 실패")
                with col_no:
                    if st.button("❌ 취소", key="confirm_no_tab4"):
                        del st.session_state['delete_confirm_target_tab4']
                        st.rerun()

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
    
    # KU 로고 이미지 로드 (base64)
    ku_logo_html = ""
    try:
        with open("ku logo.png", "rb") as f:
            encoded_ku = base64.b64encode(f.read()).decode()
            ku_logo_html = f'<img src="data:image/png;base64,{encoded_ku}" style="width: 50px; margin-top: 5px;">'
    except FileNotFoundError:
        pass

    # 회원증 카드 UI (세련된 신용카드 스타일)
    st.markdown(f"""
        <div class="membership-card">
            <div class="card-header">
                <div class="card-chip"></div>
                <div style="text-align: right;">
                    <div class="card-logo">DIGITAL MEMBER</div>
                    {ku_logo_html}
                </div>
            </div>
            <div class="card-body">
                <div class="card-label">NAME</div>
                <h2>{info['name']}</h2>
                <div class="card-label">STUDENT ID</div>
                <p class="student-id">{info['student_id']}</p>
            </div>
            <div class="card-footer">
                <p class="club">{info.get('club', '소속 없음')}</p>
                <div class="time" id="real-time"></div>
            </div>
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
