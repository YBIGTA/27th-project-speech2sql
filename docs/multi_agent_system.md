# 멀티에이전트 기반 회의 분석 시스템

## 🎯 개요

멀티에이전트 시스템을 통해 회의 내용을 심도 있게 분석하여 화자별 논리/주장과 안건별 인사이트를 제공하는 시스템입니다.

## 🏗️ 시스템 아키텍처

### 핵심 구성 요소

1. **BaseAgent**: 모든 에이전트의 기본 클래스
2. **SpeakerAnalysisAgent**: 화자별 분석 에이전트
3. **AgendaAnalysisAgent**: 안건별 분석 에이전트
4. **OrchestratorAgent**: 조율 및 통합 에이전트

### 에이전트별 역할

#### 🤖 SpeakerAnalysisAgent
- **목적**: 각 화자의 발화 패턴과 특성 분석
- **기능**:
  - 참여도 및 지배력 분석
  - 의사소통 스타일 분석
  - 주제별 관심도 분석
  - 상호작용 패턴 분석

#### 📋 AgendaAnalysisAgent
- **목적**: 특정 안건에 대한 심도 있는 분석
- **기능**:
  - 안건별 논의 패턴 분석
  - 의견 및 입장 분석
  - 결정사항 추출
  - 합의 수준 분석
  - 토론 품질 평가

#### 🎪 OrchestratorAgent
- **목적**: 전체 분석 프로세스 관리 및 결과 통합
- **기능**:
  - 멀티 에이전트 조율
  - 종합 분석 생성
  - 인사이트 추출
  - 실행 요약 생성
  - 권장사항 제시

## 🚀 사용법

### API 엔드포인트

#### 1. 종합 분석 실행
```bash
POST /api/v1/analysis/comprehensive
{
  "meeting_id": 1,
  "analysis_type": "comprehensive"
}
```

#### 2. 화자 분석만 실행
```bash
GET /api/v1/analysis/meeting/{meeting_id}/speakers
```

#### 3. 안건 분석만 실행
```bash
GET /api/v1/analysis/meeting/{meeting_id}/agendas
```

#### 4. 분석 기능 조회
```bash
GET /api/v1/analysis/capabilities
```

### 웹 인터페이스

1. **Streamlit 앱 접속**: `http://localhost:8501`
2. **메뉴에서 "🤖 멀티에이전트 분석" 선택**
3. **분석할 회의 선택**
4. **분석 유형 선택**:
   - 🤖 종합 분석 (모든 에이전트)
   - 👥 화자 분석만
   - 📋 안건 분석만
5. **"🚀 분석 시작" 버튼 클릭**

## 📊 출력 결과

### 종합 분석 결과

```json
{
  "meeting_id": 1,
  "analysis_type": "comprehensive",
  "executive_summary": "이 회의는 3명의 참가자가 45.2분 동안 진행되었으며...",
  "insights": {
    "participation_insights": {
      "warning": "참여도 불균형이 감지되었습니다."
    },
    "decision_quality": {
      "decision_count": "총 5개의 결정사항이 도출되었습니다."
    },
    "recommendations": [
      "모든 참가자의 균등한 참여를 유도하는 방안을 고려하세요."
    ]
  },
  "comprehensive_analysis": {
    "speaker_insights": {
      "speaker_profiles": {
        "Speaker_1": {
          "profile": {
            "participation_rate": 0.45,
            "dominance_score": 0.8,
            "communication_style": "직설적"
          }
        }
      }
    },
    "agenda_insights": {
      "agenda_analysis": {
        "agenda_1": {
          "agenda_info": {"title": "프로젝트 일정 조정"},
          "consensus": {"level": "높음", "score": 0.85}
        }
      }
    }
  }
}
```

### 화자 분석 결과

```json
{
  "speaker_analysis": {
    "speakers": {
      "Speaker_1": {
        "profile": {
          "participation_rate": 0.45,
          "dominance_score": 0.8,
          "communication_style": "직설적",
          "avg_words_per_utterance": 15.2
        },
        "topic_preferences": ["기술", "프로젝트 관리"],
        "engagement_patterns": {
          "engagement_level": "높음",
          "avg_response_time": 45.2
        }
      }
    },
    "meeting_summary": {
      "total_speakers": 3,
      "most_active_speaker": "Speaker_1",
      "participation_balance": "불균형"
    }
  }
}
```

### 안건 분석 결과

```json
{
  "agenda_analysis": {
    "agendas": {
      "agenda_1": {
        "agenda_info": {
          "title": "프로젝트 일정 조정",
          "keywords": ["일정", "계획", "마감"]
        },
        "discussion_patterns": {
          "total_utterances": 25,
          "unique_speakers": 3,
          "discussion_duration": 1800
        },
        "opinions": {
          "positive": [...],
          "negative": [...],
          "neutral": [...]
        },
        "consensus": {
          "level": "높음",
          "score": 0.85
        },
        "decisions": [
          {
            "speaker": "Speaker_1",
            "text": "일정을 2주 연기하기로 결정했습니다.",
            "timestamp": 1500
          }
        ]
      }
    }
  }
}
```

## 🔧 기술적 특징

### 1. 비동기 처리
- 모든 에이전트가 병렬로 실행되어 처리 속도 향상
- `asyncio.gather()`를 사용한 동시 실행

### 2. 모듈화된 설계
- 각 에이전트는 독립적으로 실행 가능
- 새로운 에이전트 추가가 용이한 구조

### 3. 표준화된 결과 형식
- 모든 에이전트가 `AgentResult` 형식으로 결과 반환
- 일관된 데이터 구조로 통합 분석 가능

### 4. 확장 가능한 아키텍처
- 새로운 분석 에이전트 추가 가능
- LangGraph나 ADK로 확장 가능한 구조

## 🚀 향후 발전 방향

### 1. 고급 NLP 통합
- 감정 분석 에이전트 추가
- 논리 구조 분석 에이전트 추가
- 전문성 분석 에이전트 추가

### 2. LangGraph 통합
- 복잡한 에이전트 간 상호작용 관리
- 조건부 분기 및 반복 처리
- 상태 기반 워크플로우

### 3. 실시간 분석
- 실시간 회의 분석
- 동적 에이전트 조정
- 실시간 피드백 제공

### 4. 고급 시각화
- 화자별 네트워크 그래프
- 안건별 토론 플로우 차트
- 감정 변화 타임라인

## 📝 사용 예시

### 1. 회의 효율성 분석
```python
# 종합 분석으로 회의 효율성 평가
result = await orchestrator.execute(meeting_data)
efficiency_score = calculate_efficiency(result)
```

### 2. 화자 참여도 개선
```python
# 화자별 참여도 분석으로 개선점 도출
speaker_analysis = await speaker_agent.execute(meeting_data)
improvement_suggestions = generate_suggestions(speaker_analysis)
```

### 3. 안건별 의사결정 품질 평가
```python
# 안건별 합의 수준과 결정 품질 분석
agenda_analysis = await agenda_agent.execute(meeting_data)
decision_quality = evaluate_decisions(agenda_analysis)
```

## 🔍 API 문서

자세한 API 문서는 다음 URL에서 확인할 수 있습니다:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc` 