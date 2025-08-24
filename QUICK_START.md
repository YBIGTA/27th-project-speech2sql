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

## 📊 테스트 데이터 추가하기

### 방법 1: insert_test_data.py 스크립트 사용 (권장)
```bash
# 팀원들이 테스트할 수 있는 샘플 회의 데이터를 DB에 추가
python insert_test_data.py
```

**⚠️ 주의사항**: 이 파일은 Git에 포함되어 있으므로 팀원들이 바로 사용할 수 있습니다.

이 스크립트는 다음과 같은 샘플 데이터를 생성합니다:
- **회의 정보**: 제목, 날짜, 참가자, 지속시간
- **발화 데이터**: 발화자별 텍스트, 타임스탬프, 신뢰도
- **액션 아이템**: 할 일, 담당자, 마감일
- **결정사항**: 회의에서 내린 결정들

### 방법 2: 수동으로 데이터 추가
```bash
# PostgreSQL에 직접 접속하여 데이터 확인/추가
psql -h localhost -U postgres -d speech2sql

# 테이블 구조 확인
\dt

# 샘플 데이터 확인
SELECT * FROM meetings LIMIT 5;
SELECT * FROM utterances WHERE meeting_id = 1 LIMIT 10;
SELECT * FROM actions WHERE meeting_id = 1;
```

### 방법 3: API를 통한 데이터 추가
```bash
# 회의 정보 조회
curl -X GET http://localhost:8000/api/v1/query/meetings

# 특정 회의 상세 정보 조회
curl -X GET http://localhost:8000/api/v1/summary/meeting/1

# 요약 생성 테스트
curl -X POST http://localhost:8000/api/v1/summary/generate \
  -H "Content-Type: application/json" \
  -d '{"meeting_id": 1, "summary_type": "general", "language": "ko"}'
```

## 🧪 기능 테스트하기

### 1. 요약 생성 테스트
```bash
# 프론트엔드에서 테스트
# 1. http://localhost:8501 접속
# 2. "요약 생성" 탭 선택
# 3. 회의 목록에서 샘플 회의 선택
# 4. 언어 선택 (한국어/영어)
# 5. "요약 생성" 버튼 클릭
# 6. 생성된 요약 확인
# 7. PDF 다운로드 테스트
```

### 2. 자연어 검색 테스트
```bash
# 프론트엔드에서 테스트
# 1. "자연어 검색" 탭 선택
# 2. 검색 예시 버튼 사용 또는 직접 질문 입력
# 3. 검색 모드 선택 (text2sql / fts)
# 4. 회의 범위 선택 (전체 또는 특정 회의)
# 5. "검색" 버튼 클릭
# 6. AI 답변 및 검색 결과 확인
```

### 3. 파일 업로드 테스트
```bash
# 1. "파일 업로드" 탭 선택
# 2. 오디오 파일 업로드 (WAV, MP3, M4A)
# 3. 처리 상태 확인
# 4. STT 결과 및 발화자 분리 확인
# 5. 업로드된 회의로 요약 생성 테스트
```

## 🔧 문제 해결

### 일반적인 문제들
```bash
# 1. 데이터베이스 연결 오류
# 해결: PostgreSQL 서비스 시작 확인
# Windows: 서비스 관리자에서 PostgreSQL 서비스 시작
# macOS: brew services start postgresql
# Ubuntu: sudo systemctl start postgresql

# 2. API 키 오류
# 해결: .env 파일에서 API 키 설정 확인
# UPSTAGE_API_KEY=your_key_here
# OPENAI_API_KEY=your_key_here

# 3. 포트 충돌
# 해결: 다른 포트 사용
# 백엔드: python -m uvicorn src.api.main:app --reload --port 8001
# 프론트엔드: streamlit run frontend/app.py --server.port 8502

# 4. 오디오 업로드 오류류
# 해결: wav 파일인지 확인, 용량 제한(100MB) 확인
# 또는 시스템 메모리 확장
```

### 로그 확인
```bash
# 백엔드 로그 확인
# 터미널에서 직접 확인 (--reload 모드)

# 데이터베이스 로그 확인
# PostgreSQL 로그 파일 위치:
# Windows: C:\Program Files\PostgreSQL\[version]\data\pg_log\
# macOS: /usr/local/var/log/postgres.log
# Ubuntu: /var/log/postgresql/postgresql-[version]-main.log
```

---

**🎯 목표**: 강의·회의록을 읽는 문서에서 검색 가능한 지식베이스로 전환하여 정보 검색 효율을 극대화하자!
