"""
Text2SQL (Natural Language to SQL) conversion module
"""
import re
from typing import Dict, List, Optional, Tuple, Any
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import requests
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
            # Load pre-trained Text2SQL model (local/HF). Optional when using Upstage.
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            print(f"✅ Text2SQL model loaded: {self.model_name}")
        except Exception as e:
            print(f"⚠️ Failed to load local Text2SQL model: {e}")
            print("Will attempt Upstage API or fallback rules")
    
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
        # Prefer Upstage API when key is configured
        if settings.upstage_api_key:
            try:
                return self._convert_with_upstage(natural_query, context)
            except Exception as e:
                print(f"Upstage conversion failed: {e}")
        try:
            if self.model and self.tokenizer:
                return self._convert_with_model(natural_query, context)
        except Exception as e:
            print(f"Local model conversion failed: {e}")
        return self._convert_with_rules(natural_query, context)

    def _convert_with_upstage(self, natural_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Use Upstage API to generate SQL with schema-aware prompting and light few-shot examples."""
        schema_context = self._prepare_schema_context()
        ctx = context or {}
        limit = int(ctx.get("limit") or 10)
        meeting_id = ctx.get("meeting_id")

        rules = [
            "Only output a single SQL SELECT statement.",
            "Never include DDL/DML (no INSERT/UPDATE/DELETE/CREATE).",
            "Use table aliases: u for utterances, m for meetings, a for actions.",
            "Prefer ILIKE for text conditions.",
            "Join u and m on u.meeting_id = m.id when utterances are referenced.",
            f"Always include LIMIT {limit} at the end.",
            "Do NOT select m.date unless the user explicitly asks about the meeting date/start/end of the meeting.",
            "For questions about introduction/release/presentation (introduce/introduced/release/launched/launch/unveil/present), query utterances (u.*) and filter u.text with those verbs; do not select m.date.",
        ]
        if meeting_id:
            rules.append("Scope results to the specified meeting: add WHERE m.id = :meeting_id (or AND ... if WHERE already exists).")

        guidance = (
            "You convert questions to SQL for PostgreSQL using the given schema.\n"
            f"Schema:\n{schema_context}\n"
            "Rules:\n- " + "\n- ".join(rules) + "\n"
        )

        few_shot = [
            {
                "role": "user",
                "content": "When did the meeting start? (meeting scoped)"
            },
            {
                "role": "assistant",
                "content": """```sql
SELECT m.title AS meeting_title, m.date AS meeting_date
FROM meetings m
WHERE m.id = :meeting_id
LIMIT 10
```""",
            },
            {
                "role": "user",
                "content": "Show utterances about project A"
            },
            {
                "role": "assistant",
                "content": f"""```sql
SELECT u.speaker, u.text, u.timestamp, m.title AS meeting_title
FROM utterances u JOIN meetings m ON u.meeting_id = m.id
WHERE u.text ILIKE '%project A%'{" AND m.id = :meeting_id" if meeting_id else ""}
ORDER BY u.timestamp
LIMIT {limit}
```""",
            },
            {
                "role": "user",
                "content": "When was iPod introduced?"
            },
            {
                "role": "assistant",
                "content": f"""```sql
SELECT u.speaker, u.text, u.timestamp, m.title AS meeting_title
FROM utterances u JOIN meetings m ON u.meeting_id = m.id
WHERE u.text ILIKE '%iPod%' AND (u.text ILIKE '%introduc%' OR u.text ILIKE '%release%' OR u.text ILIKE '%launch%' OR u.text ILIKE '%unveil%' OR u.text ILIKE '%present%')
ORDER BY u.timestamp
LIMIT {limit}
```""",
            },
        ]

        prompt_user = (
            "Question: " + natural_query + "\n"
            "Return only SQL."
        )
        payload = {
            "model": "solar-pro",  # example model; adjust as needed
            "messages": [
                {"role": "system", "content": guidance},
                *few_shot,
                {"role": "user", "content": prompt_user},
            ],
            "temperature": 0.1,
            "max_tokens": 512,
        }
        headers = {
            "Authorization": f"Bearer {settings.upstage_api_key}",
            "Content-Type": "application/json",
        }
        url = f"{settings.upstage_base_url}/chat/completions"
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"Upstage API error: {resp.status_code} {resp.text}")
        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()
        sql_query = self._extract_sql_from_text(content)
        if not sql_query:
            raise RuntimeError("No SQL produced by Upstage")
        return {
            "sql_query": sql_query,
            "natural_query": natural_query,
            "method": "upstage",
            "confidence": 0.9,
            "context": context,
        }

    def _extract_sql_from_text(self, text: str) -> Optional[str]:
        # Try to extract SQL code block or first SELECT statement
        code_block = re.search(r"```sql\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
        if code_block:
            return code_block.group(1).strip()
        m = re.search(r"SELECT[\s\S]+", text, flags=re.IGNORECASE)
        return m.group(0).strip() if m else None
    
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
        """Generate SQL for content-related queries with basic entity/year handling"""
        year = self._extract_year(query)
        action_keywords = self._extract_action_keywords(query)
        keywords = self._extract_keywords(query)
        conditions: List[str] = []
        for kw in keywords:
            conditions.append(f"u.text ILIKE '%{kw}%'")
        for ak in action_keywords:
            conditions.append(f"u.text ILIKE '%{ak}%'")
        entity_tokens = self._extract_entities(query)
        for ent in entity_tokens:
            conditions.append(f"(u.text ILIKE '%{ent}%' OR m.title ILIKE '%{ent}%')")
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        date_clause = ""
        if year:
            date_clause = f" AND m.date >= '{year}-01-01' AND m.date < '{year + 1}-01-01'"
        return (
            "SELECT u.speaker, u.text, u.timestamp, m.title as meeting_title "
            "FROM utterances u JOIN meetings m ON u.meeting_id = m.id "
            f"WHERE {where_clause}{date_clause} "
            "ORDER BY u.timestamp LIMIT 10"
        )
    
    def _generate_action_query(self, query: str, context: Dict[str, Any] = None) -> str:
        """Generate SQL for action/decision-related queries"""
        return """
        SELECT a.description, a.assignee, a.due_date, m.title as meeting_title
        FROM actions a
        JOIN meetings m ON a.meeting_id = m.id
        ORDER BY a.due_date
        """
    
    def _generate_general_query(self, query: str, context: Dict[str, Any] = None) -> str:
        """Generate SQL for general queries with simple multi-keyword/entity/year support"""
        year = self._extract_year(query)
        action_keywords = self._extract_action_keywords(query)
        keywords = self._extract_keywords(query)
        conditions: List[str] = []
        for kw in keywords:
            conditions.append(f"u.text ILIKE '%{kw}%'")
        for ak in action_keywords:
            conditions.append(f"u.text ILIKE '%{ak}%'")
        entity_tokens = self._extract_entities(query)
        for ent in entity_tokens:
            conditions.append(f"(u.text ILIKE '%{ent}%' OR m.title ILIKE '%{ent}%')")
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        date_clause = ""
        if year:
            date_clause = f" AND m.date >= '{year}-01-01' AND m.date < '{year + 1}-01-01'"
        return (
            "SELECT u.speaker, u.text, u.timestamp, m.title as meeting_title "
            "FROM utterances u JOIN meetings m ON u.meeting_id = m.id "
            f"WHERE {where_clause}{date_clause} "
            "ORDER BY u.timestamp LIMIT 10"
        )
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from natural language query (KR/EN stopwords, keep numbers)"""
        stop_words_kr = ['누가', '언제', '무엇을', '무엇', '어떻게', '왜', '언급', '말했다', '에', '에서', '을', '를', '이', '가', '의', '와', '과', '그리고', '또는', '하지만', '그런데']
        stop_words_en = [
            'a','an','the','in','on','at','to','of','for','from','by','with','about','as','into','like','through','after','over','between','out','against','during','without','before','under','around','among',
            'what','who','when','where','why','how','which','whom','whose',
            'is','am','are','was','were','be','been','being','do','does','did','done','having','have','has',
            'and','or','but','if','because','while','so','than','too','very','can','could','should','would','will','shall'
        ]
        words = re.findall(r"[A-Za-z0-9']+", query)
        filtered: List[str] = []
        for w in words:
            wl = w.lower()
            if len(wl) <= 1:
                continue
            if wl in stop_words_en:
                continue
            if w in stop_words_kr:
                continue
            filtered.append(wl)
        return filtered[:5]

    def _extract_year(self, query: str) -> Optional[int]:
        m = re.search(r"\b(19|20)\d{2}\b", query)
        if not m:
            return None
        try:
            return int(m.group(0))
        except Exception:
            return None

    def _extract_action_keywords(self, query: str) -> List[str]:
        ql = query.lower()
        hits: List[str] = []
        for stem in ['introduc', 'announce', 'release', 'launch', 'unveil', 'present']:
            if stem in ql:
                hits.append(stem)
        return hits

    def _extract_entities(self, query: str) -> List[str]:
        tokens = re.findall(r"[A-Za-z]+", query)
        entities: List[str] = []
        for t in tokens:
            tl = t.lower()
            if tl in {'apple','google','microsoft','samsung','amazon','meta','facebook','tesla'}:
                entities.append(tl)
        return entities
    
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