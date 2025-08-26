<<<<<<< HEAD
import streamlit as st
import requests
import json
from datetime import datetime
import os
from typing import Dict
=======
<<<<<<< HEAD
import streamlit as st
import requests
import json
from typing import Dict
from datetime import datetime

API_BASE_URL = "http://localhost:8000/api/v1"
>>>>>>> 88af335c9844ef7d6b0732c0dbc3330b6d0f691e

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


<<<<<<< HEAD
def search_meetings():
=======
def search_by_natural_language():   
>>>>>>> 88af335c9844ef7d6b0732c0dbc3330b6d0f691e
    st.header("🔍 자연어 검색")
    
    query = st.text_input("검색어 입력", placeholder="예: 누가 프로젝트 일정에 대해 언급했나요?")
    st.caption("💡 자연어로 질문하시면 AI가 음성 기록 내용을 분석하여 답변해드립니다.")
<<<<<<< HEAD
=======
    
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
>>>>>>> 88af335c9844ef7d6b0732c0dbc3330b6d0f691e

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
<<<<<<< HEAD
=======
=======
# 검색 인터페이스

# 임시
import streamlit as st

class Search:
>>>>>>> f4019648f6d7bc1c24203184b859f5e6aca469a8
>>>>>>> 88af335c9844ef7d6b0732c0dbc3330b6d0f691e
