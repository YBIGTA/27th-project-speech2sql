"""
빠른 테스트용 스크립트
"""
import requests
import json

# API 설정
API_BASE_URL = "http://localhost:8000/api/v1"

def quick_test():
    """빠른 테스트 실행"""
    print("🚀 빠른 멀티에이전트 분석 테스트")
    print("=" * 50)
    
    try:
        # 1. 회의 목록 조회
        print("1. 회의 목록 조회 중...")
        response = requests.get(f"{API_BASE_URL}/query/meetings", timeout=10)
        
        if response.status_code == 200:
            meetings = response.json().get("meetings", [])
            print(f"✅ 총 {len(meetings)}개의 회의가 있습니다.")
            
            if meetings:
                # 첫 번째 회의로 테스트
                test_meeting = meetings[0]
                meeting_id = test_meeting["id"]
                meeting_title = test_meeting["title"]
                
                print(f"\n📋 테스트 대상: {meeting_title} (ID: {meeting_id})")
                
                # 2. 멀티에이전트 분석 테스트
                print("\n2. 멀티에이전트 분석 테스트 중...")
                
                # 종합 분석
                print("   - 종합 분석 실행 중...")
                analysis_response = requests.post(
                    f"{API_BASE_URL}/analysis/comprehensive",
                    json={"meeting_id": meeting_id, "analysis_type": "comprehensive"},
                    timeout=120
                )
                
                if analysis_response.status_code == 200:
                    result = analysis_response.json()
                    print("   ✅ 종합 분석 성공!")
                    
                    # 결과 요약 출력
                    executive_summary = result.get("executive_summary", "")
                    if executive_summary:
                        print(f"   📋 실행 요약: {executive_summary[:100]}...")
                    
                    processing_time = result.get("processing_time", 0)
                    confidence = result.get("confidence", 0)
                    print(f"   ⏱️ 처리 시간: {processing_time}초")
                    print(f"   🎯 신뢰도: {confidence}")
                    
                    # 인사이트 확인
                    insights = result.get("insights", {})
                    if insights:
                        print("   💡 주요 인사이트:")
                        for key, value in insights.items():
                            if isinstance(value, dict):
                                for sub_key, sub_value in value.items():
                                    print(f"      - {sub_key}: {sub_value}")
                            else:
                                print(f"      - {key}: {value}")
                    
                else:
                    print(f"   ❌ 종합 분석 실패: {analysis_response.status_code}")
                    print(f"   오류: {analysis_response.text}")
                
                # 화자 분석
                print("\n   - 화자 분석 실행 중...")
                speaker_response = requests.get(
                    f"{API_BASE_URL}/analysis/meeting/{meeting_id}/speakers",
                    timeout=60
                )
                
                if speaker_response.status_code == 200:
                    speaker_result = speaker_response.json()
                    speakers = speaker_result.get("speaker_analysis", {}).get("speakers", {})
                    print(f"   ✅ 화자 분석 성공! (분석된 화자: {len(speakers)}명)")
                    
                    # 화자별 정보 출력
                    for speaker, data in speakers.items():
                        profile = data.get("profile", {})
                        participation = profile.get("participation_rate", 0)
                        style = profile.get("communication_style", "Unknown")
                        print(f"      👤 {speaker}: 참여도 {participation:.1%}, 스타일 {style}")
                
                else:
                    print(f"   ❌ 화자 분석 실패: {speaker_response.status_code}")
                
                # 안건 분석
                print("\n   - 안건 분석 실행 중...")
                agenda_response = requests.get(
                    f"{API_BASE_URL}/analysis/meeting/{meeting_id}/agendas",
                    timeout=60
                )
                
                if agenda_response.status_code == 200:
                    agenda_result = agenda_response.json()
                    agendas = agenda_result.get("agenda_analysis", {}).get("agendas", {})
                    print(f"   ✅ 안건 분석 성공! (분석된 안건: {len(agendas)}개)")
                    
                    # 안건별 정보 출력
                    for agenda_id, agenda_data in agendas.items():
                        title = agenda_data.get("agenda_info", {}).get("title", "Unknown")
                        consensus = agenda_data.get("consensus", {}).get("level", "Unknown")
                        decisions = len(agenda_data.get("decisions", []))
                        print(f"      📋 {title}: 합의수준 {consensus}, 결정사항 {decisions}개")
                
                else:
                    print(f"   ❌ 안건 분석 실패: {agenda_response.status_code}")
                
            else:
                print("❌ 분석할 회의가 없습니다. 먼저 테스트 데이터를 생성해주세요.")
                print("   실행: python insert_test_data.py")
        
        else:
            print(f"❌ 회의 목록 조회 실패: {response.status_code}")
    
    except requests.exceptions.ConnectionError:
        print("❌ API 서버에 연결할 수 없습니다.")
        print("   FastAPI 서버가 실행 중인지 확인해주세요.")
        print("   실행: python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000")
    
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
    
    print("\n" + "=" * 50)
    print("✅ 빠른 테스트 완료!")

if __name__ == "__main__":
    quick_test() 