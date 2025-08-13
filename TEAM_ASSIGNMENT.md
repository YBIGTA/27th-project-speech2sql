# 팀 역할 분배 및 담당 영역

### 🎯 팀장
**담당 영역**: 프로젝트 총괄, 시스템 아키텍처 설계, 팀 조율

**주요 업무**:
- 프로젝트 전체 방향성 설정 및 일정 관리
- 시스템 아키텍처 설계 및 기술 스택 결정
- 팀원 간 협업 조율 및 코드 리뷰 총괄
- 최종 통합 및 배포 관리
- 연구 인사이트 도출 및 논문 작성

**핵심 파일**:
- `README.md`, `TEAM_ASSIGNMENT.md`
- `config/settings.py`, `config/database.py`
- `scripts/setup.py`, `scripts/deployment.py`
- `notebooks/insights.ipynb`

---

### 🎵 오디오(Speech to Text) 담당
**담당 영역**: STT, Speaker Diarization, 오디오 전처리

**주요 업무**:
- Whisper STT 모델 구현 및 최적화
- Speaker Diarization 알고리즘 구현
- 오디오 파일 전처리 및 품질 개선
- 다국어 지원 및 잡음 환경 대응
- STT 정확도 향상 및 fine-tuning

**핵심 파일**:
- `src/audio/whisper_stt.py`
- `src/audio/speaker_diarization.py`
- `src/utils/audio_utils.py`
- `tests/test_audio.py`
- `notebooks/audio_analysis.ipynb`

**기술적 도전과제**:
- 실시간 오디오 처리 최적화
- 다양한 음성 품질에 대한 강건성 확보
- Speaker Diarization 정확도 향상

---

### 🧠 NLP/ML 담당
**담당 영역**: 요약 모델, Text2SQL, 자연어 처리

**주요 업무**:
- PEGASUS/LLaMA2 기반 요약 모델 구현
- Huggingface Text2SQL 모델 적용 및 최적화
- 자연어 질의 처리 및 SQL 변환
- 요약 품질 평가 및 개선
- Upstage API 연동 및 LLM 활용

**핵심 파일**:
- `src/nlp/summarization.py`
- `src/nlp/text2sql.py`
- `src/nlp/query_processor.py`
- `tests/test_nlp.py`
- `notebooks/model_evaluation.ipynb`

**기술적 도전과제**:
- 긴 텍스트 요약의 정확성 향상
- 복잡한 자연어 질의의 SQL 변환 정확도
- 한국어 특화 모델 fine-tuning

---

### 🗄️ 백엔드/데이터베이스 담당
**담당 영역**: FastAPI, 데이터베이스 설계, API 개발

**주요 업무**:
- FastAPI 백엔드 서버 구현
- PostgreSQL 데이터베이스 설계 및 구현
- RESTful API 엔드포인트 개발
- 데이터베이스 최적화 및 인덱싱
- API 문서화 및 테스트

**핵심 파일**:
- `src/api/main.py`
- `src/api/routes/`
- `src/database/models.py`
- `src/database/operations.py`
- `tests/test_api.py`
- `docs/api_docs.md`

**기술적 도전과제**:
- 대용량 오디오 메타데이터 효율적 저장
- 복잡한 쿼리 최적화
- 실시간 API 응답성 확보

---

### 🎨 프론트엔드/UI/UX 담당
**담당 영역**: Streamlit 프론트엔드, 사용자 인터페이스

**주요 업무**:
- Streamlit 기반 웹 애플리케이션 개발
- 파일 업로드 및 검색 인터페이스 구현
- 데이터 시각화 및 분석 대시보드
- 사용자 경험 최적화
- 반응형 디자인 및 접근성

**핵심 파일**:
- `frontend/app.py`
- `frontend/pages/`
- `frontend/static/`
- `src/utils/pdf_generator.py`
- `tests/test_frontend.py`

**기술적 도전과제**:
- 직관적인 자연어 검색 인터페이스
- 실시간 데이터 시각화
- 모바일 친화적 디자인

---

## 📋 개발 일정

### Phase 1: 기반 구축
- [ ] 프로젝트 구조 설정
- [ ] 개발 환경 구성
- [ ] 데이터베이스 스키마 설계
- [ ] 기본 API 구조 구현

### Phase 2: 핵심 기능 개발
- [ ] Whisper STT + Speaker Diarization 구현
- [ ] 요약 모델 구현
- [ ] Text2SQL 모델 연동
- [ ] 기본 프론트엔드 구현

### Phase 3: 통합 및 최적화
- [ ] 전체 시스템 통합
- [ ] 성능 최적화
- [ ] 에러 처리 및 로깅
- [ ] 사용자 테스트

### Phase 4: 분석 및 인사이트
- [ ] 데이터 분석 및 시각화
- [ ] 성능 평가 및 개선
- [ ] 연구 인사이트 도출
- [ ] 문서화 및 발표 준비

## 🤝 협업 가이드라인

### 코드 관리
- 바로 Main에 Push하지 말고 Git 브랜치에 feature/기능명 형식으로 올려주세요!
- 팀장이 코드 리뷰를 하겠지만 모두 서로서로 코드 리뷰 해주세요!
- 5명이 코드를 보는 만큼 되도록 깔끔하게 코드를 작성해주세요!

### 의사소통
- 진행상황을 정기적으로 공유해주세요!
- 특히, 기술적인 이슈가 발생했다면 즉시 공유해주세요!

### 품질 관리
- 단위 테스트를 활용해주세요. tests 폴더에 만들어놨습니다! 당연히 수정하셔도 상관없습니다.
- API 문서화를 해주세요. docs/api_docs.md 파일 만들어놨습니다. LLM으로 그냥 생성한 파일이라 자유롭게 수정하시면 됩니다.