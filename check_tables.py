from config.database import get_postgresql_engine
from sqlalchemy import text

def check_tables():
    engine = get_postgresql_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        print("현재 테이블들:")
        for row in result:
            print(f"- {row[0]}")

if __name__ == "__main__":
    check_tables() 