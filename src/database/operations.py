"""
Database CRUD operation functions
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from .models import Meeting, Utterance, Action


class MeetingOperations:
    """Meeting-related database operations"""
    
    @staticmethod
    def create_meeting(
        db: Session,
        title: str,
        participants: List[str] = None,
        audio_path: str = None,
        duration: float = None
    ) -> Meeting:
        """Create a new meeting"""
        meeting = Meeting(
            title=title,
            participants=participants or [],
            audio_path=audio_path,
            duration=duration,
            date=datetime.utcnow()
        )
        db.add(meeting)
        db.commit()
        db.refresh(meeting)
        return meeting
    
    @staticmethod
    def get_meeting(db: Session, meeting_id: int) -> Optional[Meeting]:
        """Get meeting by meeting ID"""
        return db.query(Meeting).filter(Meeting.id == meeting_id).first()
    
    @staticmethod
    def get_meetings(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        title_search: str = None,
        date_from: datetime = None,
        date_to: datetime = None
    ) -> List[Meeting]:
        """Get meetings list with filtering and pagination support"""
        query = db.query(Meeting)
        
        # Title search
        if title_search:
            query = query.filter(Meeting.title.ilike(f"%{title_search}%"))
        
        # Date range filter
        if date_from:
            query = query.filter(Meeting.date >= date_from)
        if date_to:
            query = query.filter(Meeting.date <= date_to)
        
        return query.order_by(Meeting.date.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_meeting(
        db: Session,
        meeting_id: int,
        title: str = None,
        summary: str = None,
        duration: float = None
    ) -> Optional[Meeting]:
        """Update meeting information"""
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            return None
        
        if title is not None:
            meeting.title = title
        if summary is not None:
            meeting.summary = summary
        if duration is not None:
            meeting.duration = duration
        
        meeting.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(meeting)
        return meeting
    
    @staticmethod
    def delete_meeting(db: Session, meeting_id: int) -> bool:
        """Delete meeting"""
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            return False
        
        db.delete(meeting)
        db.commit()
        return True
    
    @staticmethod
    def get_meeting_by_filename(db: Session, filename: str) -> Optional[Meeting]:
        """Get meeting by filename"""
        return db.query(Meeting).filter(
            Meeting.audio_path.like(f'%{filename}')
        ).first()
    
    @staticmethod
    def delete_meeting_by_filename(db: Session, filename: str) -> Optional[Meeting]:
        """Delete meeting by filename"""
        meeting = db.query(Meeting).filter(
            Meeting.audio_path.like(f'%{filename}')
        ).first()
        
        if not meeting:
            return None
        
        # Backup meeting info before deletion
        meeting_info = Meeting(
            id=meeting.id,
            title=meeting.title,
            audio_path=meeting.audio_path
        )
        
        db.delete(meeting)
        db.commit()
        return meeting_info


class UtteranceOperations:
    """Utterance-related database operations"""
    
    @staticmethod
    def create_utterance(
        db: Session,
        meeting_id: int,
        speaker: str,
        text: str,
        timestamp: float,
        end_timestamp: float = None,
        confidence: float = None,
        language: str = "ko"
    ) -> Utterance:
        """Create a new utterance"""
        utterance = Utterance(
            meeting_id=meeting_id,
            speaker=speaker,
            text=text,
            timestamp=timestamp,
            end_timestamp=end_timestamp,
            confidence=confidence,
            language=language
        )
        db.add(utterance)
        db.commit()
        db.refresh(utterance)
        return utterance
    
    @staticmethod
    def create_utterances_batch(
        db: Session,
        utterances_data: List[Dict[str, Any]]
    ) -> List[Utterance]:
        """Create utterances in batch (for STT results storage)"""
        utterances = []
        for data in utterances_data:
            utterance = Utterance(**data)
            utterances.append(utterance)
        
        db.add_all(utterances)
        db.commit()
        
        for utterance in utterances:
            db.refresh(utterance)
        
        return utterances
    
    @staticmethod
    def get_utterances_by_meeting(
        db: Session,
        meeting_id: int,
        speaker: str = None,
        time_from: float = None,
        time_to: float = None
    ) -> List[Utterance]:
        """Get utterances list for a meeting"""
        query = db.query(Utterance).filter(Utterance.meeting_id == meeting_id)
        
        if speaker:
            query = query.filter(Utterance.speaker == speaker)
        if time_from is not None:
            query = query.filter(Utterance.timestamp >= time_from)
        if time_to is not None:
            query = query.filter(Utterance.timestamp <= time_to)
        
        return query.order_by(Utterance.timestamp).all()
    
    @staticmethod
    def search_utterances_by_text(
        db: Session,
        search_text: str,
        meeting_id: int = None,
        speaker: str = None,
        limit: int = 50
    ) -> List[Utterance]:
        """Search utterances by text content"""
        query = db.query(Utterance).filter(
            Utterance.text.ilike(f"%{search_text}%")
        )
        
        if meeting_id:
            query = query.filter(Utterance.meeting_id == meeting_id)
        if speaker:
            query = query.filter(Utterance.speaker == speaker)
        
        return query.order_by(Utterance.timestamp).limit(limit).all()
    
    @staticmethod
    def get_speakers_by_meeting(db: Session, meeting_id: int) -> List[str]:
        """Get speakers list for a meeting"""
        result = db.query(Utterance.speaker).filter(
            Utterance.meeting_id == meeting_id
        ).distinct().all()
        
        return [row[0] for row in result]


class ActionOperations:
    """액션 아이템 관련 데이터베이스 작업"""
    
    @staticmethod
    def create_action(
        db: Session,
        meeting_id: int,
        action_type: str,
        description: str,
        assignee: str = None,
        due_date: datetime = None,
        priority: str = "medium"
    ) -> Action:
        """새 액션 아이템 생성"""
        action = Action(
            meeting_id=meeting_id,
            action_type=action_type,
            description=description,
            assignee=assignee,
            due_date=due_date,
            priority=priority,
            status="pending"
        )
        db.add(action)
        db.commit()
        db.refresh(action)
        return action
    
    @staticmethod
    def get_actions_by_meeting(db: Session, meeting_id: int) -> List[Action]:
        """회의의 액션 아이템 목록 조회"""
        return db.query(Action).filter(
            Action.meeting_id == meeting_id
        ).order_by(Action.created_at).all()
    
    @staticmethod
    def get_actions_by_assignee(
        db: Session,
        assignee: str,
        status: str = None
    ) -> List[Action]:
        """담당자별 액션 아이템 조회"""
        query = db.query(Action).filter(Action.assignee == assignee)
        
        if status:
            query = query.filter(Action.status == status)
        
        return query.order_by(Action.due_date.nulls_last()).all()
    
    @staticmethod
    def update_action_status(
        db: Session,
        action_id: int,
        status: str
    ) -> Optional[Action]:
        """액션 아이템 상태 업데이트"""
        action = db.query(Action).filter(Action.id == action_id).first()
        if not action:
            return None
        
        action.status = status
        action.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(action)
        return action


class SearchOperations:
    """검색 관련 데이터베이스 작업"""
    
    @staticmethod
    def search_meetings_and_utterances(
        db: Session,
        search_query: str,
        meeting_id: int = None,
        speaker: str = None,
        date_from: datetime = None,
        date_to: datetime = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Integrated search (meetings + utterances)"""
        
        # Build base query
        utterance_query = db.query(
            Utterance.id,
            Utterance.meeting_id,
            Utterance.speaker,
            Utterance.timestamp,
            Utterance.text,
            Meeting.title.label('meeting_title'),
            Meeting.date.label('meeting_date')
        ).join(Meeting, Utterance.meeting_id == Meeting.id)
        
        # Text search
        utterance_query = utterance_query.filter(
            Utterance.text.ilike(f"%{search_query}%")
        )
        
        # Apply filters
        if meeting_id:
            utterance_query = utterance_query.filter(Utterance.meeting_id == meeting_id)
        if speaker:
            utterance_query = utterance_query.filter(Utterance.speaker == speaker)
        if date_from:
            utterance_query = utterance_query.filter(Meeting.date >= date_from)
        if date_to:
            utterance_query = utterance_query.filter(Meeting.date <= date_to)
        
        # Execute
        utterances = utterance_query.order_by(
            Meeting.date.desc(),
            Utterance.timestamp
        ).limit(limit).all()
        
        # Format results
        results = []
        for utterance in utterances:
            results.append({
                "id": utterance.id,
                "meeting_id": utterance.meeting_id,
                "meeting_title": utterance.meeting_title,
                "meeting_date": utterance.meeting_date.isoformat(),
                "speaker": utterance.speaker,
                "timestamp": utterance.timestamp,
                "text": utterance.text
            })
        
        return {
            "results": results,
            "total_count": len(results),
            "search_query": search_query
        }
    
    @staticmethod
    def get_search_suggestions(db: Session) -> List[str]:
        """Generate search suggestions (based on frequently mentioned keywords)"""
        # Simple implementation: hardcoded suggestions
        # In practice, can be generated dynamically through text analysis
        return [
            "프로젝트 일정",
            "담당자 배정",
            "결정사항",
            "액션 아이템",
            "마감일",
            "예산 논의",
            "기술 검토",
            "다음 회의"
        ]


class AnalyticsOperations:
    """Analytics-related database operations"""
    
    @staticmethod
    def get_meeting_statistics(db: Session) -> Dict[str, Any]:
        """Get meeting statistics information"""
        total_meetings = db.query(func.count(Meeting.id)).scalar()
        total_utterances = db.query(func.count(Utterance.id)).scalar()
        total_actions = db.query(func.count(Action.id)).scalar()
        
        # Average meeting duration
        avg_duration = db.query(func.avg(Meeting.duration)).scalar() or 0
        
        # Monthly meeting count
        monthly_meetings = db.query(
            func.extract('year', Meeting.date).label('year'),
            func.extract('month', Meeting.date).label('month'),
            func.count(Meeting.id).label('count')
        ).group_by(
            func.extract('year', Meeting.date),
            func.extract('month', Meeting.date)
        ).order_by(
            func.extract('year', Meeting.date),
            func.extract('month', Meeting.date)
        ).all()
        
        return {
            "total_meetings": total_meetings,
            "total_utterances": total_utterances,
            "total_actions": total_actions,
            "average_duration_minutes": round(avg_duration / 60, 2) if avg_duration else 0,
            "monthly_meetings": [
                {
                    "year": int(row.year),
                    "month": int(row.month),
                    "count": row.count
                }
                for row in monthly_meetings
            ]
        }
    
    @staticmethod
    def get_speaker_statistics(db: Session, meeting_id: int = None) -> List[Dict[str, Any]]:
        """Get speaker statistics"""
        query = db.query(
            Utterance.speaker,
            func.count(Utterance.id).label('utterance_count'),
            func.sum(Utterance.end_timestamp - Utterance.timestamp).label('total_speaking_time')
        )
        
        if meeting_id:
            query = query.filter(Utterance.meeting_id == meeting_id)
        
        results = query.group_by(Utterance.speaker).all()
        
        return [
            {
                "speaker": row.speaker,
                "utterance_count": row.utterance_count,
                "total_speaking_time": round(row.total_speaking_time or 0, 2)
            }
            for row in results
        ]
