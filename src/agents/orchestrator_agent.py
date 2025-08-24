"""
Orchestrator Agent - Coordinates all analysis agents and generates final insights
"""
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime
from src.agents.base_agent import BaseAgent, AgentType, AgentResult
from src.agents.speaker_analysis_agent import SpeakerAnalysisAgent
from src.agents.agenda_analysis_agent import AgendaAnalysisAgent
from config.settings import settings
import requests


class OrchestratorAgent(BaseAgent):
    """Agent for orchestrating all analysis agents and generating final insights"""
    
    def __init__(self):
        super().__init__(AgentType.ORCHESTRATOR, "OrchestratorAgent")
        self.speaker_agent = SpeakerAnalysisAgent()
        self.agenda_agent = AgendaAnalysisAgent()
        
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input data contains required fields"""
        required_fields = ["meeting_id", "utterances"]
        return all(field in data for field in required_fields)
    
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate all agents and generate comprehensive analysis"""
        start_time = datetime.now()
        
        # Execute all agents in parallel
        tasks = [
            self.speaker_agent.execute(data),
            self.agenda_agent.execute(data)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        speaker_result = results[0] if not isinstance(results[0], Exception) else None
        agenda_result = results[1] if not isinstance(results[1], Exception) else None
        
        # Generate comprehensive analysis
        comprehensive_analysis = await self._generate_comprehensive_analysis(
            data, speaker_result, agenda_result
        )
        
        # Generate insights and recommendations
        insights = self._generate_insights(comprehensive_analysis)
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(comprehensive_analysis)
        
        return {
            "comprehensive_analysis": comprehensive_analysis,
            "insights": insights,
            "executive_summary": executive_summary,
            "agent_results": {
                "speaker_analysis": speaker_result.result_data if speaker_result else None,
                "agenda_analysis": agenda_result.result_data if agenda_result else None
            },
            "processing_metadata": {
                "total_processing_time": (datetime.now() - start_time).total_seconds(),
                "agents_executed": 2,
                "successful_agents": sum(1 for r in results if not isinstance(r, Exception))
            },
            "confidence": 0.90
        }
    
    async def _generate_comprehensive_analysis(self, data: Dict[str, Any], 
                                            speaker_result: Optional[AgentResult],
                                            agenda_result: Optional[AgentResult]) -> Dict[str, Any]:
        """Generate comprehensive analysis combining all agent results"""
        meeting_id = data["meeting_id"]
        utterances = data["utterances"]
        
        comprehensive = {
            "meeting_id": meeting_id,
            "analysis_timestamp": datetime.now().isoformat(),
            "total_utterances": len(utterances),
            "unique_speakers": len(set(u.get("speaker") for u in utterances)),
            "meeting_duration": self._calculate_meeting_duration(utterances)
        }
        
        # Integrate speaker analysis
        if speaker_result:
            speaker_data = speaker_result.result_data
            comprehensive["speaker_insights"] = {
                "speaker_profiles": speaker_data.get("speakers", {}),
                "meeting_dynamics": speaker_data.get("meeting_summary", {}),
                "key_insights": self._extract_speaker_insights(speaker_data)
            }
        
        # Integrate agenda analysis
        if agenda_result:
            agenda_data = agenda_result.result_data
            comprehensive["agenda_insights"] = {
                "agenda_analysis": agenda_data.get("agendas", {}),
                "meeting_overview": agenda_data.get("meeting_overview", {}),
                "key_insights": self._extract_agenda_insights(agenda_data)
            }
        
        # Generate cross-analysis insights
        comprehensive["cross_analysis"] = self._generate_cross_analysis(
            speaker_result, agenda_result
        )
        
        return comprehensive
    
    def _calculate_meeting_duration(self, utterances: List[Dict[str, Any]]) -> float:
        """Calculate total meeting duration"""
        if not utterances:
            return 0.0
        
        timestamps = [u.get("timestamp", 0) for u in utterances]
        return max(timestamps) - min(timestamps)
    
    def _extract_speaker_insights(self, speaker_data: Dict[str, Any]) -> List[str]:
        """Extract key insights from speaker analysis"""
        insights = []
        speakers = speaker_data.get("speakers", {})
        meeting_summary = speaker_data.get("meeting_summary", {})
        
        if speakers:
            # Find most active speaker
            most_active = max(speakers.items(), 
                            key=lambda x: x[1]["profile"]["participation_rate"])
            insights.append(f"가장 활발한 참여자: {most_active[0]} (참여도: {most_active[1]['profile']['participation_rate']:.1%})")
            
            # Find dominant speaker
            most_dominant = max(speakers.items(), 
                              key=lambda x: x[1]["profile"]["dominance_score"])
            insights.append(f"가장 영향력 있는 참여자: {most_dominant[0]} (지배력: {most_dominant[1]['profile']['dominance_score']:.2f})")
            
            # Communication style diversity
            styles = [s["profile"]["communication_style"] for s in speakers.values()]
            unique_styles = len(set(styles))
            insights.append(f"의사소통 스타일 다양성: {unique_styles}가지 유형")
        
        if meeting_summary:
            balance = meeting_summary.get("participation_balance", "Unknown")
            insights.append(f"참여도 균형: {balance}")
        
        return insights
    
    def _extract_agenda_insights(self, agenda_data: Dict[str, Any]) -> List[str]:
        """Extract key insights from agenda analysis"""
        insights = []
        agendas = agenda_data.get("agendas", {})
        meeting_overview = agenda_data.get("meeting_overview", {})
        
        if agendas and isinstance(agendas, dict):
            # Most discussed agenda
            try:
                most_discussed = max(agendas.items(), 
                                   key=lambda x: x[1].get("discussion_patterns", {}).get("total_utterances", 0))
                insights.append(f"가장 활발히 논의된 안건: {most_discussed[1].get('agenda_info', {}).get('title', 'Unknown')}")
            except (ValueError, KeyError):
                insights.append("안건별 논의 패턴을 분석할 수 없습니다.")
            
            # Consensus levels
            try:
                consensus_levels = [agenda.get("consensus", {}).get("level", "불명확") for agenda in agendas.values()]
                high_consensus_count = consensus_levels.count("높음")
                insights.append(f"높은 합의 수준 안건: {high_consensus_count}개")
            except (KeyError, AttributeError):
                insights.append("합의 수준을 분석할 수 없습니다.")
        
        if meeting_overview:
            total_decisions = meeting_overview.get("total_decisions", 0)
            insights.append(f"총 결정사항: {total_decisions}개")
        
        return insights
    
    def _generate_cross_analysis(self, speaker_result: Optional[AgentResult],
                               agenda_result: Optional[AgentResult]) -> Dict[str, Any]:
        """Generate cross-analysis between speaker and agenda results"""
        cross_analysis = {
            "speaker_agenda_correlation": {},
            "participation_patterns": {},
            "decision_making_patterns": {}
        }
        
        if speaker_result and agenda_result:
            speaker_data = speaker_result.result_data
            agenda_data = agenda_result.result_data
            
            # Analyze speaker participation across agendas
            speakers = speaker_data.get("speakers", {})
            agendas = agenda_data.get("agendas", {})
            
            # Find speakers who are most active in decision-making
            decision_speakers = {}
            for agenda_id, agenda_info in agendas.items():
                decisions = agenda_info.get("decisions", [])
                for decision in decisions:
                    speaker = decision.get("speaker")
                    if speaker:
                        decision_speakers[speaker] = decision_speakers.get(speaker, 0) + 1
            
            if decision_speakers:
                most_decision_maker = max(decision_speakers.items(), key=lambda x: x[1])
                cross_analysis["decision_making_patterns"]["most_decision_maker"] = {
                    "speaker": most_decision_maker[0],
                    "decision_count": most_decision_maker[1]
                }
        
        return cross_analysis
    
    def _generate_insights(self, comprehensive_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate actionable insights"""
        insights = {
            "meeting_effectiveness": {},
            "participation_insights": {},
            "decision_quality": {}
        }
        
        # Meeting effectiveness analysis
        speaker_insights = comprehensive_analysis.get("speaker_insights", {})
        agenda_insights = comprehensive_analysis.get("agenda_insights", {})
        
        # Participation insights
        if speaker_insights:
            meeting_dynamics = speaker_insights.get("meeting_dynamics", {})
            balance = meeting_dynamics.get("participation_balance", "Unknown")
            
            if balance == "불균형":
                insights["participation_insights"]["warning"] = "참여도 불균형이 감지되었습니다."
            else:
                insights["participation_insights"]["positive"] = "참여도가 균형잡혀 있습니다."
        
        # Decision quality analysis
        if agenda_insights:
            meeting_overview = agenda_insights.get("meeting_overview", {})
            total_decisions = meeting_overview.get("total_decisions", 0)
            avg_consensus = meeting_overview.get("avg_consensus", 0)
            
            if total_decisions > 0:
                insights["decision_quality"]["decision_count"] = f"총 {total_decisions}개의 결정사항이 도출되었습니다."
                
                if avg_consensus > 0.7:
                    insights["decision_quality"]["consensus"] = "높은 합의 수준으로 결정이 이루어졌습니다."
                elif avg_consensus < 0.4:
                    insights["decision_quality"]["warning"] = "낮은 합의 수준으로 추가 논의가 필요할 수 있습니다."
        
        # Meeting efficiency
        total_utterances = comprehensive_analysis.get("total_utterances", 0)
        meeting_duration = comprehensive_analysis.get("meeting_duration", 0)
        
        if meeting_duration > 0:
            utterance_rate = total_utterances / (meeting_duration / 60)  # utterances per minute
            if utterance_rate < 2:
                insights["meeting_effectiveness"]["warning"] = "회의 진행 속도가 느립니다."
            elif utterance_rate > 10:
                insights["meeting_effectiveness"]["warning"] = "회의 진행 속도가 빠릅니다."
        
        return insights
    
    def _generate_executive_summary(self, comprehensive_analysis: Dict[str, Any]) -> str:
        """Generate executive summary of the meeting analysis"""
        summary_parts = []
        
        # Basic meeting info
        total_utterances = comprehensive_analysis.get("total_utterances", 0)
        unique_speakers = comprehensive_analysis.get("unique_speakers", 0)
        meeting_duration = comprehensive_analysis.get("meeting_duration", 0)
        
        summary_parts.append(f"이 회의는 {unique_speakers}명의 참가자가 {meeting_duration/60:.1f}분 동안 진행되었으며, 총 {total_utterances}개의 발화가 있었습니다.")
        
        # Speaker insights
        speaker_insights = comprehensive_analysis.get("speaker_insights", {})
        if speaker_insights:
            meeting_dynamics = speaker_insights.get("meeting_dynamics", {})
            balance = meeting_dynamics.get("participation_balance", "Unknown")
            summary_parts.append(f"참가자들의 참여도는 {balance}한 상태였습니다.")
        
        # Agenda insights
        agenda_insights = comprehensive_analysis.get("agenda_insights", {})
        if agenda_insights:
            meeting_overview = agenda_insights.get("meeting_overview", {})
            total_agendas = meeting_overview.get("total_agendas", 0)
            total_decisions = meeting_overview.get("total_decisions", 0)
            avg_consensus = meeting_overview.get("avg_consensus", 0)
            
            summary_parts.append(f"총 {total_agendas}개의 안건이 논의되었으며, {total_decisions}개의 결정사항이 도출되었습니다.")
            summary_parts.append(f"전체적인 합의 수준은 {avg_consensus:.1%}였습니다.")
        
        # Cross-analysis insights
        cross_analysis = comprehensive_analysis.get("cross_analysis", {})
        decision_patterns = cross_analysis.get("decision_making_patterns", {})
        if decision_patterns:
            most_decision_maker = decision_patterns.get("most_decision_maker")
            if most_decision_maker:
                summary_parts.append(f"가장 많은 결정을 주도한 참가자는 {most_decision_maker['speaker']}입니다.")
        
        return " ".join(summary_parts)
    
    def get_capabilities(self) -> List[str]:
        return [
            "멀티 에이전트 조율",
            "종합 분석 생성",
            "인사이트 추출",
            "실행 요약 생성"
        ]
    
    def get_requirements(self) -> List[str]:
        return ["meeting_id", "utterances"] 