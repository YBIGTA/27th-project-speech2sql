"""
Natural language query API routes
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import time
from config.database import get_db
from src.database.operations import SearchOperations, AnalyticsOperations

router = APIRouter()


class QueryRequest(BaseModel):
    """Natural language query request model"""
    query: str
    meeting_id: Optional[int] = None
    speaker: Optional[str] = None
    date_range: Optional[Dict[str, str]] = None
    limit: Optional[int] = 10


class QueryResponse(BaseModel):
    """Query response model"""
    query: str
    sql_query: str
    results: List[Dict[str, Any]]
    total_count: int
    execution_time: float


@router.post("/natural", response_model=QueryResponse)
async def natural_language_query(request: QueryRequest, db: Session = Depends(get_db)):
    """
    Process natural language query and return results
    
    Args:
        request: Query request with natural language text
    
    Returns:
        Query results with SQL translation
    """
    start_time = time.time()
    
    # TODO: Implement Text2SQL conversion with LLM
    # This will be implemented by 팀원 B
    # For now, use simple text search
    
    try:
        # Use the search operations to find relevant content
        search_results = SearchOperations.search_meetings_and_utterances(
            db=db,
            search_query=request.query,
            meeting_id=request.meeting_id,
            speaker=request.speaker,
            limit=request.limit or 10
        )
        
        # Generate mock SQL for demonstration
        conditions = []
        if request.query:
            conditions.append(f"text ILIKE '%{request.query}%'")
        if request.meeting_id:
            conditions.append(f"meeting_id = {request.meeting_id}")
        if request.speaker:
            conditions.append(f"speaker = '{request.speaker}'")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        mock_sql = f"SELECT u.*, m.title FROM utterances u JOIN meetings m ON u.meeting_id = m.id WHERE {where_clause} LIMIT {request.limit or 10}"
        
        execution_time = time.time() - start_time
        
        return QueryResponse(
            query=request.query,
            sql_query=mock_sql,
            results=search_results["results"],
            total_count=search_results["total_count"],
            execution_time=round(execution_time, 3)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@router.get("/suggestions")
async def get_query_suggestions(db: Session = Depends(get_db)):
    """
    Get query suggestions for common questions
    
    Returns:
        List of suggested queries
    """
    # Get dynamic suggestions from database
    db_suggestions = SearchOperations.get_search_suggestions(db)
    
    # Combine with static suggestions
    static_suggestions = [
        "누가 프로젝트 일정에 대해 언급했나요?",
        "어떤 결정사항이 나왔나요?",
        "담당자가 할당된 작업은 무엇인가요?",
        "회의에서 논의된 주요 주제는 무엇인가요?"
    ]
    
    all_suggestions = static_suggestions + db_suggestions
    
    return {
        "suggestions": all_suggestions,
        "total": len(all_suggestions),
        "static_count": len(static_suggestions),
        "dynamic_count": len(db_suggestions)
    }


@router.get("/analytics")
async def get_query_analytics(db: Session = Depends(get_db)):
    """
    Get query analytics and usage statistics
    
    Returns:
        Analytics data
    """
    stats = AnalyticsOperations.get_meeting_statistics(db)
    
    # TODO: Implement actual query logging and analytics
    # For now, return basic stats from meetings and utterances
    
    return {
        "total_meetings": stats["total_meetings"],
        "total_utterances": stats["total_utterances"],
        "searchable_content": stats["total_utterances"] > 0,
        "average_meeting_duration": stats["average_duration_minutes"],
        "data_coverage": "meetings and utterances available for search"
    }


@router.post("/feedback")
async def submit_query_feedback(
    query_id: str,
    rating: int,
    feedback: Optional[str] = None
):
    """
    Submit feedback for query results
    
    Args:
        query_id: Query identifier
        rating: Rating (1-5)
        feedback: Optional feedback text
    
    Returns:
        Feedback submission confirmation
    """
    # TODO: Implement feedback collection
    return {
        "message": "Feedback submitted successfully",
        "query_id": query_id,
        "rating": rating
    } 