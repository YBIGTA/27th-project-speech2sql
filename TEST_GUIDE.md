# 🤖 멀티에이전트 분석 테스트 가이드

## 📋 개요

가상의 회의 데이터를 생성하여 멀티에이전트 분석 기능을 테스트할 수 있는 도구들을 제공합니다.

## 🚀 빠른 시작

### 1단계: 서버 실행
```bash
# FastAPI 서버 실행
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Streamlit 프론트엔드 실행 (새 터미널에서)
streamlit run frontend/app.py
```

### 2단계: 테스트 데이터 생성
```bash
# 가상 회의 데이터 생성 및 삽입
python insert_test_data.py
```

### 3단계: 빠른 테스트
```bash
# API 기능 빠른 테스트
python quick_test.py
```

## 📊 생성되는 테스트 데이터

### 회의 1: 2024년 1분기 프로젝트 기획 회의
- **참가자**: 김팀장, 이과장, 박대리
- **주제**: 프로젝트, 일정, 예산
- **결정사항**: 3개
- **예상 발화 수**: ~50개

### 회의 2: 신제품 출시 전략 논의
- **참가자**: 정부장, 김팀장, 이과장, 최사원
- **주제**: 마케팅, 기술, 예산
- **결정사항**: 3개
- **예상 발화 수**: ~70개

### 회의 3: 팀 조직 개편 안건 검토
- **참가자**: 정부장, 김팀장, 이과장
- **주제**: 인사, 조직
- **결정사항**: 3개
- **예상 발화 수**: ~40개

## 🔍 테스트 방법

### 1. API 테스트

#### 종합 분석 테스트
```bash
curl -X POST "http://localhost:8000/api/v1/analysis/comprehensive" \
  -H "Content-Type: application/json" \
  -d '{"meeting_id": 1, "analysis_type": "comprehensive"}'
```

#### 화자 분석 테스트
```bash
curl -X GET "http://localhost:8000/api/v1/analysis/meeting/1/speakers"
```

#### 안건 분석 테스트
```bash
curl -X GET "http://localhost:8000/api/v1/analysis/meeting/1/agendas"
```

### 2. 프론트엔드 테스트

1. **Streamlit 앱 접속**: `http://localhost:8501`
2. **메뉴에서 "🤖 멀티에이전트 분석" 선택**
3. **생성된 테스트 회의 선택**
4. **분석 유형 선택**:
   - 🤖 종합 분석 (모든 에이전트)
   - 👥 화자 분석만
   - 📋 안건 분석만
5. **"🚀 분석 시작" 버튼 클릭**

## 📈 예상 결과

### 화자 분석 결과
- **김팀장**: 체계적 접근, 높은 참여도
- **이과장**: 실무적 관점, 중간 참여도
- **박대리**: 조사 기반 의견, 중간 참여도
- **최사원**: 사용자 관점, 낮은 참여도
- **정부장**: 전략적 관점, 높은 참여도

### 안건 분석 결과
- **프로젝트**: 높은 합의 수준, 구체적 결정사항
- **예산**: 중간 합의 수준, 추가 검토 필요
- **인사**: 높은 합의 수준, 명확한 방향성

### 종합 분석 결과
- **실행 요약**: 회의 개요 및 주요 결정사항
- **인사이트**: 참여도, 결정 품질, 권장사항
- **상세 분석**: 화자별/안건별 심층 분석

## 🛠️ 문제 해결

### API 서버 연결 오류
```bash
# 서버 상태 확인
curl http://localhost:8000/health

# 포트 확인
netstat -an | grep 8000
```

### 데이터베이스 오류
```bash
# 데이터베이스 연결 확인
python -c "from config.database import get_db; next(get_db())"
```

### 테스트 데이터 재생성
```bash
# 기존 데이터 삭제 후 재생성
python insert_test_data.py
```

## 📝 테스트 체크리스트

- [ ] FastAPI 서버 실행 확인
- [ ] Streamlit 프론트엔드 실행 확인
- [ ] 테스트 데이터 생성 완료
- [ ] 회의 목록 조회 테스트
- [ ] 종합 분석 API 테스트
- [ ] 화자 분석 API 테스트
- [ ] 안건 분석 API 테스트
- [ ] 프론트엔드 분석 기능 테스트
- [ ] 결과 데이터 검증

## 🔧 고급 테스트

### 커스텀 테스트 데이터 생성
```python
from test_data_generator import generate_utterances

# 커스텀 회의 템플릿
custom_template = {
    "title": "커스텀 회의",
    "duration": 30,
    "speakers": ["사용자1", "사용자2"],
    "topics": ["주제1", "주제2"],
    "decisions": ["결정1", "결정2"]
}

# 발화 데이터 생성
utterances = generate_utterances(custom_template)
```

### 성능 테스트
```bash
# 대용량 데이터 테스트
python -c "
from test_data_generator import generate_test_meeting_data
templates = generate_test_meeting_data()
for template in templates:
    template['duration'] = 120  # 2시간 회의로 확장
    template['speakers'].extend(['추가화자1', '추가화자2'])
"
```

## 📚 추가 리소스

- **API 문서**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **멀티에이전트 시스템 문서**: `docs/multi_agent_system.md`

## 🎯 다음 단계

1. **실제 오디오 파일로 테스트**
2. **더 복잡한 회의 시나리오 추가**
3. **성능 최적화 테스트**
4. **사용자 피드백 수집**
5. **기능 개선 및 확장** 