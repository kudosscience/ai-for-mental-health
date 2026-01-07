"""Chat API endpoints."""

from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status

from mindwell.core.chat import get_chat_service
from mindwell.core.risk import get_risk_assessor
from mindwell.core.sentiment import get_sentiment_analyzer
from mindwell.schemas import ChatMessage, ChatRequest, ChatResponse, MessageRole, RiskLevel

router = APIRouter()
logger = structlog.get_logger()

# In-memory session storage for prototype
# In production, use database storage
_session_history: dict[UUID, list[ChatMessage]] = {}


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a chat message",
    description="Send a message to the AI mental health assistant and receive a supportive response",
)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Process a chat message and return an AI response.

    The endpoint:
    1. Analyzes the user's message for sentiment and risk
    2. Generates an empathetic AI response
    3. Returns crisis resources if high risk is detected
    4. Maintains conversation context for the session

    Args:
        request: ChatRequest containing the user's message and optional session_id

    Returns:
        ChatResponse with AI response, sentiment analysis, and risk assessment
    """
    try:
        chat_service = get_chat_service()
        sentiment_analyzer = get_sentiment_analyzer()
        risk_assessor = get_risk_assessor()

        # Get or create session history
        session_id = request.session_id
        history = _session_history.get(session_id, []) if session_id else []

        # Analyze user message
        sentiment_result = sentiment_analyzer.analyze(request.message)
        context_messages = [msg.content for msg in history if msg.role == MessageRole.USER]
        risk_result = risk_assessor.assess(request.message, context_messages)

        # Generate AI response
        response = await chat_service.generate_response(
            user_message=request.message,
            conversation_history=history,
            session_id=session_id,
        )

        # Update response with analysis results
        response.sentiment = sentiment_result.overall_sentiment
        response.risk_level = risk_result.overall_level
        response.show_crisis_resources = risk_result.crisis_resources_shown

        # Append crisis message if needed
        if risk_result.overall_level == RiskLevel.CRITICAL:
            crisis_message = risk_assessor.get_crisis_message()
            response.message = f"{response.message}\n\n---\n{crisis_message}"

        # Store messages in session history
        user_message = ChatMessage(role=MessageRole.USER, content=request.message)
        assistant_message = ChatMessage(role=MessageRole.ASSISTANT, content=response.message)

        if response.session_id not in _session_history:
            _session_history[response.session_id] = []
        _session_history[response.session_id].extend([user_message, assistant_message])

        logger.info(
            "chat_completed",
            session_id=str(response.session_id),
            sentiment=response.sentiment.value if response.sentiment else None,
            risk_level=response.risk_level.value if response.risk_level else None,
        )

        return response

    except Exception as e:
        logger.error("chat_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat message. Please try again.",
        )


@router.get(
    "/chat/{session_id}/history",
    response_model=list[ChatMessage],
    summary="Get chat history",
    description="Retrieve the conversation history for a specific session",
)
async def get_chat_history(session_id: UUID) -> list[ChatMessage]:
    """
    Get the chat history for a session.

    Args:
        session_id: The UUID of the chat session

    Returns:
        List of ChatMessage objects in chronological order
    """
    if session_id not in _session_history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    return _session_history[session_id]


@router.delete(
    "/chat/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="End chat session",
    description="End and clear a chat session",
)
async def end_chat_session(session_id: UUID):
    """
    End a chat session and clear its history.

    Args:
        session_id: The UUID of the chat session to end
    """
    if session_id in _session_history:
        del _session_history[session_id]
        logger.info("session_ended", session_id=str(session_id))
