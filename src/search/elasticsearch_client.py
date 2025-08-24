"""
Elasticsearch client and index management for Speech2SQL
"""
from typing import Dict, List, Any, Optional
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import json
from datetime import datetime
from config.settings import settings


class ElasticsearchClient:
    """Elasticsearch client for meeting data search"""
    
    def __init__(self):
        self.es = Elasticsearch([settings.elasticsearch_url])
        self.index_name = "meetings"
        self.utterance_index = "utterances"
        
    def create_indices(self):
        """Create Elasticsearch indices with proper mappings"""
        
        # Meeting index mapping
        meeting_mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "integer"},
                    "title": {
                        "type": "text",
                        "analyzer": "standard",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "date": {"type": "date"},
                    "duration": {"type": "float"},
                    "participants": {"type": "keyword"},
                    "summary": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "created_at": {"type": "date"}
                }
            },
            "settings": {
                "analysis": {
                    "analyzer": {
                        "korean_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "stop"]
                        }
                    }
                }
            }
        }
        
        # Utterance index mapping
        utterance_mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "integer"},
                    "meeting_id": {"type": "integer"},
                    "speaker": {
                        "type": "text",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "timestamp": {"type": "float"},
                    "end_timestamp": {"type": "float"},
                    "text": {
                        "type": "text",
                        "analyzer": "standard",
                        "fields": {
                            "keyword": {"type": "keyword"},
                            "ngram": {
                                "type": "text",
                                "analyzer": "ngram_analyzer"
                            }
                        }
                    },
                    "confidence": {"type": "float"},
                    "language": {"type": "keyword"},
                    "meeting_title": {"type": "text"},
                    "meeting_date": {"type": "date"}
                }
            },
            "settings": {
                "analysis": {
                    "analyzer": {
                        "ngram_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "ngram_filter"]
                        }
                    },
                    "filter": {
                        "ngram_filter": {
                            "type": "ngram",
                            "min_gram": 2,
                            "max_gram": 3
                        }
                    }
                }
            }
        }
        
        # Create indices
        if not self.es.indices.exists(index=self.index_name):
            self.es.indices.create(index=self.index_name, body=meeting_mapping)
            print(f"✅ Created index: {self.index_name}")
            
        if not self.es.indices.exists(index=self.utterance_index):
            self.es.indices.create(index=self.utterance_index, body=utterance_mapping)
            print(f"✅ Created index: {self.utterance_index}")
    
    def index_meeting(self, meeting_data: Dict[str, Any]):
        """Index a meeting document"""
        doc = {
            "id": meeting_data["id"],
            "title": meeting_data["title"],
            "date": meeting_data["date"],
            "duration": meeting_data.get("duration", 0),
            "participants": meeting_data.get("participants", []),
            "summary": meeting_data.get("summary", ""),
            "created_at": meeting_data.get("created_at", datetime.now())
        }
        
        self.es.index(index=self.index_name, id=meeting_data["id"], body=doc)
    
    def index_utterances(self, utterances: List[Dict[str, Any]], meeting_data: Dict[str, Any]):
        """Index utterances for a meeting"""
        actions = []
        
        for utterance in utterances:
            doc = {
                "id": utterance["id"],
                "meeting_id": utterance["meeting_id"],
                "speaker": utterance["speaker"],
                "timestamp": utterance["timestamp"],
                "end_timestamp": utterance.get("end_timestamp"),
                "text": utterance["text"],
                "confidence": utterance.get("confidence", 0),
                "language": utterance.get("language", "ko"),
                "meeting_title": meeting_data["title"],
                "meeting_date": meeting_data["date"]
            }
            
            actions.append({
                "_index": self.utterance_index,
                "_id": utterance["id"],
                "_source": doc
            })
        
        if actions:
            bulk(self.es, actions)
    
    def search_meetings(self, query: str, filters: Optional[Dict] = None, size: int = 10) -> Dict[str, Any]:
        """Search meetings using Elasticsearch"""
        
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["title^2", "summary", "participants"],
                                "type": "best_fields",
                                "fuzziness": "AUTO"
                            }
                        }
                    ]
                }
            },
            "highlight": {
                "fields": {
                    "title": {},
                    "summary": {}
                }
            },
            "size": size
        }
        
        # Add filters
        if filters:
            filter_conditions = []
            
            if filters.get("date_range"):
                date_range = filters["date_range"]
                filter_conditions.append({
                    "range": {
                        "date": {
                            "gte": date_range["start"],
                            "lte": date_range["end"]
                        }
                    }
                })
            
            if filters.get("participants"):
                filter_conditions.append({
                    "terms": {
                        "participants": filters["participants"]
                    }
                })
            
            if filter_conditions:
                search_body["query"]["bool"]["filter"] = filter_conditions
        
        response = self.es.search(index=self.index_name, body=search_body)
        
        return {
            "total": response["hits"]["total"]["value"],
            "results": [hit["_source"] for hit in response["hits"]["hits"]],
            "highlights": [hit.get("highlight", {}) for hit in response["hits"]["hits"]]
        }
    
    def search_utterances(self, query: str, filters: Optional[Dict] = None, size: int = 20) -> Dict[str, Any]:
        """Search utterances using Elasticsearch"""
        
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["text^2", "speaker", "meeting_title"],
                                "type": "best_fields",
                                "fuzziness": "AUTO"
                            }
                        }
                    ]
                }
            },
            "highlight": {
                "fields": {
                    "text": {
                        "fragment_size": 150,
                        "number_of_fragments": 3
                    }
                }
            },
            "sort": [
                {"timestamp": {"order": "asc"}}
            ],
            "size": size
        }
        
        # Add filters
        if filters:
            filter_conditions = []
            
            if filters.get("meeting_id"):
                filter_conditions.append({
                    "term": {
                        "meeting_id": filters["meeting_id"]
                    }
                })
            
            if filters.get("speaker"):
                filter_conditions.append({
                    "term": {
                        "speaker.keyword": filters["speaker"]
                    }
                })
            
            if filters.get("time_range"):
                time_range = filters["time_range"]
                filter_conditions.append({
                    "range": {
                        "timestamp": {
                            "gte": time_range["start"],
                            "lte": time_range["end"]
                        }
                    }
                })
            
            if filter_conditions:
                search_body["query"]["bool"]["filter"] = filter_conditions
        
        response = self.es.search(index=self.utterance_index, body=search_body)
        
        return {
            "total": response["hits"]["total"]["value"],
            "results": [hit["_source"] for hit in response["hits"]["hits"]],
            "highlights": [hit.get("highlight", {}) for hit in response["hits"]["hits"]]
        }
    
    def semantic_search(self, query: str, size: int = 10) -> Dict[str, Any]:
        """Semantic search using dense vectors (requires model integration)"""
        # TODO: Implement with sentence-transformers or similar
        # This would require embedding the query and comparing with document embeddings
        pass
    
    def get_suggestions(self, query: str, field: str = "text") -> List[str]:
        """Get search suggestions"""
        search_body = {
            "suggest": {
                "text_suggestions": {
                    "prefix": query,
                    "completion": {
                        "field": f"{field}_suggest",
                        "size": 5
                    }
                }
            }
        }
        
        response = self.es.search(index=self.utterance_index, body=search_body)
        suggestions = []
        
        for suggestion in response["suggest"]["text_suggestions"][0]["options"]:
            suggestions.append(suggestion["text"])
        
        return suggestions


# Global client instance
es_client = None

def get_elasticsearch_client() -> ElasticsearchClient:
    """Get or create Elasticsearch client instance"""
    global es_client
    if es_client is None:
        es_client = ElasticsearchClient()
        es_client.create_indices()
    return es_client 