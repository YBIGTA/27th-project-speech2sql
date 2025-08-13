# 🔍 자연어 검색 API

## 📋 개요

자연어 질의를 SQL로 변환하고 데이터베이스에서 검색하는 API입니다.

**담당자**: 

## 🔗 관련 파일

- **구현**: `src/nlp/text2sql.py`
- **API**: `src/api/routes/query.py`
- **테스트**: `tests/test_nlp.py`

## 📡 API 엔드포인트

### POST /query/natural

자연어 질의를 SQL로 변환하고 데이터베이스에서 검색합니다.

#### 요청

```json
{
  "query": "누가 프로젝트 일정에 대해 언급했나요?",
  "meeting_id": 1,
  "speaker": "김철수",
  "date_range": {
    "start": "2024-01-01",
    "end": "2024-01-31"
  },
  "limit": 10
}
```

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `query` | string | ✅ | 자연어 질의 |
| `meeting_id` | integer | ❌ | 특정 회의 ID |
| `speaker` | string | ❌ | 특정 발화자 |
| `date_range` | object | ❌ | 날짜 범위 |
| `limit` | integer | ❌ | 결과 개수 제한 (기본값: 10) |

#### 응답

```json
{
  "query": "누가 프로젝트 일정에 대해 언급했나요?",
  "sql_query": "SELECT DISTINCT u.speaker, u.text, u.timestamp, m.title as meeting_title FROM utterances u JOIN meetings m ON u.meeting_id = m.id WHERE u.text LIKE '%프로젝트%' AND u.text LIKE '%일정%' ORDER BY u.timestamp",
  "results": [
    {
      "id": 1,
      "speaker": "김철수",
      "timestamp": 120.5,
      "text": "프로젝트 일정은 다음 달 15일까지로 확정했습니다.",
      "meeting_title": "팀 프로젝트 기획 회의"
    }
  ],
  "total_count": 1,
  "execution_time": 0.15
}
```

#### 예시 질의들

| 자연어 질의 | 설명 | 예상 SQL |
|-------------|------|----------|
| "누가 프로젝트에 대해 언급했나요?" | 발화자별 프로젝트 관련 발언 검색 | `SELECT speaker FROM utterances WHERE text LIKE '%프로젝트%'` |
| "언제 마감일이 결정되었나요?" | 시간 관련 정보 검색 | `SELECT timestamp FROM utterances WHERE text LIKE '%마감일%'` |
| "무엇을 결정했나요?" | 결정사항 검색 | `SELECT text FROM utterances WHERE text LIKE '%결정%'` |
| "액션 아이템이 뭐가 있나요?" | 액션 아이템 검색 | `SELECT * FROM actions` |

### GET /query/suggestions

자주 사용되는 검색 제안을 제공합니다.

#### 응답

```json
{
  "suggestions": [
    "누가 프로젝트에 대해 언급했나요?",
    "언제 마감일이 결정되었나요?",
    "무엇을 결정했나요?",
    "액션 아이템이 뭐가 있나요?",
    "김철수가 언급한 내용은?",
    "지난 주 회의에서 논의된 내용은?"
  ]
}
```

### GET /query/analytics

검색 분석 데이터를 제공합니다.

#### 응답

```json
{
  "total_queries": 150,
  "popular_queries": [
    {
      "query": "프로젝트 일정",
      "count": 25,
      "avg_response_time": 0.12
    }
  ],
  "query_types": {
    "speaker_search": 40,
    "content_search": 35,
    "time_search": 25
  }
}
```

## 🔧 기술적 세부사항

### Text2SQL 변환 과정

1. **자연어 파싱**: 질의에서 키워드와 의도 추출
2. **스키마 매핑**: 데이터베이스 테이블/컬럼과 매핑
3. **SQL 생성**: 적절한 SQL 쿼리 생성
4. **검증**: 생성된 SQL의 유효성 검사
5. **실행**: 데이터베이스에서 쿼리 실행

### 지원하는 질의 유형

#### 발화자 관련 질의
- "누가 [주제]에 대해 언급했나요?"
- "[이름]이 말한 내용은?"
- "발화자별로 [주제] 언급 횟수는?"

#### 시간 관련 질의
- "언제 [이벤트]가 발생했나요?"
- "[기간] 동안 논의된 내용은?"
- "가장 최근에 언급된 [주제]는?"

#### 내용 관련 질의
- "무엇을 [동작]했나요?"
- "[주제]에 대한 결정사항은?"
- "액션 아이템이 뭐가 있나요?"

### 성능 지표

| 지표 | 목표값 | 측정 방법 |
|------|--------|-----------|
| 응답 시간 | < 1초 | 실제 측정 |
| 변환 정확도 | > 85% | 수동 검증 |
| 쿼리 성공률 | > 95% | 로그 분석 |

## 🚨 에러 처리

### 일반적인 에러

| 에러 코드 | 상황 | 해결 방법 |
|-----------|------|-----------|
| `INVALID_QUERY` | 잘못된 질의 형식 | 질의 문법 확인 |
| `SQL_GENERATION_FAILED` | SQL 생성 실패 | 질의 단순화 |
| `DATABASE_ERROR` | 데이터베이스 오류 | 시스템 상태 확인 |

### 디버깅 팁

1. **질의 단순화**: 복잡한 질의를 단순한 형태로 분해
2. **키워드 확인**: 핵심 키워드가 데이터에 존재하는지 확인
3. **SQL 로그**: 생성된 SQL 쿼리 로그 확인

## 📊 모니터링

### 쿼리 성능 모니터링

```bash
# 느린 쿼리 확인
grep "slow_query" logs/query.log

# 에러율 확인
grep "ERROR" logs/query.log | wc -l
```

### 사용 패턴 분석

- **인기 질의**: 자주 사용되는 질의 패턴
- **실패 패턴**: 자주 실패하는 질의 유형
- **응답 시간**: 질의별 평균 응답 시간

## 🔄 개선 요소

- [ ] 복잡한 질의 지원 (조건문, 집계함수 등)
- [ ] 동의어 및 유사어 처리
- [ ] 질의 히스토리 기반 개인화