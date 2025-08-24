"""
테스트 데이터를 데이터베이스에 삽입하는 스크립트 (수정된 버전)
"""
import json
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from config.database import get_postgresql_engine
from src.database.models import Meeting, Utterance
from test_data_generator import generate_test_meeting_data, generate_utterances

def insert_test_data_directly():
    """직접 데이터베이스에 테스트 데이터 삽입 (수정된 버전)"""
    try:
        # 직접 engine 사용
        engine = get_postgresql_engine()
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # 테스트 회의 템플릿 생성
        meeting_templates = generate_test_meeting_data()
        
        created_meetings = []
        
        for i, template in enumerate(meeting_templates, 1):
            print(f"\n📊 회의 {i} 생성 중: {template['title']}")
            
            # 회의 생성
            meeting = Meeting(
                title=template["title"],
                date=datetime.now().date(),
                participants=template["speakers"],
                duration=template["duration"] * 60  # 초 단위로 변환
            )
            
            session.add(meeting)
            session.commit()
            session.refresh(meeting)
            
            print(f"✅ 회의 생성 완료 (ID: {meeting.id})")
            
            # 발화 데이터 생성 및 삽입
            utterances = generate_utterances(template)
            
            for utterance_data in utterances:
                utterance = Utterance(
                    meeting_id=meeting.id,
                    speaker=utterance_data["speaker"],
                    timestamp=utterance_data["timestamp"],
                    end_timestamp=utterance_data["end_timestamp"],
                    text=utterance_data["text"],
                    confidence=0.95,
                    language="ko"
                )
                session.add(utterance)
            
            session.commit()
            print(f"✅ 발화 데이터 {len(utterances)}개 삽입 완료")
            
            created_meetings.append({
                "id": meeting.id,
                "title": meeting.title,
                "utterance_count": len(utterances)
            })
        
        session.close()
        
        return created_meetings
        
    except Exception as e:
        print(f"❌ 데이터베이스 삽입 오류: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    """메인 실행 함수"""
    print("🤖 테스트 데이터 삽입 (수정된 버전)")
    print("=" * 60)
    
    # 1. 테스트 데이터 삽입
    print("\n📥 1단계: 테스트 데이터 삽입")
    created_meetings = insert_test_data_directly()
    
    if not created_meetings:
        print("❌ 테스트 데이터 삽입 실패")
        return
    
    print(f"\n✅ 총 {len(created_meetings)}개의 테스트 회의가 생성되었습니다.")
    
    # 2. 생성된 회의 정보 출력
    print("\n📋 생성된 회의 목록:")
    for meeting in created_meetings:
        print(f"   - ID: {meeting['id']}, 제목: {meeting['title']}, 발화 수: {meeting['utterance_count']}")
    
    print("\n" + "=" * 60)
    print("✅ 테스트 데이터 삽입 완료!")
    print("\n💡 다음 단계:")
    print("1. 프론트엔드에서 멀티에이전트 분석 페이지 접속")
    print("2. 생성된 테스트 회의 선택")
    print("3. 다양한 분석 유형 테스트")

if __name__ == "__main__":
    main() 