# 디지털 회원증 시스템 (Digital Membership System)

FastAPI와 Streamlit으로 구현된 웹 기반 디지털 회원증 시스템입니다. 사용자는 로그인을 통해 자신의 회원증을 확인할 수 있으며, 관리자는 회원 목록 관리, 일괄 등록, 상태 변경 등의 기능을 수행할 수 있습니다.

## ✨ 주요 기능

- **사용자 기능**
  - 학번/비밀번호 기반 로그인 (JWT 인증)
  - 디지털 회원증 확인 (이름, 학번, 소속 동아리)
  - 실시간 시간 표시
  - 비밀번호 변경
- **관리자 기능**
  - 관리자 전용 대시보드
  - 전체 회원 목록 조회 및 검색
  - CSV 파일을 통한 회원 일괄 등록
  - 개별 회원 실시간 등록
  - 특정 회원의 활동 상태 변경 및 비밀번호 초기화

## 🛠️ 기술 스택

- **Backend**: Python, FastAPI, SQLAlchemy, Pydantic, Passlib, python-jose
- **Frontend**: Streamlit
- **Database**: PostgreSQL (for deployment), SQLite (for local)
- **Deployment**: Render.com

---

## 🚀 로컬 환경에서 실행하기

### 1. 사전 준비
- Python 3.8 이상 설치
- Git 설치

### 2. 프로젝트 클론 및 설정
```bash
# 1. 프로젝트 코드를 컴퓨터로 복제합니다.
git clone https://github.com/your-username/your-repository.git
cd your-repository

# 2. 필요한 라이브러리를 설치합니다.
pip install -r requirements.txt
```

### 3. 서버 실행
이 프로젝트는 백엔드와 프론트엔드가 분리되어 있으므로, **두 개의 터미널**을 열어 각각 실행해야 합니다.

**터미널 1: 백엔드 서버 (FastAPI)**
```bash
uvicorn main:app --reload
```
> 서버가 `http://127.0.0.1:8000` 에서 실행됩니다.

**터미널 2: 프론트엔드 앱 (Streamlit)**
```bash
streamlit run app.py
```
> 잠시 후 웹 브라우저에서 `http://localhost:8501` 주소로 앱이 자동으로 열립니다.

### 4. 로컬 DB 초기화 및 로그인
1.  백엔드 서버가 켜진 상태에서, 웹 브라우저에 다음 주소를 입력하여 초기 계정을 생성합니다.
    `http://127.0.0.1:8000/init-db?secret=local-init-secret`
2.  프론트엔드 앱에서 아래 정보로 로그인합니다.
    - **관리자**: ID `admin` / PW `admin1234`
    - **일반 회원**: ID `20240001` / PW `1234`

---

## ☁️ Render.com 배포 가이드

이 프로젝트는 **데이터베이스, 백엔드, 프론트엔드** 세 부분으로 나누어 배포합니다.

### 1단계: 데이터베이스 생성 (PostgreSQL)
1.  Render 대시보드에서 **New +** > **PostgreSQL** 선택.
2.  이름(예: `membership-db`)을 정하고 **Free** 플랜으로 데이터베이스를 생성합니다.
3.  생성 후, **Info** 탭에서 **Internal Database URL**을 복사합니다.

### 2단계: 백엔드 배포 (FastAPI)
1.  Render 대시보드에서 **New +** > **Web Service** 선택 후, GitHub 저장소를 연결합니다.
2.  아래와 같이 설정합니다.
    - **Name**: `membership-api` (또는 원하는 이름)
    - **Runtime**: `Python 3`
    - **Build Command**: `pip install -r requirements.txt`
    - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
    - **Instance Type**: `Free`
3.  **Environment** 탭에서 아래 환경 변수를 추가합니다.
    - `DATABASE_URL`: (1단계에서 복사한 Internal Database URL)
    - `SECRET_KEY`: (JWT 암호화를 위한 임의의 긴 비밀 문자열)
    - `INIT_DB_SECRET`: (DB 초기화용 비밀 문자열)
4.  **Create Web Service**를 클릭하여 배포를 시작합니다.
5.  배포가 완료되면, 서비스 상단에 표시된 URL(예: `https://membership-api.onrender.com`)을 복사합니다.

### 3단계: 프론트엔드 배포 (Streamlit)
1.  다시 **New +** > **Web Service**를 선택하고 같은 저장소를 연결합니다.
2.  아래와 같이 설정합니다.
    - **Name**: `membership-app` (또는 원하는 이름)
    - **Runtime**: `Python 3`
    - **Build Command**: `pip install -r requirements.txt`
    - **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
    - **Instance Type**: `Free`
3.  **Environment** 탭에서 아래 환경 변수를 추가합니다.
    - `API_URL`: (2단계에서 복사한 백엔드 서비스 URL)
4.  **Create Web Service**를 클릭하여 배포합니다.

### 4단계: 배포 후 최초 DB 초기화
1.  백엔드 배포가 완료된 후, 웹 브라우저에서 아래 형식의 주소로 접속하여 데이터베이스에 초기 계정을 생성합니다.
    > `https://<백엔드_URL>/init-db?secret=<설정한_INIT_DB_SECRET_값>`

2.  화면에 `{"status":"success", ...}` 메시지가 뜨면 성공입니다.
3.  이제 프론트엔드 URL로 접속하여 `admin` / `admin1234`로 로그인할 수 있습니다.

## ⚠️ Render 무료 플랜 참고사항
- **절전 모드(Sleep Mode)**: 15분 동안 트래픽이 없으면 서비스가 절전 모드로 전환됩니다. 절전 상태에서 첫 요청이 오면 다시 깨어나는 데 30초 정도 소요될 수 있습니다.
- **파일 시스템**: 배포된 서비스의 파일 시스템은 영구적이지 않습니다. 재배포되거나 재시작될 때마다 초기화되므로, SQLite 같은 파일 기반 DB는 사용할 수 없습니다. (이 프로젝트는 PostgreSQL을 사용하도록 설정되어 있습니다.)