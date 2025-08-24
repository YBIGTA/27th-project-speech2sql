#!/usr/bin/env python3
"""
Database connection and setup test script
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import get_postgresql_engine, create_tables, get_db
from src.database.models import Meeting, Utterance, Action
from sqlalchemy.orm import sessionmaker
from config.settings import settings


def test_database_connection():
    """Test PostgreSQL connection"""
    print("🔍 Testing database connection...")
    
    try:
        engine = get_postgresql_engine()
        with engine.connect() as conn:
            result = conn.execute("SELECT version();")
            version = result.fetchone()[0]
            print(f"✅ Database connected successfully!")
            print(f"📊 PostgreSQL version: {version}")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def test_table_creation():
    """Test table creation"""
    print("\n🔍 Testing table creation...")
    
    try:
        create_tables()
        print("✅ Tables created successfully!")
        
        # Test inserting sample data
        engine = get_postgresql_engine()
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Create sample meeting
        sample_meeting = Meeting(
            title="테스트 회의",
            duration=3600.0,
            participants=["김철수", "이영희", "박민수"],
            summary="테스트 회의 요약입니다."
        )
        
        db.add(sample_meeting)
        db.commit()
        db.refresh(sample_meeting)
        
        print(f"✅ Sample meeting created with ID: {sample_meeting.id}")
        
        # Create sample utterance
        sample_utterance = Utterance(
            meeting_id=sample_meeting.id,
            speaker="김철수",
            timestamp=10.5,
            text="안녕하세요, 테스트 발언입니다.",
            confidence=0.95
        )
        
        db.add(sample_utterance)
        db.commit()
        
        print("✅ Sample utterance created successfully!")
        
        # Clean up
        db.delete(sample_meeting)
        db.commit()
        db.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Table creation failed: {e}")
        return False


def test_full_text_search():
    """Test PostgreSQL full-text search"""
    print("\n🔍 Testing full-text search...")
    
    try:
        engine = get_postgresql_engine()
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Create test data
        meeting = Meeting(
            title="프로젝트 기획 회의",
            duration=7200.0,
            participants=["개발팀", "기획팀"],
            summary="새로운 프로젝트 기획에 대한 논의"
        )
        db.add(meeting)
        db.commit()
        db.refresh(meeting)
        
        utterance = Utterance(
            meeting_id=meeting.id,
            speaker="개발팀장",
            timestamp=30.0,
            text="이 프로젝트는 AI 기술을 활용한 혁신적인 솔루션입니다.",
            confidence=0.92
        )
        db.add(utterance)
        db.commit()
        
        # Test full-text search
        search_result = db.query(Utterance).filter(
            Utterance.text.op('@@')('프로젝트 & AI')
        ).first()
        
        if search_result:
            print("✅ Full-text search working correctly!")
        else:
            print("⚠️ Full-text search may need configuration")
        
        # Clean up
        db.delete(meeting)
        db.commit()
        db.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Full-text search test failed: {e}")
        return False


def main():
    """Main test function"""
    print("🚀 Database Setup Test")
    print("=" * 50)
    
    # Test connection
    if not test_database_connection():
        print("\n❌ Database connection failed. Please check:")
        print("1. PostgreSQL is running")
        print("2. .env file has correct database settings")
        print("3. Database 'speech2sql' exists")
        return False
    
    # Test table creation
    if not test_table_creation():
        print("\n❌ Table creation failed. Please check:")
        print("1. Database permissions")
        print("2. SQLAlchemy models")
        return False
    
    # Test full-text search
    if not test_full_text_search():
        print("\n⚠️ Full-text search test failed. This may need manual configuration.")
    
    print("\n" + "=" * 50)
    print("✅ Database setup test completed successfully!")
    print("\n📋 Next steps:")
    print("1. 팀원들이 setup.py 실행")
    print("2. 각자 담당 모듈 개발 시작")
    print("3. 정기적인 통합 테스트")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 