import httpx
import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field, ValidationError
from datetime import datetime, timezone, timedelta

from config.settings import settings

# --- Pydantic 모델 정의 (API 명세 기반) ---
class ActionItem(BaseModel):
    description: str = Field(..., description="실행할 작업 내용")
    assignee: Optional[str] = Field(None, description="담당자")
    due_date: Optional[str] = Field(None, description="마감일 (YYYY-MM-DD)")

class Decision(BaseModel):
    topic: str = Field(..., description="결정 주제")
    decision: str = Field(..., description="결정 내용")
    voted_by: Optional[List[str]] = Field([], description="투표/동의자")

class SummaryResult(BaseModel):
    summary_text: Optional[str] = Field("", description="회의 전체 요약")
    key_points: List[str] = Field([], description="핵심 포인트")
    action_items: List[ActionItem] = Field([], description="액션 아이템")
    decisions: List[Decision] = Field([], description="결정 사항")

# --- Upstage API 설정 ---
UPSTAGE_API_URL = "https://api.upstage.ai/v1/solar"
# .env 의 SUMMARIZATION_MODEL을 우선 사용, 없으면 solar-pro-2
UPSTAGE_MODEL = getattr(settings, "summarization_model", None) or "solar-pro-2"

# 서울 시간 (요약 내 상대날짜 계산 지시용)
KST = timezone(timedelta(hours=9))

class UpstageSummarizer:
    """
    Upstage Solar LLM으로 회의록을 구조화 요약(JSON)하는 클래스
    - 다국어(ko/en) 지원
    - 응답은 반드시 JSON (response_format=json_object)
    """

    def __init__(self):
        self.api_key = settings.upstage_api_key
        if not self.api_key:
            raise ValueError("Upstage API 키가 .env에 설정되지 않았습니다 (UPSTAGE_API_KEY).")

        self.client = httpx.AsyncClient(
            base_url=UPSTAGE_API_URL,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=60.0,
        )
        print(f"✅ UpstageSummarizer 초기화 완료 (model={UPSTAGE_MODEL})")

    # -------------------- 프롬프트 생성 --------------------
    def _create_summary_prompt(self, transcript: str, language: str = "ko", summary_type: str = "general") -> List[Dict[str, str]]:
        """
        언어/요약유형에 맞는 system/user 메시지 생성
        """
        json_schema_description = """
{
  "summary_text": "General summary text.",
  "key_points": ["bullet point 1", "bullet point 2"],
  "action_items": [{
    "description": "task to perform",
    "assignee": "name (optional)",
    "due_date": "YYYY-MM-DD (optional)"
  }],
  "decisions": [{
    "topic": "topic discussed",
    "decision": "what was decided",
    "voted_by": ["name1","name2"]
  }]
}
        """.strip()

        if language == "en":
            today_date = datetime.now(tz=KST).strftime("%B %d, %Y")
            base_instruction = (
                "You are a meeting summarizer. Analyze the transcript and output "
                "a STRICT JSON object following the schema. No markdown, no code fences, JSON only."
            )
            date_note = f"Note: Today's date (KST) is {today_date}. Compute relative dates accordingly."
            if summary_type == "action_items":
                task_instruction = "Focus ONLY on extracting 'action_items'. Other fields may be empty."
            elif summary_type == "decisions":
                task_instruction = "Focus ONLY on extracting 'decisions'. Other fields may be empty."
            else:
                task_instruction = "Provide a comprehensive summary covering all fields."

            system_prompt = f"{base_instruction}\n{task_instruction}\nJSON Schema:\n{json_schema_description}"
            user_prompt = f"{date_note}\n\nTRANSCRIPT:\n{transcript}"
        else:
            today_date = datetime.now(tz=KST).strftime("%Y년 %m월 %d일")
            base_instruction = (
                "당신은 회의록 요약가입니다. 아래 텍스트를 분석해 스키마를 따르는 "
                "JSON 객체만 출력하세요. 마크다운/코드펜스 없이 순수 JSON만 허용합니다."
            )
            date_note = f"참고: 오늘 날짜(KST)는 {today_date}입니다. 상대 날짜를 이 기준으로 계산하세요."
            if summary_type == "action_items":
                task_instruction = "오직 'action_items' 추출에 집중하세요. 다른 필드는 비워도 됩니다."
            elif summary_type == "decisions":
                task_instruction = "오직 'decisions' 추출에 집중하세요. 다른 필드는 비워도 됩니다."
            else:
                task_instruction = "모든 필드를 포함하는 포괄 요약을 생성하세요."

            system_prompt = f"{base_instruction}\n{task_instruction}\nJSON 스키마:\n{json_schema_description}"
            user_prompt = f"{date_note}\n\n회의록 원문:\n{transcript}"

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    # -------------------- 내부 유틸 --------------------
    def _strip_code_fences(self, s: str) -> str:
        """
        혹시 모델이 ```json ... ``` 같은 코드펜스를 붙이면 제거
        """
        s = s.strip()
        if s.startswith("```"):
            s = s.strip("`")
            # 흔한 패턴 제거
            s = s.replace("json\n", "", 1).replace("JSON\n", "", 1)
        return s.strip()

    async def _post_with_retry(self, path: str, json_payload: Dict[str, Any], retries: int = 3) -> httpx.Response:
        """
        429/5xx에 대해 지수백오프로 재시도
        """
        backoff = 1.0
        for attempt in range(retries):
            try:
                resp = await self.client.post(path, json=json_payload)
                if resp.status_code < 500 and resp.status_code != 429:
                    return resp
                # 429 또는 5xx → 재시도
                print(f"⏳ Upstage 응답 상태 {resp.status_code}, 재시도 {attempt+1}/{retries}")
            except httpx.RequestError as e:
                print(f"⚠️ 요청 오류: {e} (재시도 {attempt+1}/{retries})")
            await asyncio.sleep(backoff)
            backoff *= 2
        # 마지막 시도
        return await self.client.post(path, json=json_payload)

    # -------------------- 퍼블릭 메서드 --------------------
    async def summarize(
        self,
        transcript: str,
        language: str = "ko",
        summary_type: str = "general",
        allow_chunking: bool = True,
        chunk_chars: int = 12000
    ) -> Optional[SummaryResult]:
        """
        긴 본문은 청킹→병합 방식으로 처리(옵션)
        """
        if not transcript.strip():
            print("⚠️ 요약할 내용이 없습니다.")
            return None

        # 청킹: 너무 긴 경우 여러 청크 요약 후 최종 요약
        if allow_chunking and len(transcript) > chunk_chars:
            print(f"ℹ️ 본문이 깁니다(len={len(transcript)}). 청크 요약을 수행합니다.")
            chunks = self._split_into_chunks(transcript, chunk_chars)
            partials: List[SummaryResult] = []
            for i, ch in enumerate(chunks, 1):
                partial = await self._summarize_once(ch, language, summary_type)
                if partial:
                    partials.append(partial)
                print(f"  - 청크 {i}/{len(chunks)} 처리 완료")

            # 부분 요약들을 합쳐 최종 요청(간단 병합)
            merged_transcript = self._merge_partial_summaries(partials, language)
            return await self._summarize_once(merged_transcript, language, summary_type)

        # 단일 요청
        return await self._summarize_once(transcript, language, summary_type)

    async def _summarize_once(self, transcript: str, language: str, summary_type: str) -> Optional[SummaryResult]:
        messages = self._create_summary_prompt(transcript, language, summary_type)
        payload = {
            "model": UPSTAGE_MODEL,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 1024,
            "response_format": {"type": "json_object"},
        }

        try:
            print(f"⏳ Upstage 요약 요청: model={UPSTAGE_MODEL}, lang={language}, type={summary_type}")
            # 기본은 바로 호출(문제 시 _post_with_retry로 교체 가능)
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()

            content = response.json()["choices"][0]["message"]["content"]
            content = self._strip_code_fences(content)

            parsed_json = json.loads(content)
            result = SummaryResult.model_validate(parsed_json)
            print("✅ 구조화 요약 성공")
            return result

        except (httpx.HTTPStatusError, json.JSONDecodeError, ValidationError) as e:
            print(f"❌ 구조화 요약 실패: {e}")
            return None
        except Exception as e:
            print(f"❌ 요약 중 알 수 없는 오류: {e}")
            return None

    def _split_into_chunks(self, text: str, chunk_chars: int) -> List[str]:
        """
        매우 단순한 길이 기준 분할(문단 기준 개선 여지 있음)
        """
        chunks = []
        start = 0
        n = len(text)
        while start < n:
            end = min(start + chunk_chars, n)
            chunks.append(text[start:end])
            start = end
        return chunks

    def _merge_partial_summaries(self, parts: List[SummaryResult], language: str) -> str:
        """
        부분 요약들을 최종 요약의 입력용 텍스트로 합침.
        (간단: JSON 필드를 텍스트로 직렬화)
        """
        lines = []
        for i, p in enumerate(parts, 1):
            lines.append(f"[PART {i}]")
            if p.summary_text:
                lines.append(f"- summary_text: {p.summary_text}")
            if p.key_points:
                for k in p.key_points:
                    lines.append(f"- key: {k}")
            if p.action_items:
                for a in p.action_items:
                    lines.append(f"- action: {a.description} | assignee={a.assignee} | due={a.due_date}")
            if p.decisions:
                for d in p.decisions:
                    vb = ", ".join(d.voted_by or [])
                    lines.append(f"- decision: [{d.topic}] {d.decision} | voted_by={vb}")
        header = "아래는 부분 요약들을 합친 메모입니다. 이를 바탕으로 최종 JSON 요약을 생성하세요." if language=="ko" \
                 else "Here are merged notes from partial summaries. Produce the final JSON summary."
        return header + "\n\n" + "\n".join(lines)

    async def close(self):
        await self.client.aclose()
        print("ℹ️ UpstageSummarizer 클라이언트를 종료했습니다.")
