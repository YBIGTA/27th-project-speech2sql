# 🎵 오디오 처리 API

## 📋 개요

오디오 파일 업로드, STT 처리, Speaker Diarization을 담당하는 API입니다.

**작성자**: 

## 🔗 관련 파일

- **구현**: `src/audio/whisper_stt.py`, `src/audio/speaker_diarization.py`
- **API**: `src/api/routes/audio.py`
- **테스트**: `tests/test_audio.py`

## 📡 API 엔드포인트

### POST /audio/upload

오디오 파일을 업로드하고 STT 처리 및 발화자 분리를 시작합니다.

#### 요청

**Content-Type**: `multipart/form-data`

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `file` | File | ✅ | 오디오 파일 (wav, mp3, m4a) |
| `title` | string | ❌ | 회의 제목 |
| `participants` | array | ❌ | 참가자 목록 |

#### 응답

```json
{
  "message": "Audio file uploaded successfully",
  "filename": "20240101_120000_meeting.mp3",
  "file_path": "./data/raw/20240101_120000_meeting.mp3",
  "file_size": 1024000,
  "title": "팀 프로젝트 기획 회의",
  "participants": ["김철수", "이영희", "박민수"],
  "status": "uploaded"
}
```

#### 예시

```bash
curl -X POST "http://localhost:8000/api/v1/audio/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@meeting.mp3" \
  -F "title=팀 프로젝트 기획 회의" \
  -F "participants=김철수,이영희,박민수"
```

### GET /audio/status/{filename}

오디오 파일 처리 상태를 확인합니다.

#### 요청

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `filename` | string | ✅ | 파일명 |

#### 응답

```json
{
  "filename": "20240101_120000_meeting.mp3",
  "status": "processing",
  "progress": 75,
  "stt_completed": true,
  "diarization_completed": false,
  "summary_completed": false,
  "estimated_completion": "2024-01-01T12:05:00Z"
}
```

### GET /audio/list

업로드된 오디오 파일 목록을 조회합니다.

#### 응답

```json
{
  "files": [
    {
      "filename": "20240101_120000_meeting.mp3",
      "title": "팀 프로젝트 기획 회의",
      "upload_date": "2024-01-01T12:00:00Z",
      "status": "completed",
      "duration": 3600,
      "participants": ["김철수", "이영희", "박민수"]
    }
  ],
  "total_count": 1
}
```

### DELETE /audio/{filename}

오디오 파일을 삭제합니다.

#### 요청

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `filename` | string | ✅ | 파일명 |

#### 응답

```json
{
  "message": "Audio file deleted successfully",
  "filename": "20240101_120000_meeting.mp3"
}
```

## 🔧 기술적 세부사항

### 지원하는 오디오 형식

- **WAV**: 무손실 압축, 고품질
- **MP3**: 손실 압축, 일반적인 용도
- **M4A**: AAC 코덱, iOS 호환

### 파일 크기 제한

- **최대 파일 크기**: 100MB
- **권장 파일 크기**: 50MB 이하
- **최소 파일 크기**: 1KB

### 처리 단계

1. **파일 검증**: 형식, 크기 확인
2. **STT 처리**: Whisper 모델로 음성→텍스트 변환
3. **Speaker Diarization**: 발화자 분리
4. **메타데이터 추출**: 시간, 참가자 정보
5. **데이터베이스 저장**: 처리 결과 저장

### 성능 지표

| 지표 | 목표값 | 측정 방법 |
|------|--------|-----------|
| STT 정확도 | > 90% | WER (Word Error Rate) |
| 처리 시간 | < 5분 (10분 오디오) | 실제 측정 |
| 메모리 사용량 | < 2GB | 시스템 모니터링 |

## 🚨 에러 처리

### 일반적인 에러

| 에러 코드 | 상황 | 해결 방법 |
|-----------|------|-----------|
| `FILE_TOO_LARGE` | 파일 크기 초과 | 파일을 더 작게 분할 |
| `UNSUPPORTED_FORMAT` | 지원하지 않는 형식 | WAV, MP3, M4A로 변환 |
| `PROCESSING_ERROR` | 처리 중 오류 | 파일 재업로드 |

### 디버깅 팁

1. **파일 형식 확인**: `file` 명령어로 실제 형식 확인
2. **파일 크기 확인**: 업로드 전 파일 크기 체크
3. **네트워크 상태**: 업로드 중 네트워크 연결 확인

## 📊 모니터링

### 로그 확인

```bash
# 실시간 로그 확인
tail -f logs/audio_processing.log

# 에러 로그만 확인
grep "ERROR" logs/audio_processing.log
```

### 성능 모니터링

- **처리 시간**: 평균, 최대, 최소 시간 추적
- **성공률**: 처리 성공/실패 비율
- **리소스 사용량**: CPU, 메모리, 디스크 사용량

## 🔄 개선 요소

- [ ] 실시간 처리 상태 업데이트
- [ ] 배치 처리 기능 추가
- [ ] 에러 복구 메커니즘
- [ ] 다국어 지원 확장
- [ ] 노이즈 제거 기능
- [ ] 음성 품질 향상