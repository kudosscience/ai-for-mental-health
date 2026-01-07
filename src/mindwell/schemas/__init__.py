"""Pydantic schemas for API request/response models."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================


class SentimentLevel(str, Enum):
    """Sentiment classification levels."""

    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


class RiskLevel(str, Enum):
    """Risk assessment levels for mental health indicators."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class MessageRole(str, Enum):
    """Role of the message sender."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class SessionStatus(str, Enum):
    """Status of a chat session."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FLAGGED = "flagged"


# =============================================================================
# Base Schemas
# =============================================================================


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    class Config:
        from_attributes = True


# =============================================================================
# User Schemas
# =============================================================================


class UserBase(BaseSchema):
    """Base user schema."""

    email: str = Field(..., description="User email address")
    full_name: str | None = Field(None, description="User's full name")


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(..., min_length=8, description="User password")


class UserResponse(UserBase):
    """Schema for user response."""

    id: UUID
    is_active: bool
    is_clinician: bool
    created_at: datetime


# =============================================================================
# Chat Schemas
# =============================================================================


class ChatMessage(BaseSchema):
    """A single chat message."""

    role: MessageRole
    content: str = Field(..., min_length=1, max_length=10000)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseSchema):
    """Request schema for chat endpoint."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="The user's message",
    )
    session_id: UUID | None = Field(
        None,
        description="Existing session ID to continue conversation",
    )


class ChatResponse(BaseSchema):
    """Response schema for chat endpoint."""

    session_id: UUID
    message: str
    sentiment: SentimentLevel | None = None
    risk_level: RiskLevel | None = None
    show_crisis_resources: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Session Schemas
# =============================================================================


class SessionBase(BaseSchema):
    """Base session schema."""

    title: str | None = Field(None, description="Optional session title")


class SessionCreate(SessionBase):
    """Schema for creating a new session."""

    pass


class SessionSummary(BaseSchema):
    """Summary of a chat session for listing."""

    id: UUID
    title: str | None
    status: SessionStatus
    message_count: int
    average_sentiment: SentimentLevel | None
    highest_risk_level: RiskLevel | None
    created_at: datetime
    updated_at: datetime


class SessionDetail(SessionSummary):
    """Detailed session information including messages."""

    messages: list[ChatMessage]
    clinician_notes: str | None = None


# =============================================================================
# Sentiment Analysis Schemas
# =============================================================================


class SentimentAnalysis(BaseSchema):
    """Result of sentiment analysis."""

    level: SentimentLevel
    confidence: float = Field(..., ge=0.0, le=1.0)
    emotions: dict[str, float] = Field(
        default_factory=dict,
        description="Detected emotions with confidence scores",
    )


# =============================================================================
# Risk Assessment Schemas
# =============================================================================


class RiskIndicator(BaseSchema):
    """A specific risk indicator detected."""

    category: str
    description: str
    severity: RiskLevel
    requires_attention: bool = False


class RiskAssessment(BaseSchema):
    """Result of risk assessment."""

    overall_level: RiskLevel
    indicators: list[RiskIndicator]
    recommended_actions: list[str]
    crisis_resources_shown: bool


# =============================================================================
# Analytics Schemas
# =============================================================================


class SessionAnalytics(BaseSchema):
    """Analytics for a specific session."""

    session_id: UUID
    total_messages: int
    user_messages: int
    assistant_messages: int
    average_response_time_ms: float | None
    sentiment_trend: list[SentimentLevel]
    risk_events: list[RiskIndicator]
    duration_minutes: float


class UserAnalytics(BaseSchema):
    """Aggregated analytics for a user."""

    user_id: UUID
    total_sessions: int
    total_messages: int
    average_session_duration_minutes: float
    sentiment_distribution: dict[SentimentLevel, int]
    most_common_topics: list[str]
    engagement_score: float = Field(..., ge=0.0, le=100.0)


# =============================================================================
# Clinician Schemas
# =============================================================================


class ClinicianNote(BaseSchema):
    """Note added by a clinician to a session."""

    session_id: UUID
    note: str = Field(..., min_length=1, max_length=5000)
    is_private: bool = Field(
        default=True,
        description="Whether note is visible only to clinicians",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ClinicianAlert(BaseSchema):
    """Alert sent to clinician about a patient."""

    patient_id: UUID
    session_id: UUID
    alert_type: str
    risk_level: RiskLevel
    summary: str
    requires_immediate_attention: bool
    created_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Health Check Schemas
# =============================================================================


class HealthCheck(BaseSchema):
    """Health check response."""

    status: str = "healthy"
    version: str
    environment: str
    database_connected: bool
    llm_available: bool
