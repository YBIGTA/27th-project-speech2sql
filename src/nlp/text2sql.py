"""
Text2SQL (Natural Language to SQL) conversion module
"""
import re
from typing import Dict, List, Optional, Tuple, Any
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from config.settings import settings


class Text2SQLConverter:
    """Natural language to SQL query converter"""
    
    def __init__(self, model_name: str = None):
        """
        Initialize Text2SQL converter
        
        Args:
            model_name: Huggingface model name for Text2SQL
        """
        self.model_name = model_name or settings.text2sql_model
        self.tokenizer = None
        self.model = None
        self.schema_info = None
        
        # Initialize model (lazy loading)
        self._load_model()
    
    def _load_model(self):
        """Load Text2SQL model"""
        try:
            # Load pre-trained Text2SQL model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            print(f"✅ Text2SQL model loaded: {self.model_name}")
        except Exception as e:
            print(f"⚠️ Failed to load Text2SQL model: {e}")
            print("Using fallback SQL generation method")
    
    def set_schema_info(self, schema_info: Dict[str, Any]):
        """
        Set database schema information
        
        Args:
            schema_info: Database schema information including tables and columns
        """
        self.schema_info = schema_info
    
    def convert_to_sql(self, natural_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Convert natural language query to SQL
        
        Args:
            natural_query: Natural language query
            context: Additional context (meeting_id, speaker, etc.)
        
        Returns:
            Dictionary containing SQL query and metadata
        """
        try:
            if self.model and self.tokenizer:
                return self._convert_with_model(natural_query, context)
            else:
                return self._convert_with_rules(natural_query, context)
        except Exception as e:
            print(f"Error converting to SQL: {e}")
            return self._convert_with_rules(natural_query, context)
    
    def _convert_with_model(self, natural_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Convert using pre-trained Text2SQL model"""
        # Prepare input with schema context
        schema_context = self._prepare_schema_context()
        input_text = f"Schema: {schema_context}\nQuery: {natural_query}"
        
        # Tokenize and generate
        inputs = self.tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)
        
        with torch.no_grad():
            outputs = self.model.generate(
                inputs.input_ids,
                max_length=128,
                num_beams=4,
                early_stopping=True
            )
        
        sql_query = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return {
            "sql_query": sql_query,
            "natural_query": natural_query,
            "method": "model",
            "confidence": 0.8,
            "context": context
        }
    
    def _convert_with_rules(self, natural_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Convert using rule-based approach"""
        query_lower = natural_query.lower()
        
        # Basic pattern matching for common queries
        if "누가" in natural_query and "언급" in natural_query:
            sql = self._generate_speaker_query(natural_query, context)
        elif "언제" in natural_query or "시간" in natural_query:
            sql = self._generate_time_query(natural_query, context)
        elif "무엇" in natural_query or "내용" in natural_query:
            sql = self._generate_content_query(natural_query, context)
        elif "결정" in natural_query or "액션" in natural_query:
            sql = self._generate_action_query(natural_query, context)
        else:
            sql = self._generate_general_query(natural_query, context)
        
        return {
            "sql_query": sql,
            "natural_query": natural_query,
            "method": "rules",
            "confidence": 0.6,
            "context": context
        }
    
    def _prepare_schema_context(self) -> str:
        """Prepare database schema context for model input"""
        if not self.schema_info:
            return "meetings(id, title, date, duration, participants, summary), utterances(id, meeting_id, speaker, timestamp, text), actions(id, meeting_id, description, assignee, due_date)"
        
        schema_parts = []
        for table, columns in self.schema_info.items():
            schema_parts.append(f"{table}({', '.join(columns)})")
        
        return ", ".join(schema_parts)
    
    def _generate_speaker_query(self, query: str, context: Dict[str, Any] = None) -> str:
        """Generate SQL for speaker-related queries"""
        base_sql = """
        SELECT DISTINCT u.speaker, u.text, u.timestamp, m.title as meeting_title
        FROM utterances u
        JOIN meetings m ON u.meeting_id = m.id
        WHERE u.text LIKE '%{}%'
        ORDER BY u.timestamp
        """
        
        # Extract keywords from query
        keywords = self._extract_keywords(query)
        if keywords:
            return base_sql.format(keywords[0])
        else:
            return base_sql.format("")
    
    def _generate_time_query(self, query: str, context: Dict[str, Any] = None) -> str:
        """Generate SQL for time-related queries"""
        return """
        SELECT u.speaker, u.text, u.timestamp, m.title as meeting_title
        FROM utterances u
        JOIN meetings m ON u.meeting_id = m.id
        ORDER BY u.timestamp
        LIMIT 10
        """
    
    def _generate_content_query(self, query: str, context: Dict[str, Any] = None) -> str:
        """Generate SQL for content-related queries"""
        keywords = self._extract_keywords(query)
        if keywords:
            return f"""
            SELECT u.speaker, u.text, u.timestamp, m.title as meeting_title
            FROM utterances u
            JOIN meetings m ON u.meeting_id = m.id
            WHERE u.text LIKE '%{keywords[0]}%'
            ORDER BY u.timestamp
            """
        else:
            return """
            SELECT u.speaker, u.text, u.timestamp, m.title as meeting_title
            FROM utterances u
            JOIN meetings m ON u.meeting_id = m.id
            ORDER BY u.timestamp DESC
            LIMIT 10
            """
    
    def _generate_action_query(self, query: str, context: Dict[str, Any] = None) -> str:
        """Generate SQL for action/decision-related queries"""
        return """
        SELECT a.description, a.assignee, a.due_date, m.title as meeting_title
        FROM actions a
        JOIN meetings m ON a.meeting_id = m.id
        ORDER BY a.due_date
        """
    
    def _generate_general_query(self, query: str, context: Dict[str, Any] = None) -> str:
        """Generate SQL for general queries"""
        keywords = self._extract_keywords(query)
        if keywords:
            return f"""
            SELECT u.speaker, u.text, u.timestamp, m.title as meeting_title
            FROM utterances u
            JOIN meetings m ON u.meeting_id = m.id
            WHERE u.text LIKE '%{keywords[0]}%'
            ORDER BY u.timestamp
            LIMIT 10
            """
        else:
            return """
            SELECT u.speaker, u.text, u.timestamp, m.title as meeting_title
            FROM utterances u
            JOIN meetings m ON u.meeting_id = m.id
            ORDER BY u.timestamp DESC
            LIMIT 10
            """
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from natural language query"""
        # Remove common words and extract meaningful keywords
        stop_words = ['누가', '언제', '무엇을', '무엇', '어떻게', '왜', '언급', '말했다', '말했다', '에', '에서', '을', '를', '이', '가', '의', '와', '과', '그리고', '또는', '하지만', '그런데']
        
        words = re.findall(r'\w+', query)
        keywords = [word for word in words if word not in stop_words and len(word) > 1]
        
        return keywords[:3]  # Return top 3 keywords
    
    def validate_sql(self, sql_query: str) -> bool:
        """
        Validate generated SQL query
        
        Args:
            sql_query: SQL query to validate
        
        Returns:
            True if valid, False otherwise
        """
        # Basic SQL validation
        required_keywords = ['SELECT', 'FROM']
        sql_upper = sql_query.upper()
        
        for keyword in required_keywords:
            if keyword not in sql_upper:
                return False
        
        # Check for SQL injection patterns
        dangerous_patterns = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'ALTER']
        for pattern in dangerous_patterns:
            if pattern in sql_upper:
                return False
        
        return True


# Global Text2SQL converter instance
text2sql_converter = Text2SQLConverter()


def convert_natural_to_sql(natural_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Convert natural language query to SQL
    
    Args:
        natural_query: Natural language query
        context: Additional context
    
    Returns:
        Dictionary with SQL query and metadata
    """
    return text2sql_converter.convert_to_sql(natural_query, context)


def set_database_schema(schema_info: Dict[str, Any]):
    """
    Set database schema for Text2SQL conversion
    
    Args:
        schema_info: Database schema information
    """
    text2sql_converter.set_schema_info(schema_info) 