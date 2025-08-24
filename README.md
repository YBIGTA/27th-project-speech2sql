# 강의·회의록 생성 및 검색 시스템 (Speech2SQL)

## 📋 프로젝트 개요

### 목표
- 오디오 파일 → **자동 요약 PDF** + **구조화 DB 저장**
- 자연어 질의를 SQL로 변환해 DB에서 직접 검색
- 발언자, 타임스탬프, 키워드 인덱스를 활용한 고속 조회 가능

### 핵심 가치
- 강의·회의록을 **읽는 문서 → 검색 가능한 지식베이스**로 전환
- 기업·학술·강의 환경에서 정보 검색 효율 극대화
- 빅데이터를 통한 인사이트 도출 및 새로운 가치 창출

## 🏗️ 시스템 아키텍처

```
[Audio File Upload] → [Whisper STT + Speaker Diarization] → [Summarization] → [PDF Summary]
                                    ↓
                              [NL2SQL 변환] → [Database 저장] → [자연어 질의] → [SQL 실행] → [결과 테이블]
```

## 🛠️ 기술 스택

- **STT**: OpenAI Whisper (다국어·잡음 환경 인식)
- **요약**: Upstage LLM API (한국어 특화 요약)
- **NL2SQL**: Huggingface Text2SQL 모델
- **백엔드**: FastAPI
- **DB**: PostgreSQL
- **프론트**: Streamlit
- **LLM API**: Upstage, OpenAI

## ✨ 주요 기능

### 🎵 **오디오 처리**
- 다국어 오디오 파일 업로드 (WAV, MP3, M4A)
- Whisper 기반 Speech-to-Text 변환
- Speaker Diarization (발화자 분리)
- 실시간 처리 상태 확인

### 📝 **요약 생성**
- **일반 요약**: 회의 전체 내용의 핵심 요약
- **액션 아이템 중심**: 할 일과 담당자 추출
- **결정사항 중심**: 회의에서 내린 결정 추출
- **다국어 지원**: 한국어/영어 요약 생성
- **PDF 생성**: 깔끔한 PDF 요약본 다운로드

### 🔍 **자연어 검색**
- **Text2SQL 모드**: 자연어를 SQL로 변환하여 정확한 검색
- **Full-Text Search 모드**: 키워드 기반 빠른 검색
- **AI 답변**: 검색 결과를 자연어로 요약 제공
- **회의별 필터링**: 특정 회의 범위로 검색 제한

### 📊 **분석 및 인사이트**
- 회의별 참가자 분석
- 액션 아이템 및 결정사항 추적
- 회의 효율성 지표 제공
- 월별 트렌드 분석

## 📁 프로젝트 구조

```
speech2sql/
├── README.md
├── requirements.txt
├── .env.example
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── database.py
├── data/
│   ├── raw/                 # 원본 오디오 파일
│   ├── processed/           # 처리된 데이터
│   └── summaries/           # 생성된 PDF 요약본
├── src/
│   ├── __init__.py
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── whisper_stt.py   # Whisper STT 처리
│   │   └── speaker_diarization.py  # 발화자 분리
│   ├── nlp/
│   │   ├── __init__.py
│   │   ├── summarization.py # 요약 모델
│   │   └── text2sql.py      # NL2SQL 변환
│   ├── agents/
│   │   ├── __init__.py
│   │   └── agenda_analysis_agent.py  # 회의 분석 에이전트
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py        # DB 스키마
│   │   └── operations.py    # DB 작업
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI 앱
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── audio.py     # 오디오 업로드
│   │       ├── query.py     # 자연어 질의
│   │       ├── summary.py   # 요약 생성
│   │       ├── search.py    # 검색 기능
│   │       └── analysis.py  # 분석 기능
│   └── utils/
│       ├── __init__.py
│       ├── file_utils.py    # 파일 처리
│       └── pdf_generator.py # PDF 생성
├── frontend/
│   ├── app.py               # Streamlit 메인 앱
│   └── static/
│       ├── css/
│       └── js/
├── tests/
│   ├── __init__.py
│   ├── test_audio.py
│   ├── test_nlp.py
│   ├── test_api.py
│   └── test_llm_extraction.py  # LLM 추출 테스트
├── notebooks/
│   ├── data_analysis.ipynb  # 데이터 분석
│   ├── model_evaluation.ipynb  # 모델 평가
│   └── insights.ipynb       # 인사이트 도출
├── docs/
│   └── api/                 # API 문서
└── scripts/
    ├── setup.py             # 환경 설정
    ├── data_preparation.py  # 데이터 준비
    └── model_training.py    # 모델 학습
```

## 🚀 실행 방법

### 🎯 **팀원 첫 설정 (권장)**
```bash
# 1. 프로젝트 클론
git clone <repository-url>
cd speech2sql

# 2. 자동 설정 스크립트 실행
python scripts/setup.py

# 3. .env 파일에서 API 키 설정
# UPSTAGE_API_KEY=your_upstage_api_key_here
# OPENAI_API_KEY=your_openai_api_key_here
# POSTGRESQL_PASSWORD=your_database_password_here

# 4. 백엔드 실행
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# 5. 새 터미널에서 프론트엔드 실행
streamlit run frontend/app.py

# 6. 접속
# 프론트엔드: http://localhost:8501
# 백엔드 API: http://localhost:8000
# API 문서: http://localhost:8000/docs
```

### 🔧 **수동 설정 (고급 사용자)**
```bash
# 1. 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 환경 변수 설정
cp .env.example .env
# .env 파일 편집

# 4. PostgreSQL 설치 및 설정
# Windows: https://www.postgresql.org/download/windows/
# macOS: brew install postgresql
# Ubuntu: sudo apt install postgresql postgresql-contrib

# 5. 애플리케이션 실행
python -m uvicorn src.api.main:app --reload
streamlit run frontend/app.py
```

## 🎨 사용자 인터페이스

### 📤 **파일 업로드**
- 드래그 앤 드롭으로 오디오 파일 업로드
- 지원 형식: WAV, MP3, M4A
- 실시간 처리 상태 확인
- 자동 STT 및 발화자 분리

### 📝 **요약 생성**
- **간편한 요약 생성**: 언어 선택만으로 즉시 요약 생성
- **회의 주제 표시**: LLM이 추출한 회의 제목을 상단에 표시
- **깔끔한 레이아웃**: 회색 박스에 요약 내용 표시
- **PDF 다운로드**: 부가 기능으로 PDF 요약본 생성

### 🔍 **자연어 검색**
- **직관적인 검색**: 자연어로 질문하면 AI가 답변
- **검색 모드 선택**: Text2SQL (정확한 검색) vs FTS (빠른 검색)
- **회의별 필터링**: 특정 회의로 검색 범위 제한
- **AI 답변**: 검색 결과를 자연어로 요약 제공

### 📊 **분석 대시보드**
- 회의별 참가자 분석
- 액션 아이템 및 결정사항 추적
- 월별 트렌드 분석
- 회의 효율성 지표

## 📊 데이터베이스 스키마

### meetings 테이블
- id: 고유 식별자
- title: 회의 제목
- date: 회의 날짜
- duration: 회의 시간
- participants: 참가자 목록
- summary: 요약 내용
- summary_type: 요약 유형 (general, action_items, decisions)
- audio_path: 오디오 파일 경로

### utterances 테이블
- id: 고유 식별자
- meeting_id: 회의 ID (FK)
- speaker: 발화자
- timestamp: 타임스탬프
- text: 발화 내용
- confidence: STT 신뢰도

### actions 테이블
- id: 고유 식별자
- meeting_id: 회의 ID (FK)
- action_type: 액션 타입 (decision, assignment, discussion)
- description: 액션 설명
- assignee: 담당자
- due_date: 마감일
- status: 상태 (pending, completed, cancelled)
- priority: 우선순위 (low, medium, high)