"""
데이터베이스 리셋 스크립트
"""
from sqlalchemy import text
from config.database import get_postgresql_engine, create_tables

def reset_database():
    """데이터베이스 테이블을 삭제하고 다시 생성"""
    print("🗄️ 데이터베이스 리셋 중...")
    
    try:
        # 기존 테이블 삭제
        engine = get_postgresql_engine()
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS actions CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS utterances CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS meetings CASCADE"))
            conn.commit()
        
        print("✅ 기존 테이블 삭제 완료")
        
        # 새 테이블 생성
        create_tables()
        print("✅ 새 테이블 생성 완료")
        
        print("🎉 데이터베이스 리셋 완료!")
        
    except Exception as e:
        print(f"❌ 데이터베이스 리셋 오류: {e}")

if __name__ == "__main__":
    reset_database() 