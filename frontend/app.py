"""
Streamlit main application for Speech2SQL
"""
import streamlit as st
import requests
import json
from datetime import datetime
import os
<<<<<<< HEAD
from typing import Dict

from modules.upload import upload_file
<<<<<<< HEAD
from modules.search import search_meetings, _fetch_meetings
from modules.analytics import analyze_meetings, _display_comprehensive_analysis
=======
from modules.search import search_by_natural_language, _fetch_meetings
=======
# from modules.upload import Upload
# from modules.search import Search
# from modules.analytics import Analytics
>>>>>>> f4019648f6d7bc1c24203184b859f5e6aca469a8
>>>>>>> 88af335c9844ef7d6b0732c0dbc3330b6d0f691e

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
    .feature-fard:hover {
        cursor: pointer;
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
<<<<<<< HEAD
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
    .stSelectbox > div:focus-within {
        border-color: #145a86;
=======
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
>>>>>>> f4019648f6d7bc1c24203184b859f5e6aca469a8
    }
</style>
""", unsafe_allow_html=True)

# API configuration
API_BASE_URL = "http://localhost:8000/api/v1"


def main():
    """Main application"""
    
    # Header
    st.markdown('<h1 class="main-header">🎤 Speech2SQL 📑</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">강의·회의록 생성 및 검색 시스템</p>', unsafe_allow_html=True)
    
    # Sidebar navigation
    # st.sidebar.title("📋 메뉴")
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
    st.header("📱 기능 소개")
    
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
<<<<<<< HEAD
    upload_file()

=======
<<<<<<< HEAD
    upload_file()
=======
    st.header("📁 파일 업로드")
    
    # Upload form
    with st.form("upload_form"):
        uploaded_file = st.file_uploader(
            "오디오 파일 선택",
            type=['wav', 'mp3', 'm4a'],
            help="지원 형식: WAV, MP3, M4A (최대 100MB)"
        )
        
        title = st.text_input("회의 제목", placeholder="예: 팀 프로젝트 기획 회의")
        
        participants = st.text_area(
            "참가자 목록",
            placeholder="참가자 이름을 줄바꿈으로 구분하여 입력하세요 \n예:\n김철수\n이영희\n박민수"
        )
        
        submitted = st.form_submit_button("업로드 및 처리 시작")
        
        if submitted and uploaded_file:
            # TODO: Implement file upload to API
            st.success(f"파일 '{uploaded_file.name}' 업로드 완료!")
            st.info("음성 인식 및 요약 처리가 진행 중입니다. 잠시만 기다려주세요.")
>>>>>>> f4019648f6d7bc1c24203184b859f5e6aca469a8
>>>>>>> 88af335c9844ef7d6b0732c0dbc3330b6d0f691e


def show_search_page():
    """Natural language search page"""
<<<<<<< HEAD
    search_meetings()

def show_agent_analysis_page():
    """Multi-agent analysis page"""
    analyze_meetings()
=======
    search_by_natural_language()


def show_analytics_page():
    """Analytics dashboard page"""
    st.header("📊 분석 대시보드")
    st.info("향후 구현 예정")
>>>>>>> 88af335c9844ef7d6b0732c0dbc3330b6d0f691e


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
    
<<<<<<< HEAD
    if selected_meeting:
        meeting_id = meetings_map[selected_meeting]
=======
    summary_type = st.selectbox(
        "요약 유형",
        ["일반 요약", "액션 아이템", "결정사항"]
    )
    
    if st.button("▶️ 요약 생성", type="primary"):
        # TODO: Implement summary generation
        st.success("요약 생성이 시작되었습니다!")
>>>>>>> f4019648f6d7bc1c24203184b859f5e6aca469a8
        
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
                    duration_minutes = round (meeting_info.get('duration', 0) / 60, 1)
                    st.metric("회의 시간", f"{duration_minutes}분")
                
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