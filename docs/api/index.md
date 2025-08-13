# Speech2SQL API 문서

## 📋 개요

Speech2SQL API는 강의·회의록 생성 및 검색 시스템의 백엔드 API입니다.

**작성자**: 박용우

- **Base URL**: `http://localhost:8000/api/v1`
- **Content-Type**: `application/json`
- **인증**: 현재 미구현 (향후 JWT 토큰 기반 인증 예정)

## 🗂️ API 분류

### 🎵 [오디오 처리 API](./audio_api.md)
- 오디오 파일 업로드 및 처리
- STT (Speech-to-Text) 변환
- Speaker Diarization (발화자 분리)
- 처리 상태 확인

### 🔍 [자연어 검색 API](./query_api.md)
- 자연어 질의 처리
- Text2SQL 변환
- 검색 결과 반환
- 검색 제안 및 분석

### 📝 [요약 생성 API](./summary_api.md)
- 회의록 요약 생성
- 다양한 요약 유형 지원
- PDF 요약본 생성
- 요약 분석

## 🚨 공통 에러 응답

모든 API는 에러 발생 시 다음과 같은 형식으로 응답합니다:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "에러 메시지",
    "details": {
      "field": "필드명",
      "value": "값"
    }
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 에러 코드

| 코드 | 설명 |
|------|------|
| `VALIDATION_ERROR` | 입력값 검증 실패 |
| `FILE_TOO_LARGE` | 파일 크기 초과 |
| `UNSUPPORTED_FORMAT` | 지원하지 않는 파일 형식 |
| `PROCESSING_ERROR` | 처리 중 오류 발생 |
| `NOT_FOUND` | 리소스를 찾을 수 없음 |
| `DATABASE_ERROR` | 데이터베이스 오류 |

## 📊 상태 코드

| 코드 | 설명 |
|------|------|
| 200 | 성공 |
| 201 | 생성됨 |
| 400 | 잘못된 요청 |
| 404 | 찾을 수 없음 |
| 500 | 서버 내부 오류 |

## 🔧 개발 환경 설정

### 로컬 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp env.example .env
# .env 파일 편집

# 서버 실행
python -m uvicorn src.api.main:app --reload
```

### API 문서 확인

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📈 성능 지표

### 응답 시간 목표

| API 분류 | 목표 응답 시간 |
|----------|---------------|
| 오디오 업로드 | < 5초 |
| 자연어 검색 | < 1초 |
| 요약 생성 | < 10초 |
| PDF 생성 | < 30초 |

### 처리 용량

- **동시 업로드**: 최대 10개 파일
- **파일 크기**: 최대 100MB
- **동시 검색**: 최대 100개 요청/분

## 🔄 버전 관리

현재 API 버전: `v1`

버전 변경 시 하위 호환성을 유지하며, 새로운 기능은 새로운 엔드포인트로 추가됩니다.

## 📞 지원

- **기술 문서**: 각 API 문서 참조
- **예제 코드**: [examples/](../examples/) 폴더
- **테스트**: [tests/](../tests/) 폴더 