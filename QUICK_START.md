# 🚀 Speech2SQL 빠른 시작 가이드

## 📋 프로젝트 개요

**Speech2SQL**은 강의·회의록을 자동으로 생성하고 자연어로 검색할 수 있는 시스템입니다.

### 주요 기능
- 🎵 **오디오 처리**: Whisper STT + Speaker Diarization
- 🧠 **자연어 처리**: 요약 생성 + Text2SQL 변환
- 🗄️ **데이터베이스**: 구조화된 저장 및 검색
- 📊 **분석**: 회의 패턴 및 인사이트 도출

## 🛠️ 설치 및 실행

### 1. 환경 설정
```bash
# Python 3.8+ 설치 확인
python --version

# 프로젝트 클론
git clone <repository-url>
cd speech2sql

# 자동 설정 스크립트 실행
python scripts/setup.py

# 또는 수동 설정
# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정
```bash
# setup.py가 자동으로 .env 파일을 생성합니다
# .env 파일 편집하여 API 키 설정
# UPSTAGE_API_KEY=your_upstage_api_key_here
# OPENAI_API_KEY=your_openai_api_key_here
# POSTGRESQL_PASSWORD=your_database_password_here
```

### 3. 데이터베이스 설정
```bash
# PostgreSQL 설치 (setup.py가 설치 가이드를 제공합니다)

# Windows:
# 1. https://www.postgresql.org/download/windows/ 에서 다운로드
# 2. 설치 시 비밀번호 설정 (기본: password)
# 3. .env 파일에서 POSTGRESQL_PASSWORD 수정

# macOS:
# brew install postgresql
# brew services start postgresql

# Ubuntu/Debian:
# sudo apt update && sudo apt install postgresql postgresql-contrib
# sudo systemctl start postgresql
# sudo systemctl enable postgresql
```

### 4. 프로젝트 실행
```bash
# 백엔드 서버 실행
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# 새 터미널에서 프론트엔드 실행
streamlit run frontend/app.py
```

### 5. 접속
- **프론트엔드**: http://localhost:8501
- **백엔드 API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs


## 📁 프로젝트 구조

```
speech2sql/
├── README.md              # 프로젝트 개요
├── TEAM_ASSIGNMENT.md     # 팀 역할 분배
├── QUICK_START.md         # 빠른 시작 가이드
├── requirements.txt       # Python 의존성
├── env.example           # 환경 변수 템플릿
├── config/               # 설정 파일
├── src/                  # 소스 코드
│   ├── audio/           # 오디오 처리 (팀원 A)
│   ├── nlp/             # 자연어 처리 (팀원 B)
│   ├── database/        # 데이터베이스 (팀원 C)
│   ├── api/             # FastAPI 백엔드 (팀원 C)
│   └── utils/           # 유틸리티 (팀원 D)
├── frontend/            # Streamlit 프론트엔드 (팀원 D)
├── data/                # 데이터 저장소
├── tests/               # 테스트 코드
├── notebooks/           # 분석 노트북
├── docs/                # 문서
└── scripts/             # 스크립트
```

## 🔧 개발 워크플로우

### 1. 브랜치 전략
```bash
# 기능 개발
git checkout -b feature/audio-processing
git checkout -b feature/nlp-models
git checkout -b feature/api-endpoints
git checkout -b feature/frontend-ui

# 버그 수정
git checkout -b fix/audio-bug
```

### 2. 코드 리뷰
- 모든 PR은 팀장의 리뷰 필수
- 테스트 코드 작성 권장
- 문서화 필수

### 3. 테스트 실행
```bash
# 전체 테스트
pytest

# 특정 모듈 테스트
pytest tests/test_audio.py
pytest tests/test_nlp.py
pytest tests/test_api.py
```

## 📊 성과 지표

### 팀원별 KPI
- **팀장**: 프로젝트 완성도, 팀 협업 효율성
- **팀원 A**: STT 정확도 (WER), 처리 속도
- **팀원 B**: 요약 품질, Text2SQL 정확도
- **팀원 C**: API 응답 시간, 데이터베이스 성능
- **팀원 D**: 사용자 만족도, UI/UX 품질

## 🔬 연구 및 인사이트

### 분석 영역
1. **회의 효율성**: 시간 대비 결정사항 수
2. **참가자별 특성**: 발화 패턴, 영향력 분석
3. **의사결정 프로세스**: 논의 과정과 결과의 상관관계

### 오픈소스 기술 이해
- Whisper 아키텍처 및 fine-tuning
- Speaker Diarization 알고리즘
- Text2SQL 모델 내부 동작
- 대용량 오디오 처리 최적화

## 🚨 문제 해결

### 자주 발생하는 문제
1. **의존성 설치 실패**: Python 버전 확인 (3.8+)
2. **API 키 오류**: .env 파일 설정 확인
3. **데이터베이스 연결 실패**: PostgreSQL 서비스 실행 확인
4. **포트 충돌**: 다른 포트 사용 (8001, 8502 등)
5. **setup.py 실행 실패**: Python 경로 확인, 권한 문제 해결

### setup.py 관련 문제
```bash
# 권한 문제 (Windows)
python scripts/setup.py

# 가상환경 활성화 후 실행
source venv/bin/activate  # Windows: venv\Scripts\activate
python scripts/setup.py

# 수동으로 .env 파일 생성
cp .env.example .env
```

### 로그 확인
```bash
# 백엔드 로그
tail -f logs/backend.log

# 프론트엔드 로그
tail -f logs/frontend.log
```

## 📞 지원 및 문의

- **기술적 이슈**: GitHub Issues 사용
- **팀 내 소통**: 정기 미팅 및 Slack/Teams
- **문서**: `docs/` 폴더 참조

---

**🎯 목표**: 강의·회의록을 읽는 문서에서 검색 가능한 지식베이스로 전환하여 정보 검색 효율을 극대화하자! 