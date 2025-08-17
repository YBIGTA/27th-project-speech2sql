"""
Database configuration and connection management
"""
import os
from typing import Optional
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config.settings import settings

# SQLAlchemy setup for PostgreSQL
Base = declarative_base()
metadata = MetaData()

# Database engine
postgresql_engine: Optional[create_engine] = None
postgresql_session_local: Optional[sessionmaker] = None


def get_postgresql_engine():
    """Get PostgreSQL database engine"""
    global postgresql_engine
    if postgresql_engine is None:
        postgresql_url = settings.postgresql_url
        postgresql_engine = create_engine(
            postgresql_url,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=settings.debug
        )
    return postgresql_engine


def get_postgresql_session():
    """Get PostgreSQL database session"""
    global postgresql_session_local
    if postgresql_session_local is None:
        engine = get_postgresql_engine()
        postgresql_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return postgresql_session_local()


def create_tables():
    """Create database tables"""
    import importlib
    try:
        importlib.import_module("src.database.models")  # 모델 강제 로드
    except ModuleNotFoundError:
        importlib.import_module("database.models")      # 경로가 다른 경우 대비
    Base.metadata.create_all(bind=get_postgresql_engine())


def close_connections():
    """Close database connections"""
    global postgresql_engine
    
    if postgresql_engine:
        postgresql_engine.dispose()
        postgresql_engine = None


# Database dependency for FastAPI
def get_db():
    """Database dependency for FastAPI"""
    db = get_postgresql_session()
    try:
        yield db
    finally:
        db.close() 