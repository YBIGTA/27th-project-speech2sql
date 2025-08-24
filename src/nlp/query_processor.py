"""
Query Processor for refining natural language queries before Text2SQL conversion.
- 다국어/코드믹스 질의 표준화
- 상대 날짜 표현 → 절대 범위 추출(KST)
- 테이블/컬럼 힌트, LIMIT 힌트 추출
"""
import re
import unicodedata
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any

# --- 타임존 (서울) ---
KST = timezone(timedelta(hours=9))

# --- 다국어 동의어 사전(표준어 -> 동의어들) ---
SYNONYM_MAP = {
    "ko": {
        "actions": ["액션 아이템", "액션아이템", "할 일", "할일", "작업", "to-do", "투두"],
        "meetings": ["회의", "미팅", "회의록"],
        "utterances": ["발언", "대화", "언급", "이야기", "내용"],
        "assignee": ["담당자", "책임자", "누구한테", "누가 담당"],
        "due_date": ["마감일", "기한", "언제까지", "마감"],
        "decision": ["결정 사항", "결정된 것", "결정", "확정", "합의"],
        "keyword": ["키워드", "주제"]
    },
    "en": {
        "actions": ["action item", "action items", "task", "tasks", "to-do", "to do"],
        "meetings": ["meeting", "meetings", "sync-up", "sync up", "discussion"],
        "utterances": ["utterance", "utterances", "statement", "comment", "mention", "mentions"],
        "assignee": ["assignee", "person in charge", "responsible for"],
        "due_date": ["due date", "deadline", "by when"],
        "decision": ["decision", "decisions", "what was decided"],
        "keyword": ["keyword", "topic", "topics"]
    }
}

# --- 영어/한국어 불용어(키워드 추출 시 사용 가능) ---
STOP_WORDS_KO = {
    '누가','언제','무엇을','무엇','어떻게','왜','언급','말했다','에','에서','을','를','이','가','의','와','과',
    '그리고','또는','하지만','그런데','있는','없는','대한','관련','해주세요','해줘','찾아줘'
}
STOP_WORDS_EN = {
    'the','a','an','and','or','but','if','then','else','with','without','of','to','in','on','for','by','from','at',
    'is','are','was','were','be','been','being','do','does','did','who','what','when','where','why','how','show',
    'list','find','get','give','display','please','all','any','each','every','about','that','this','those','these'
}

# --- 상대 날짜 패턴 ---
RELATIVE_DATE_PATTERNS = [
    # Korean
    (r"(오늘|금일)", "today"),
    (r"(어제|전날)", "yesterday"),
    (r"(이번주|이 주|금주)", "this_week"),
    (r"(지난주|저번주|전주)", "last_week"),
    (r"(이번달|이 달|금월|당월)", "this_month"),
    (r"(지난달|저번달|전월)", "last_month"),
    (r"최근\s*(\d+)\s*일", "last_n_days"),
    # English
    (r"\btoday\b", "today"),
    (r"\byesterday\b", "yesterday"),
    (r"\bthis\s*week\b", "this_week"),
    (r"\blast\s*week\b", "last_week"),
    (r"\bthis\s*month\b", "this_month"),
    (r"\blast\s*month\b", "last_month"),
    (r"\blast\s*(\d+)\s*days\b", "last_n_days"),
]

TOP_LIMIT_PATTERNS = [
    (r"(상위|탑|top)\s*(\d+)", 2),
    (r"\blimit\s*(\d+)\b", 1),
]

@dataclass
class QueryMeta:
    language: str                   # 'ko' | 'en' | 'mix'
    tables_hint: List[str]          # ['actions','utterances',...]
    columns_hint: List[str]         # ['assignee','due_date',...]
    date_range: Optional[Dict[str, str]]  # {'start':'YYYY-MM-DD','end':'YYYY-MM-DD'}
    limit_hint: Optional[int]       # e.g., 10
    keywords: List[str]             # up to 5

class QueryProcessor:
    """
    자연어 질문을 Text2SQL 모델이 더 잘 이해할 수 있도록 정제 + 메타 추출
    """

    def __init__(self):
        # '동의어 -> 표준어' 룩업 테이블 생성(언어별, 길이순 정렬)
        self._lookups = {
            lang: self._build_lookup(smap)
            for lang, smap in SYNONYM_MAP.items()
        }
        print("✅ QueryProcessor 초기화 완료")

    # ----------------- Public APIs -----------------
    def process_query(self, natural_query: str, language: str = None) -> str:
        """
        (하위호환) 정제된 질의 문자열만 반환
        """
        refined, _ = self._process(natural_query, language)
        return refined

    def process_query_with_meta(self, natural_query: str, language: str = None) -> Tuple[str, QueryMeta]:
        """
        정제 문자열 + 메타(테이블/컬럼/날짜/limit/키워드) 반환
        """
        return self._process(natural_query, language)

    # ----------------- Core pipeline -----------------
    def _process(self, natural_query: str, language: Optional[str]) -> Tuple[str, QueryMeta]:
        raw = natural_query or ""
        norm = self._normalize(raw)
        lang = language or self._detect_language(norm)

        # 용어 표준화(혼합이면 ko+en 모두 적용)
        std = self._standardize_terms(norm, lang)

        # 힌트 추출
        tables = self._extract_tables_hint(std, lang)
        cols = self._extract_columns_hint(std, lang)
        date_range = self._extract_date_range(std)
        limit_hint = self._extract_limit(std)
        keywords = self._extract_keywords(std, topk=5)

        # 최소한의 로그
        print(f"    - lang={lang}, tables={tables}, cols={cols}, date={date_range}, limit={limit_hint}, kw={keywords}")

        meta = QueryMeta(
            language=lang,
            tables_hint=tables,
            columns_hint=cols,
            date_range=date_range,
            limit_hint=limit_hint,
            keywords=keywords
        )
        return std, meta

    # ----------------- Helpers -----------------
    def _normalize(self, s: str) -> str:
        # 유니코드 정규화 + 공백 정리
        s = unicodedata.normalize("NFKC", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def _detect_language(self, q: str) -> str:
        has_en = bool(re.search(r"[A-Za-z]", q))
        has_ko = bool(re.search(r"[\uac00-\ud7a3]", q))
        if has_en and has_ko:
            return "mix"
        if has_en:
            return "en"
        return "ko"

    def _build_lookup(self, synonym_map: Dict[str, List[str]]) -> Dict[str, str]:
        # '동의어 -> 표준어' 매핑
        lookup = {}
        for standard, syns in synonym_map.items():
            for s in syns:
                lookup[s.lower()] = standard
        # 긴 표현부터 매칭
        lookup["_sorted_keys"] = sorted(lookup.keys(), key=len, reverse=True)
        return lookup

    def _standardize_terms(self, q: str, lang: str) -> str:
        # 혼합이면 ko, en 둘 다 적용
        langs = ["ko","en"] if lang == "mix" else [lang]
        std = q
        for l in langs:
            lk = self._lookups.get(l)
            if not lk:
                continue
            keys = lk["_sorted_keys"]
            # 영어는 단어경계, 한국어는 단순 포함 매칭(띄어쓰기/조사 이슈)
            pattern_parts = []
            for k in keys:
                if not k or k == "_sorted_keys":
                    continue
                if re.search(r"[A-Za-z]", k):
                    pattern_parts.append(rf"\b{re.escape(k)}\b")
                else:
                    pattern_parts.append(re.escape(k))
            if not pattern_parts:
                continue
            pattern = re.compile("|".join(pattern_parts), flags=re.IGNORECASE)

            def repl(m):
                token = m.group(0).lower()
                return lk.get(token, token)

            std = pattern.sub(repl, std)
        if std != q:
            print(f"    - 용어 표준화: '{q}' -> '{std}'")
        return std

    def _extract_tables_hint(self, q: str, lang: str) -> List[str]:
        hints = set()
        ql = q.lower()
        # 표준어 키워드 기반
        if "actions" in ql or "action" in ql:
            hints.add("actions")
        if "utterances" in ql or "mention" in ql or "발언" in q:
            hints.add("utterances")
        if "meetings" in ql or "meeting" in ql or "회의" in q:
            hints.add("meetings")
        return sorted(hints)

    def _extract_columns_hint(self, q: str, lang: str) -> List[str]:
        cols = set()
        ql = q.lower()
        for c in ["assignee","due_date","decision","keyword","speaker","timestamp","amount","status","paid_at"]:
            if c in ql:
                cols.add(c)
        # 한국어 단어로 잡히는 것들
        if re.search(r"(담당자|책임자)", q):
            cols.add("assignee")
        if re.search(r"(마감일|기한|언제까지|마감)", q):
            cols.add("due_date")
        if re.search(r"(결정|합의|확정)", q):
            cols.add("decision")
        if re.search(r"(발언자|화자|스피커)", q):
            cols.add("speaker")
        if re.search(r"(시간|타임스탬프|시각)", q):
            cols.add("timestamp")
        return sorted(cols)

    def _extract_date_range(self, q: str) -> Optional[Dict[str, str]]:
        ql = q.lower()
        now = datetime.now(tz=KST).date()

        for pat, kind in RELATIVE_DATE_PATTERNS:
            m = re.search(pat, q, flags=re.IGNORECASE)
            if not m:
                continue
            if kind == "today":
                s = e = now
            elif kind == "yesterday":
                s = e = (now - timedelta(days=1))
            elif kind == "this_week":
                # 월요일 시작, 일요일 끝
                s = now - timedelta(days=now.weekday())
                e = s + timedelta(days=6)
            elif kind == "last_week":
                e = now - timedelta(days=now.weekday() + 1)
                s = e - timedelta(days=6)
            elif kind == "this_month":
                s = now.replace(day=1)
                # 다음 달 1일 - 1일
                if s.month == 12:
                    e = s.replace(year=s.year+1, month=1, day=1) - timedelta(days=1)
                else:
                    e = s.replace(month=s.month+1, day=1) - timedelta(days=1)
            elif kind == "last_month":
                first_this = now.replace(day=1)
                e = first_this - timedelta(days=1)
                s = e.replace(day=1)
            elif kind == "last_n_days":
                n = int(m.group(1))
                e = now
                s = now - timedelta(days=n-1)
            else:
                continue
            return {"start": s.isoformat(), "end": e.isoformat()}

        # YYYY-MM-DD ~ YYYY-MM-DD 형태 직접 지정된 경우
        m2 = re.search(r"(\d{4}-\d{2}-\d{2})\s*[~\-–]\s*(\d{4}-\d{2}-\d{2})", q)
        if m2:
            return {"start": m2.group(1), "end": m2.group(2)}

        return None

    def _extract_limit(self, q: str) -> Optional[int]:
        for pat, gi in TOP_LIMIT_PATTERNS:
            m = re.search(pat, q, flags=re.IGNORECASE)
            if m:
                try:
                    return int(m.group(gi))
                except Exception:
                    continue
        return None

    def _extract_keywords(self, q: str, topk: int = 5) -> List[str]:
        # 간단 키워드: 한글/영문만 추출, 불용어 제거, 중복 제거
        tokens = re.findall(r"[A-Za-z]+|[가-힣]+", q)
        out, seen = [], set()
        for t in tokens:
            t_en = t.lower()
            if t in STOP_WORDS_KO or t_en in STOP_WORDS_EN:
                continue
            if len(t) <= 1:
                continue
            key = t_en
            if key in seen:
                continue
            seen.add(key)
            out.append(t)
            if len(out) == topk:
                break
        return out


# --- 전역 인스턴스 및 헬퍼 ---
query_processor = QueryProcessor()

def refine_query(natural_query: str, language: str = None) -> str:
    """(하위호환) 정제 문자열만 반환"""
    return query_processor.process_query(natural_query, language)

def refine_query_with_meta(natural_query: str, language: str = None) -> Dict[str, Any]:
    """정제 문자열 + 메타 반환(딕셔너리)"""
    refined, meta = query_processor.process_query_with_meta(natural_query, language)
    data = asdict(meta)
    data["refined_query"] = refined
    return data
