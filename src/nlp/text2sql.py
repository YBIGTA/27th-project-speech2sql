import re
from typing import Dict, List, Optional, Tuple, Any
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import requests
import torch
from config.settings import settings
from konlpy.tag import Okt
from typing import List

okt = Okt()


class Text2SQLConverter:
    """Natural language to SQL query converter"""
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.text2sql_model
        self.tokenizer = None
        self.model = None
        self.schema_info = None
        self.is_encoder_decoder = False
        self.dialect = getattr(settings, "text2sql_dialect", "postgresql")  # 옵션 없으면 postgresql 가정
        self._load_model()

    def _load_model(self):
        """Load Text2SQL model (Seq2Seq or CausalLM)"""
        try:
            # Load pre-trained Text2SQL model (local/HF). Optional when using Upstage.
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

            # 안전한 dtype 결정 (CPU=fp32, CUDA 8.0+=bf16, 그 외 fp16)
            if torch.cuda.is_available():
                cc_major = torch.cuda.get_device_capability(0)[0]
                dtype = torch.bfloat16 if cc_major >= 8 else torch.float16
            else:
                dtype = torch.float32

            if self.is_encoder_decoder:
                # Seq2Seq (T5 등)
                self.model = AutoModelForSeq2SeqLM.from_pretrained(
                    self.model_name,
                    device_map="auto",
                    torch_dtype=dtype,
                )
            else:
                # Causal LM (e.g., Qwen/Llama/Mistral)
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=dtype,
                    device_map="auto",
                )

            # pad/eos 안전 설정
            if getattr(self.tokenizer, "pad_token_id", None) is None and getattr(self.tokenizer, "eos_token_id", None) is not None:
                self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

            print(f"✅ Text2SQL model loaded: {self.model_name} (encoder_decoder={self.is_encoder_decoder})")
        except Exception as e:
            print(f"⚠️ Failed to load local Text2SQL model: {e}")
            print("Will attempt Upstage API or fallback rules")
    
    def set_schema_info(self, schema_info: Dict[str, Any]):
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
        schema_context = self._prepare_schema_context()
        if self.is_encoder_decoder:
            # T5/Pegasus style (beam search, 샘플링 파라미터 사용 안 함)
            input_text = self._build_seq2seq_input(schema_context, natural_query)
            inputs = self.tokenizer(input_text, return_tensors="pt", max_length=1024, truncation=True)
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=220,
                    num_beams=4,
                    length_penalty=0.0,
                    early_stopping=True,
                    eos_token_id=self.tokenizer.eos_token_id,
                    pad_token_id=self.tokenizer.pad_token_id,
                )
            raw = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        else:
            # Chat-style causal LM (Qwen/Llama/Mistral)
            sys_prompt, user_prompt = self._build_chat_prompts(schema_context, natural_query, context)
            messages = [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt}
            ]
            prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = self.tokenizer(prompt, return_tensors="pt", max_length=2048, truncation=True)
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

            # ✅ CausalLM에서는 do_sample=True와 함께 샘플링 파라미터를 GenerationConfig로만 전달
            gen_cfg = GenerationConfig.from_model_config(self.model.config)
            gen_cfg.max_new_tokens = 220
            gen_cfg.do_sample = True
            gen_cfg.temperature = 0.2
            gen_cfg.top_p = 0.95
            gen_cfg.top_k = 50
            gen_cfg.num_beams = 1  # 샘플링과 beam을 섞지 않음

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    generation_config=gen_cfg,
                    eos_token_id=self.tokenizer.eos_token_id,
                    pad_token_id=self.tokenizer.pad_token_id,
                )
            raw = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        sql_query = self._postprocess_sql(raw)

        return {
            "sql_query": sql_query,
            "natural_query": natural_query,
            "method": "model",
            "confidence": 0.8 if sql_query else 0.3,
            "context": context
        }
    
    def _classify_intent(self, query: str) -> str:
        """Classify the user's intent based on a scoring system."""
        query_lower = query.lower()
        scores = {
            'speaker': 0,
            'time': 0,
            'action': 0,
            'general': 1 # 기본값 설정
        }
    
        # 의도 키워드 점수 부여
        if '누가' in query_lower or '발화자' in query_lower:
            scores['speaker'] += 5
        if '언제' in query_lower or '날짜' in query_lower or '시간' in query_lower:
            scores['time'] += 5
        if '결정' in query_lower or '액션' in query_lower or '무엇을' in query_lower:
            scores['action'] += 5
    
        # 최종 의도 결정
        return max(scores, key=scores.get)
    
    def _convert_with_rules(self, natural_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Convert using rule-based approach"""
    
        # 1. 의도 분류 함수 호출 (여기서 한 번만 실행)
        intent = self._classify_intent(natural_query)

        # 2. 분류된 의도에 따라 SQL 생성 함수 호출
        if intent == 'speaker':
            sql = self._generate_speaker_query(natural_query, context)
        elif intent == 'time':
            sql = self._generate_time_query(natural_query, context)
        elif intent == 'action':
            sql = self._generate_action_query(natural_query, context)
        else: # 'general'을 포함한 모든 경우
            sql = self._generate_general_query(natural_query, context)
    
        # 3. 결과 반환
        return {
            "sql_query": sql,
            "natural_query": natural_query,
            "method": "rules",
            "confidence": 0.6,
            "context": context
        }

    def _prepare_schema_context(self) -> str:
        if not self.schema_info:
            return (
                "meetings(id, title, date, duration, participants, summary, audio_path), "
                "utterances(id, meeting_id, speaker, timestamp, text, confidence), "
                "actions(id, meeting_id, action_type, description, assignee, due_date)"
            )
        schema_parts = []
        for table, columns in self.schema_info.items():
            schema_parts.append(f"{table}({', '.join(columns)})")
        return ", ".join(schema_parts)

    # ---------- Rule-based SQL helpers (use ILIKE + escape) ----------
    def _escape_like(self, s: str) -> str:
        # %, _, ' 를 단순 이스케이프
        return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_").replace("'", "''")

    def _generate_speaker_query(self, query: str, context: Dict[str, Any] = None) -> str:
        kw = self._extract_keywords(query)
        needle = self._escape_like(kw[0]) if kw else ""
        return f"""
        SELECT DISTINCT u.speaker, u.text, u.timestamp, m.title AS meeting_title
        FROM utterances u
        JOIN meetings m ON u.meeting_id = m.id
        WHERE u.text ILIKE '%{needle}%' ESCAPE '\\'
        ORDER BY u.timestamp;
        """.strip()

    def _generate_time_query(self, query: str, context: Dict[str, Any] = None) -> str:
        return """
        SELECT u.speaker, u.text, u.timestamp, m.title AS meeting_title
        FROM utterances u
        JOIN meetings m ON u.meeting_id = m.id
        ORDER BY u.timestamp
        LIMIT 10;
        """.strip()

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
        return """
        SELECT a.description, a.assignee, a.due_date, m.title AS meeting_title
        FROM actions a
        JOIN meetings m ON a.meeting_id = m.id
        ORDER BY a.due_date;
        """.strip()

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
        """
        Extracts keywords from a natural language query using Konlpy's Okt
        to identify nouns and then filters them.
        """
        # 1. Okt를 사용해 쿼리에서 명사(nouns)만 추출
        nouns = okt.nouns(query)

        # 2. 불용어(Stopwords) 정의 및 필터링
        # 기존 불용어 리스트에 명사형 불용어를 추가하는 것이 좋습니다.
        stop_words = {
            '누가', '언제', '무엇', '어떻게', '왜', '언급', '말했다',
            '이', '그', '저', '것', '때', '곳', '분', '회의', '미팅'
        }

        filtered_nouns = [
            noun for noun in nouns
            if len(noun) > 1 and noun not in stop_words
        ]

        return filtered_nouns

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
        if not sql_query:
            return False
        upper = sql_query.upper()
        if "SELECT" not in upper or "FROM" not in upper:
            return False
        # 금지 동사
        for pattern in [' DROP ', ' DELETE ', ' UPDATE ', ' INSERT ', ' CREATE ', ' ALTER ']:
            if pattern in f" {upper} ":
                return False
        # 세미콜론 하나만 허용(마지막 종료용)
        if upper.count(";") > 1:
            return False
        return True


# Global instance & helpers stay the same
text2sql_converter = Text2SQLConverter()

def convert_natural_to_sql(natural_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    return text2sql_converter.convert_to_sql(natural_query, context)

def set_database_schema(schema_info: Dict[str, Any]):
    text2sql_converter.set_schema_info(schema_info)
