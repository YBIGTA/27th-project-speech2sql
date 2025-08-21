"""
Search API routes for hybrid search functionality
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from config.database import get_db
from src.search.hybrid_search import create_hybrid_search

router = APIRouter()


class SearchRequest(BaseModel):
    """Search request model"""
    query: str
    search_type: Optional[str] = "hybrid"  # exact, semantic, llm, hybrid
    meeting_id: Optional[int] = None
    speaker: Optional[str] = None
    date_range: Optional[Dict[str, str]] = None
    time_range: Optional[Dict[str, float]] = None
    limit: Optional[int] = 20


class SearchResponse(BaseModel):
    """Search response model"""
    query: str
    search_type: str
    total_results: int
    execution_time: float
    utterances: List[Dict[str, Any]]
    meetings: List[Dict[str, Any]]
    suggestions: Optional[List[str]] = None


@router.post("/search", response_model=SearchResponse)
async def search_meetings(
    request: SearchRequest,
    db: Session = Depends(get_db)
):
    """
    Perform hybrid search across meetings and utterances
    """
    try:
        # Create search engine
        search_engine = create_hybrid_search(db)
        
        # Prepare filters
        filters = {}
        if request.meeting_id:
            filters["meeting_id"] = request.meeting_id
        if request.speaker:
            filters["speaker"] = request.speaker
        if request.date_range:
            filters["date_range"] = request.date_range
        if request.time_range:
            filters["time_range"] = request.time_range
        
        # Perform search
        results = search_engine.search(
            query=request.query,
            search_type=request.search_type,
            filters=filters,
            limit=request.limit
        )
        
        # Get suggestions
        suggestions = search_engine.get_search_suggestions(request.query)
        
        return SearchResponse(
            query=results["query"],
            search_type=results["search_type"],
            total_results=results["total_results"],
            execution_time=results["execution_time"],
            utterances=results["utterances"]["results"],
            meetings=results["meetings"]["results"],
            suggestions=suggestions
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/suggestions")
async def get_search_suggestions(
    query: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):
    """
    Get search suggestions based on partial query
    """
    try:
        search_engine = create_hybrid_search(db)
        suggestions = search_engine.get_search_suggestions(query)
        
        return {
            "query": query,
            "suggestions": suggestions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")


@router.post("/index/{meeting_id}")
async def index_meeting(
    meeting_id: int,
    db: Session = Depends(get_db)
):
    """
    Index a specific meeting in Elasticsearch
    """
    try:
        search_engine = create_hybrid_search(db)
        search_engine.index_meeting_data(meeting_id)
        
        return {
            "message": f"Successfully indexed meeting {meeting_id}",
            "meeting_id": meeting_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to index meeting: {str(e)}")


@router.post("/index/all")
async def index_all_meetings(
    db: Session = Depends(get_db)
):
    """
    Index all meetings in Elasticsearch
    """
    try:
        from src.database.models import Meeting
        
        search_engine = create_hybrid_search(db)
        meetings = db.query(Meeting).all()
        
        indexed_count = 0
        for meeting in meetings:
            try:
                search_engine.index_meeting_data(meeting.id)
                indexed_count += 1
            except Exception as e:
                print(f"Failed to index meeting {meeting.id}: {e}")
        
        return {
            "message": f"Indexed {indexed_count} out of {len(meetings)} meetings",
            "total_meetings": len(meetings),
            "indexed_count": indexed_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to index meetings: {str(e)}")


@router.get("/stats")
async def get_search_stats(
    db: Session = Depends(get_db)
):
    """
    Get search statistics and index information
    """
    try:
        from src.database.models import Meeting, Utterance
        from src.search.elasticsearch_client import get_elasticsearch_client
        
        # Database stats
        total_meetings = db.query(Meeting).count()
        total_utterances = db.query(Utterance).count()
        
        # Elasticsearch stats
        es_client = get_elasticsearch_client()
        
        try:
            meeting_stats = es_client.es.indices.stats(index=es_client.index_name)
            utterance_stats = es_client.es.indices.stats(index=es_client.utterance_index)
            
            es_meeting_count = meeting_stats["indices"][es_client.index_name]["total"]["docs"]["count"]
            es_utterance_count = utterance_stats["indices"][es_client.utterance_index]["total"]["docs"]["count"]
        except Exception:
            es_meeting_count = 0
            es_utterance_count = 0
        
        return {
            "database": {
                "total_meetings": total_meetings,
                "total_utterances": total_utterances
            },
            "elasticsearch": {
                "indexed_meetings": es_meeting_count,
                "indexed_utterances": es_utterance_count,
                "sync_percentage": {
                    "meetings": round((es_meeting_count / total_meetings * 100) if total_meetings > 0 else 0, 2),
                    "utterances": round((es_utterance_count / total_utterances * 100) if total_utterances > 0 else 0, 2)
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}") 