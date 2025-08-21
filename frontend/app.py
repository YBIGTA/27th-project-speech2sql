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
    
    # Example queries
    st.subheader("💡 검색 예시")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📅 날짜/시간", use_container_width=True):
            st.session_state.query = "이 음성 기록은 언제 녹음되었나요?"
    with col2:
        if st.button("👥 참가자/화자", use_container_width=True):
            st.session_state.query = "누가 이 음성 기록에 참여했나요?"
    with col3:
        if st.button("📋 주요 내용", use_container_width=True):
            st.session_state.query = "이 음성 기록에서 주요하게 다룬 내용은 무엇인가요?"
    
    # Use session state for query
    if hasattr(st.session_state, 'query') and st.session_state.query:
        query = st.session_state.query
        st.session_state.query = ""  # Clear after use

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


def show_analytics_page():
    """Analytics dashboard page"""
    st.header("📊 분석 대시보드")
    st.info("향후 구현 예정")


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
                
                # Current summary status
                summary_status = meeting_info.get('status', 'pending')
                current_summary = meeting_info.get('summary', '')
                
                st.subheader("📝 현재 요약 상태")
                if summary_status == "completed" and current_summary:
                    st.success("✅ 요약이 생성되었습니다")
                    with st.expander("현재 요약 보기"):
                        st.write(current_summary)
                else:
                    st.info("📝 요약이 아직 생성되지 않았습니다")
                
                # Action items and decisions
                action_count = meeting_info.get('action_count', 0)
                decision_count = meeting_info.get('decision_count', 0)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("액션 아이템", action_count)
                with col2:
                    st.metric("결정 사항", decision_count)
                
                st.divider()
                
                # Summary generation
                st.subheader("🔄 요약 생성")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    summary_type = st.selectbox(
                        "요약 타입",
                        ["general", "action_items", "decisions"],
                        format_func=lambda x: {
                            "general": "📋 일반 요약",
                            "action_items": "✅ 액션 아이템 중심",
                            "decisions": "🎯 결정사항 중심"
                        }.get(x, x)
                    )
                
                with col2:
                    language = st.selectbox(
                        "언어",
                        ["ko", "en"],
                        format_func=lambda x: {"ko": "🇰🇷 한국어", "en": "🇺🇸 English"}.get(x, x)
                    )
                
                # Generate summary button
                if st.button("📝 요약 생성", type="primary", use_container_width=True):
                    with st.spinner("요약을 생성하고 있습니다..."):
                        try:
                            payload = {
                                "meeting_id": meeting_id,
                                "summary_type": summary_type,
                                "language": language
                            }
                            response = requests.post(f"{API_BASE_URL}/summary/generate", json=payload, timeout=120)
                            
                            if response.status_code == 200:
                                summary_data = response.json()
                                st.success("✅ 요약이 성공적으로 생성되었습니다!")
                                
                                # Display generated summary
                                st.subheader("📋 생성된 요약")
                                st.write(summary_data.get('summary_text', ''))
                                
                                # Key points
                                key_points = summary_data.get('key_points', [])
                                if key_points:
                                    st.subheader("🔑 핵심 포인트")
                                    for i, point in enumerate(key_points, 1):
                                        st.write(f"{i}. {point}")
                                
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
                                
                                # Decisions
                                decisions = summary_data.get('decisions', [])
                                if decisions:
                                    st.subheader("🎯 결정 사항")
                                    for decision in decisions:
                                        st.write(f"• {decision.get('decision', '')}")
                                
                                # Refresh the page to show updated status
                                st.rerun()
                                
                            else:
                                st.error(f"요약 생성 실패: {response.status_code} {response.text}")
                        except Exception as e:
                            st.error(f"요청 중 오류가 발생했습니다: {e}")
                
                st.divider()
                
                # PDF generation
                st.subheader("📑 PDF 보고서 생성")
                st.write("회의 요약을 PDF 파일로 다운로드할 수 있습니다.")
                
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