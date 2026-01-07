"""Clinician collaboration API endpoints."""

from datetime import datetime
from uuid import UUID, uuid4

import structlog
from fastapi import APIRouter, HTTPException, status

from mindwell.schemas import (
    ClinicianAlert,
    ClinicianNote,
    RiskLevel,
    SessionAnalytics,
    UserAnalytics,
)

router = APIRouter()
logger = structlog.get_logger()

# In-memory storage for prototype
_clinician_notes: dict[UUID, list[ClinicianNote]] = {}
_alerts: list[ClinicianAlert] = []


@router.post(
    "/clinician/sessions/{session_id}/notes",
    response_model=ClinicianNote,
    status_code=status.HTTP_201_CREATED,
    summary="Add clinician note",
    description="Add a clinical note to a patient's session",
)
async def add_clinician_note(
    session_id: UUID,
    note: str,
    is_private: bool = True,
) -> ClinicianNote:
    """
    Add a clinical note to a session.

    Notes can be:
    - Private: Visible only to clinicians
    - Shared: Visible to the patient as well

    Args:
        session_id: The session to add the note to
        note: The clinical note content
        is_private: Whether the note is private to clinicians
    """
    clinical_note = ClinicianNote(
        session_id=session_id,
        note=note,
        is_private=is_private,
        created_at=datetime.utcnow(),
    )

    if session_id not in _clinician_notes:
        _clinician_notes[session_id] = []
    _clinician_notes[session_id].append(clinical_note)

    logger.info(
        "clinician_note_added",
        session_id=str(session_id),
        is_private=is_private,
    )

    return clinical_note


@router.get(
    "/clinician/sessions/{session_id}/notes",
    response_model=list[ClinicianNote],
    summary="Get session notes",
    description="Get all clinical notes for a session",
)
async def get_session_notes(session_id: UUID) -> list[ClinicianNote]:
    """
    Get all clinical notes for a session.

    Returns notes in chronological order.
    """
    return _clinician_notes.get(session_id, [])


@router.get(
    "/clinician/alerts",
    response_model=list[ClinicianAlert],
    summary="Get alerts",
    description="Get alerts for clinician review",
)
async def get_alerts(
    unacknowledged_only: bool = True,
    risk_level: RiskLevel | None = None,
) -> list[ClinicianAlert]:
    """
    Get alerts requiring clinician attention.

    Args:
        unacknowledged_only: Only return unacknowledged alerts
        risk_level: Filter by specific risk level
    """
    alerts = _alerts.copy()

    if unacknowledged_only:
        alerts = [a for a in alerts if not getattr(a, "is_acknowledged", False)]

    if risk_level:
        alerts = [a for a in alerts if a.risk_level == risk_level]

    # Sort by risk level (critical first) then by creation time
    def sort_key(alert):
        risk_order = {
            RiskLevel.CRITICAL: 0,
            RiskLevel.HIGH: 1,
            RiskLevel.MODERATE: 2,
            RiskLevel.LOW: 3,
        }
        return (risk_order.get(alert.risk_level, 4), -alert.created_at.timestamp())

    alerts.sort(key=sort_key)

    return alerts


@router.post(
    "/clinician/alerts/{alert_id}/acknowledge",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Acknowledge alert",
    description="Mark an alert as acknowledged",
)
async def acknowledge_alert(alert_id: UUID):
    """
    Acknowledge a clinician alert.

    This marks the alert as reviewed but does not dismiss it.
    """
    # In production, this would update the database
    logger.info("alert_acknowledged", alert_id=str(alert_id))


@router.get(
    "/clinician/analytics/session/{session_id}",
    response_model=SessionAnalytics,
    summary="Get session analytics",
    description="Get detailed analytics for a specific session",
)
async def get_session_analytics(session_id: UUID) -> SessionAnalytics:
    """
    Get analytics for a specific session.

    Provides insights into:
    - Message counts and patterns
    - Sentiment trends over the session
    - Risk events that occurred
    - Session duration
    """
    # Mock data for prototype
    # In production, this would query the database
    return SessionAnalytics(
        session_id=session_id,
        total_messages=10,
        user_messages=5,
        assistant_messages=5,
        average_response_time_ms=250.5,
        sentiment_trend=[],
        risk_events=[],
        duration_minutes=15.5,
    )


@router.get(
    "/clinician/analytics/patient/{patient_id}",
    response_model=UserAnalytics,
    summary="Get patient analytics",
    description="Get aggregated analytics for a patient across all sessions",
)
async def get_patient_analytics(patient_id: UUID) -> UserAnalytics:
    """
    Get aggregated analytics for a patient.

    Provides a holistic view of:
    - Session history and engagement
    - Overall sentiment patterns
    - Common topics and concerns
    - Engagement trends
    """
    # Mock data for prototype
    return UserAnalytics(
        user_id=patient_id,
        total_sessions=12,
        total_messages=156,
        average_session_duration_minutes=18.5,
        sentiment_distribution={},
        most_common_topics=["anxiety", "sleep", "work stress"],
        engagement_score=75.5,
    )


@router.get(
    "/clinician/dashboard/summary",
    summary="Get dashboard summary",
    description="Get summary statistics for clinician dashboard",
)
async def get_dashboard_summary():
    """
    Get summary statistics for the clinician dashboard.

    Includes:
    - Active patients count
    - Sessions today
    - Pending alerts
    - High-risk patients
    """
    # Mock data for prototype
    return {
        "active_patients": 24,
        "sessions_today": 8,
        "pending_alerts": len([a for a in _alerts if not getattr(a, "is_acknowledged", False)]),
        "high_risk_patients": 2,
        "critical_alerts": len([a for a in _alerts if a.risk_level == RiskLevel.CRITICAL]),
        "average_sentiment_today": "neutral",
        "total_messages_today": 156,
    }
