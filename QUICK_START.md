# 🚀 Speech2SQL 빠른 시작 가이드

## 📋 프로젝트 개요

**Speech2SQL**은 강의·회의록을 자동으로 생성하고 자연어로 검색할 수 있는 시스템입니다.

### 주요 기능
- 🎵 **오디오 처리**: Whisper STT + Speaker Diarization
- 🧠 **자연어 처리**: 요약 생성 + Text2SQL 변환
- 🗄️ **데이터베이스**: 구조화된 저장 및 검색
- 📊 **분석**: 회의 패턴 및 인사이트 도출

## 🛠️ 빠른 설치·실행 (권장 플로우)
```bash
# 0) Python 3.8+ 확인
python --version

# 1) 저장소 클론
git clone <repository-url>
cd speech2sql

# 2) PostgreSQL 설치 및 데이터베이스 생성
#    - Windows: https://www.postgresql.org/download/windows/
#    - macOS:   brew install postgresql && brew services start postgresql
#    - Ubuntu:  sudo apt update && sudo apt install postgresql postgresql-contrib
#    - 관리자 툴(pgAdmin 등)에서 생성: Databases 우클릭 → Create → Database → 이름: speech2sql, Owner: postgres
#      (또는 psql에서: CREATE DATABASE speech2sql;)

# 3) 초기 설정 스크립트 실행 (의존성/폴더 생성)
python scripts/setup.py

# 4) .env에 PostgreSQL 비밀번호 설정
#    - POSTGRESQL_PASSWORD=your_password
#    - 비밀번호에 특수문자 있으면 POSTGRESQL_URL에는 URL 인코딩 반영 필요

# 5) 설정 반영 점검 (선택)
python scripts/setup.py

# 6) AMI 샘플 적재 (30GB 여유 공간 필요)
python scripts/import_hf_ami.py

# 7) 백엔드 서버 실행 (터미널 A)
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# 8) 적재 확인 (터미널 B에서 실행)
curl -X POST http://localhost:8000/api/v1/query/natural \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"data\",\"limit\":5}"

# 9) 프론트엔드 실행 (터미널 C)
#    - 브라우저에서 http://localhost:8501 접속
#    - 업로드 탭에서 WAV 파일 업로드(현재 WAV만 지원)
#    - 참고: data/raw 폴더에 sample.wav를 두고 테스트해도 좋음
streamlit run frontend/app.py
```

### 접속 정보
- **프론트엔드**: http://localhost:8501
- **백엔드 API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs

---

**🎯 목표**: 강의·회의록을 읽는 문서에서 검색 가능한 지식베이스로 전환하여 정보 검색 효율을 극대화하자!
