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
        # Add consensus level to each decision
        for decision in decisions:
            decision["consensus_level"] = consensus.get("level", "불명확")
            decision["consensus_score"] = consensus.get("score", 0.0)
        
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
        """Analyze opinions and positions expressed in discussions"""
        if not utterances:
            return {}
        
        # Simple sentiment and position analysis
        positive_keywords = ["좋다", "찬성", "동의", "적절", "효과적", "성공"]
        negative_keywords = ["나쁘다", "반대", "부적절", "문제", "위험", "실패"]
        neutral_keywords = ["검토", "논의", "고려", "분석", "확인"]
        
        opinions = {
            "positive": [],
            "negative": [],
            "neutral": [],
            "uncertain": []
        }
        
        for utterance in utterances:
            text = utterance.get("text", "").lower()
            speaker = utterance.get("speaker")
            
            positive_count = sum(1 for keyword in positive_keywords if keyword in text)
            negative_count = sum(1 for keyword in negative_keywords if keyword in text)
            neutral_count = sum(1 for keyword in neutral_keywords if keyword in text)
            
            if positive_count > negative_count:
                opinions["positive"].append({
                    "speaker": speaker,
                    "text": utterance.get("text"),
                    "timestamp": utterance.get("timestamp")
                })
            elif negative_count > positive_count:
                opinions["negative"].append({
                    "speaker": speaker,
                    "text": utterance.get("text"),
                    "timestamp": utterance.get("timestamp")
                })
            elif neutral_count > 0:
                opinions["neutral"].append({
                    "speaker": speaker,
                    "text": utterance.get("text"),
                    "timestamp": utterance.get("timestamp")
                })
            else:
                opinions["uncertain"].append({
                    "speaker": speaker,
                    "text": utterance.get("text"),
                    "timestamp": utterance.get("timestamp")
                })
        
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
        """Analyze consensus level in the discussion"""
        # Ensure opinions has the expected structure
        if not isinstance(opinions, dict):
            return {"level": "불명확", "score": 0.0}
        
        positive_count = len(opinions.get("positive", []))
        negative_count = len(opinions.get("negative", []))
        neutral_count = len(opinions.get("neutral", []))
        
        total_opinions = positive_count + negative_count + neutral_count
        
        if total_opinions == 0:
            return {"level": "불명확", "score": 0.0}
        
        positive_ratio = positive_count / total_opinions
        negative_ratio = negative_count / total_opinions
        
        # Calculate consensus score
        if positive_ratio > 0.7:
            consensus_level = "높음"
            consensus_score = positive_ratio
        elif negative_ratio > 0.7:
            consensus_level = "높음"
            consensus_score = negative_ratio
        elif abs(positive_ratio - negative_ratio) < 0.2:
            consensus_level = "보통"
            consensus_score = 0.5
        else:
            consensus_level = "낮음"
            consensus_score = min(positive_ratio, negative_ratio)
        
        return {
            "level": consensus_level,
            "score": round(consensus_score, 2),
            "positive_ratio": round(positive_ratio, 2),
            "negative_ratio": round(negative_ratio, 2)
        }
    
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