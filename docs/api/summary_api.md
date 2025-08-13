# 📝 요약 생성 API

## 📋 개요

회의록 요약 생성 및 PDF 변환을 담당하는 API입니다.

**작성자**: 

## 🔗 관련 파일

- **구현**: `src/nlp/summarization.py`, `src/utils/pdf_generator.py`
- **API**: `src/api/routes/summary.py`
- **테스트**: `tests/test_nlp.py`

## 📡 API 엔드포인트

### POST /summary/generate

회의록 요약을 생성합니다.

#### 요청

```json
{
  "meeting_id": 1,
  "summary_type": "general",
  "language": "ko"
}
```

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `meeting_id` | integer | ✅ | 회의 ID |
| `summary_type` | string | ❌ | 요약 유형 (general, action_items, decisions) |
| `language` | string | ❌ | 언어 (ko, en) |

#### 응답

```json
{
  "meeting_id": 1,
  "summary_type": "general",
  "summary_text": "이 회의에서는 프로젝트 일정과 담당자 배정에 대해 논의했습니다. 김철수가 프론트엔드 개발을 담당하고, 이영희가 백엔드 개발을 담당하기로 결정했습니다.",
  "key_points": [
    "프로젝트 마감일은 다음 달 15일로 확정",
    "김철수가 프론트엔드 개발 담당",
    "이영희가 백엔드 개발 담당"
  ],
  "action_items": [
    {
      "description": "프로젝트 계획서 작성",
      "assignee": "김철수",
      "due_date": "2024-01-10"
    }
  ],
  "decisions": [
    {
      "topic": "프로젝트 일정",
      "decision": "다음 달 15일 마감으로 확정",
      "voted_by": ["김철수", "이영희", "박민수"]
    }
  ],
  "generated_at": "2024-01-01T12:00:00Z"
}
```

### GET /summary/{meeting_id}

특정 회의의 요약을 조회합니다.

#### 요청

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `meeting_id` | integer | ✅ | 회의 ID |

#### 응답

```json
{
  "meeting_id": 1,
  "title": "팀 프로젝트 기획 회의",
  "date": "2024-01-01T10:00:00Z",
  "duration": 3600,
  "summary": {
    "general": "이 회의에서는...",
    "action_items": [
      {
        "description": "프로젝트 계획서 작성",
        "assignee": "김철수",
        "due_date": "2024-01-10"
      }
    ],
    "decisions": [
      {
        "topic": "프로젝트 일정",
        "decision": "다음 달 15일 마감으로 확정",
        "voted_by": ["김철수", "이영희", "박민수"]
      }
    ]
  }
}
```

### POST /summary/generate-pdf

PDF 요약본을 생성합니다.

#### 요청

```json
{
  "meeting_id": 1,
  "template": "standard"
}
```

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `meeting_id` | integer | ✅ | 회의 ID |
| `template` | string | ❌ | PDF 템플릿 (standard, detailed, executive) |

#### 응답

```json
{
  "meeting_id": 1,
  "pdf_url": "/static/summaries/meeting_1_summary.pdf",
  "generated_at": "2024-01-01T12:00:00Z"
}
```

### GET /summary/analytics

요약 생성 분석 데이터를 제공합니다.

#### 응답

```json
{
  "total_summaries": 50,
  "summary_types": {
    "general": 30,
    "action_items": 15,
    "decisions": 5
  },
  "avg_generation_time": 8.5,
  "popular_templates": {
    "standard": 25,
    "detailed": 15,
    "executive": 10
  }
}
```

## 🔧 기술적 세부사항

### 요약 유형

#### General Summary (일반 요약)
- 회의 전체 내용의 핵심 요약
- 주요 논의 사항과 결과
- 참가자별 기여도

#### Action Items (액션 아이템)
- 할 일 목록 추출
- 담당자와 마감일 지정
- 우선순위 분류

#### Decisions (결정사항)
- 회의에서 내린 결정들
- 투표 결과 (있는 경우)
- 결정 근거

### 요약 생성 과정

1. **텍스트 전처리**: STT 결과 정제
2. **핵심 내용 추출**: 키워드 및 중요 문장 식별
3. **요약 생성**: LLM 기반 요약 생성
4. **구조화**: 액션 아이템, 결정사항 분류
5. **검증**: 요약 품질 확인

### PDF 템플릿

#### Standard Template
- 기본적인 회의록 형식
- 요약, 액션 아이템, 결정사항 포함
- 깔끔하고 읽기 쉬운 레이아웃

#### Detailed Template
- 상세한 회의 내용
- 발화자별 발언 요약
- 시간별 진행 상황

#### Executive Template
- 경영진용 요약
- 핵심 결정사항 중심
- 비즈니스 임팩트 강조

### 성능 지표

| 지표 | 목표값 | 측정 방법 |
|------|--------|-----------|
| 요약 품질 | > 80% | 사용자 평가 |
| 생성 시간 | < 10초 | 실제 측정 |
| 정확도 | > 85% | 수동 검증 |

## 🚨 에러 처리

### 일반적인 에러

| 에러 코드 | 상황 | 해결 방법 |
|-----------|------|-----------|
| `MEETING_NOT_FOUND` | 회의를 찾을 수 없음 | 회의 ID 확인 |
| `SUMMARY_GENERATION_FAILED` | 요약 생성 실패 | 텍스트 품질 확인 |
| `PDF_GENERATION_FAILED` | PDF 생성 실패 | 템플릿 확인 |

### 디버깅 팁

1. **텍스트 품질**: STT 결과의 품질 확인
2. **모델 상태**: LLM 모델 로딩 상태 확인
3. **메모리 사용량**: PDF 생성 시 메모리 부족 확인

## 📊 모니터링

### 요약 품질 모니터링

```bash
# 요약 생성 로그 확인
tail -f logs/summary_generation.log

# 품질 지표 확인
grep "quality_score" logs/summary_generation.log
```

### 사용 패턴 분석

- **인기 요약 유형**: 자주 사용되는 요약 유형
- **PDF 템플릿 선호도**: 사용자별 템플릿 선택 패턴
- **생성 시간**: 요약별 평균 생성 시간

## 🔄 개선 요소

- [ ] 한국어 특화 or 다국어 요약 지원
- [ ] 요약 히스토리 관리 