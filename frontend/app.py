"""
Streamlit main application for Speech2SQL
"""
import streamlit as st
import requests
import json
from datetime import datetime
import os

# Page configuration
st.set_page_config(
    page_title="Speech2SQL - 강의·회의록 생성 및 검색 시스템",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
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
        ["🏠 홈", "📁 파일 업로드", "🔍 자연어 검색", "📊 분석 대시보드", "📄 요약 생성"]
    )
    
    # Page routing
    if page == "🏠 홈":
        show_home_page()
    elif page == "📁 파일 업로드":
        show_upload_page()
    elif page == "🔍 자연어 검색":
        show_search_page()
    elif page == "📊 분석 대시보드":
        show_analytics_page()
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
            <h3>📊 인사이트</h3>
            <p>회의 패턴 분석 및 효율성 지표 제공</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick start guide
    st.header("🚀 빠른 시작")
    st.markdown("""
    1. **파일 업로드**: 강의나 회의 녹음 파일을 업로드하세요
    2. **자동 처리**: STT와 요약이 자동으로 생성됩니다
    3. **자연어 검색**: 원하는 정보를 자연어로 검색하세요
    4. **분석 확인**: 회의 패턴과 인사이트를 확인하세요
    """)


def show_upload_page():
    """File upload page"""
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
            placeholder="참가자 이름을 줄바꿈으로 구분하여 입력하세요\n예:\n김철수\n이영희\n박민수"
        )
        
        submitted = st.form_submit_button("업로드 및 처리 시작")
        
        if submitted and uploaded_file:
            # TODO: Implement file upload to API
            st.success(f"파일 '{uploaded_file.name}' 업로드 완료!")
            st.info("음성 인식 및 요약 처리가 진행 중입니다. 잠시만 기다려주세요.")


def show_search_page():
    """Natural language search page"""
    st.header("🔍 자연어 검색")
    
    # Search interface
    query = st.text_input(
        "검색어 입력",
        placeholder="예: 누가 프로젝트 일정에 대해 언급했나요?"
    )
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_button = st.button("🔍 검색", type="primary")
    
    with col2:
        limit = st.selectbox("결과 수", [5, 10, 20, 50])
    
    if search_button and query:
        # TODO: Implement search API call
        st.info("검색 중...")
        
        # Mock results
        st.subheader("검색 결과")
        st.markdown(f"**검색어**: {query}")
        st.markdown(f"**결과 수**: 3개")
        
        for i in range(3):
            with st.expander(f"결과 {i+1}"):
                st.markdown("**발화자**: 김철수")
                st.markdown("**시간**: 2분 30초")
                st.markdown("**내용**: 프로젝트 일정에 대해 논의했습니다.")
                st.markdown("**회의**: 팀 프로젝트 기획 회의")


def show_analytics_page():
    """Analytics dashboard page"""
    st.header("📊 분석 대시보드")
    
    # Statistics cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 회의 수", "15")
    
    with col2:
        st.metric("총 발화 시간", "45시간")
    
    with col3:
        st.metric("평균 회의 시간", "3시간")
    
    with col4:
        st.metric("결정사항 수", "23개")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("회의 참가자별 발화 시간")
        # TODO: Add chart
        st.info("차트가 여기에 표시됩니다")
    
    with col2:
        st.subheader("월별 회의 빈도")
        # TODO: Add chart
        st.info("차트가 여기에 표시됩니다")


def show_summary_page():
    """Summary generation page"""
    st.header("📄 요약 생성")
    
    # Meeting selection
    meeting_id = st.selectbox(
        "회의 선택",
        ["회의 1: 팀 프로젝트 기획", "회의 2: 개발 일정 논의", "회의 3: 마케팅 전략"]
    )
    
    summary_type = st.selectbox(
        "요약 유형",
        ["일반 요약", "액션 아이템", "결정사항"]
    )
    
    if st.button("📄 요약 생성", type="primary"):
        # TODO: Implement summary generation
        st.success("요약 생성이 시작되었습니다!")
        
        # Mock summary
        st.subheader("생성된 요약")
        st.markdown("""
        ### 주요 내용
        이 회의에서는 프로젝트 일정과 담당자 배정에 대해 논의했습니다.
        
        ### 핵심 포인트
        - 프로젝트 마감일은 다음 달 15일로 확정
        - 김철수가 프론트엔드 개발 담당
        - 이영희가 백엔드 개발 담당
        
        ### 액션 아이템
        1. 프로젝트 계획서 작성 (담당: 김철수, 마감: 2024-01-10)
        """)


if __name__ == "__main__":
    main() 