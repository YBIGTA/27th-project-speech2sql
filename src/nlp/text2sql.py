import re
from typing import Dict, List, Optional, Tuple, Any
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    AutoModelForCausalLM,
    AutoConfig,
    GenerationConfig,
)
import torch
from config.settings import settings


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
            cfg = AutoConfig.from_pretrained(self.model_name)
            self.is_encoder_decoder = bool(getattr(cfg, "is_encoder_decoder", False))

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
            print(f"⚠️ Failed to load Text2SQL model: {e}")
            print("Using fallback SQL generation method")

    def set_schema_info(self, schema_info: Dict[str, Any]):
        self.schema_info = schema_info

    def convert_to_sql(self, natural_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        try:
            if self.model and self.tokenizer:
                return self._convert_with_model(natural_query, context)
            else:
                return self._convert_with_rules(natural_query, context)
        except Exception as e:
            print(f"Error converting to SQL: {e}")
            return self._convert_with_rules(natural_query, context)

    # -------------------- MODEL PATH --------------------
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

    def _build_seq2seq_input(self, schema_context: str, natural_query: str) -> str:
        # 간단한 포맷 (T5류)
        rules = self._dialect_rules_for_prompt()
        return f"Schema: {schema_context}\nRules: {rules}\nQuery: {natural_query}\nSQL:"

    def _build_chat_prompts(
        self,
        schema_context: str,
        natural_query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, str]:

        def _fmt_date(v):
            if v is None:
                return None
            # datetime/date 지원 + 문자열 그대로
            try:
                return v.isoformat() if hasattr(v, "isoformat") else str(v)
            except Exception:
                return str(v)

        hints = []
        if context:
            tables = context.get("tables_hint") or []
            cols   = context.get("columns_hint") or []
            if tables:
                hints.append(f"Tables-hint: {', '.join(tables)}")
            if cols:
                hints.append(f"Columns-hint: {', '.join(cols)}")

            # ✅ date_range 안전 처리 (dict/tuple/list 모두 케어)
            dr = context.get("date_range")
            if isinstance(dr, dict):
                s, e = _fmt_date(dr.get("start")), _fmt_date(dr.get("end"))
                if s and e:
                    hints.append(f"Date-range: {s} ~ {e}")
            elif isinstance(dr, (tuple, list)) and len(dr) == 2:
                s, e = _fmt_date(dr[0]), _fmt_date(dr[1])
                if s and e:
                    hints.append(f"Date-range: {s} ~ {e}")

            kws = context.get("keywords") or []
            if kws:
                hints.append(f"Keywords: {', '.join(map(str, kws))}")

            # 선택 힌트(있으면 도움)
            if context.get("meeting_id"):
                hints.append(f"Filter: meeting_id = {context['meeting_id']}")
            if context.get("speaker"):
                hints.append(f"Filter: speaker ILIKE '%{context['speaker']}%'")
            if context.get("limit_hint"):
                try:
                    hints.append(f"Limit-hint: {int(context['limit_hint'])}")
                except Exception:
                    pass

        hints_txt = ("\n".join(hints)).strip()

        sys_prompt = (
            "You are a Text-to-SQL generator.\n"
            f"Dialect: {self.dialect} (PostgreSQL 16).\n"
            "Rules:\n"
            "- Return ONLY one SQL SELECT statement; end with a single semicolon.\n"
            "- Use ONLY provided schema objects.\n"
            "- Case-insensitive search: use ILIKE.\n"
            "- Time bucketing: use DATE_TRUNC; durations: use INTERVAL syntax.\n"
            "- Prefer WHERE filters when hints are provided.\n"
            "- Do not write/alter/drop anything.\n"
            '- Quote identifiers with \"...\" if uppercase/special chars exist.\n'
        )

        user_prompt = f"Schema:\n{schema_context}\n\nQuestion:\n{natural_query.strip()}\n"
        if hints_txt:
            user_prompt += f"\nHints:\n{hints_txt}\n"
        user_prompt += "\nAnswer with only the SQL:"
        return sys_prompt, user_prompt


    def _postprocess_sql(self, text: str) -> str:
        # 마지막 SELECT ~ ; 만 추출
        m = re.findall(r"(SELECT\b.*?;)", text, flags=re.IGNORECASE | re.DOTALL)
        if not m:
            return text.strip() if text.strip().upper().startswith("SELECT") else ""
        # 가장 마지막 후보를 채택
        sql = m[-1].strip()
        # 여러 문장 방지: 첫 세미콜론까지만
        return sql[: sql.find(";") + 1]

    def _dialect_rules_for_prompt(self) -> str:
        return (
            "Output one PostgreSQL SELECT; finish with ';'. "
            "Use ILIKE for case-insensitive search; DATE_TRUNC/INTERVAL for time; "
            'quote identifiers with \"...\" when needed.'
        )

    # -------------------- RULES PATH --------------------
    def _convert_with_rules(self, natural_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        query_lower = natural_query.lower()
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
        kw = self._extract_keywords(query)
        if kw:
            needle = self._escape_like(kw[0])
            return f"""
            SELECT u.speaker, u.text, u.timestamp, m.title AS meeting_title
            FROM utterances u
            JOIN meetings m ON u.meeting_id = m.id
            WHERE u.text ILIKE '%{needle}%' ESCAPE '\\'
            ORDER BY u.timestamp;
            """.strip()
        return """
        SELECT u.speaker, u.text, u.timestamp, m.title AS meeting_title
        FROM utterances u
        JOIN meetings m ON u.meeting_id = m.id
        ORDER BY u.timestamp DESC
        LIMIT 10;
        """.strip()

    def _generate_action_query(self, query: str, context: Dict[str, Any] = None) -> str:
        return """
        SELECT a.description, a.assignee, a.due_date, m.title AS meeting_title
        FROM actions a
        JOIN meetings m ON a.meeting_id = m.id
        ORDER BY a.due_date;
        """.strip()

    def _generate_general_query(self, query: str, context: Dict[str, Any] = None) -> str:
        kw = self._extract_keywords(query)
        if kw:
            needle = self._escape_like(kw[0])
            return f"""
            SELECT u.speaker, u.text, u.timestamp, m.title AS meeting_title
            FROM utterances u
            JOIN meetings m ON u.meeting_id = m.id
            WHERE u.text ILIKE '%{needle}%' ESCAPE '\\'
            ORDER BY u.timestamp
            LIMIT 10;
            """.strip()
        return """
        SELECT u.speaker, u.text, u.timestamp, m.title AS meeting_title
        FROM utterances u
        JOIN meetings m ON u.meeting_id = m.id
        ORDER BY u.timestamp DESC
        LIMIT 10;
        """.strip()

    def _extract_keywords(self, query: str) -> List[str]:
        """
        Prefer the query_processor's keyword extraction to avoid duplication.
        Fallback to a light local extractor if unavailable.
        """
        try:
            from .query_processor import refine_query_with_meta  # 경로는 프로젝트 구조에 맞게
            meta = refine_query_with_meta(query)
            kws = meta.get("keywords", []) or []
            return kws[:3]
        except Exception:
            # 간단한 로컬 백업
            words = re.findall(r"\w+", query, flags=re.UNICODE)
            stop_words = {"누가","언제","무엇","어떻게","왜","언급","말했다","에","에서","을","를","이","가","의","와","과","그리고","또는","하지만","그런데"}
            return [w for w in words if w not in stop_words and len(w) > 1][:3]

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
