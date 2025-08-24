from config.database import get_postgresql_engine
from sqlalchemy import text

def check_database_connection():
    """데이터베이스 연결 상태와 스키마 정보 확인"""
    print("🔍 데이터베이스 연결 상태 확인")
    print("=" * 50)
    
    try:
        engine = get_postgresql_engine()
        
        with engine.connect() as conn:
            # 1. 현재 데이터베이스 정보
            print("1. 현재 데이터베이스 정보:")
            result = conn.execute(text("SELECT current_database(), current_user, current_schema"))
            db_info = result.fetchone()
            print(f"   - 데이터베이스: {db_info[0]}")
            print(f"   - 사용자: {db_info[1]}")
            print(f"   - 스키마: {db_info[2]}")
            print()
            
            # 2. 사용 가능한 스키마 목록
            print("2. 사용 가능한 스키마 목록:")
            result = conn.execute(text("SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT LIKE 'pg_%' AND schema_name != 'information_schema'"))
            schemas = [row[0] for row in result]
            for schema in schemas:
                print(f"   - {schema}")
            print()
            
            # 3. public 스키마의 테이블 목록
            print("3. public 스키마의 테이블 목록:")
            result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"))
            tables = [row[0] for row in result]
            for table in tables:
                print(f"   - {table}")
            print()
            
            # 4. meetings 테이블 구조 확인
            if 'meetings' in tables:
                print("4. meetings 테이블 구조:")
                result = conn.execute(text("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'meetings' ORDER BY ordinal_position"))
                for row in result:
                    print(f"   - {row[0]}: {row[1]} ({'NULL' if row[2] == 'YES' else 'NOT NULL'})")
                print()
                
                # 5. meetings 테이블 데이터 개수 확인
                result = conn.execute(text("SELECT COUNT(*) FROM meetings"))
                count = result.fetchone()[0]
                print(f"5. meetings 테이블 데이터 개수: {count}")
                print()
            
            # 6. 연결 정보
            print("6. 연결 정보:")
            print(f"   - 연결 URL: {engine.url}")
            print(f"   - 연결 상태: 정상")
            
    except Exception as e:
        print(f"❌ 데이터베이스 연결 오류: {e}")
        print(f"   - 오류 타입: {type(e).__name__}")

if __name__ == "__main__":
    check_database_connection() 