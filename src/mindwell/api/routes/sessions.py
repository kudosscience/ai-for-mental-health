"""Session management API endpoints."""

from datetime import datetime
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status

from mindwell.schemas import (
    RiskLevel,
    SentimentLevel,
    SessionCreate,
    SessionDetail,
    SessionStatus,
    SessionSummary,
)

router = APIRouter()
logger = structlog.get_logger()

# In-memory session storage for prototype
# In production, use database storage via SQLAlchemy
_sessions: dict[UUID, SessionDetail] = {}


@router.post(
    "/sessions",
    response_model=SessionSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new session",
    description="Create a new chat session for tracking conversations",
)
async def create_session(request: SessionCreate) -> SessionSummary:
    """
    Create a new chat session.

    Sessions are used to group related conversations and track
    analytics over time.
    """
    from uuid import uuid4

    session_id = uuid4()
    now = datetime.utcnow()

    session = SessionDetail(
        id=session_id,
        title=request.title,
        status=SessionStatus.ACTIVE,
        message_count=0,
        average_sentiment=None,
        highest_risk_level=None,
        created_at=now,
        updated_at=now,
        messages=[],
        clinician_notes=None,
    )

    _sessions[session_id] = session

    logger.info("session_created", session_id=str(session_id))

    return SessionSummary(
        id=session.id,
        title=session.title,
        status=session.status,
        message_count=session.message_count,
        average_sentiment=session.average_sentiment,
        highest_risk_level=session.highest_risk_level,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.get(
    "/sessions",
    response_model=list[SessionSummary],
    summary="List sessions",
    description="List all chat sessions with optional filtering",
)
async def list_sessions(
    status: SessionStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[SessionSummary]:
    """
    List chat sessions with optional filtering.

    Args:
        status: Filter by session status
        limit: Maximum number of results (default 50)
        offset: Number of results to skip for pagination
    """
    sessions = list(_sessions.values())

    if status:
        sessions = [s for s in sessions if s.status == status]

    # Sort by updated_at descending
    sessions.sort(key=lambda s: s.updated_at, reverse=True)

    # Apply pagination
    paginated = sessions[offset : offset + limit]

    return [
        SessionSummary(
            id=s.id,
            title=s.title,
            status=s.status,
            message_count=s.message_count,
            average_sentiment=s.average_sentiment,
            highest_risk_level=s.highest_risk_level,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in paginated
    ]


@router.get(
    "/sessions/{session_id}",
    response_model=SessionDetail,
    summary="Get session details",
    description="Get detailed information about a specific session including messages",
)
async def get_session(session_id: UUID) -> SessionDetail:
    """
    Get detailed session information.

    Returns the full session including all messages and clinician notes.
    """
    if session_id not in _sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    return _sessions[session_id]


@router.patch(
    "/sessions/{session_id}/status",
    response_model=SessionSummary,
    summary="Update session status",
    description="Update the status of a chat session",
)
async def update_session_status(
    session_id: UUID,
    new_status: SessionStatus,
) -> SessionSummary:
    """
    Update the status of a session.

    Valid status transitions:
    - ACTIVE -> PAUSED, COMPLETED, FLAGGED
    - PAUSED -> ACTIVE, COMPLETED
    - FLAGGED -> ACTIVE (after review)
    """
    if session_id not in _sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    session = _sessions[session_id]
    old_status = session.status

    # Update status
    session.status = new_status
    session.updated_at = datetime.utcnow()

    logger.info(
        "session_status_updated",
        session_id=str(session_id),
        old_status=old_status.value,
        new_status=new_status.value,
    )

    return SessionSummary(
        id=session.id,
        title=session.title,
        status=session.status,
        message_count=session.message_count,
        average_sentiment=session.average_sentiment,
        highest_risk_level=session.highest_risk_level,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.get(
    "/sessions/flagged",
    response_model=list[SessionSummary],
    summary="Get flagged sessions",
    description="Get all sessions that have been flagged for clinician review",
)
async def get_flagged_sessions() -> list[SessionSummary]:
    """
    Get all flagged sessions requiring clinician attention.

    Sessions are flagged when:
    - High or critical risk is detected
    - Manual flagging by the system or clinician
    """
    flagged = [
        s for s in _sessions.values()
        if s.status == SessionStatus.FLAGGED
        or s.highest_risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    ]

    # Sort by risk level (critical first) then by updated_at
    def sort_key(session):
        risk_order = {
            RiskLevel.CRITICAL: 0,
            RiskLevel.HIGH: 1,
            RiskLevel.MODERATE: 2,
            RiskLevel.LOW: 3,
            None: 4,
        }
        return (risk_order.get(session.highest_risk_level, 4), -session.updated_at.timestamp())

    flagged.sort(key=sort_key)

    return [
        SessionSummary(
            id=s.id,
            title=s.title,
            status=s.status,
            message_count=s.message_count,
            average_sentiment=s.average_sentiment,
            highest_risk_level=s.highest_risk_level,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in flagged
    ]
