"""
Database models for Speech2SQL application
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, JSON, Index, text as sa_text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from config.database import Base


class Meeting(Base):
    """Meeting model for storing meeting information"""
    __tablename__ = "meetings"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    duration = Column(Float)  # Duration in seconds
    participants = Column(JSON)  # List of participant names
    summary = Column(Text)
    audio_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # PostgreSQL functional GIN index on tsvector for full-text search
    __table_args__ = (
        # Basic btree indexes are created by ORM for 'index=True' columns
        # Full-text search index using to_tsvector on title
        Index(
            'idx_meetings_title_tsv',
            sa_text("to_tsvector('simple', coalesce(title, ''))"),
            postgresql_using='gin'
        ),
    )
    
    # Relationships
    utterances = relationship("Utterance", back_populates="meeting", cascade="all, delete-orphan")
    actions = relationship("Action", back_populates="meeting", cascade="all, delete-orphan")


class Utterance(Base):
    """Utterance model for storing individual speech segments"""
    __tablename__ = "utterances"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False, index=True)
    speaker = Column(String(100), nullable=False, index=True)
    timestamp = Column(Float, nullable=False)  # Start time in seconds
    end_timestamp = Column(Float)  # End time in seconds
    text = Column(Text, nullable=False)
    confidence = Column(Float)  # STT confidence score
    language = Column(String(10), default="ko")  # Language code
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # PostgreSQL functional GIN index on tsvector for full-text search
    __table_args__ = (
        Index(
            'idx_utterances_text_tsv',
            sa_text("to_tsvector('simple', coalesce(text, ''))"),
            postgresql_using='gin'
        ),
    )
    
    # Relationships
    meeting = relationship("Meeting", back_populates="utterances")


class Action(Base):
    """Action model for storing meeting actions and decisions"""
    __tablename__ = "actions"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False, index=True)
    action_type = Column(String(50), nullable=False, index=True)  # decision, assignment, discussion
    description = Column(Text, nullable=False)
    assignee = Column(String(100))
    due_date = Column(DateTime)
    status = Column(String(20), default="pending")  # pending, completed, cancelled
    priority = Column(String(20), default="medium")  # low, medium, high
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    meeting = relationship("Meeting", back_populates="actions")


 