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

    conv = convert_natural_to_sql(request.query)
    sql_query = conv.get("sql_query", "").strip()

    if not sql_query:
        raise HTTPException(status_code=400, detail="Failed to generate SQL from query")

    # Safety: allow SELECT only
    if not sql_query.upper().startswith("SELECT"):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed")

    # Ensure limit
    if " limit " not in sql_query.lower():
        sql_query = f"{sql_query} LIMIT {int(request.limit or 10)}"

    params: Dict[str, Any] = {}

    # Scope by meeting if provided: wrap as subquery and filter by meeting_title
    if request.meeting_id:
        mt = db.query(Meeting.title).filter(Meeting.id == request.meeting_id).scalar()
        if mt:
            wrapped = f"SELECT * FROM ({sql_query}) AS sub WHERE sub.meeting_title = :meeting_title"
            sql_query = wrapped
            params["meeting_title"] = mt

    try:
        result = db.execute(sa_text(sql_query), params)
        rows = result.fetchall()
        results = [dict(row._mapping) for row in rows]
        total_count = len(results)
        return {"sql_query": sql_query, "results": results, "total_count": total_count}
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
    )


@router.get("/suggestions")
async def get_query_suggestions():
    suggestions = [
        "누가 프로젝트 일정에 대해 언급했나요?",
        "어떤 결정사항이 나왔나요?",
        "담당자가 할당된 작업은 무엇인가요?",
        "특정 키워드가 언급된 부분을 찾아주세요",
        "회의에서 논의된 주요 주제는 무엇인가요?",
    ]
    return {"suggestions": suggestions, "total": len(suggestions)}


@router.get("/analytics")
async def get_query_analytics():
    return {
        "total_queries": 0,
        "popular_queries": [],
        "average_response_time": 0.0,
        "success_rate": 0.0,
    }


@router.post("/feedback")
async def submit_query_feedback(
    query_id: str, rating: int, feedback: Optional[str] = None
):
    return {"message": "Feedback submitted successfully", "query_id": query_id, "rating": rating} 