"""
Hybrid search system combining PostgreSQL and vector search
"""
from typing import Dict, List, Any, Optional
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.database.models import Meeting, Utterance, Action
from src.nlp.text2sql import convert_natural_to_sql


class HybridSearch:
    """Hybrid search combining exact SQL queries and semantic vector search"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.vector_enabled = False  # Set to True when pgvector is available
    
    def search(self, query: str, search_type: str = "hybrid", limit: int = 20) -> Dict[str, Any]:
        """
        Perform hybrid search
        
        Args:
            query: Natural language query
            search_type: "exact", "semantic", or "hybrid"
            limit: Maximum number of results
        
        Returns:
            Search results with metadata
        """
        results = {
            "query": query,
            "search_type": search_type,
            "results": [],
            "metadata": {}
        }
        
        if search_type == "exact" or search_type == "hybrid":
            exact_results = self._exact_search(query, limit)
            results["results"].extend(exact_results)
            results["metadata"]["exact_count"] = len(exact_results)
        
        if search_type == "semantic" or search_type == "hybrid":
            if self.vector_enabled:
                semantic_results = self._semantic_search(query, limit)
                results["results"].extend(semantic_results)
                results["metadata"]["semantic_count"] = len(semantic_results)
        
        # Remove duplicates and rank results
        results["results"] = self._deduplicate_and_rank(results["results"])
        results["metadata"]["total_count"] = len(results["results"])
        
        return results
    
    def _exact_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Perform exact search using Text2SQL"""
        try:
            # Convert natural language to SQL
            sql_result = convert_natural_to_sql(query)
            sql_query = sql_result["sql_query"]
            
            if not sql_result.get("valid", True):
                # Fallback to keyword search
                return self._keyword_search(query, limit)
            
            # Execute SQL query
            result = self.db.execute(text(sql_query))
            rows = result.fetchall()
            
            return [
                {
                    "type": "exact",
                    "source": "sql",
                    "data": dict(row._mapping),
                    "confidence": sql_result.get("confidence", 0.8)
                }
                for row in rows[:limit]
            ]
            
        except Exception as e:
            print(f"SQL search failed: {e}")
            return self._keyword_search(query, limit)
    
    def _keyword_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Fallback keyword search"""
        # Simple keyword-based search
        keywords = self._extract_keywords(query)
        
        if not keywords:
            return []
        
        # Search in utterances
        utterances = (
            self.db.query(Utterance)
            .filter(Utterance.text.contains(keywords[0]))
            .limit(limit)
            .all()
        )
        
        return [
            {
                "type": "keyword",
                "source": "utterance",
                "data": {
                    "speaker": u.speaker,
                    "text": u.text,
                    "timestamp": u.timestamp,
                    "meeting_id": u.meeting_id
                },
                "confidence": 0.6
            }
            for u in utterances
        ]
    
    def _semantic_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Perform semantic search using vector similarity"""
        # TODO: Implement when pgvector is available
        return []
    
    def _deduplicate_and_rank(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicates and rank results by confidence"""
        # Remove duplicates based on content
        seen = set()
        unique_results = []
        
        for result in results:
            content_key = f"{result['data'].get('meeting_id', '')}-{result['data'].get('timestamp', '')}-{result['data'].get('text', '')[:50]}"
            
            if content_key not in seen:
                seen.add(content_key)
                unique_results.append(result)
        
        # Sort by confidence
        unique_results.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        
        return unique_results
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract meaningful keywords from query"""
        import re
        
        # Remove common words
        stop_words = ['누가', '언제', '무엇을', '무엇', '어떻게', '왜', '언급', '말했다', '에', '에서', '을', '를', '이', '가', '의', '와', '과', '그리고', '또는', '하지만', '그런데']
        
        words = re.findall(r'\w+', query)
        keywords = [word for word in words if word not in stop_words and len(word) > 1]
        
        return keywords[:3]
    
    def enable_vector_search(self):
        """Enable vector search functionality"""
        self.vector_enabled = True
    
    def disable_vector_search(self):
        """Disable vector search functionality"""
        self.vector_enabled = False


# Example usage
def create_hybrid_search(db_session: Session) -> HybridSearch:
    """Create hybrid search instance"""
    return HybridSearch(db_session) 