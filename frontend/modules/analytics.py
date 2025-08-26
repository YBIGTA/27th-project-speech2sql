<<<<<<< HEAD
=======
<<<<<<< HEAD
# 분석 대시보드
=======
# 분석 대시보드

# 임시
>>>>>>> 88af335c9844ef7d6b0732c0dbc3330b6d0f691e
import streamlit as st
import requests
import json
from datetime import datetime
import os
from typing import Dict

<<<<<<< HEAD
@st.cache_data(ttl=30)
def _fetch_meetings() -> Dict[str, int]:
    try:
        r = requests.get(f"{API_BASE_URL}/query/meetings", timeout=10)
        if r.status_code == 200:
            data = r.json().get("meetings", [])
            # map title (display) to id
            return {f"{m.get('title')} (id:{m.get('id')})": m.get('id') for m in data}
    except Exception:
        pass
    return {}


def analyze_meetings():
    st.header("🤖 멀티에이전트 분석")
    st.caption("AI 에이전트들이 회의 내용을 심도 있게 분석하여 인사이트를 제공합니다.")
    
    # Meeting selection
    meetings_map = _fetch_meetings()
    if not meetings_map:
        st.warning("분석할 회의가 없습니다. 먼저 오디오 파일을 업로드해주세요.")
        return
    
    st.subheader("📋 회의 선택")
    meeting_titles = list(meetings_map.keys())
    selected_meeting = st.selectbox(
        "분석할 회의를 선택하세요",
        meeting_titles,
        help="업로드된 회의 목록에서 선택하세요"
    )
    
    if selected_meeting:
        meeting_id = meetings_map[selected_meeting]
        
        # Run analysis button
        if st.button("🚀 분석 시작", type="primary", use_container_width=True):
            with st.spinner("AI 에이전트들이 분석을 수행하고 있습니다..."):
                try:
                    payload = {
                        "meeting_id": meeting_id,
                        "analysis_type": "comprehensive"
                    }
                    
                    response = requests.post(f"{API_BASE_URL}/analysis/comprehensive", 
                                           json=payload, timeout=120)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success("✅ 분석이 완료되었습니다!")
                        
                        # Display comprehensive analysis results
                        _display_comprehensive_analysis(result)
                    else:
                        st.error(f"분석 실패: {response.status_code} {response.text}")
                        
                except Exception as e:
                    st.error(f"분석 중 오류가 발생했습니다: {e}")


def _display_comprehensive_analysis(result):
    """Display comprehensive analysis results"""
    st.subheader("📊 종합 분석 결과")
    
    # Executive summary
    if "executive_summary" in result:
        st.success("📋 실행 요약")
        st.write(result["executive_summary"])
        st.divider()
    
    # Detailed analysis
    if "comprehensive_analysis" in result:
        st.subheader("🔍 상세 분석")
        analysis = result["comprehensive_analysis"]
        
        # Speaker insights
        if "speaker_insights" in analysis:
            with st.expander("👥 화자 분석 결과"):
                speaker_insights = analysis["speaker_insights"]
                if "speaker_profiles" in speaker_insights:
                    speakers = speaker_insights["speaker_profiles"]
                    for speaker, profile in speakers.items():
                        st.write(f"**{speaker}**:")
                        st.write(f"- 참여도: {profile['profile']['participation_rate']:.1%}")
                        st.write(f"- 의사소통 스타일: {profile['profile']['communication_style']}")
                        st.write(f"- 주제 관심도: {', '.join(profile['topic_preferences'])}")
                        st.divider()
        
        # Agenda insights
        if "agenda_insights" in analysis:
            agenda_insights = analysis["agenda_insights"]
            if "agenda_analysis" in agenda_insights:
                agendas = agenda_insights["agenda_analysis"]
                
                # Individual agenda analysis
                st.subheader("🔍 안건별 결정사항")
                
                for agenda_id, agenda_data in agendas.items():
                    agenda_info = agenda_data.get('agenda_info', {})
                    consensus = agenda_data.get("consensus", {})
                    decisions = agenda_data.get("decisions", [])
                    summary = agenda_data.get("summary", "")
                    
                    # 결정사항이 있는 안건만 표시
                    if not decisions:
                        continue
                    
                    # 안건 제목을 짧게 요약
                    title = agenda_info.get('title', 'Unknown')
                    if len(title) > 30:
                        title = title[:30] + "..."
                    
                    # Consensus level에 따른 색상 설정
                    consensus_level = consensus.get('level', '불명확')
                    if consensus_level == '높음':
                        consensus_color = "🟢"
                    elif consensus_level == '보통':
                        consensus_color = "🟡"
                    else:
                        consensus_color = "🔴"
                    
                    with st.expander(f"{consensus_color} {title}"):
                        # 합의 수준
                        consensus_score = consensus.get('score', 0)
                        st.write(f"**🤝 합의 수준**: {consensus_level} ({consensus_score:.1%})")
                        
                        # 결정사항 (합의 수준별로 정렬되어 있음)
                        st.write("**✅ 결정사항:**")
                        
                        # 합의 수준별로 그룹화
                        high_consensus = [d for d in decisions if d.get('consensus_score', 0) > 0.7]
                        medium_consensus = [d for d in decisions if 0.4 <= d.get('consensus_score', 0) <= 0.7]
                        low_consensus = [d for d in decisions if d.get('consensus_score', 0) < 0.4]
                        
                        if high_consensus:
                            st.write("**🟢 높은 합의 결정사항:**")
                            for i, decision in enumerate(high_consensus, 1):
                                st.write(f"  {i}. {decision.get('content', 'N/A')}")
                        
                        if medium_consensus:
                            st.write("**🟡 보통 합의 결정사항:**")
                            for i, decision in enumerate(medium_consensus, 1):
                                st.write(f"  {i}. {decision.get('content', 'N/A')}")
                        
                        if low_consensus:
                            st.write("**🔴 낮은 합의 결정사항:**")
                            for i, decision in enumerate(low_consensus, 1):
                                st.write(f"  {i}. {decision.get('content', 'N/A')}")
=======
class Analytics:
>>>>>>> f4019648f6d7bc1c24203184b859f5e6aca469a8
>>>>>>> 88af335c9844ef7d6b0732c0dbc3330b6d0f691e
