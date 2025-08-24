"""
Agenda Analysis Agent - Analyzes specific agenda items and their discussion patterns
"""
from typing import Dict, Any, List, Tuple
import re
from collections import defaultdict, Counter
from src.agents.base_agent import BaseAgent, AgentType
from config.settings import settings
import requests


class AgendaAnalysisAgent(BaseAgent):
    """Agent for analyzing specific agenda items and their discussion patterns"""
    
    def __init__(self):
        super().__init__(AgentType.AGENDA_ANALYSIS, "AgendaAnalysisAgent")
        
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input data contains required fields"""
        required_fields = ["meeting_id", "utterances"]
        return all(field in data for field in required_fields)
    
    def preprocess(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess utterances and identify agenda items"""
        utterances = data.get("utterances", [])
        
        # Identify agenda items from utterances
        agenda_items = self._identify_agenda_items(utterances)
        
        # Group utterances by agenda item
        agenda_data = defaultdict(list)
        for utterance in utterances:
            agenda_id = self._classify_utterance_to_agenda(utterance, agenda_items)
            if agenda_id:
                agenda_data[agenda_id].append(utterance)
        
        return {
            "meeting_id": data["meeting_id"],
            "agenda_items": agenda_items,
            "agenda_data": dict(agenda_data),
            "utterances": utterances
        }
    
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze agenda items and their discussion patterns"""
        agenda_items = data["agenda_items"]
        agenda_data = data["agenda_data"]
        
        analysis_results = {}
        
        for agenda_id, agenda_info in agenda_items.items():
            utterances = agenda_data.get(agenda_id, [])
            
            # Analyze discussion patterns
            discussion_patterns = self._analyze_discussion_patterns(utterances)
            
            # Analyze opinions and positions
            opinions = self._analyze_opinions_and_positions(utterances)
            
            # Extract and analyze decisions
            decisions = self._extract_decisions(utterances)
            
            # Analyze consensus level
            consensus = self._analyze_consensus(utterances, opinions)
            
            # Sort decisions by consensus level
            sorted_decisions = self._sort_decisions_by_consensus(decisions, consensus)
            
            # Generate agenda summary
            summary = self._generate_agenda_summary(agenda_info.get("title", ""), consensus, sorted_decisions)
            
            analysis_results[agenda_id] = {
                "agenda_info": agenda_info,
                "consensus": consensus,
                "decisions": sorted_decisions,
                "summary": summary
            }
        
        return {
            "agendas": analysis_results,
            "meeting_overview": self._generate_meeting_overview(agenda_items, analysis_results),
            "confidence": 0.80
        }
    
    def _extract_decisions(self, utterances: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract and analyze decisions from utterances"""
        decisions = []
        decision_keywords = ["결정", "확정", "의결", "합의", "동의", "승인", "결론"]
        
        for utterance in utterances:
            text = utterance.get("text", "").lower()
            
            if any(keyword in text for keyword in decision_keywords):
                # Extract the actual decision content
                decision_content = self._extract_decision_content(utterance.get("text", ""))
                if decision_content:
                    # Check if this decision is already captured (avoid duplicates)
                    if not self._is_duplicate_decision(decision_content, decisions):
                        decisions.append({
                            "content": decision_content,
                            "speaker": utterance.get("speaker"),
                            "timestamp": utterance.get("timestamp"),
                            "confidence": 0.9
                        })
        
        return decisions
    
    def _is_duplicate_decision(self, new_content: str, existing_decisions: List[Dict[str, Any]]) -> bool:
        """Check if a decision is duplicate of existing ones"""
        new_content_clean = self._clean_decision_text(new_content)
        
        for decision in existing_decisions:
            existing_content_clean = self._clean_decision_text(decision.get("content", ""))
            
            # If content is very similar (80% similarity), consider it duplicate
            if self._calculate_similarity(new_content_clean, existing_content_clean) > 0.8:
                return True
        
        return False
    
    def _clean_decision_text(self, text: str) -> str:
        """Clean decision text for comparison"""
        # Remove common prefixes and suffixes
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
        text = re.sub(r'\s+', ' ', text).strip()  # Normalize whitespace
        return text
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        if not text1 or not text2:
            return 0.0
        
        # Simple word-based similarity
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _extract_decision_content(self, text: str) -> str:
        """Extract the actual decision content from text using LLM"""
        text = text.strip()
        
        # First, try to identify if this is actually a decision
        decision_indicators = [
            "결정", "확정", "의결", "합의", "동의", "승인", "결론", "통합", "개편", "설립", "추진"
        ]
        
        has_decision_indicator = any(indicator in text for indicator in decision_indicators)
        
        if not has_decision_indicator:
            return ""
        
        # Use LLM to extract decision content
        return self._extract_decision_with_llm(text)
    
    def _extract_decision_with_llm(self, text: str) -> str:
        """Extract decision content using LLM API"""
        try:
            # Try Upstage API first
            if settings.upstage_api_key:
                return self._extract_with_upstage(text)
            
            # Fallback to OpenAI API
            if settings.openai_api_key:
                return self._extract_with_openai(text)
                
        except Exception as e:
            print(f"LLM extraction failed: {e}")
        
        # Fallback to rule-based approach
        return self._extract_meaningful_sentence(text)
    
    def _extract_with_upstage(self, text: str) -> str:
        """Extract decision using Upstage API"""
        prompt = f"""
다음 회의 발언에서 실제 결정사항만 추출해주세요.

규칙:
1. 형식적인 표현("감사드립니다", "바랍니다", "하겠습니다" 등)은 제외
2. 핵심 결정 내용만 간결하게 추출 (30자 이내)
3. 결정사항이 없으면 "없음"이라고만 답변
4. 한국어로 답변
5. "결정사항:" 같은 라벨은 제외하고 내용만 답변

발언: {text}

결정사항:"""

        headers = {
            "Authorization": f"Bearer {settings.upstage_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "solar-1-mini-chat",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 100,
            "temperature": 0.1
        }
        
        response = requests.post(
            f"{settings.upstage_base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            # "없음" 또는 빈 문자열인 경우 빈 문자열 반환
            if not content or content in ["없음", "결정사항이 없습니다", "결정사항: 없음"]:
                return ""
            return content
        
        return ""
    
    def _extract_with_openai(self, text: str) -> str:
        """Extract decision using OpenAI API"""
        prompt = f"""
다음 회의 발언에서 실제 결정사항만 추출해주세요.

규칙:
1. 형식적인 표현("감사드립니다", "바랍니다", "하겠습니다" 등)은 제외
2. 핵심 결정 내용만 간결하게 추출 (30자 이내)
3. 결정사항이 없으면 "없음"이라고만 답변
4. 한국어로 답변
5. "결정사항:" 같은 라벨은 제외하고 내용만 답변

발언: {text}

결정사항:"""

        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 100,
            "temperature": 0.1
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            # "없음" 또는 빈 문자열인 경우 빈 문자열 반환
            if not content or content in ["없음", "결정사항이 없습니다", "결정사항: 없음"]:
                return ""
            return content
        
        return ""
    
    def _extract_meaningful_sentence(self, text: str) -> str:
        """Extract the most meaningful sentence from text"""
        # Split into sentences
        sentences = re.split(r'[.!?]', text)
        
        # Score each sentence based on decision-related keywords
        sentence_scores = []
        decision_keywords = {
            "통합": 5, "개편": 5, "설립": 5, "추진": 4, "진행": 4, "시작": 4, "완료": 4,
            "검토": 3, "수립": 4, "개발": 3, "결정": 5, "확정": 5, "합의": 4, "동의": 3
        }
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            score = 0
            for keyword, weight in decision_keywords.items():
                if keyword in sentence:
                    score += weight
            
            # Penalize very short or very long sentences
            if len(sentence) < 5:
                score -= 2
            elif len(sentence) > 100:
                score -= 3
            
            # Penalize sentences with too many formal phrases
            formal_phrases = ["감사드립니다", "바랍니다", "하겠습니다", "동의합니다"]
            for phrase in formal_phrases:
                if phrase in sentence:
                    score -= 1
            
            sentence_scores.append((sentence, score))
        
        # Return the sentence with the highest score
        if sentence_scores:
            best_sentence = max(sentence_scores, key=lambda x: x[1])
            if best_sentence[1] > 0:  # Only return if score is positive
                return self._clean_sentence(best_sentence[0])
        
        return ""
    
    def _clean_sentence(self, sentence: str) -> str:
        """Clean and format a sentence"""
        # Remove common prefixes
        prefixes = ["결정사항을 정리하겠습니다", "결정사항을 정리하면", "결정된 사항은", "결론은", "합의된 내용은"]
        for prefix in prefixes:
            if sentence.startswith(prefix):
                sentence = sentence[len(prefix):].strip()
                break
        
        # Clean up whitespace and punctuation
        sentence = re.sub(r'\s+', ' ', sentence).strip()
        sentence = re.sub(r'^[,.!?]+', '', sentence)  # Remove leading punctuation
        sentence = re.sub(r'[,.!?]+$', '', sentence)  # Remove trailing punctuation
        
        # Limit length
        if len(sentence) > 50:
            # Try to find a good break point
            break_points = [',', ';', ' ']
            for point in break_points:
                if point in sentence[:50]:
                    end_idx = sentence[:50].rfind(point)
                    if end_idx > 10:
                        sentence = sentence[:end_idx].strip()
                        break
            if len(sentence) > 50:
                sentence = sentence[:50].strip()
        
        return sentence
    
    def _summarize_decision_content(self, content: str) -> str:
        """Summarize decision content using LLM for better clarity"""
        content = content.strip()
        
        if not content or len(content) < 5:
            return ""
        
        # Use LLM to summarize if content is long or complex
        if len(content) > 30:
            return self._summarize_with_llm(content)
        
        # For short content, just clean it up
        return self._clean_decision_text(content)
    
    def _summarize_with_llm(self, content: str) -> str:
        """Summarize decision content using LLM"""
        try:
            # Try Upstage API first
            if settings.upstage_api_key:
                return self._summarize_with_upstage(content)
            
            # Fallback to OpenAI API
            if settings.openai_api_key:
                return self._summarize_with_openai(content)
                
        except Exception as e:
            print(f"LLM summarization failed: {e}")
        
        # Fallback to simple cleaning
        return self._clean_decision_text(content)
    
    def _summarize_with_upstage(self, content: str) -> str:
        """Summarize using Upstage API"""
        prompt = f"""
다음 결정사항을 더 간결하고 명확하게 요약해주세요.

규칙:
1. 핵심 내용만 추출 (30자 이내)
2. 형식적인 표현 제거
3. 명확하고 이해하기 쉽게 작성
4. 한국어로 답변

결정사항: {content}

요약:"""

        headers = {
            "Authorization": f"Bearer {settings.upstage_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "solar-1-mini-chat",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 50,
            "temperature": 0.1
        }
        
        response = requests.post(
            f"{settings.upstage_base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            summary = result["choices"][0]["message"]["content"].strip()
            return summary if summary else self._clean_decision_text(content)
        
        return self._clean_decision_text(content)
    
    def _summarize_with_openai(self, content: str) -> str:
        """Summarize using OpenAI API"""
        prompt = f"""
다음 결정사항을 더 간결하고 명확하게 요약해주세요.

규칙:
1. 핵심 내용만 추출 (30자 이내)
2. 형식적인 표현 제거
3. 명확하고 이해하기 쉽게 작성
4. 한국어로 답변

결정사항: {content}

요약:"""

        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 50,
            "temperature": 0.1
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            summary = result["choices"][0]["message"]["content"].strip()
            return summary if summary else self._clean_decision_text(content)
        
        return self._clean_decision_text(content)
    
    def _clean_decision_text(self, content: str) -> str:
        """Clean decision text using simple rules"""
        content = content.strip()
        
        # Remove excessive formal language
        formal_phrases = [
            "이 결정사항에 대해서는 모든 참가자분들의 동의를 받아서 진행하겠습니다",
            "이 결정사항의 실행을 위해서는 구체적인 실행 계획과 일정을 수립해야 하고",
            "이 결정사항이 회사의 발전에 도움이 될 것이라고 생각하고",
            "성공적인 실행을 위해 최선을 다하겠습니다",
            "네 동의합니다",
            "에 대해 찬성합니다",
            "감사드립니다",
            "바랍니다"
        ]
        
        for phrase in formal_phrases:
            content = content.replace(phrase, "")
        
        # Clean up
        content = re.sub(r'\s+', ' ', content).strip()
        content = re.sub(r'[,.!?]+$', '', content)
        
        # Ensure reasonable length
        if len(content) > 40:
            content = content[:40].strip()
        
        return content if len(content) >= 5 else ""
    
    def _sort_decisions_by_consensus(self, decisions: List[Dict[str, Any]], consensus: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Sort decisions by consensus level and importance"""
        # Add consensus level and agreement percentage to each decision
        for decision in decisions:
            consensus_score = consensus.get("score", 0.0)
            decision["consensus_level"] = consensus.get("level", "불명확")
            decision["consensus_score"] = consensus_score
            decision["agreement_level"] = int(consensus_score * 100)  # Convert to percentage
            decision["agenda_title"] = decision.get("agenda_title", "일반 안건")
            
            # Add consensus reason
            decision["consensus_reason"] = consensus.get("consensus_reason", "")
            
            # Add disagreement details if consensus is low
            if consensus_score < 1.0:
                disagreement_details = consensus.get("disagreement_details", {})
                decision["disagreement_details"] = disagreement_details
            else:
                decision["disagreement_details"] = {}
        
        # Sort by consensus score (descending)
        sorted_decisions = sorted(decisions, key=lambda x: x["consensus_score"], reverse=True)
        
        return sorted_decisions
    
    def _generate_agenda_summary(self, agenda_title: str, consensus: Dict[str, Any], decisions: List[Dict[str, Any]]) -> str:
        """Generate a concise summary of the agenda"""
        consensus_level = consensus.get("level", "불명확")
        consensus_score = consensus.get("score", 0.0)
        
        if not decisions:
            return f"합의 수준 {consensus_level} ({consensus_score:.1%})"
        
        # Extract key decision content for summary
        decision_summaries = []
        for decision in decisions[:3]:  # Take first 3 decisions
            content = decision.get("content", "")
            if content:
                # Extract first meaningful phrase
                summary = self._extract_decision_summary(content)
                if summary:
                    decision_summaries.append(summary)
        
        if decision_summaries:
            return f"합의 수준 {consensus_level} ({consensus_score:.1%}) - {', '.join(decision_summaries)}"
        else:
            return f"합의 수준 {consensus_level} ({consensus_score:.1%}) - {len(decisions)}개 결정사항"
    
    def _extract_decision_summary(self, content: str) -> str:
        """Extract a concise summary from decision content"""
        # Remove common prefixes
        prefixes = ["결정사항을 정리하겠습니다.", "결정사항을 정리하면", "결정된 사항은", "결론은", "합의된 내용은"]
        for prefix in prefixes:
            if content.startswith(prefix):
                content = content[len(prefix):].strip()
                break
        
        # Take first meaningful phrase (up to 20 characters)
        if len(content) > 20:
            # Try to find a natural break point
            break_points = ['.', ',', ';', ' ']
            for point in break_points:
                if point in content[:20]:
                    end_idx = content[:20].rfind(point)
                    if end_idx > 10:  # At least 10 characters
                        return content[:end_idx].strip()
            
            return content[:20].strip()
        
        return content.strip()
    
    def _identify_agenda_items(self, utterances: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Identify agenda items from meeting utterances"""
        agenda_items = {}
        agenda_keywords = [
            "안건", "주제", "토론", "검토", "논의", "의결", "결정", "확정",
            "agenda", "topic", "discussion", "review", "decision"
        ]
        
        current_agenda = None
        agenda_counter = 1
        
        for utterance in utterances:
            text = utterance.get("text", "").lower()
            
            # Check if this utterance introduces a new agenda item
            if any(keyword in text for keyword in agenda_keywords):
                # Extract agenda title
                agenda_title = self._extract_agenda_title(text)
                if agenda_title:
                    agenda_id = f"agenda_{agenda_counter}"
                    agenda_items[agenda_id] = {
                        "id": agenda_id,
                        "title": agenda_title,
                        "introduced_by": utterance.get("speaker"),
                        "introduced_at": utterance.get("timestamp"),
                        "keywords": self._extract_keywords(text)
                    }
                    current_agenda = agenda_id
                    agenda_counter += 1
        
        # If no explicit agenda items found, create default ones based on topic clustering
        if not agenda_items:
            agenda_items = self._create_default_agendas(utterances)
        
        return agenda_items
    
    def _extract_agenda_title(self, text: str) -> str:
        """Extract agenda title from utterance text"""
        # Simple extraction - can be enhanced with NLP
        text = text.strip()
        
        # Remove common prefixes
        prefixes = ["안건:", "주제:", "토론:", "검토:", "논의:"]
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
                break
        
        # Extract meaningful keywords for title
        keywords = self._extract_meaningful_keywords(text)
        if keywords:
            return " ".join(keywords[:3])  # Use first 3 keywords
        
        # Fallback: take first meaningful phrase
        if len(text) > 30:
            text = text[:30] + "..."
        
        return text if text else "일반 논의"
    
    def _extract_meaningful_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        # Common business keywords
        business_keywords = [
            "프로젝트", "개발", "기획", "팀", "조직", "인력", "채용", "예산", "일정", "품질",
            "시스템", "기술", "고객", "시장", "전략", "운영", "관리", "검토", "통합", "개편"
        ]
        
        # Extract keywords that appear in the text
        found_keywords = []
        for keyword in business_keywords:
            if keyword in text:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction - can be enhanced with NLP
        keywords = []
        common_keywords = [
            "프로젝트", "일정", "예산", "팀", "기술", "품질", "고객", "시장",
            "개발", "테스트", "배포", "유지보수", "보안", "성능"
        ]
        
        for keyword in common_keywords:
            if keyword in text:
                keywords.append(keyword)
        
        return keywords
    
    def _create_default_agendas(self, utterances: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Create default agenda items based on topic clustering"""
        # Simple topic clustering based on keyword frequency
        all_text = " ".join(u.get("text", "") for u in utterances)
        
        topic_patterns = {
            "프로젝트 계획": ["계획", "일정", "스케줄", "마감"],
            "기술 검토": ["기술", "개발", "코드", "시스템"],
            "팀 협력": ["팀", "협력", "소통", "의견"],
            "품질 관리": ["품질", "테스트", "검증", "확인"],
            "비즈니스 전략": ["전략", "비즈니스", "시장", "고객"]
        }
        
        agenda_items = {}
        agenda_counter = 1
        
        for topic, keywords in topic_patterns.items():
            if any(keyword in all_text for keyword in keywords):
                agenda_id = f"agenda_{agenda_counter}"
                agenda_items[agenda_id] = {
                    "id": agenda_id,
                    "title": topic,
                    "introduced_by": "시스템",
                    "introduced_at": 0,
                    "keywords": keywords
                }
                agenda_counter += 1
        
        return agenda_items
    
    def _classify_utterance_to_agenda(self, utterance: Dict[str, Any], 
                                   agenda_items: Dict[str, Dict[str, Any]]) -> str:
        """Classify utterance to specific agenda item"""
        text = utterance.get("text", "").lower()
        
        # Simple classification based on keyword matching
        best_match = None
        best_score = 0
        
        for agenda_id, agenda_info in agenda_items.items():
            keywords = agenda_info.get("keywords", [])
            score = sum(1 for keyword in keywords if keyword in text)
            
            if score > best_score:
                best_score = score
                best_match = agenda_id
        
        return best_match if best_score > 0 else None
    
    def _analyze_discussion_patterns(self, utterances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze discussion patterns for an agenda item"""
        if not utterances:
            return {}
        
        # Analyze participation
        speakers = [u.get("speaker") for u in utterances]
        speaker_counts = Counter(speakers)
        
        # Analyze timing
        timestamps = [u.get("timestamp", 0) for u in utterances]
        duration = max(timestamps) - min(timestamps) if timestamps else 0
        
        # Analyze interaction patterns
        interaction_patterns = self._analyze_interaction_patterns(utterances)
        
        return {
            "total_utterances": len(utterances),
            "unique_speakers": len(speaker_counts),
            "most_active_speaker": speaker_counts.most_common(1)[0][0] if speaker_counts and speaker_counts.most_common(1) else "Unknown",
            "discussion_duration": duration,
            "avg_utterance_length": sum(len(u.get("text", "").split()) for u in utterances) / len(utterances) if utterances else 0,
            "interaction_patterns": interaction_patterns
        }
    
    def _analyze_opinions_and_positions(self, utterances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze opinions and positions expressed in discussions using LLM"""
        if not utterances:
            return {}
        
        # Use LLM for more accurate opinion analysis
        return self._analyze_opinions_with_llm(utterances)
    
    def _analyze_opinions_with_llm(self, utterances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze opinions using LLM for better accuracy"""
        try:
            # Try Upstage API first
            if settings.upstage_api_key:
                return self._analyze_opinions_with_upstage(utterances)
            
            # Fallback to OpenAI API
            if settings.openai_api_key:
                return self._analyze_opinions_with_openai(utterances)
                
        except Exception as e:
            print(f"LLM opinion analysis failed: {e}")
        
        # Fallback to rule-based approach
        return self._analyze_opinions_fallback(utterances)
    
    def _analyze_opinions_with_upstage(self, utterances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze opinions using Upstage API"""
        # Combine all utterances for context
        combined_text = "\n".join([
            f"{u.get('speaker', 'Unknown')}: {u.get('text', '')}"
            for u in utterances
        ])
        
        prompt = f"""
다음 회의 발언들을 분석하여 각 참가자의 의견과 입장을 분류해주세요.

분류 기준:
1. **찬성/긍정**: 명확히 찬성하거나 긍정적인 의견을 표현한 경우
2. **반대/부정**: 명확히 반대하거나 부정적인 의견을 표현한 경우  
3. **중립/검토**: 추가 검토나 논의를 제안하는 경우
4. **불확실**: 의견이 명확하지 않거나 중립적인 경우

각 발언에 대해 다음 JSON 형식으로 답변해주세요:
{{
    "opinions": [
        {{
            "speaker": "발언자명",
            "text": "원본 발언",
            "sentiment": "찬성/반대/중립/불확실",
            "confidence": 0.0-1.0,
            "reason": "분류 이유 (간단히)"
        }}
    ]
}}

회의 발언:
{combined_text}

분석 결과:"""

        headers = {
            "Authorization": f"Bearer {settings.upstage_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "solar-1-mini-chat",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000,
            "temperature": 0.1
        }
        
        response = requests.post(
            f"{settings.upstage_base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            # Parse JSON response
            try:
                import json
                analysis = json.loads(content)
                return self._process_llm_opinion_analysis(analysis, utterances)
            except json.JSONDecodeError:
                print("Failed to parse LLM response as JSON")
                return self._analyze_opinions_fallback(utterances)
        
        return self._analyze_opinions_fallback(utterances)
    
    def _analyze_opinions_with_openai(self, utterances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze opinions using OpenAI API"""
        # Similar implementation to Upstage but with OpenAI
        combined_text = "\n".join([
            f"{u.get('speaker', 'Unknown')}: {u.get('text', '')}"
            for u in utterances
        ])
        
        prompt = f"""
다음 회의 발언들을 분석하여 각 참가자의 의견과 입장을 분류해주세요.

분류 기준:
1. **찬성/긍정**: 명확히 찬성하거나 긍정적인 의견을 표현한 경우
2. **반대/부정**: 명확히 반대하거나 부정적인 의견을 표현한 경우  
3. **중립/검토**: 추가 검토나 논의를 제안하는 경우
4. **불확실**: 의견이 명확하지 않거나 중립적인 경우

각 발언에 대해 다음 JSON 형식으로 답변해주세요:
{{
    "opinions": [
        {{
            "speaker": "발언자명",
            "text": "원본 발언",
            "sentiment": "찬성/반대/중립/불확실",
            "confidence": 0.0-1.0,
            "reason": "분류 이유 (간단히)"
        }}
    ]
}}

회의 발언:
{combined_text}

분석 결과:"""

        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000,
            "temperature": 0.1
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            try:
                import json
                analysis = json.loads(content)
                return self._process_llm_opinion_analysis(analysis, utterances)
            except json.JSONDecodeError:
                print("Failed to parse LLM response as JSON")
                return self._analyze_opinions_fallback(utterances)
        
        return self._analyze_opinions_fallback(utterances)
    
    def _process_llm_opinion_analysis(self, analysis: Dict[str, Any], utterances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process LLM opinion analysis results"""
        opinions = {
            "positive": [],
            "negative": [],
            "neutral": [],
            "uncertain": []
        }
        
        llm_opinions = analysis.get("opinions", [])
        
        for llm_opinion in llm_opinions:
            sentiment = llm_opinion.get("sentiment", "불확실")
            speaker = llm_opinion.get("speaker", "Unknown")
            text = llm_opinion.get("text", "")
            confidence = llm_opinion.get("confidence", 0.5)
            reason = llm_opinion.get("reason", "")
            
            opinion_data = {
                "speaker": speaker,
                "text": text,
                "timestamp": self._find_timestamp_for_text(text, utterances),
                "confidence": confidence,
                "reason": reason
            }
            
            if sentiment in ["찬성", "긍정"]:
                opinions["positive"].append(opinion_data)
            elif sentiment in ["반대", "부정"]:
                opinions["negative"].append(opinion_data)
            elif sentiment in ["중립", "검토"]:
                opinions["neutral"].append(opinion_data)
            else:
                opinions["uncertain"].append(opinion_data)
        
        return opinions
    
    def _find_timestamp_for_text(self, text: str, utterances: List[Dict[str, Any]]) -> int:
        """Find timestamp for a given text in utterances"""
        for utterance in utterances:
            if utterance.get("text", "") == text:
                return utterance.get("timestamp", 0)
        return 0
    
    def _analyze_opinions_fallback(self, utterances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback opinion analysis using rule-based approach"""
        # Enhanced keyword-based analysis
        positive_patterns = [
            r"좋[다겠습니다]", r"찬성", r"동의", r"적절", r"효과적", r"성공", 
            r"진행하[겠습니다자]", r"추진", r"승인", r"합의", r"결정"
        ]
        negative_patterns = [
            r"나쁘[다겠습니다]", r"반대", r"부적절", r"문제", r"위험", r"실패",
            r"어렵[다겠습니다]", r"불가능", r"우려", r"부정"
        ]
        neutral_patterns = [
            r"검토", r"논의", r"고려", r"분석", r"확인", r"추가", r"다시"
        ]
        
        opinions = {
            "positive": [],
            "negative": [],
            "neutral": [],
            "uncertain": []
        }
        
        for utterance in utterances:
            text = utterance.get("text", "").lower()
            speaker = utterance.get("speaker")
            
            positive_score = sum(1 for pattern in positive_patterns if re.search(pattern, text))
            negative_score = sum(1 for pattern in negative_patterns if re.search(pattern, text))
            neutral_score = sum(1 for pattern in neutral_patterns if re.search(pattern, text))
            
            opinion_data = {
                "speaker": speaker,
                "text": utterance.get("text"),
                "timestamp": utterance.get("timestamp"),
                "confidence": 0.6,  # Lower confidence for rule-based
                "reason": "키워드 기반 분석"
            }
            
            if positive_score > negative_score and positive_score > 0:
                opinions["positive"].append(opinion_data)
            elif negative_score > positive_score and negative_score > 0:
                opinions["negative"].append(opinion_data)
            elif neutral_score > 0:
                opinions["neutral"].append(opinion_data)
            else:
                opinions["uncertain"].append(opinion_data)
        
        return opinions
    
    def _analyze_decisions(self, utterances: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze decisions made during the discussion"""
        decisions = []
        decision_keywords = ["결정", "확정", "의결", "합의", "동의", "승인", "결론"]
        
        for utterance in utterances:
            text = utterance.get("text", "").lower()
            
            if any(keyword in text for keyword in decision_keywords):
                decisions.append({
                    "speaker": utterance.get("speaker"),
                    "text": utterance.get("text"),
                    "timestamp": utterance.get("timestamp"),
                    "confidence": 0.8  # Placeholder
                })
        
        return decisions
    
    def _analyze_consensus(self, utterances: List[Dict[str, Any]], 
                         opinions: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze consensus level in the discussion with detailed reasoning"""
        # Ensure opinions has the expected structure
        if not isinstance(opinions, dict):
            return {"level": "불명확", "score": 0.0}
        
        positive_count = len(opinions.get("positive", []))
        negative_count = len(opinions.get("negative", []))
        neutral_count = len(opinions.get("neutral", []))
        uncertain_count = len(opinions.get("uncertain", []))
        
        total_opinions = positive_count + negative_count + neutral_count + uncertain_count
        
        if total_opinions == 0:
            return {"level": "불명확", "score": 0.0}
        
        # Calculate weighted ratios (neutral opinions count as 0.5)
        positive_ratio = positive_count / total_opinions
        negative_ratio = negative_count / total_opinions
        neutral_ratio = neutral_count / total_opinions
        uncertain_ratio = uncertain_count / total_opinions
        
        # Calculate consensus score with more nuanced logic
        if positive_ratio >= 0.6:  # 60% 이상 찬성
            consensus_level = "높음"
            consensus_score = positive_ratio + (neutral_ratio * 0.3)  # 중립 의견도 부분적으로 반영
        elif negative_ratio >= 0.6:  # 60% 이상 반대
            consensus_level = "높음"
            consensus_score = negative_ratio + (neutral_ratio * 0.3)
        elif positive_ratio > negative_ratio and (positive_ratio - negative_ratio) >= 0.2:
            consensus_level = "보통"
            consensus_score = 0.6 + (positive_ratio - negative_ratio) * 0.2
        elif negative_ratio > positive_ratio and (negative_ratio - positive_ratio) >= 0.2:
            consensus_level = "보통"
            consensus_score = 0.6 + (negative_ratio - positive_ratio) * 0.2
        elif neutral_ratio >= 0.5:  # 중립 의견이 많음
            consensus_level = "보통"
            consensus_score = 0.5
        elif uncertain_ratio >= 0.4:  # 불확실한 의견이 많음
            consensus_level = "낮음"
            consensus_score = 0.3
        else:
            consensus_level = "낮음"
            consensus_score = min(positive_ratio, negative_ratio) + (neutral_ratio * 0.2)
        
        # Analyze disagreement details with LLM for better quality
        disagreement_details = self._analyze_disagreement_details_enhanced(opinions, utterances, consensus_score)
        
        return {
            "level": consensus_level,
            "score": round(consensus_score, 2),
            "positive_ratio": round(positive_ratio, 2),
            "negative_ratio": round(negative_ratio, 2),
            "neutral_ratio": round(neutral_ratio, 2),
            "uncertain_ratio": round(uncertain_ratio, 2),
            "disagreement_details": disagreement_details,
            "consensus_reason": self._generate_consensus_reason(consensus_level, consensus_score, positive_ratio, negative_ratio, neutral_ratio, uncertain_ratio)
        }
    
    def _generate_consensus_reason(self, level: str, score: float, positive_ratio: float, 
                                 negative_ratio: float, neutral_ratio: float, uncertain_ratio: float) -> str:
        """Generate human-readable reason for consensus level"""
        if level == "높음":
            if positive_ratio >= 0.6:
                return f"찬성 의견이 {positive_ratio:.1%}로 높아 명확한 합의가 이루어졌습니다."
            else:
                return f"반대 의견이 {negative_ratio:.1%}로 높아 명확한 반대 합의가 이루어졌습니다."
        elif level == "보통":
            if positive_ratio > negative_ratio:
                return f"찬성 의견({positive_ratio:.1%})이 반대 의견({negative_ratio:.1%})보다 높지만, 중립 의견({neutral_ratio:.1%})이 있어 추가 논의가 필요합니다."
            elif negative_ratio > positive_ratio:
                return f"반대 의견({negative_ratio:.1%})이 찬성 의견({positive_ratio:.1%})보다 높지만, 중립 의견({neutral_ratio:.1%})이 있어 추가 논의가 필요합니다."
            else:
                return f"중립 의견이 {neutral_ratio:.1%}로 많아 추가 검토가 필요합니다."
        else:  # 낮음
            if uncertain_ratio >= 0.4:
                return f"불확실한 의견이 {uncertain_ratio:.1%}로 많아 명확한 합의가 어렵습니다."
            else:
                return f"찬성({positive_ratio:.1%})과 반대({negative_ratio:.1%}) 의견이 비슷하여 합의가 어렵습니다."
    
    def _analyze_disagreement_details_enhanced(self, opinions: Dict[str, Any], utterances: List[Dict[str, Any]], consensus_score: float) -> Dict[str, Any]:
        """Analyze detailed disagreement information with LLM for better quality"""
        # Only analyze disagreement details if consensus is low
        if consensus_score >= 0.8:
            return {
                "who_disagreed": [],
                "what_disagreed": "",
                "why_disagreed": "",
                "analysis_quality": "high_consensus"
            }
        
        try:
            # Use LLM for better disagreement analysis
            if settings.upstage_api_key:
                return self._analyze_disagreement_with_upstage(opinions, utterances, consensus_score)
            elif settings.openai_api_key:
                return self._analyze_disagreement_with_openai(opinions, utterances, consensus_score)
        except Exception as e:
            print(f"LLM disagreement analysis failed: {e}")
        
        # Fallback to rule-based analysis
        return self._analyze_disagreement_details_fallback(opinions, utterances, consensus_score)
    
    def _analyze_disagreement_with_upstage(self, opinions: Dict[str, Any], utterances: List[Dict[str, Any]], consensus_score: float) -> Dict[str, Any]:
        """Analyze disagreement using Upstage API"""
        # Prepare context for LLM
        negative_opinions = opinions.get("negative", [])
        neutral_opinions = opinions.get("neutral", [])
        uncertain_opinions = opinions.get("uncertain", [])
        
        context_text = "회의에서 합의가 어려운 상황입니다.\n\n"
        
        if negative_opinions:
            context_text += "반대 의견:\n"
            for op in negative_opinions:
                context_text += f"- {op.get('speaker', 'Unknown')}: {op.get('text', '')}\n"
        
        if neutral_opinions:
            context_text += "\n중립/검토 의견:\n"
            for op in neutral_opinions[:3]:  # Limit to 3
                context_text += f"- {op.get('speaker', 'Unknown')}: {op.get('text', '')}\n"
        
        if uncertain_opinions:
            context_text += "\n불확실한 의견:\n"
            for op in uncertain_opinions[:3]:  # Limit to 3
                context_text += f"- {op.get('speaker', 'Unknown')}: {op.get('text', '')}\n"
        
        prompt = f"""
다음 회의 상황에서 합의가 어려운 이유를 분석해주세요.

{context_text}

다음 JSON 형식으로 답변해주세요:
{{
    "who_disagreed": ["반대한 사람들의 이름"],
    "what_disagreed": "구체적으로 무엇에 대해 합의가 안 되었는지 (간단명료하게)",
    "why_disagreed": "합의가 안 된 주요 이유들 (예: 시간적 제약, 비용 문제, 기술적 한계 등)",
    "suggestions": "합의를 위한 제안사항 (간단히)"
}}

분석 결과:"""

        headers = {
            "Authorization": f"Bearer {settings.upstage_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "solar-1-mini-chat",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500,
            "temperature": 0.1
        }
        
        response = requests.post(
            f"{settings.upstage_base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            try:
                import json
                analysis = json.loads(content)
                return {
                    "who_disagreed": analysis.get("who_disagreed", []),
                    "what_disagreed": analysis.get("what_disagreed", ""),
                    "why_disagreed": analysis.get("why_disagreed", ""),
                    "suggestions": analysis.get("suggestions", ""),
                    "analysis_quality": "llm_enhanced"
                }
            except json.JSONDecodeError:
                print("Failed to parse LLM disagreement analysis as JSON")
        
        return self._analyze_disagreement_details_fallback(opinions, utterances, consensus_score)
    
    def _analyze_disagreement_with_openai(self, opinions: Dict[str, Any], utterances: List[Dict[str, Any]], consensus_score: float) -> Dict[str, Any]:
        """Analyze disagreement using OpenAI API"""
        # Similar implementation to Upstage
        negative_opinions = opinions.get("negative", [])
        neutral_opinions = opinions.get("neutral", [])
        uncertain_opinions = opinions.get("uncertain", [])
        
        context_text = "회의에서 합의가 어려운 상황입니다.\n\n"
        
        if negative_opinions:
            context_text += "반대 의견:\n"
            for op in negative_opinions:
                context_text += f"- {op.get('speaker', 'Unknown')}: {op.get('text', '')}\n"
        
        if neutral_opinions:
            context_text += "\n중립/검토 의견:\n"
            for op in neutral_opinions[:3]:
                context_text += f"- {op.get('speaker', 'Unknown')}: {op.get('text', '')}\n"
        
        if uncertain_opinions:
            context_text += "\n불확실한 의견:\n"
            for op in uncertain_opinions[:3]:
                context_text += f"- {op.get('speaker', 'Unknown')}: {op.get('text', '')}\n"
        
        prompt = f"""
다음 회의 상황에서 합의가 어려운 이유를 분석해주세요.

{context_text}

다음 JSON 형식으로 답변해주세요:
{{
    "who_disagreed": ["반대한 사람들의 이름"],
    "what_disagreed": "구체적으로 무엇에 대해 합의가 안 되었는지 (간단명료하게)",
    "why_disagreed": "합의가 안 된 주요 이유들 (예: 시간적 제약, 비용 문제, 기술적 한계 등)",
    "suggestions": "합의를 위한 제안사항 (간단히)"
}}

분석 결과:"""

        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500,
            "temperature": 0.1
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            try:
                import json
                analysis = json.loads(content)
                return {
                    "who_disagreed": analysis.get("who_disagreed", []),
                    "what_disagreed": analysis.get("what_disagreed", ""),
                    "why_disagreed": analysis.get("why_disagreed", ""),
                    "suggestions": analysis.get("suggestions", ""),
                    "analysis_quality": "llm_enhanced"
                }
            except json.JSONDecodeError:
                print("Failed to parse LLM disagreement analysis as JSON")
        
        return self._analyze_disagreement_details_fallback(opinions, utterances, consensus_score)
    
    def _analyze_disagreement_details_fallback(self, opinions: Dict[str, Any], utterances: List[Dict[str, Any]], consensus_score: float) -> Dict[str, Any]:
        """Fallback disagreement analysis using rule-based approach"""
        disagreement_details = {
            "who_disagreed": [],
            "what_disagreed": "",
            "why_disagreed": "",
            "analysis_quality": "rule_based"
        }
        
        # Who disagreed
        negative_speakers = [op.get("speaker") for op in opinions.get("negative", [])]
        if negative_speakers:
            disagreement_details["who_disagreed"] = list(set(negative_speakers))
        
        # What was disagreed (extract from negative opinions)
        negative_texts = [op.get("text", "") for op in opinions.get("negative", [])]
        if negative_texts:
            # Combine negative opinion texts to understand what was disagreed
            combined_negative = " ".join(negative_texts)
            disagreement_details["what_disagreed"] = self._extract_disagreement_content(combined_negative)
        
        # Why disagreed (analyze reasons from negative opinions)
        if negative_texts:
            disagreement_details["why_disagreed"] = self._analyze_disagreement_reasons(negative_texts)
        
        return disagreement_details
    
    def _extract_disagreement_content(self, text: str) -> str:
        """Extract what was disagreed from negative opinion text"""
        # Simple keyword-based extraction
        disagreement_keywords = ["반대", "동의하지 않음", "문제", "우려", "부적절", "불가능", "어려움"]
        
        sentences = text.split(".")
        disagreement_sentences = []
        
        for sentence in sentences:
            if any(keyword in sentence for keyword in disagreement_keywords):
                disagreement_sentences.append(sentence.strip())
        
        if disagreement_sentences:
            return ". ".join(disagreement_sentences[:3])  # Limit to 3 sentences
        else:
            return "구체적인 반대 내용이 명시되지 않음"
    
    def _analyze_disagreement_reasons(self, negative_texts: List[str]) -> str:
        """Analyze reasons for disagreement"""
        combined_text = " ".join(negative_texts).lower()
        
        # Common disagreement reasons
        reasons = []
        
        if any(word in combined_text for word in ["시간", "일정", "기간"]):
            reasons.append("시간적 제약")
        
        if any(word in combined_text for word in ["비용", "예산", "금액"]):
            reasons.append("비용 문제")
        
        if any(word in combined_text for word in ["기술", "구현", "실행"]):
            reasons.append("기술적 한계")
        
        if any(word in combined_text for word in ["인력", "담당자", "역할"]):
            reasons.append("인력 부족")
        
        if any(word in combined_text for word in ["위험", "리스크", "불확실"]):
            reasons.append("위험 요소")
        
        if any(word in combined_text for word in ["우선순위", "중요도", "필요성"]):
            reasons.append("우선순위 문제")
        
        if reasons:
            return ", ".join(reasons)
        else:
            return "구체적인 이유가 명시되지 않음"
    
    def _analyze_discussion_quality(self, utterances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the quality of discussion"""
        if not utterances:
            return {}
        
        # Calculate various quality metrics
        avg_length = sum(len(u.get("text", "").split()) for u in utterances) / len(utterances)
        
        # Count questions and responses
        questions = sum(1 for u in utterances if u.get("text", "").endswith("?"))
        question_ratio = questions / len(utterances) if utterances else 0
        
        # Analyze engagement (time between utterances)
        timestamps = sorted([u.get("timestamp", 0) for u in utterances])
        intervals = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
        avg_interval = sum(intervals) / len(intervals) if intervals else 0
        
        return {
            "avg_utterance_length": avg_length,
            "question_ratio": question_ratio,
            "avg_response_time": avg_interval,
            "engagement_level": "높음" if avg_interval < 60 else "보통" if avg_interval < 180 else "낮음"
        }
    
    def _analyze_interaction_patterns(self, utterances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze interaction patterns between speakers"""
        if len(utterances) < 2:
            return {}
        
        # Analyze turn-taking patterns
        speakers = [u.get("speaker") for u in utterances]
        unique_speakers = list(set(speakers))
        
        # Calculate interaction matrix
        interactions = defaultdict(int)
        for i in range(len(speakers) - 1):
            current_speaker = speakers[i]
            next_speaker = speakers[i + 1]
            if current_speaker != next_speaker:
                interactions[(current_speaker, next_speaker)] += 1
        
        return {
            "unique_speakers": len(unique_speakers),
            "total_interactions": sum(interactions.values()),
            "most_active_interaction": max(interactions.items(), key=lambda x: x[1]) if interactions and interactions.items() else (None, 0)
        }
    

    
    def _generate_meeting_overview(self, agenda_items: Dict[str, Dict[str, Any]], 
                                 analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate meeting-level overview"""
        total_agendas = len(agenda_items)
        total_decisions = sum(len(result.get("decisions", [])) for result in analysis_results.values())
        
        # Calculate overall consensus
        consensus_scores = [result.get("consensus", {}).get("score", 0) for result in analysis_results.values()]
        avg_consensus = sum(consensus_scores) / len(consensus_scores) if consensus_scores else 0
        
        return {
            "total_agendas": total_agendas,
            "total_decisions": total_decisions,
            "avg_consensus": round(avg_consensus, 2),
            "agenda_titles": [agenda.get("title") for agenda in agenda_items.values()]
        }
    
    def get_capabilities(self) -> List[str]:
        return [
            "안건별 논의 패턴 분석",
            "의견 및 입장 분석",
            "결정사항 추출",
            "합의 수준 분석",
            "토론 품질 평가"
        ]
    
    def get_requirements(self) -> List[str]:
        return ["meeting_id", "utterances"] 