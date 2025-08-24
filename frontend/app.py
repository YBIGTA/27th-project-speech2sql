"""
Streamlit main application for Speech2SQL
"""
import streamlit as st
import requests
import json
from datetime import datetime
import os
from typing import Dict

# Page configuration
st.set_page_config(
    page_title="Speech2SQL - 강의·회의록 생성 및 검색 시스템",
    page_icon="📑",
    layout="wide",
    initial_sidebar_state="auto"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #666;
        text-align: center;
        margin-bottom: 3rem;
    }
    .feature-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .upload-area {
        border: 2px dashed #ccc;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background-color: #fafafa;
    }
    .upload-area:hover {
        cursor: pointer;
    }
    .stButton > button {
        background-color: #1f77b4;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-weight: bold;
        transition: background-color 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #145a86;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# API configuration
API_BASE_URL = "http://localhost:8000/api/v1"


def main():
    """Main application"""
    
    # Header
    st.markdown('<h1 class="main-header">🎤 Speech2SQL</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">강의·회의록 생성 및 검색 시스템</p>', unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("📋 메뉴")
    page = st.sidebar.selectbox(
        "페이지 선택",
        ["🏠 홈", "📁 파일 업로드", "🔍 자연어 검색", "🤖 멀티에이전트 분석", "📄 요약 생성"]
    )
    
    # Page routing
    if page == "🏠 홈":
        show_home_page()
    elif page == "📁 파일 업로드":
        show_upload_page()
    elif page == "🔍 자연어 검색":
        show_search_page()
    elif page == "🤖 멀티에이전트 분석":
        show_agent_analysis_page()
    elif page == "📄 요약 생성":
        show_summary_page()


def show_home_page():
    """Home page content"""
    st.header("🏠 환영합니다!")
    
    # Features overview
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>🎵 오디오 처리</h3>
            <p>Whisper STT와 Speaker Diarization을 통한 정확한 음성 인식</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <h3>🧠 자연어 처리</h3>
            <p>PEGASUS/LLaMA2 기반 요약 및 Text2SQL 변환</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>🗄️ 데이터베이스</h3>
            <p>구조화된 데이터 저장 및 고속 검색</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <h3>🤖 멀티에이전트 분석</h3>
            <p>AI 에이전트들이 화자별/안건별 심도 있는 분석 제공</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick start guide
    st.header("🚀 빠른 시작")
    st.markdown("""
    1. **파일 업로드**: 강의나 회의 녹음 파일을 업로드하세요
    2. **자동 처리**: STT와 요약이 자동으로 생성됩니다
    3. **자연어 검색**: 원하는 정보를 자연어로 검색하세요
    4. **멀티에이전트 분석**: AI 에이전트들이 심도 있는 분석을 제공합니다
    """)


def show_upload_page():
    """File upload page"""
    st.header("📁 파일 업로드")
    
    # Upload form
    with st.form("upload_form"):
        uploaded_file = st.file_uploader(
            "오디오 파일 선택",
            type=['wav'],
            help="지원 형식: WAV (최대 100MB)"
        )
        title = st.text_input("회의 제목", placeholder="예: 팀 프로젝트 기획 회의")
        
        # Meeting date selection
        meeting_date = st.date_input(
            "회의 날짜",
            value=datetime.now().date(),
            help="실제 회의가 진행된 날짜를 선택하세요"
        )
        
        participants_text = st.text_area(
            "참가자 목록",
            placeholder="참가자 이름을 줄바꿈으로 구분하여 입력하세요\n예:\n김철수\n이영희\n박민수"
        )
        submitted = st.form_submit_button("업로드 및 처리 시작")

        if submitted:
            if not uploaded_file:
                st.error("파일을 선택하세요.")
                return
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "application/octet-stream")}
            data = {
                "title": title,
                "meeting_date": meeting_date.isoformat(),
                "participants": participants_text.strip().split('\n') if participants_text.strip() else []
            }
            try:
                resp = requests.post(f"{API_BASE_URL}/audio/upload", files=files, data=data, timeout=600)
                if resp.status_code == 200:
                    j = resp.json()
                    st.success(f"업로드 성공: segments={j.get('segments')} 파일={j.get('filename')}")
                else:
                    st.error(f"업로드 실패: {resp.status_code} {resp.text}")
            except Exception as e:
                st.error(f"요청 오류: {e}")


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


def show_search_page():
    """Natural language search page"""
    st.header("🔍 자연어 검색")
    
    query = st.text_input("검색어 입력", placeholder="예: 누가 프로젝트 일정에 대해 언급했나요?")
    st.caption("💡 자연어로 질문하시면 AI가 음성 기록 내용을 분석하여 답변해드립니다.")

    meetings_map = _fetch_meetings()
    titles = ["전체(미지정)"] + list(meetings_map.keys())
    sel = st.selectbox("회의 선택(선택)", titles, index=0, help="text2sql 모드에서는 회의 지정 시 해당 회의로 범위를 제한합니다.")
    selected_meeting_id = None if sel == "전체(미지정)" else meetings_map.get(sel)

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        mode = st.selectbox("검색 모드", ["text2sql", "fts"], index=0, help="text2sql: NL→SQL, fts: Full-Text Search")
    with col2:
        limit = st.selectbox("결과 수", [5, 10, 20, 50], index=0)
    with col3:
        run = st.button("🔍 검색", type="primary")

    if run and query:
        st.info("검색 중...")
        try:
            payload = {"query": query, "limit": int(limit), "mode": mode}
            if selected_meeting_id:
                payload["meeting_id"] = int(selected_meeting_id)
            resp = requests.post(f"{API_BASE_URL}/query/natural", json=payload, timeout=60)
            if resp.status_code == 200:
                j = resp.json()
                st.subheader("검색 결과")
                
                # Display natural language answer prominently
                answer = j.get('answer')
                if answer:
                    st.success("🤖 AI 답변")
                    st.write(answer)
                    st.divider()
                
                # Display technical details in collapsible section
                with st.expander("🔧 기술적 세부사항"):
                    st.caption(f"SQL: {j.get('sql_query')}")
                    st.caption(f"총 {j.get('total_count')}건, 실행 {j.get('execution_time')}s")
                
                # Display source utterances
                results = j.get("results", [])
                if results:
                    st.subheader("📋 참고 발화")
                    for i, r in enumerate(results[:5], start=1):  # Show first 5 results
                        with st.expander(f"발화 {i}"):
                            st.markdown(f"**발화자**: {r.get('speaker','-')}")
                            st.markdown(f"**시간**: {r.get('timestamp','-')}")
                            st.markdown(f"**내용**: {r.get('text','')}")
                            st.markdown(f"**회의**: {r.get('meeting_title','-')}")
                    
                    if len(results) > 5:
                        st.info(f"... 및 {len(results) - 5}개의 추가 발화가 있습니다.")
            else:
                st.error(f"검색 실패: {resp.status_code} {resp.text}")
        except Exception as e:
            st.error(f"요청 오류: {e}")


def show_agent_analysis_page():
    """Multi-agent analysis page"""
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








def show_summary_page():
    """Summary generation page"""
    st.header("📄 요약 생성")
    
    # Meeting selection
    meetings_map = _fetch_meetings()
    if not meetings_map:
        st.warning("생성된 회의가 없습니다. 먼저 오디오 파일을 업로드해주세요.")
        return
    
    st.subheader("📋 회의 선택")
    meeting_titles = list(meetings_map.keys())
    selected_meeting = st.selectbox(
        "요약을 생성할 회의를 선택하세요",
        meeting_titles,
        help="업로드된 회의 목록에서 선택하세요"
    )
    
    if selected_meeting:
        meeting_id = meetings_map[selected_meeting]
        
        # Get meeting details
        try:
            response = requests.get(f"{API_BASE_URL}/summary/meeting/{meeting_id}", timeout=10)
            if response.status_code == 200:
                meeting_info = response.json()
                
                # Display meeting info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("회의 제목", meeting_info.get('title', 'N/A'))
                with col2:
                    st.metric("회의 날짜", meeting_info.get('date', 'N/A')[:10] if meeting_info.get('date') else 'N/A')
                with col3:
                    st.metric("회의 시간", f"{meeting_info.get('duration', 0)}분")
                
                # Participants
                participants = meeting_info.get('participants', [])
                if participants:
                    st.write("**참가자:**", ", ".join(participants))
                
                st.divider()
                
                # Summary generation
                st.subheader("🔄 요약 생성")
                
                # Language selection only
                language = st.selectbox(
                    "언어 선택",
                    ["ko", "en"],
                    format_func=lambda x: {"ko": "🇰🇷 한국어", "en": "🇺🇸 English"}.get(x, x)
                )
                
                # Generate summary button
                if st.button("📝 요약 생성", type="primary", use_container_width=True):
                    with st.spinner("요약을 생성하고 있습니다..."):
                        try:
                            payload = {
                                "meeting_id": meeting_id,
                                "summary_type": "general",  # Always use general summary
                                "language": language
                            }
                            response = requests.post(f"{API_BASE_URL}/summary/generate", json=payload, timeout=120)
                            
                            if response.status_code == 200:
                                summary_data = response.json()
                                # Store summary data in session state
                                st.session_state.summary_data = summary_data
                                st.session_state.show_summary = True
                                st.success("✅ 요약이 성공적으로 생성되었습니다!")
                                st.rerun()
                            else:
                                st.error(f"요약 생성 실패: {response.status_code} {response.text}")
                        except Exception as e:
                            st.error(f"요청 중 오류가 발생했습니다: {e}")
                
                # Display summary if available in session state
                if hasattr(st.session_state, 'show_summary') and st.session_state.show_summary and hasattr(st.session_state, 'summary_data'):
                    summary_data = st.session_state.summary_data
                    
                    # Display generated summary
                    st.subheader("📋 생성된 요약")
                    
                    # Show meeting title in bold
                    meeting_title = meeting_info.get('title', '')
                    if meeting_title:
                        st.markdown(f"**회의 주제: {meeting_title}**")
                    
                    # Create a nice summary display
                    summary_text = summary_data.get('summary_text', '')
                    if summary_text:
                        st.markdown("""
                        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #1f77b4; margin-bottom: 20px;">
                        """, unsafe_allow_html=True)
                        st.markdown(summary_text)
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Action items
                    action_items = summary_data.get('action_items', [])
                    if action_items:
                        st.subheader("✅ 액션 아이템")
                        for item in action_items:
                            with st.expander(f"📌 {item.get('description', '')[:50]}..."):
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write(f"**담당자:** {item.get('assignee', 'N/A')}")
                                    st.write(f"**우선순위:** {item.get('priority', 'N/A')}")
                                with col2:
                                    st.write(f"**마감일:** {item.get('due_date', 'N/A')}")
                                    st.write(f"**상태:** {item.get('status', 'N/A')}")
                    
                    # Decisions with improved agreement level display
                    decisions = summary_data.get('decisions', [])
                    if decisions:
                        st.subheader("🎯 결정 사항")
                        for decision in decisions:
                            # Get agreement level and format display
                            agreement_level = decision.get('agreement_level', 100)
                            agenda_title = decision.get('agenda_title', '알 수 없음')
                            
                            # Format agreement level display
                            if agreement_level == 100:
                                agreement_text = "완전 합의"
                                color = "🟢"
                            elif agreement_level >= 80:
                                agreement_text = "높음"
                                color = "🟡"
                            elif agreement_level >= 50:
                                agreement_text = "보통"
                                color = "🟠"
                            else:
                                agreement_text = "낮음"
                                color = "🔴"
                            
                            # Display with improved format
                            st.markdown(f"**{color} {agenda_title} (합의 수준: {agreement_level}% - {agreement_text})**")
                            
                            # Show decision details
                            decision_text = decision.get('decision', '')
                            if decision_text:
                                st.write(f"• {decision_text}")
                            
                            # Show disagreement details if agreement level is not 100%
                            if agreement_level < 100:
                                disagreement_details = decision.get('disagreement_details', {})
                                consensus_reason = decision.get('consensus_reason', '')
                                
                                if disagreement_details:
                                    analysis_quality = disagreement_details.get('analysis_quality', 'unknown')
                                    
                                    with st.expander(f"⚠️ 합의되지 않은 부분 상세 분석 (합의 수준: {agreement_level}%)"):
                                        # Show consensus reason if available
                                        if consensus_reason:
                                            st.info(f"**합의 수준 판단 근거:** {consensus_reason}")
                                        
                                        # Analysis quality indicator
                                        if analysis_quality == 'llm_enhanced':
                                            st.success("🤖 AI 기반 정교한 분석")
                                        elif analysis_quality == 'rule_based':
                                            st.warning("📋 규칙 기반 기본 분석")
                                        
                                        # Who disagreed
                                        who_disagreed = disagreement_details.get('who_disagreed', [])
                                        if who_disagreed:
                                            st.write(f"**합의하지 않은 참가자:** {', '.join(who_disagreed)}")
                                        
                                        # What was disagreed
                                        what_disagreed = disagreement_details.get('what_disagreed', '')
                                        if what_disagreed:
                                            st.write(f"**합의되지 않은 내용:** {what_disagreed}")
                                        
                                        # Why disagreed
                                        why_disagreed = disagreement_details.get('why_disagreed', '')
                                        if why_disagreed:
                                            st.write(f"**합의 실패 이유:** {why_disagreed}")
                                        
                                        # Suggestions for agreement
                                        suggestions = disagreement_details.get('suggestions', '')
                                        if suggestions:
                                            st.write(f"**합의를 위한 제안:** {suggestions}")
                                else:
                                    st.info(f"⚠️ 합의 수준이 {agreement_level}%로 낮습니다. 구체적인 합의되지 않은 부분 정보가 없습니다.")
                                    
                                    if consensus_reason:
                                        st.write(f"**합의 수준 판단 근거:** {consensus_reason}")
                            
                            st.divider()
                
                st.divider()
                
                # PDF generation (secondary option)
                st.subheader("📑 PDF 다운로드")
                st.info("💡 요약을 PDF로 다운로드하려면 아래 버튼을 클릭하세요.")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("📄 PDF 생성", use_container_width=True):
                        with st.spinner("PDF를 생성하고 있습니다..."):
                            try:
                                response = requests.post(f"{API_BASE_URL}/summary/pdf/{meeting_id}", timeout=180)
                                
                                if response.status_code == 200:
                                    result = response.json()
                                    st.success("✅ PDF가 성공적으로 생성되었습니다!")
                                    st.json(result)
                                else:
                                    st.error(f"PDF 생성 실패: {response.status_code} {response.text}")
                            except Exception as e:
                                st.error(f"PDF 생성 중 오류가 발생했습니다: {e}")
                
                with col2:
                    if st.button("📥 PDF 다운로드", use_container_width=True):
                        try:
                            download_url = f"{API_BASE_URL}/summary/pdf/{meeting_id}/download"
                            st.link_button("🔗 PDF 다운로드 링크", download_url)
                            st.info("위 링크를 클릭하면 PDF 파일이 다운로드됩니다.")
                        except Exception as e:
                            st.error(f"다운로드 링크 생성 실패: {e}")
            
            else:
                st.error(f"회의 정보를 가져올 수 없습니다: {response.status_code}")
                
        except Exception as e:
            st.error(f"회의 정보 조회 중 오류가 발생했습니다: {e}")


if __name__ == "__main__":
    main() 