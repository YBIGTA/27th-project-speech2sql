"""
Speaker Analysis Agent - Analyzes individual speaker patterns and characteristics
"""
from typing import Dict, Any, List
import re
from collections import defaultdict, Counter
from src.agents.base_agent import BaseAgent, AgentType, AgentResult
from config.settings import settings
import requests


class SpeakerAnalysisAgent(BaseAgent):
    """Agent for analyzing individual speaker patterns and characteristics"""
    
    def __init__(self):
        super().__init__(AgentType.SPEAKER_ANALYSIS, "SpeakerAnalysisAgent")
        
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input data contains required fields"""
        required_fields = ["meeting_id", "utterances"]
        return all(field in data for field in required_fields)
    
    def preprocess(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess utterances by speaker"""
        utterances = data.get("utterances", [])
        
        # Group utterances by speaker
        speaker_data = defaultdict(list)
        for utterance in utterances:
            speaker = utterance.get("speaker", "Unknown")
            speaker_data[speaker].append(utterance)
        
        # Calculate basic statistics
        speaker_stats = {}
        total_utterances = len(utterances)
        
        for speaker, speaker_utterances in speaker_data.items():
            total_duration = sum(u.get("end_timestamp", 0) - u.get("timestamp", 0) 
                               for u in speaker_utterances)
            total_words = sum(len(u.get("text", "").split()) for u in speaker_utterances)
            
            speaker_stats[speaker] = {
                "utterance_count": len(speaker_utterances),
                "participation_rate": len(speaker_utterances) / total_utterances if total_utterances > 0 else 0,
                "total_duration": total_duration,
                "total_words": total_words,
                "avg_words_per_utterance": total_words / len(speaker_utterances) if speaker_utterances else 0,
                "utterances": speaker_utterances
            }
        
        return {
            "meeting_id": data["meeting_id"],
            "speaker_data": dict(speaker_data),
            "speaker_stats": speaker_stats,
            "total_utterances": total_utterances
        }
    
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze speaker patterns and characteristics"""
        speaker_stats = data["speaker_stats"]
        speaker_data = data["speaker_data"]
        
        analysis_results = {}
        
        for speaker, stats in speaker_stats.items():
            # Analyze communication style
            communication_style = self._analyze_communication_style(
                speaker_data[speaker]
            )
            
            # Analyze dominance patterns
            dominance_score = self._calculate_dominance_score(stats, speaker_stats)
            
            # Analyze engagement patterns
            engagement_patterns = self._analyze_engagement_patterns(
                speaker_data[speaker]
            )
            
            # Analyze topic preferences
            topic_preferences = self._analyze_topic_preferences(
                speaker_data[speaker]
            )
            
            analysis_results[speaker] = {
                "profile": {
                    "participation_rate": stats["participation_rate"],
                    "dominance_score": dominance_score,
                    "communication_style": communication_style,
                    "avg_words_per_utterance": stats["avg_words_per_utterance"],
                    "total_speaking_time": stats["total_duration"]
                },
                "engagement_patterns": engagement_patterns,
                "topic_preferences": topic_preferences,
                "interaction_patterns": self._analyze_interaction_patterns(
                    speaker, speaker_data
                )
            }
        
        return {
            "speakers": analysis_results,
            "meeting_summary": self._generate_meeting_summary(speaker_stats),
            "confidence": 0.85
        }
    
    def _analyze_communication_style(self, utterances: List[Dict[str, Any]]) -> str:
        """Analyze communication style based on utterance patterns"""
        if not utterances:
            return "Unknown"
        
        # Analyze sentence patterns
        question_count = 0
        statement_count = 0
        avg_length = 0
        
        for utterance in utterances:
            text = utterance.get("text", "")
            if text.endswith("?"):
                question_count += 1
            else:
                statement_count += 1
            avg_length += len(text.split())
        
        avg_length = avg_length / len(utterances) if utterances else 0
        
        # Determine style based on patterns
        if question_count > statement_count * 0.3:
            return "질문형"
        elif avg_length > 20:
            return "상세형"
        elif avg_length < 10:
            return "간결형"
        else:
            return "균형형"
    
    def _calculate_dominance_score(self, speaker_stats: Dict[str, Any], 
                                 all_speaker_stats: Dict[str, Any]) -> float:
        """Calculate dominance score based on participation and influence"""
        participation_rate = speaker_stats["participation_rate"]
        
        # Calculate relative dominance
        max_participation = max(stats["participation_rate"] 
                              for stats in all_speaker_stats.values())
        
        if max_participation > 0:
            dominance_score = participation_rate / max_participation
        else:
            dominance_score = 0.0
        
        return round(dominance_score, 2)
    
    def _analyze_engagement_patterns(self, utterances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze engagement patterns over time"""
        if not utterances:
            return {}
        
        # Analyze timing patterns
        timestamps = [u.get("timestamp", 0) for u in utterances]
        intervals = []
        
        for i in range(1, len(timestamps)):
            interval = timestamps[i] - timestamps[i-1]
            intervals.append(interval)
        
        avg_interval = sum(intervals) / len(intervals) if intervals else 0
        
        # Determine engagement level
        if avg_interval < 30:  # Less than 30 seconds between utterances
            engagement_level = "높음"
        elif avg_interval < 120:  # Less than 2 minutes
            engagement_level = "보통"
        else:
            engagement_level = "낮음"
        
        return {
            "engagement_level": engagement_level,
            "avg_response_time": avg_interval,
            "utterance_frequency": len(utterances) / (timestamps[-1] - timestamps[0]) if len(timestamps) > 1 else 0
        }
    
    def _analyze_topic_preferences(self, utterances: List[Dict[str, Any]]) -> List[str]:
        """Analyze topic preferences based on keyword frequency"""
        if not utterances:
            return []
        
        # Extract keywords from utterances
        all_text = " ".join(u.get("text", "") for u in utterances)
        
        # Define topic keywords
        topic_keywords = {
            "기술": ["기술", "개발", "코드", "프로그램", "시스템", "플랫폼"],
            "프로젝트 관리": ["일정", "마감", "계획", "진행", "관리", "스케줄"],
            "비즈니스": ["매출", "수익", "고객", "시장", "전략", "비즈니스"],
            "팀워크": ["협력", "팀", "소통", "의견", "합의", "토론"],
            "품질": ["품질", "테스트", "검증", "확인", "점검", "검토"]
        }
        
        topic_scores = {}
        for topic, keywords in topic_keywords.items():
            score = sum(all_text.count(keyword) for keyword in keywords)
            topic_scores[topic] = score
        
        # Return top 3 topics
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, score in sorted_topics[:3] if score > 0]
    
    def _analyze_interaction_patterns(self, speaker: str, 
                                   speaker_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Analyze how the speaker interacts with others"""
        # This is a simplified analysis - can be enhanced with more sophisticated NLP
        return {
            "interaction_style": "협력적",  # Placeholder
            "response_patterns": "즉시",    # Placeholder
            "collaboration_level": "높음"   # Placeholder
        }
    
    def _generate_meeting_summary(self, speaker_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Generate meeting-level speaker summary"""
        total_speakers = len(speaker_stats)
        participation_rates = [stats["participation_rate"] for stats in speaker_stats.values()]
        
        return {
            "total_speakers": total_speakers,
            "most_active_speaker": max(speaker_stats.items(), 
                                     key=lambda x: x[1]["participation_rate"])[0],
            "participation_balance": "균형" if max(participation_rates) - min(participation_rates) < 0.3 else "불균형",
            "avg_participation_rate": sum(participation_rates) / len(participation_rates) if participation_rates else 0
        }
    
    def get_capabilities(self) -> List[str]:
        return [
            "화자별 발화 패턴 분석",
            "참여도 및 지배력 분석",
            "의사소통 스타일 분석",
            "주제별 관심도 분석",
            "상호작용 패턴 분석"
        ]
    
    def get_requirements(self) -> List[str]:
        return ["meeting_id", "utterances"] 