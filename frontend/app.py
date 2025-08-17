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
            type=['wav'],
            help="지원 형식: WAV (최대 100MB)"
        )
        title = st.text_input("회의 제목", placeholder="예: 팀 프로젝트 기획 회의")
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
            data = {"title": title}
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
                st.caption(f"SQL: {j.get('sql_query')}")
                st.caption(f"총 {j.get('total_count')}건, 실행 {j.get('execution_time')}s")
                for i, r in enumerate(j.get("results", []), start=1):
                    with st.expander(f"결과 {i}"):
                        st.markdown(f"**발화자**: {r.get('speaker','-')}")
                        st.markdown(f"**시간**: {r.get('timestamp','-')}")
                        st.markdown(f"**내용**: {r.get('text','')}")
                        st.markdown(f"**회의**: {r.get('meeting_title','-')}")
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
    st.info("향후 구현 예정")


if __name__ == "__main__":
    main() 