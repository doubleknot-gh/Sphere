
import streamlit as st
import requests
import time
import base64
import os
import io
import random
import pandas as pd
from datetime import datetime, timedelta
from PIL import Image
import altair as alt

# --- 기본 설정 ---
# FastAPI 백엔드 주소
API_URL = "http://127.0.0.1:8000"  # 로컬 개발용 기본값

if "API_URL" in os.environ: # Render 환경
    API_URL = os.environ["API_URL"].rstrip("/") # 끝에 붙은 슬래시 제거 (오류 방지)
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

# --- 이미지 로딩 캐싱 (매 렌더링마다 파일 읽기 방지) ---
@st.cache_data
def load_base64_image(file_path):
    try:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return ""

# --- 파티클 배경 효과 (CSS + Python) ---
def add_particle_effect():
    particles_html = ""
    for _ in range(30): # 파티클 개수 최적화 (50 -> 30)
        size = random.uniform(1, 4)
        left = random.uniform(0, 100)
        top = random.uniform(0, 100)
        duration = random.uniform(10, 30)
        delay = random.uniform(-20, 0)
        # 색상 랜덤 (흰색 또는 골드)
        color = random.choice(["rgba(255, 255, 255, 0.5)", "rgba(228, 212, 164, 0.6)"])
        
        particles_html += f"""
        <div class="particle" style="
            width: {size}px;
            height: {size}px;
            left: {left}vw;
            top: {top}vh;
            background: {color};
            box-shadow: 0 0 10px {color};
            animation-duration: {duration}s;
            animation-delay: {delay}s;
        "></div>
        """

    st.markdown(f"""
        <style>
            #particles {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                z-index: 1;
                pointer-events: none;
            }}
            .particle {{
                position: absolute;
                border-radius: 50%;
                animation: float infinite linear;
            }}
            @keyframes float {{
                0% {{ transform: translateY(0) translateX(0); opacity: 0; }}
                10% {{ opacity: 1; }}
                50% {{ opacity: 0.4; }} /* 반짝이는 효과 추가 */
                90% {{ opacity: 1; }}
                100% {{ transform: translateY(-100vh) translateX(20px); opacity: 0; }}
            }}
        </style>
        <div id="particles">
            {particles_html}
        </div>
    """, unsafe_allow_html=True)

# --- 세션 상태 초기화 ---
if 'token' not in st.session_state:
    st.session_state.token = None
if 'member_info' not in st.session_state:
    st.session_state.member_info = None
if 'expire_time' not in st.session_state:
    st.session_state.expire_time = None
if 'local_storage_checked' not in st.session_state:
    st.session_state.local_storage_checked = False
if 'extend_count' not in st.session_state:
    st.session_state.extend_count = 0

# --- 로컬 스토리지 저장/삭제 이벤트 처리 ---
if st.session_state.get('save_ls'):
    st.components.v1.html(f"""
        <script>
            window.parent.localStorage.setItem('access_token', '{st.session_state.token}');
            window.parent.localStorage.setItem('expire_time', '{st.session_state.expire_time.isoformat() if st.session_state.expire_time else ""}');
            window.parent.localStorage.setItem('extend_count', '{st.session_state.extend_count}');
        </script>
    """, height=0)
    st.session_state.save_ls = False

if st.session_state.get('clear_ls'):
    st.components.v1.html("""
        <script>
            window.parent.localStorage.removeItem('access_token');
            window.parent.localStorage.removeItem('expire_time');
            window.parent.localStorage.removeItem('extend_count');
        </script>
    """, height=0)
    st.session_state.clear_ls = False

# --- 로컬 스토리지(자동 로그인) 읽기 연동 ---
if not st.session_state.local_storage_checked:
    st.markdown("""
        <style>
            div[data-testid="stTextInput"]:has(input[aria-label="hidden_ls_token"]),
            div[data-testid="stTextInput"]:has(input[aria-label="hidden_ls_expire"]),
            div[data-testid="stTextInput"]:has(input[aria-label="hidden_ls_extend"]) {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)
    
    ls_token = st.text_input("hidden_ls_token", key="ls_token_input", label_visibility="collapsed")
    ls_expire = st.text_input("hidden_ls_expire", key="ls_expire_input", label_visibility="collapsed")
    ls_extend = st.text_input("hidden_ls_extend", key="ls_extend_input", label_visibility="collapsed")
    
    st.components.v1.html("""
        <script>
            const parentDoc = window.parent.document;
            
            // 화면이 그려질 때까지 최대 2초간 반복해서 찾는 로직 (빈 화면 방지)
            let attempts = 0;
            let checkInterval = setInterval(function() {
                const tokenInput = parentDoc.querySelector('input[aria-label="hidden_ls_token"]');
                const expireInput = parentDoc.querySelector('input[aria-label="hidden_ls_expire"]');
                const extendInput = parentDoc.querySelector('input[aria-label="hidden_ls_extend"]');
                
                if (tokenInput) {
                    clearInterval(checkInterval);
                    const savedToken = window.parent.localStorage.getItem('access_token');
                    const savedExpire = window.parent.localStorage.getItem('expire_time');
                    const savedExtend = window.parent.localStorage.getItem('extend_count');
                    
                    if (savedToken && tokenInput.value === "") {
                        let setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                        setter.call(tokenInput, savedToken);
                        tokenInput.dispatchEvent(new Event('input', { bubbles: true }));
                        
                        if (savedExpire && expireInput) {
                            setter.call(expireInput, savedExpire);
                            expireInput.dispatchEvent(new Event('input', { bubbles: true }));
                        }
                        if (savedExtend && extendInput) {
                            setter.call(extendInput, savedExtend);
                            extendInput.dispatchEvent(new Event('input', { bubbles: true }));
                        }
                    } else if (!savedToken && tokenInput.value === "") {
                        let setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                        setter.call(tokenInput, "NONE");
                        tokenInput.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                }
                attempts++;
                if(attempts > 20) clearInterval(checkInterval);
            }, 100);
        </script>
    """, height=0)
    
    if ls_token == "NONE":
        st.session_state.local_storage_checked = True
        st.rerun()
    elif ls_token and ls_token != "NONE":
        st.session_state.token = ls_token
        if ls_expire:
            try:
                st.session_state.expire_time = datetime.fromisoformat(ls_expire)
            except:
                pass
        if ls_extend and ls_extend.isdigit():
            st.session_state.extend_count = int(ls_extend)
        st.session_state.local_storage_checked = True
        st.rerun()
        

# --- 헬퍼 함수: 강제 로그아웃 처리 ---
def do_logout():
    st.session_state.clear()
    st.session_state.clear_ls = True
    st.session_state.local_storage_checked = True
    st.rerun()

# --- 헬퍼 함수: 분과 및 동아리 매핑 ---
CLUB_DIVISIONS = {
    "예술음악분과": ["LACOV", "한울", "딕트", "스타피쉬", "JB", "한사랑 오케스트라", "백우회", "거트", "우서", "어쿠스틱스", "4D"],
    "창업학술분과": ["유토피아", "소란", "PSM", "제5세대", "리더", "우하오"],
    "취미교양분과": ["왓치", "가비", "산악부", "FOCUS", "두점머리", "워너비", "만화마을", "0AE"],
    "봉사종교분과": ["JYM", "CCC", "뉴라이프", "로타랙트", "LEO", "필리아", "Team911"],
    "체육레저분과": ["K.B", "아웃사이더", "보디가드", "팬서스", "RELAX", "SPLASH", "KUBIC", "건무회"]
}

def get_division(club_name):
    if not club_name: return "미분류"
    club_upper = str(club_name).strip().upper()
    for div, clubs in CLUB_DIVISIONS.items():
        if any(c.upper() == club_upper for c in clubs):
            return div
    if club_upper in ["총동아리연합회"]:
        return "학생자치기구"
    return "미분류"

# --- 헬퍼 함수: 회원증 HTML 생성 (재사용 목적) ---
def get_card_html(info, is_preview=False):
    # KU 로고 이미지 로드
    ku_logo_html = ""
    encoded_ku = load_base64_image("ku logo.png")
    if encoded_ku:
        ku_logo_html = f'<img src="data:image/png;base64,{encoded_ku}" style="width: 50px; margin-top: 5px;">'

    # 소속 동아리가 여러 개일 경우 (콤마 구분), 쉼표를 없애고 각각 간격을 두어 옆으로 나열
    raw_club = info.get('club')
    raw_club = raw_club if raw_club else '소속 없음'
    club_html = "".join([f"<span style='margin-right: 8px;'>{c.strip()}</span>" for c in raw_club.split(',')])

    return f"""
        <style>
            .membership-card {{
                max-width: 600px !important; /* 카드 너비 확대 */
            }}
        </style>
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
                <p class="club">{club_html}</p>
            </div>
        </div>
    """

# --- 페이지 로직 ---

# 1. 로그인 페이지
def show_login_page():
    # 배경 파티클 효과 적용
    add_particle_effect()
    
    # [수정] 애니메이션을 위한 빈 공간 확보 (폼 바깥쪽)
    animation_placeholder = st.empty()
    
    # 화면 중앙 정렬을 위한 컬럼 분할
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        # 로고 중앙 정렬
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            # 로고에 애니메이션 클래스 적용을 위해 HTML로 렌더링
            encoded_logo = load_base64_image("logo.png")
            if encoded_logo:
                st.markdown(f'<img src="data:image/png;base64,{encoded_logo}" class="login-logo">', unsafe_allow_html=True)
            else:
                st.image(logo_image, use_container_width=True)
        
        st.markdown("<h1 style='text-align: center; margin-bottom: 40px;'>MEMBER LOGIN</h1>", unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=True):
            st.markdown("<h3 style='color: #E4D4A4; text-align: center; margin-bottom: 20px;'>환영합니다</h3>", unsafe_allow_html=True)
            student_id = st.text_input("학번", placeholder="학번을 입력해주세요")
            password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력해주세요")
            
            st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True) # 간격 추가
            submitted = st.form_submit_button("로그인")

            if submitted:
                # [UX 개선] 서버 응답 대기 중 로딩 표시 추가
                with st.spinner("서버에 접속 중입니다... (무료 서버가 깨어나는 데 최대 1분 소요될 수 있습니다)"):
                    try:
                        response = requests.post(
                            f"{API_URL}/token",
                            data={"username": student_id, "password": password}
                        )
                        if response.status_code == 200:
                            token = response.json()['access_token']
                            
                            # 사용자 이름 가져오기 (환영 메시지용)
                            user_name = ""
                            role = "member"
                            try:
                                headers = {"Authorization": f"Bearer {token}"}
                                me_res = requests.get(f"{API_URL}/members/me", headers=headers)
                                if me_res.status_code == 200:
                                    user_info = me_res.json()
                                    user_name = user_info['name']
                                    role = user_info.get('role', 'member')
                            except:
                                pass

                            # 로그인 만료 시간 설정 (관리자, 회원 모두 10분)
                            expire_mins = 10
                            st.session_state.expire_time = datetime.now() + timedelta(minutes=expire_mins)
                            st.session_state.extend_count = 0

                            # 로그인 성공 애니메이션 (로고 확대 및 페이드아웃)
                            try:
                                welcome_html = ""
                                if user_name:
                                    welcome_html = f"<h2 style='color: #E4D4A4; margin-top: 20px; font-size: 2rem; font-weight: 800; text-shadow: 0 2px 4px rgba(0,0,0,0.5); animation: fadeInUp 0.5s ease-out;'>환영합니다, {user_name}님!</h2>"

                                # [수정] 폼 내부가 아닌 외부 placeholder에 애니메이션 렌더링
                                with animation_placeholder:
                                    anim_logo = load_base64_image("logo.png")
                                    img_tag = f'<img src="data:image/png;base64,{anim_logo}" style="width: 200px; animation: zoomOutLogo 0.6s cubic-bezier(0.19, 1, 0.22, 1) forwards;">' if anim_logo else ""
                                    st.markdown(f"""
                                        <div style="
                                            position: fixed;
                                            top: 0; left: 0;
                                            width: 100vw; height: 100vh;
                                            background-color: #050A18;
                                            z-index: 999999;
                                            display: flex;
                                            flex-direction: column;
                                            justify-content: center;
                                            align-items: center;
                                            animation: fadeOutOverlay 0.8s forwards;
                                        ">
                                            {img_tag}
                                            {welcome_html}
                                        </div>
                                        <style>
                                            @keyframes zoomOutLogo {{
                                                0% {{ transform: scale(1); opacity: 1; }}
                                                100% {{ transform: scale(5); opacity: 0; }}
                                            }}
                                            @keyframes fadeOutOverlay {{
                                                0% {{ opacity: 1; }}
                                                70% {{ opacity: 1; }}
                                                100% {{ opacity: 0; pointer-events: none; }}
                                            }}
                                        </style>
                                    """, unsafe_allow_html=True)
                                time.sleep(0.7) 
                            except:
                                pass

                            st.session_state.token = token
                            st.session_state.save_ls = True
                            st.rerun() # 페이지를 다시 실행하여 회원증 페이지로 이동
                        else:
                            st.error("학번 또는 비밀번호가 일치하지 않습니다.")
                    except requests.exceptions.ConnectionError:
                        st.error("백엔드 서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.")


# 1.5 관리자 대시보드 (신규 추가)
def show_admin_dashboard():
    st.title("🛡️ 관리자 대시보드")
    st.info(f"관리자: {st.session_state.member_info['name']}님 접속 중")
    
    headers = {"Authorization": f"Bearer {st.session_state.token}"}

    # [기능 추가] 데이터 자동 로드 및 통계 위젯 표시
    if 'admin_member_list' not in st.session_state or not st.session_state.admin_member_list:
        try:
            res = requests.get(f"{API_URL}/admin/members", headers=headers)
            if res.status_code == 200:
                st.session_state.admin_member_list = res.json()
        except:
            pass
            
    if st.session_state.get('admin_member_list'):
        df_stats = pd.DataFrame(st.session_state.admin_member_list)
        
        # [수정] 차트 및 통계를 위해 데이터 분리 및 완벽 정제
        def get_clean_clubs_for_stats(club_str):
            if pd.isnull(club_str) or str(club_str).strip() == "": return []
            import re
            clean_str = str(club_str).replace('[', '').replace(']', '').replace("'", "").replace('"', '')
            # 쉼표(,), 전각 쉼표(，), 슬래시(/), 앰퍼샌드(&), 더하기(+) 등 다양한 기호로 확실히 분리
            clubs = re.split(r'[,，/&+]', clean_str)
            # 앞뒤 공백을 완벽히 제거(strip)하여 동일한 동아리가 공백 때문에 두 번 세어지는 현상 방지
            return list(set(c.strip() for c in clubs if c.strip() and c.strip().lower() not in ["소속없음", "소속 없음", "none", "null"]))
            
        exploded_clubs = df_stats['club'].apply(get_clean_clubs_for_stats).explode().dropna()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("총 회원 수", f"{len(df_stats)}명")
        c2.metric("활동 회원", f"{len(df_stats[df_stats['status'] == 'active'])}명")
        c3.metric("관리자", f"{len(df_stats[df_stats['role'] == 'admin'])}명")
        c4.metric("등록 동아리", f"{exploded_clubs.nunique()}개")
        st.markdown("---")
        
        # [기능 추가] 등록된 전체 동아리 목록 작게 표시 (접이식 메뉴)
        with st.expander("📋 등록된 전체 동아리 목록 보기", expanded=False):
            unique_clubs = sorted(exploded_clubs.unique().tolist())
            st.caption(", ".join(unique_clubs))

    # 탭으로 기능 분리
    tab1, tab2, tab3, tab4 = st.tabs(["👥 전체 회원 조회", "📂 명단 일괄 등록", "➕ 신규 회원 등록", "⚙️ 개별 회원 관리"])

    with tab1:
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
            # 데이터프레임 생성
            df = pd.DataFrame(st.session_state.admin_member_list)

            # [기능 추가] 동아리 필터링
            all_clubs = set()
            for clubs_str in df['club'].dropna():
                for c in str(clubs_str).split(','):
                    if c.strip(): all_clubs.add(c.strip())
            all_clubs = sorted(list(all_clubs))
            
            # [기능 추가] 분과 필터링 적용
            available_divisions = sorted(list(set(get_division(c) for c in all_clubs)))
            
            col_div, col_club = st.columns(2)
            with col_div:
                selected_division = st.selectbox("분과별 보기", options=["전체 분과"] + available_divisions)
            
            filtered_clubs_by_div = all_clubs
            if selected_division != "전체 분과":
                filtered_clubs_by_div = [c for c in all_clubs if get_division(c) == selected_division]
                
            with col_club:
                selected_clubs = st.multiselect("동아리별 보기", options=filtered_clubs_by_div, placeholder="해당 분과의 전체 동아리")
                
            # 필터링 적용
            if selected_clubs:
                mask = df['club'].apply(lambda x: any(c in [cs.strip() for cs in str(x).split(',')] for c in selected_clubs) if pd.notnull(x) else False)
                df = df[mask]
            elif selected_division != "전체 분과":
                mask = df['club'].apply(lambda x: any(get_division(c.strip()) == selected_division for c in str(x).split(',')) if pd.notnull(x) else False)
                df = df[mask]

            # [기능 추가] 엑셀(CSV) 다운로드 버튼 (필터링된 결과 반영)
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 회원 명단 다운로드 (CSV)",
                data=csv,
                file_name=f"members_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

            # [기능 개선] 여러 동아리에 소속된 경우 데이터 표에서 행(row)을 분리하여 각 동아리별로 표시
            df_display = df.copy()
            df_display['club'] = df_display['club'].apply(lambda x: [c.strip() for c in str(x).split(',')] if pd.notnull(x) and str(x).strip() else ["소속없음"])
            df_display = df_display.explode('club')
            
            # 필터가 선택된 상태라면 선택한 동아리(또는 분과) 행만 화면에 표시
            if selected_clubs:
                df_display = df_display[df_display['club'].isin(selected_clubs)]
            elif selected_division != "전체 분과":
                df_display = df_display[df_display['club'].apply(lambda c: get_division(c) == selected_division)]

            # 선택 컬럼 추가 (화면 표시용)
            df_display.insert(0, "선택", False)
            
            # 데이터 에디터로 출력 (체크박스 기능)
            edited_df = st.data_editor(
                df_display,
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
                        time.sleep(0.5) # 삭제 후 대기 시간 단축
                        st.rerun()
                with col_no:
                    if st.button("❌ 취소", key="confirm_no_bulk"):
                        del st.session_state['delete_confirm_targets']
                        st.rerun()

    with tab2:
        st.info("엑셀 파일의 컬럼 순서가 달라도 아래에서 직접 지정하여 업로드할 수 있습니다.")
        st.warning("💡 **한글 파일(.hwp) 관련 안내**\n\n한글 문서는 내부에 여러 표와 텍스트가 섞여 있어 시스템이 명단만 정확히 추출하기 어렵습니다. 한글 파일의 명단 표를 복사하여 **엑셀에 붙여넣고 .xlsx 형식으로 저장**한 뒤 업로드해 주세요.")
        uploaded_file = st.file_uploader("명단 파일 업로드 (xlsx, csv)", type=["xlsx", "csv"])
        
        if uploaded_file:
            try:
                # 1. 파일 읽기 (Pandas 활용)
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                st.write("▼ 파일 미리보기 (상위 5개 행)")
                st.dataframe(df.head(), use_container_width=True)
                
                # 2. 컬럼 매핑 UI
                st.subheader("컬럼 연결 (Mapping)")
                cols = df.columns.tolist()
                
                c1, c2, c3 = st.columns(3)
                with c1:
                    name_col = st.selectbox("이름이 있는 열", cols, index=0 if len(cols) > 0 else 0)
                with c2:
                    sid_col = st.selectbox("학번이 있는 열", cols, index=1 if len(cols) > 1 else 0)
                with c3:
                    club_col = st.selectbox("소속이 있는 열", cols, index=2 if len(cols) > 2 else 0)
                
                # 3. 업로드 버튼
                if st.button("설정된 내용으로 업로드 시작", type="primary"):
                    # 데이터 정제 (문자열 변환 및 소수점 제거)
                    new_df = pd.DataFrame()
                    new_df['name'] = df[name_col].astype(str).str.strip()
                    # 학번이 숫자로 읽혔을 경우 .0 제거 로직
                    new_df['sid'] = df[sid_col].apply(lambda x: str(int(x)) if pd.notnull(x) and isinstance(x, float) and x.is_integer() else str(x).strip())
                    new_df['club'] = df[club_col].astype(str).str.strip()
                    
                    # CSV로 변환 (메모리 상에서 처리) - 백엔드는 (이름, 학번, 소속) 순서의 CSV를 기대함
                    csv_buffer = io.StringIO()
                    # 헤더 없이 데이터만 전송 (백엔드 로직 단순화)
                    new_df.to_csv(csv_buffer, index=False, header=False)
                    csv_bytes = csv_buffer.getvalue().encode('utf-8-sig')
                    
                    files = {"file": ("upload.csv", csv_bytes, "text/csv")}
                    
                    try:
                        res = requests.post(f"{API_URL}/admin/upload-csv", headers=headers, files=files)
                        if res.status_code == 200:
                            st.success(f"업로드 성공! {res.json().get('message', '')}")
                        elif res.status_code == 401:
                            st.error("세션이 만료되었습니다. 다시 로그인해주세요.")
                            time.sleep(1)
                            do_logout()
                        else:
                            try: err_msg = res.json().get('detail')
                            except: err_msg = res.text
                            st.error(f"업로드 실패: {err_msg}")
                    except requests.exceptions.RequestException:
                        st.error("서버 연결 실패")
                        
            except Exception as e:
                st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")

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
                            st.success(f"✅ {new_name}({new_sid}) 등록 (또는 동아리 추가) 완료!")
                        elif res.status_code == 401:
                            st.error("세션이 만료되었습니다. 다시 로그인해주세요.")
                            time.sleep(1)
                            do_logout()
                        else:
                            st.error(f"❌ 등록 실패: {res.json().get('detail')}")
                    except requests.exceptions.RequestException:
                        st.error("서버 오류 발생")
                else:
                    st.warning("모든 정보를 입력해주세요.")

    with tab4:
        # 회원 목록 데이터가 없으면 로드 시도
        if not st.session_state.get('admin_member_list'):
            try:
                res = requests.get(f"{API_URL}/admin/members", headers=headers)
                if res.status_code == 200:
                    st.session_state.admin_member_list = res.json()
            except:
                pass

        if st.session_state.get('admin_member_list'):
            # 개별 동아리 목록 추출
            all_clubs_tab4 = set()
            for m in st.session_state.admin_member_list:
                for c in (m.get('club') or "").split(','):
                    if c.strip(): all_clubs_tab4.add(c.strip())
            all_clubs_tab4 = sorted(list(all_clubs_tab4))
            
            # [기능 추가] 개별 회원 관리에도 분과 필터 연동
            available_divisions_tab4 = sorted(list(set(get_division(c) for c in all_clubs_tab4)))
            
            col_div_4, col_club_4 = st.columns(2)
            with col_div_4:
                selected_division_tab4 = st.selectbox("분과 필터", options=["전체 분과"] + available_divisions_tab4)
            
            filtered_clubs_tab4 = all_clubs_tab4
            if selected_division_tab4 != "전체 분과":
                filtered_clubs_tab4 = [c for c in all_clubs_tab4 if get_division(c) == selected_division_tab4]
                
            with col_club_4:
                selected_club_tab4 = st.selectbox("동아리 필터", options=["전체 동아리"] + filtered_clubs_tab4)
                
            filtered_members = st.session_state.admin_member_list
            
            if selected_division_tab4 != "전체 분과":
                filtered_members = [m for m in filtered_members if any(get_division(c.strip()) == selected_division_tab4 for c in (m.get('club') or "").split(','))]
                
            if selected_club_tab4 != "전체 동아리":
                filtered_members = [m for m in filtered_members if selected_club_tab4 in [c.strip() for c in (m.get('club') or "").split(',')]]
            
            # [기능 추가] 특정 동아리 선택 시, 해당 동아리 전체 회원증 갤러리 뷰 제공
            if selected_club_tab4 != "전체 동아리" and filtered_members:
                with st.expander(f"🖼️ '{selected_club_tab4}' 소속 회원증 한눈에 보기", expanded=False):
                    cols = st.columns(2) # 2열로 회원증 나열
                    for i, m in enumerate(filtered_members):
                        with cols[i % 2]:
                            st.markdown(get_card_html(m, is_preview=True), unsafe_allow_html=True)

            if filtered_members:
                # [기능 개선] 여러 동아리에 소속된 경우 콤마로 묶지 않고 각각 분리하여 목록에 표시
                member_dict = {}
                for m in filtered_members:
                    clubs = [c.strip() for c in (m.get('club') or "소속없음").split(',') if c.strip()]
                    if not clubs:
                        clubs = ["소속없음"]
                    
                    if selected_club_tab4 != "전체 동아리":
                        # 특정 동아리를 필터링한 경우 해당 동아리 이름으로만 표시
                        label = f"[{selected_club_tab4}] {m['name']} ({m['student_id']})"
                        member_dict[label] = m['student_id']
                    elif selected_division_tab4 != "전체 분과":
                        # 분과 필터만 적용된 경우, 해당 분과의 동아리만 표시
                        for c in clubs:
                            if get_division(c) == selected_division_tab4:
                                label = f"[{c}] {m['name']} ({m['student_id']})"
                                member_dict[label] = m['student_id']
                    else:
                        # 전체 동아리일 경우, 각각의 동아리별로 개별 항목 생성
                        for c in clubs:
                            label = f"[{c}] {m['name']} ({m['student_id']})"
                            member_dict[label] = m['student_id']
                            
                sorted_labels = sorted(list(member_dict.keys()))
                selected_member = st.selectbox("관리할 대상 선택", options=sorted_labels)
                target_id = member_dict[selected_member]
            else:
                st.warning("해당 동아리에 등록된 회원이 없습니다.")
                target_id = None
        else:
            target_id = st.text_input("관리할 대상 학번")
        
        # [기능 추가] 선택된 회원의 회원증 미리보기
        if st.session_state.get('admin_member_list') and target_id:
            target_member = next((m for m in st.session_state.admin_member_list if m['student_id'] == target_id), None)
            if target_member:
                with st.expander("💳 회원증 미리보기 (디자인 확인용)", expanded=False):
                    st.markdown(get_card_html(target_member, is_preview=True), unsafe_allow_html=True)

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
                    elif res.status_code == 401:
                        st.error("세션이 만료되었습니다. 다시 로그인해주세요.")
                        time.sleep(1)
                        do_logout()
                    else:
                        st.error(f"변경 실패: {res.json().get('detail')}")
                except requests.exceptions.RequestException:
                    st.error("서버 연결 실패")
            else:
                st.warning("학번과 변경할 동아리 이름을 모두 입력해주세요.")

        st.markdown("---")
        st.subheader("학번 변경")
        new_sid_input = st.text_input("변경할 새로운 학번", placeholder="예: 20250001")
        if st.button("학번 변경 적용"):
            if target_id and new_sid_input:
                try:
                    res = requests.patch(f"{API_URL}/admin/members/{target_id}/id", 
                                         headers=headers, params={"new_id": new_sid_input})
                    if res.status_code == 200:
                        st.success(f"학번이 '{new_sid_input}'로 변경되었습니다.")
                        st.session_state.admin_member_list = None # 목록 갱신 유도
                        time.sleep(1)
                        st.rerun()
                    elif res.status_code == 401:
                        st.error("세션이 만료되었습니다. 다시 로그인해주세요.")
                        time.sleep(1)
                        do_logout()
                    else:
                        st.error(f"변경 실패: {res.json().get('detail')}")
                except requests.exceptions.RequestException:
                    st.error("서버 연결 실패")
            else:
                st.warning("변경할 학번을 입력해주세요.")

        st.markdown("---")
        st.subheader("계정 상태 및 관리")
        
        # 권한 변경 기능 추가
        new_role = st.selectbox("권한 설정", ["member", "admin"], index=0)
        if st.button("권한 변경 적용"):
            if target_id:
                try:
                    res = requests.patch(f"{API_URL}/admin/members/{target_id}/role", 
                                         headers=headers, params={"role": new_role})
                    if res.status_code == 200: st.success(f"권한이 '{new_role}'로 변경되었습니다.")
                    if res.status_code == 200: 
                        st.success(f"권한이 '{new_role}'로 변경되었습니다.")
                    elif res.status_code == 401:
                        st.error("세션이 만료되었습니다. 다시 로그인해주세요.")
                        time.sleep(1)
                        do_logout()
                    else: st.error(f"변경 실패: {res.json().get('detail')}")
                except requests.exceptions.RequestException:
                    st.error("서버 연결 실패")
            else:
                st.warning("학번을 입력해주세요.")

        col1, col2 = st.columns(2)
        with col1:
            new_status = st.selectbox("상태 선택", ["active", "inactive"])
            if st.button("상태 변경 적용"):
                res = requests.patch(f"{API_URL}/admin/members/{target_id}/status", 
                                     headers=headers, params={"status": new_status})
                if res.status_code == 200: st.success("변경 완료")
                elif res.status_code == 401:
                    do_logout()
                else: st.error("변경 실패")
        with col2:
            if st.button("비밀번호 초기화 ('1234')"):
                if target_id:
                    res = requests.patch(f"{API_URL}/admin/members/{target_id}/reset-password", headers=headers)
                    if res.status_code == 200:
                        st.success(f"{target_id}의 비밀번호가 '1234'로 초기화되었습니다.")
                    elif res.status_code == 401:
                        do_logout()
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
                                time.sleep(0.3) # 삭제 후 대기 시간 단축
                                st.rerun()
                            elif res.status_code == 401:
                                do_logout()
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
    # --- 만료 시간 체크 및 자동 로그아웃 (새로고침) ---
    if st.session_state.get('expire_time'):
        remaining = (st.session_state.expire_time - datetime.now()).total_seconds()
        if remaining <= 0:
            st.warning("세션이 만료되었습니다. 자동으로 로그아웃됩니다.")
            time.sleep(1)
            do_logout()
            return
        else:
            # [기능 추가] 세션 연장 기능 (백엔드 토큰 갱신 및 프론트 시간 초기화)
            st.markdown("""
                <style>
                    /* 파이썬 연장 버튼이 화면에 보이지 않도록 CSS로 완벽하게 숨김 (깜빡임 방지) */
                    div[data-testid="stElementContainer"]:has(.hide-extend-btn) { display: none; }
                    div[data-testid="stElementContainer"]:has(.hide-extend-btn) + div[data-testid="stElementContainer"] { 
                        position: absolute !important; opacity: 0 !important; z-index: -1 !important; 
                    }
                </style>
                <div class="hide-extend-btn"></div>
            """, unsafe_allow_html=True)
            if st.button("extend_hidden_btn", key="extend_session_btn"):
                if st.session_state.extend_count < 3:
                    headers = {"Authorization": f"Bearer {st.session_state.token}"}
                    try:
                        res = requests.post(f"{API_URL}/token/refresh", headers=headers)
                        if res.status_code == 200:
                            st.session_state.token = res.json()['access_token']
                            st.session_state.expire_time = datetime.now() + timedelta(minutes=10)
                            st.session_state.extend_count += 1
                            st.session_state.save_ls = True
                            st.rerun()
                        elif res.status_code == 401:
                            do_logout()
                    except:
                        pass

            # 화면 우측 상단에 남은 시간을 표시하고, 시간이 지나면 새로고침하여 로그아웃 처리
            st.components.v1.html(f"""
                <script>
                    const parentDoc = window.parent.document;
                    const parentWin = window.parent;
                    let remaining = {int(remaining)};
                    
                    // 매번 렌더링될 때마다 실제 파이썬 연장 버튼(extend_hidden_btn)을 화면에서 숨기기 처리
                    const btns = Array.from(parentDoc.querySelectorAll('button'));
                    const hiddenBtn = btns.find(b => b.textContent.includes('extend_hidden_btn'));
                    if (hiddenBtn) {{
                        const btnContainer = hiddenBtn.closest('.stButton');
                        if (btnContainer) {{
                            btnContainer.style.position = 'absolute';
                            btnContainer.style.opacity = '0';
                            btnContainer.style.zIndex = '-1';
                        }}
                    }}

                    // 기존 타이머 초기화 (중복 방지)
                    if (parentWin.logoutTimerInterval) {{
                        parentWin.clearInterval(parentWin.logoutTimerInterval);
                    }}
                    
                    // 타이머 UI 생성 또는 선택
                    let timerDiv = parentDoc.getElementById('logout-timer');
                    if (!timerDiv) {{
                        timerDiv = parentDoc.createElement('div');
                        timerDiv.id = 'logout-timer';
                        timerDiv.style.cssText = 'position: fixed; top: 15px; right: 15px; background: rgba(10, 25, 47, 0.8); border: 1px solid rgba(228, 212, 164, 0.4); padding: 8px 15px; border-radius: 8px; color: #E4D4A4; font-weight: bold; z-index: 999999; box-shadow: 0 4px 10px rgba(0,0,0,0.5); font-family: monospace; font-size: 1.1rem; backdrop-filter: blur(5px); transition: color 0.3s, border-color 0.3s; display: flex; align-items: center; gap: 12px;';
                        
                        // 시간 표시 영역
                        let timeSpan = parentDoc.createElement('span');
                        timeSpan.id = 'logout-time-span';
                        timerDiv.appendChild(timeSpan);
                        
                        parentDoc.body.appendChild(timerDiv);
                    }}
                    
                    let timeSpan = parentDoc.getElementById('logout-time-span');

                    // 연장 버튼 (렌더링될 때마다 남은 횟수 텍스트 새로고침)
                    let extendBtn = parentDoc.getElementById('extend-session-btn');
                    if (!extendBtn) {{
                        extendBtn = parentDoc.createElement('button');
                        extendBtn.id = 'extend-session-btn';
                        timerDiv.appendChild(extendBtn);
                    }}

                    let extendCount = {st.session_state.extend_count};
                    if (extendCount >= 3) {{
                        extendBtn.innerText = '연장 불가';
                        extendBtn.style.cssText = 'background: rgba(255,255,255,0.2); color: rgba(255,255,255,0.5); border: none; border-radius: 6px; padding: 4px 10px; font-size: 0.85rem; font-weight: 800; cursor: not-allowed;';
                        extendBtn.disabled = true;
                    }} else {{
                        extendBtn.innerText = '연장 (' + (3 - extendCount) + '회)';
                        extendBtn.style.cssText = 'background: #E4D4A4; color: #050A18; border: none; border-radius: 6px; padding: 4px 10px; font-size: 0.85rem; font-weight: 800; cursor: pointer; transition: transform 0.1s;';
                        extendBtn.disabled = false;
                        extendBtn.onmouseover = () => extendBtn.style.transform = 'scale(1.05)';
                        extendBtn.onmouseout = () => extendBtn.style.transform = 'scale(1)';
                        extendBtn.onclick = function() {{
                            extendBtn.innerText = '연장 중...';
                            extendBtn.disabled = true;
                            const currentBtns = Array.from(parentDoc.querySelectorAll('button'));
                            const currentHiddenBtns = currentBtns.filter(b => b.textContent.includes('extend_hidden_btn'));
                            if (currentHiddenBtns.length > 0) {{
                                currentHiddenBtns[currentHiddenBtns.length - 1].click();
                            }}
                        }};
                    }}

                    function updateTimer() {{
                        if (remaining <= 0) {{
                            parentWin.clearInterval(parentWin.logoutTimerInterval);
                            if (timeSpan) timeSpan.innerText = '⏱️ 00:00';
                            parentWin.location.reload();
                            return;
                        }}
                        
                        let m = Math.floor(remaining / 60);
                        let s = Math.floor(remaining % 60);
                        if (timeSpan) timeSpan.innerText = '⏱️ ' + (m < 10 ? '0' + m : m) + ':' + (s < 10 ? '0' + s : s);
                        
                        // 1분 이하로 남으면 빨간색으로 경고 표시
                        if (remaining <= 60) {{
                            timerDiv.style.color = '#ff4b4b';
                            timerDiv.style.borderColor = '#ff4b4b';
                        }} else {{
                            timerDiv.style.color = '#E4D4A4';
                            timerDiv.style.borderColor = 'rgba(228, 212, 164, 0.4)';
                        }}
                        
                        remaining--;
                    }}
                    
                    updateTimer(); // 즉시 실행
                    parentWin.logoutTimerInterval = parentWin.setInterval(updateTimer, 1000);
                </script>
            """, height=0)

    # 토큰을 사용하여 회원 정보 가져오기
    if st.session_state.member_info is None:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        try:
            with st.spinner("회원 정보를 불러오는 중입니다..."):
                response = requests.get(f"{API_URL}/members/me", headers=headers)
                if response.status_code == 200:
                    st.session_state.member_info = response.json()
                else: # 토큰이 만료되었거나 유효하지 않은 경우
                    do_logout()
                    return
        except requests.exceptions.ConnectionError:
            st.error("백엔드 서버에 연결할 수 없습니다.")
            st.session_state.clear()
            st.session_state.clear_ls = True
            st.session_state.local_storage_checked = True
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
    # [수정] 공통 함수 사용하여 회원증 렌더링
    st.markdown(get_card_html(info), unsafe_allow_html=True)

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
        do_logout()


# --- 메인 실행 로직 ---

if st.session_state.token is None:
    # 로그아웃 상태일 때, 떠 있는 타이머가 남아있다면 깔끔하게 제거
    st.components.v1.html("""
        <script>
            const parentDoc = window.parent.document;
            const timerDiv = parentDoc.getElementById('logout-timer');
            if (timerDiv) timerDiv.remove();
            if (window.parent.logoutTimerInterval) {
                window.parent.clearInterval(window.parent.logoutTimerInterval);
            }
        </script>
    """, height=0)
    show_login_page()
else:
    show_membership_card()
