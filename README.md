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
- **요약**: PEGASUS, LLaMA2 fine-tune (긴 텍스트 요약)
- **NL2SQL**: Huggingface Text2SQL 모델
- **백엔드**: FastAPI
- **DB**: PostgreSQL
- **프론트**: Streamlit
- **LLM API**: Upstage

## 📁 프로젝트 구조 (참고만 해주세요! 다른 부분이 있을 수 있습니다.)

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
│   ├── models/              # 학습된 모델
│   └── datasets/            # 데이터셋
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
│   │       └── summary.py   # 요약 생성
│   └── utils/
│       ├── __init__.py
│       ├── file_utils.py    # 파일 처리
│       └── pdf_generator.py # PDF 생성
├── frontend/
│   ├── app.py               # Streamlit 앱
│   ├── pages/
│   │   ├── upload.py        # 파일 업로드
│   │   ├── search.py        # 검색 인터페이스
│   │   └── analytics.py     # 분석 대시보드
│   └── static/
│       ├── css/
│       └── js/
├── tests/
│   ├── __init__.py
│   ├── test_audio.py
│   ├── test_nlp.py
│   └── test_api.py
├── notebooks/
│   ├── data_analysis.ipynb  # 데이터 분석
│   ├── model_evaluation.ipynb  # 모델 평가
│   └── insights.ipynb       # 인사이트 도출
├── docs/
│   ├── api_docs.md
│   ├── deployment.md
│   └── research_insights.md
└── scripts/
    ├── setup.sh             # 환경 설정
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

## 📊 데이터베이스 스키마

### meetings 테이블
- id: 고유 식별자
- title: 회의 제목
- date: 회의 날짜
- duration: 회의 시간
- participants: 참가자 목록
- summary: 요약 내용
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
- action_type: 액션 타입 (결정, 할당, 논의 등)
- description: 액션 설명
- assignee: 담당자
- due_date: 마감일

## 🔬 연구 및 인사이트 도출

### 분석 영역
1. **회의 패턴 분석**: 발화 시간, 참여도, 주제별 분포
2. **의사결정 프로세스**: 결정 사항과 논의 과정의 상관관계
3. **효율성 지표**: 회의 시간 대비 결정 사항 수
4. **참가자별 특성**: 발화 스타일, 영향력 분석

### 오픈소스 기술 이해
- Whisper 아키텍처 및 fine-tuning 방법
- Speaker Diarization 알고리즘 비교
- Text2SQL 모델의 내부 동작 원리
- 대용량 오디오 처리 최적화 기법 