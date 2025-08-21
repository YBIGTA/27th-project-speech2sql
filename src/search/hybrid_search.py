"""
Hybrid search system combining PostgreSQL, Elasticsearch, and LLM
"""
from typing import Dict, List, Any, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import text
import time
from src.database.models import Meeting, Utterance, Action
from src.search.elasticsearch_client import get_elasticsearch_client
from config.settings import settings


class HybridSearchEngine:
    """Hybrid search engine combining multiple search strategies"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.es_client = get_elasticsearch_client()
        self.search_strategies = {
            "exact": self._exact_search,
            "semantic": self._semantic_search,
            "llm": self._llm_search,
            "hybrid": self._hybrid_search
        }
    
    def search(self, query: str, search_type: str = "hybrid", 
               filters: Optional[Dict] = None, limit: int = 20) -> Dict[str, Any]:
        """
        Perform search using specified strategy
        
        Args:
            query: Search query
            search_type: "exact", "semantic", "llm", or "hybrid"
            filters: Search filters
            limit: Maximum results
            
        Returns:
            Search results with metadata
        """
        start_time = time.time()
        
        if search_type not in self.search_strategies:
            search_type = "hybrid"
        
        strategy_func = self.search_strategies[search_type]
        results = strategy_func(query, filters, limit)
        
        results["execution_time"] = time.time() - start_time
        results["search_type"] = search_type
        results["query"] = query
        
        return results
    
    def _exact_search(self, query: str, filters: Optional[Dict] = None, limit: int = 20) -> Dict[str, Any]:
        """Exact keyword search using Elasticsearch"""
        try:
            # Search utterances
            utterance_results = self.es_client.search_utterances(query, filters, limit)
            
            # Search meetings
            meeting_results = self.es_client.search_meetings(query, filters, limit//2)
            
            return {
                "utterances": utterance_results,
                "meetings": meeting_results,
                "total_results": utterance_results["total"] + meeting_results["total"],
                "strategy": "exact_keyword"
            }
        except Exception as e:
            print(f"Elasticsearch search failed: {e}")
            return self._fallback_sql_search(query, filters, limit)
    
    def _semantic_search(self, query: str, filters: Optional[Dict] = None, limit: int = 20) -> Dict[str, Any]:
        """Semantic search using embeddings"""
        # TODO: Implement with sentence-transformers
        # For now, fallback to exact search
        return self._exact_search(query, filters, limit)
    
    def _llm_search(self, query: str, filters: Optional[Dict] = None, limit: int = 20) -> Dict[str, Any]:
        """LLM-powered search for complex queries"""
        try:
            # Use LLM to understand query intent and generate search strategy
            enhanced_query = self._enhance_query_with_llm(query)
            
            # Apply enhanced search
            results = self._exact_search(enhanced_query, filters, limit)
            results["llm_enhanced_query"] = enhanced_query
            
            return results
        except Exception as e:
            print(f"LLM search failed: {e}")
            return self._exact_search(query, filters, limit)
    
    def _hybrid_search(self, query: str, filters: Optional[Dict] = None, limit: int = 20) -> Dict[str, Any]:
        """Combine multiple search strategies"""
        results = {
            "utterances": [],
            "meetings": [],
            "total_results": 0,
            "strategy": "hybrid"
        }
        
        # Try exact search first
        exact_results = self._exact_search(query, filters, limit)
        results["utterances"].extend(exact_results["utterances"]["results"])
        results["meetings"].extend(exact_results["meetings"]["results"])
        
        # If not enough results, try LLM enhancement
        if len(results["utterances"]) < limit // 2:
            try:
                llm_results = self._llm_search(query, filters, limit - len(results["utterances"]))
                results["utterances"].extend(llm_results["utterances"]["results"])
                results["meetings"].extend(llm_results["meetings"]["results"])
            except Exception as e:
                print(f"LLM enhancement failed: {e}")
        
        # Remove duplicates
        results["utterances"] = self._deduplicate_utterances(results["utterances"])
        results["meetings"] = self._deduplicate_meetings(results["meetings"])
        
        results["total_results"] = len(results["utterances"]) + len(results["meetings"])
        
        return results
    
    def _fallback_sql_search(self, query: str, filters: Optional[Dict] = None, limit: int = 20) -> Dict[str, Any]:
        """Fallback to PostgreSQL full-text search"""
        try:
            # Build SQL query
            sql_query = """
                SELECT u.id, u.speaker, u.timestamp, u.text, u.confidence,
                       m.title as meeting_title, m.date as meeting_date
                FROM utterances u
                JOIN meetings m ON u.meeting_id = m.id
                WHERE to_tsvector('simple', u.text) @@ plainto_tsquery('simple', :query)
            """
            
            params = {"query": query}
            
            # Add filters
            if filters:
                if filters.get("meeting_id"):
                    sql_query += " AND u.meeting_id = :meeting_id"
                    params["meeting_id"] = filters["meeting_id"]
                
                if filters.get("speaker"):
                    sql_query += " AND u.speaker = :speaker"
                    params["speaker"] = filters["speaker"]
            
            sql_query += " ORDER BY u.timestamp LIMIT :limit"
            params["limit"] = limit
            
            # Execute query
            result = self.db.execute(text(sql_query), params)
            utterances = []
            
            for row in result:
                utterances.append({
                    "id": row.id,
                    "speaker": row.speaker,
                    "timestamp": row.timestamp,
                    "text": row.text,
                    "confidence": row.confidence,
                    "meeting_title": row.meeting_title,
                    "meeting_date": row.meeting_date.isoformat() if row.meeting_date else None
                })
            
            return {
                "utterances": {"results": utterances, "total": len(utterances)},
                "meetings": {"results": [], "total": 0},
                "total_results": len(utterances),
                "strategy": "sql_fallback"
            }
            
        except Exception as e:
            print(f"SQL fallback search failed: {e}")
            return {
                "utterances": {"results": [], "total": 0},
                "meetings": {"results": [], "total": 0},
                "total_results": 0,
                "strategy": "failed"
            }
    
    def _enhance_query_with_llm(self, query: str) -> str:
        """Use LLM to enhance search query"""
        if not settings.upstage_api_key:
            return query
        
        try:
            import requests
            
            prompt = f"""
            다음 검색 쿼리를 더 효과적인 키워드 검색으로 변환해주세요.
            원본 쿼리: "{query}"
            
            변환 규칙:
            1. 핵심 키워드만 추출
            2. 동의어나 관련어 추가
            3. 불필요한 조사나 형식적 표현 제거
            4. 검색에 유용한 키워드로 변환
            
            변환된 쿼리만 답변해주세요.
            """
            
            headers = {
                "Authorization": f"Bearer {settings.upstage_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "solar-1-mini-chat",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 100,
                "temperature": 0.1
            }
            
            response = requests.post(
                f"{settings.upstage_base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                enhanced_query = result["choices"][0]["message"]["content"].strip()
                return enhanced_query if enhanced_query else query
            else:
                return query
                
        except Exception as e:
            print(f"LLM query enhancement failed: {e}")
            return query
    
    def _deduplicate_utterances(self, utterances: List[Dict]) -> List[Dict]:
        """Remove duplicate utterances"""
        seen = set()
        unique_utterances = []
        
        for utterance in utterances:
            key = f"{utterance.get('id', '')}-{utterance.get('text', '')[:50]}"
            if key not in seen:
                seen.add(key)
                unique_utterances.append(utterance)
        
        return unique_utterances
    
    def _deduplicate_meetings(self, meetings: List[Dict]) -> List[Dict]:
        """Remove duplicate meetings"""
        seen = set()
        unique_meetings = []
        
        for meeting in meetings:
            key = meeting.get('id', '')
            if key not in seen:
                seen.add(key)
                unique_meetings.append(meeting)
        
        return unique_meetings
    
    def get_search_suggestions(self, query: str) -> List[str]:
        """Get search suggestions"""
        try:
            return self.es_client.get_suggestions(query)
        except Exception as e:
            print(f"Search suggestions failed: {e}")
            return []
    
    def index_meeting_data(self, meeting_id: int):
        """Index meeting data in Elasticsearch"""
        try:
            # Get meeting data
            meeting = self.db.query(Meeting).filter(Meeting.id == meeting_id).first()
            if not meeting:
                return
            
            # Get utterances
            utterances = self.db.query(Utterance).filter(Utterance.meeting_id == meeting_id).all()
            
            # Prepare data
            meeting_data = {
                "id": meeting.id,
                "title": meeting.title,
                "date": meeting.date.isoformat() if meeting.date else None,
                "duration": meeting.duration,
                "participants": meeting.participants or [],
                "summary": meeting.summary,
                "created_at": meeting.created_at.isoformat() if meeting.created_at else None
            }
            
            utterance_data = []
            for utterance in utterances:
                utterance_data.append({
                    "id": utterance.id,
                    "meeting_id": utterance.meeting_id,
                    "speaker": utterance.speaker,
                    "timestamp": utterance.timestamp,
                    "end_timestamp": utterance.end_timestamp,
                    "text": utterance.text,
                    "confidence": utterance.confidence,
                    "language": utterance.language
                })
            
            # Index in Elasticsearch
            self.es_client.index_meeting(meeting_data)
            self.es_client.index_utterances(utterance_data, meeting_data)
            
            print(f"✅ Indexed meeting {meeting_id} in Elasticsearch")
            
        except Exception as e:
            print(f"Failed to index meeting {meeting_id}: {e}")


# Convenience function
def create_hybrid_search(db_session: Session) -> HybridSearchEngine:
    """Create hybrid search engine instance"""
    return HybridSearchEngine(db_session) 