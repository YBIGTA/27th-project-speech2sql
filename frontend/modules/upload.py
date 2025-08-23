<<<<<<< HEAD
import streamlit as st
import requests
import json
from datetime import datetime

API_BASE_URL = "http://localhost:8000/api/v1"

def upload_file():

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
=======
# 파일 업로드

# 임시
import streamlit as st

class Upload:
>>>>>>> f4019648f6d7bc1c24203184b859f5e6aca469a8
