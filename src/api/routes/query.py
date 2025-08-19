"""
Natural language query API routes
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, text as sa_text
from config.database import get_db
from src.database.models import Utterance, Meeting
from config.settings import settings
import requests
from src.database.operations import AnalyticsOperations, SearchOperations
import time

# Text2SQL
from src.nlp.text2sql import convert_natural_to_sql, set_database_schema

router = APIRouter()


class QueryRequest(BaseModel):
    """Natural language query request model"""
    query: str
    meeting_id: Optional[int] = None
    speaker: Optional[str] = None
    date_range: Optional[Dict[str, str]] = None
    limit: Optional[int] = 10
    mode: Optional[str] = "text2sql"  # default to text2sql


class QueryResponse(BaseModel):
    """Query response model"""
    query: str
    sql_query: str
    results: List[Dict[str, Any]]
    total_count: int
    execution_time: float
    answer: Optional[str] = None


def _run_fts(request: QueryRequest, db: Session) -> Dict[str, Any]:
    # Use english dictionary and websearch query for better relevance on AMI (English)
    tsvector = func.to_tsvector('english', Utterance.text)
    tsquery = func.websearch_to_tsquery('english', request.query)
    rank = func.ts_rank(tsvector, tsquery)

    base_query = (
        db.query(
            Utterance.id.label("id"),
            Utterance.speaker.label("speaker"),
            Utterance.timestamp.label("timestamp"),
            Utterance.text.label("text"),
            Meeting.title.label("meeting_title"),
            rank.label("rank"),
        )
        .join(Meeting, Utterance.meeting_id == Meeting.id)
        .filter(tsvector.op('@@')(tsquery))
    )

    if request.meeting_id:
        base_query = base_query.filter(Utterance.meeting_id == request.meeting_id)
    if request.speaker:
        base_query = base_query.filter(Utterance.speaker == request.speaker)

    count_query = (
        db.query(func.count(Utterance.id))
        .join(Meeting, Utterance.meeting_id == Meeting.id)
        .filter(tsvector.op('@@')(tsquery))
    )
    if request.meeting_id:
        count_query = count_query.filter(Utterance.meeting_id == request.meeting_id)
    if request.speaker:
        count_query = count_query.filter(Utterance.speaker == request.speaker)

    total_count = count_query.scalar() or 0

    rows = (
        base_query
        .order_by(rank.desc(), Utterance.timestamp.asc())
        .limit(request.limit or 10)
        .all()
    )

    results = [
        {
            "id": r.id,
            "speaker": r.speaker,
            "timestamp": r.timestamp,
            "text": r.text,
            "meeting_title": r.meeting_title,
            "rank": float(r.rank) if r.rank is not None else 0.0,
        }
        for r in rows
    ]

    # Fallback to ILIKE if no results (helps for non-English or short queries)
    if total_count == 0 or len(results) == 0:
        like_pattern = f"%{request.query}%"
        fallback_q = (
            db.query(
                Utterance.id.label("id"),
                Utterance.speaker.label("speaker"),
                Utterance.timestamp.label("timestamp"),
                Utterance.text.label("text"),
                Meeting.title.label("meeting_title"),
            )
            .join(Meeting, Utterance.meeting_id == Meeting.id)
            .filter(Utterance.text.ilike(like_pattern))
        )
        if request.meeting_id:
            fallback_q = fallback_q.filter(Utterance.meeting_id == request.meeting_id)
        if request.speaker:
            fallback_q = fallback_q.filter(Utterance.speaker == request.speaker)
        fb_rows = fallback_q.order_by(Utterance.timestamp.asc()).limit(request.limit or 10).all()
        results = [
            {
                "id": r.id,
                "speaker": r.speaker,
                "timestamp": r.timestamp,
                "text": r.text,
                "meeting_title": r.meeting_title,
                "rank": 0.0,
            }
            for r in fb_rows
        ]
        total_count = len(results)

    sql_preview = (
        "SELECT u.id, u.speaker, u.timestamp, u.text, m.title AS meeting_title "
        "FROM utterances u JOIN meetings m ON u.meeting_id = m.id "
        "WHERE to_tsvector('english', u.text) @@ websearch_to_tsquery('english', :q) "
        "ORDER BY ts_rank(to_tsvector('english', u.text), websearch_to_tsquery('english', :q)) DESC"
    )

    return {
        "sql_query": sql_preview,
        "results": results,
        "total_count": total_count,
    }


def _run_text2sql(request: QueryRequest, db: Session) -> Dict[str, Any]:
    # Provide schema context
    schema = {
        "meetings": ["id", "title", "date", "duration", "participants", "summary", "audio_path"],
        "utterances": ["id", "meeting_id", "speaker", "timestamp", "end_timestamp", "text", "confidence", "language"],
        "actions": ["id", "meeting_id", "action_type", "description", "assignee", "due_date", "status", "priority"],
    }
    set_database_schema(schema)

    # Pass context for better SQL generation
    conv = convert_natural_to_sql(request.query, context={
        "meeting_id": request.meeting_id,
        "limit": request.limit,
    })
    sql_query = conv.get("sql_query", "").strip()

    # Normalize SQL: strip trailing semicolons/newlines
    def _strip_trailing_semicolons(sql: str) -> str:
        return sql.rstrip().rstrip(";").rstrip()

    sql_query = _strip_trailing_semicolons(sql_query)

    if not sql_query:
        raise HTTPException(status_code=400, detail="Failed to generate SQL from query")

    # Safety: allow SELECT only
    if not sql_query.upper().startswith("SELECT"):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed")

    # Ensure limit (robust detection)
    import re as _re
    if not _re.search(r"\blimit\s+\d+\b", sql_query, flags=_re.IGNORECASE):
        sql_query = f"{sql_query} LIMIT {int(request.limit or 10)}"

    params: Dict[str, Any] = {}

    # Special-case: meeting start date only when the question explicitly refers to the meeting itself
    def _is_start_date_question(q: str) -> bool:
        ql = q.lower()
        meeting_terms = ["회의", "미팅", "meeting"]
        start_terms = ["시작일", "시작", "start date", "start time", "begin"]
        exclude_release = ["출시", "발표", "소개", "introduce", "introduced", "release", "launched", "launch", "unveil", "present"]
        if any(t in q or t in ql for t in exclude_release):
            return False
        return (any(t in q or t in ql for t in meeting_terms) and any(t in q or t in ql for t in start_terms))

    if request.meeting_id and _is_start_date_question(request.query):
        sql_query = "SELECT m.title AS meeting_title, m.date AS meeting_date FROM meetings m WHERE m.id = :meeting_id LIMIT 1"
        params = {"meeting_id": int(request.meeting_id)}

    # Scope by meeting if provided: try to inject a filter on meetings alias; fallback smartly
    if request.meeting_id:
        # If SQL already binds :meeting_id, just set the param
        if ":meeting_id" in sql_query.lower():
            params["meeting_id"] = int(request.meeting_id)
        mt = db.query(Meeting.title).filter(Meeting.id == request.meeting_id).scalar()
        if mt:
            import re as _re2

            def _inject_meeting_filter(sql: str, meeting_title_param: str) -> str | None:
                s = _strip_trailing_semicolons(sql)
                lower = s.lower()
                alias = None
                # Find meetings alias in FROM or JOIN
                m_from = _re2.search(r"\bfrom\s+meetings\s+(?:as\s+)?([a-zA-Z_][\w]*)", lower)
                if m_from:
                    alias = m_from.group(1)
                else:
                    if " from meetings" in lower:
                        alias = "meetings"
                if not alias:
                    m_join = _re2.search(r"\bjoin\s+meetings\s+(?:as\s+)?([a-zA-Z_][\w]*)", lower)
                    if m_join:
                        alias = m_join.group(1)
                if not alias:
                    return None
                # Determine insertion point (before ORDER BY / LIMIT / OFFSET), robust to newlines/casing
                order_m = _re2.search(r"\border\s+by\b", lower)
                group_m = _re2.search(r"\bgroup\s+by\b", lower)
                limit_m = _re2.search(r"\blimit\b", lower)
                offset_m = _re2.search(r"\boffset\b", lower)
                indices = [m.start() for m in [order_m, group_m, limit_m, offset_m] if m]
                insert_pos = min(indices) if indices else len(s)
                head = s[:insert_pos]
                tail = s[insert_pos:]
                head_lower = lower[:insert_pos]
                if _re2.search(r"\bwhere\b", head_lower):
                    head = f"{head.rstrip()} AND {alias}.title = :meeting_title "
                else:
                    head = f"{head.rstrip()} WHERE {alias}.title = :meeting_title "
                return head + tail.lstrip()

            injected = _inject_meeting_filter(sql_query, mt)
            if injected:
                sql_query = injected
                params["meeting_title"] = mt
            else:
                # As a last resort, only wrap if inner query exposes meeting_title column
                lower_sel = sql_query.lower()
                if "meeting_title" in lower_sel:
                    sql_inner = _strip_trailing_semicolons(sql_query)
                    sql_query = f"SELECT * FROM ({sql_inner}) AS sub WHERE sub.meeting_title = :meeting_title"
                    params["meeting_title"] = mt
                else:
                    # If we cannot safely inject or wrap, append a filter clause respecting ORDER/LIMIT positions
                    # This assumes the query selects from meetings as alias m (common in our prompts)
                    # If not present, this step is skipped
                    import re
                    _lower = sql_query.lower()
                    if " from meetings " in _lower or " join meetings " in _lower:
                        # Append condition at safe position
                        s = _strip_trailing_semicolons(sql_query)
                        grm = re.search(r"\bgroup\s+by\b", _lower)
                        lm = re.search(r"\blimit\b", _lower)
                        om = re.search(r"\boffset\b", _lower)
                        ordm = re.search(r"\border\s+by\b", _lower)
                        idxs = [m.start() for m in [ordm, grm, lm, om] if m]
                        pos = min(idxs) if idxs else len(s)
                        head, tail = s[:pos], s[pos:]
                        if re.search(r"\bwhere\b", _lower[:pos]):
                            sql_query = f"{head.rstrip()} AND meetings.title = :meeting_title {tail.lstrip()}"
                        else:
                            sql_query = f"{head.rstrip()} WHERE meetings.title = :meeting_title {tail.lstrip()}"
                        params["meeting_title"] = mt

    def _format_answer(rows: List[Dict[str, Any]]) -> Optional[str]:
        # 1) Date-only rows
        for r in rows:
            if ("text" not in r) and ("meeting_date" in r or "date" in r):
                val = r.get("meeting_date") or r.get("date")
                try:
                    if hasattr(val, "date"):
                        d = val.date() if hasattr(val, "hour") else val
                        return f"{d.year}년 {d.month}월 {d.day}일입니다."
                    if isinstance(val, str):
                        s = val.split("T")[0]
                        y, m, d = s.split("-")[:3]
                        return f"{y}년 {int(m)}월 {int(d)}일입니다."
                except Exception:
                    return str(val)
        # 2) Single short utterance
        if rows and all(len((r.get("text") or "")) < 120 for r in rows):
            return rows[0].get("text")
        # 3) Try extract a year from utterance texts
        import re as _yre
        counts: Dict[str, int] = {}
        for r in rows:
            txt = r.get("text") or ""
            for m in _yre.findall(r"\b(19|20)\d{2}\b", txt):
                # full match not captured; fix pattern
                pass
        # re-run with full captures
        for r in rows:
            txt = r.get("text") or ""
            for m in _yre.findall(r"\b((?:19|20)\d{2})\b", txt):
                counts[m] = counts.get(m, 0) + 1
        if counts:
            year = max(counts.items(), key=lambda kv: kv[1])[0]
            return f"{int(year)}년입니다."
        return None

    def _llm_answer_from_rows(question: str, rows: List[Dict[str, Any]]) -> Optional[str]:
        if not settings.upstage_api_key or not rows:
            return None
        # Build compact context from rows
        snippets = []
        for r in rows[:10]:
            txt = (r.get("text") or "").strip()
            if txt:
                snippets.append(txt)
        if not snippets:
            return None
        sys = (
            "You answer user questions STRICTLY using the provided snippets. "
            "Return a single short phrase (e.g., a date like '2001년', '2001년 1월 1일', a name, or a number). "
            "Do not add extra words. If unknown, return '정보 없음'."
        )
        user = (
            f"Question: {question}\n\nSnippets:\n- " + "\n- ".join(snippets)
        )
        payload = {
            "model": "solar-pro",
            "messages": [
                {"role": "system", "content": sys},
                {"role": "user", "content": user},
            ],
            "temperature": 0.0,
            "max_tokens": 64,
        }
        headers = {"Authorization": f"Bearer {settings.upstage_api_key}", "Content-Type": "application/json"}
        try:
            resp = requests.post(f"{settings.upstage_base_url}/chat/completions", json=payload, headers=headers, timeout=20)
            if resp.status_code != 200:
                return None
            data = resp.json()
            ans = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            return ans or None
        except Exception:
            return None

    try:
        result = db.execute(sa_text(sql_query), params)
        rows = result.fetchall()
        raw_results = [dict(row._mapping) for row in rows]
        # Normalize results for frontend: if only meeting_date is present, render concise natural text
        results: List[Dict[str, Any]] = []
        for r in raw_results:
            if ("text" not in r) and ("meeting_date" in r or "date" in r):
                dt = r.get("meeting_date") or r.get("date")
                # Format date as 'YYYY년 M월 D일입니다.' without time part
                def _fmt_kr_date(val: Any) -> str:
                    try:
                        if hasattr(val, "date"):
                            d = val.date() if hasattr(val, "hour") else val
                            return f"{d.year}년 {d.month}월 {d.day}일입니다."
                        if isinstance(val, str):
                            s = val.split("T")[0]
                            parts = s.split("-")
                            if len(parts) >= 3:
                                y, m, d = parts[0], str(int(parts[1])), str(int(parts[2]))
                                return f"{y}년 {m}월 {d}일입니다."
                            return s
                    except Exception:
                        pass
                    return str(val)
                dt_str = _fmt_kr_date(dt)
                results.append({
                    "speaker": "-",
                    "timestamp": None,
                    "text": dt_str,
                    "meeting_title": r.get("meeting_title") or r.get("title")
                })
            else:
                results.append(r)
        total_count = len(results)
        # Try LLM-based answering first
        answer = _llm_answer_from_rows(request.query, results)
        if not answer:
            answer = _format_answer(results)
        if total_count == 0:
            # Fallback: if Text2SQL returned nothing, retry with FTS scoped by meeting/speaker
            fts_out = _run_fts(request, db)
            llm_ans = _llm_answer_from_rows(request.query, fts_out["results"]) or _format_answer(fts_out["results"])            
            return {"sql_query": sql_query, "results": fts_out["results"], "total_count": fts_out["total_count"], "answer": llm_ans }
        return {"sql_query": sql_query, "results": results, "total_count": total_count, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SQL execution failed: {e}")


@router.get("/meetings")
async def list_meetings(db: Session = Depends(get_db)):
    rows = db.query(Meeting.id, Meeting.title).order_by(Meeting.id.desc()).limit(100).all()
    return {"meetings": [{"id": r.id, "title": r.title} for r in rows]}


@router.post("/natural", response_model=QueryResponse)
async def natural_language_query(request: QueryRequest, db: Session = Depends(get_db)):
    """
    Process natural language query using FTS or Text2SQL
    """
    start_time = time.perf_counter()

    try:
        if request.mode == "text2sql":
            out = _run_text2sql(request, db)
        else:
            out = _run_fts(request, db)
    except HTTPException:
        raise
    except Exception:
        out = _run_fts(request, db)

    execution_time = round(time.perf_counter() - start_time, 4)

    return QueryResponse(
        query=request.query,
        sql_query=out["sql_query"],
        results=out["results"],
        total_count=out["total_count"],
        execution_time=execution_time,
        answer=out.get("answer"),
    )


@router.get("/suggestions")
async def get_query_suggestions(db: Session = Depends(get_db)):
    static_suggestions = [
        "누가 프로젝트 일정에 대해 언급했나요?",
        "어떤 결정사항이 나왔나요?",
        "담당자가 할당된 작업은 무엇인가요?",
        "특정 키워드가 언급된 부분을 찾아주세요",
        "회의에서 논의된 주요 주제는 무엇인가요?",
    ]
    try:
        dynamic = SearchOperations.get_search_suggestions(db)
    except Exception:
        dynamic = []
    all_suggestions = static_suggestions + dynamic
    return {"suggestions": all_suggestions, "total": len(all_suggestions)}


@router.get("/analytics")
async def get_query_analytics(db: Session = Depends(get_db)):
    try:
        stats = AnalyticsOperations.get_meeting_statistics(db)
        return {
            "total_meetings": stats.get("total_meetings", 0),
            "total_utterances": stats.get("total_utterances", 0),
            "total_actions": stats.get("total_actions", 0),
            "average_duration_minutes": stats.get("average_duration_minutes", 0.0),
            "monthly_meetings": stats.get("monthly_meetings", []),
        }
    except Exception:
        return {
            "total_meetings": 0,
            "total_utterances": 0,
            "total_actions": 0,
            "average_duration_minutes": 0.0,
            "monthly_meetings": [],
        }


@router.post("/feedback")
async def submit_query_feedback(
    query_id: str, rating: int, feedback: Optional[str] = None
):
    return {"message": "Feedback submitted successfully", "query_id": query_id, "rating": rating} 