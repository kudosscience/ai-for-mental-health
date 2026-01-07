"""Core chat service for mental health conversations."""

from uuid import UUID, uuid4

import structlog
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from mindwell.config import Settings, get_settings
from mindwell.schemas import ChatMessage, ChatResponse, MessageRole, RiskLevel, SentimentLevel

logger = structlog.get_logger()


# System prompt for the mental health support AI
SYSTEM_PROMPT = """You are MindWell, a compassionate and supportive AI assistant specialized in mental health support. Your role is to:

1. Listen actively and empathetically to users sharing their feelings and experiences
2. Provide supportive, non-judgmental responses that validate their emotions
3. Offer evidence-based coping strategies when appropriate
4. Encourage professional help when needed, without being pushy
5. Maintain appropriate boundaries - you are not a replacement for professional therapy

IMPORTANT GUIDELINES:
- Never provide medical diagnoses or prescribe treatments
- If someone expresses thoughts of self-harm or suicide, immediately provide crisis resources
- Use warm, conversational language while maintaining professionalism
- Ask open-ended questions to encourage users to share more
- Recognize and validate emotions before offering suggestions
- Be culturally sensitive and inclusive

CRISIS RESOURCES TO PROVIDE WHEN NEEDED:
- National Suicide Prevention Lifeline: 988
- Crisis Text Line: Text HOME to 741741
- Emergency: 911

Remember: Your goal is to provide immediate emotional support and guide users toward appropriate resources, not to replace professional mental health care."""


class ChatService:
    """Service for handling AI-powered mental health conversations."""

    def __init__(self, settings: Settings | None = None):
        """Initialize the chat service."""
        self.settings = settings or get_settings()
        self._client: AsyncOpenAI | None = None

    @property
    def client(self) -> AsyncOpenAI:
        """Get or create the OpenAI client."""
        if self._client is None:
            if self.settings.use_azure_openai:
                from openai import AsyncAzureOpenAI

                self._client = AsyncAzureOpenAI(
                    api_key=self.settings.azure_openai_api_key.get_secret_value(),
                    azure_endpoint=self.settings.azure_openai_endpoint,
                    api_version=self.settings.azure_openai_api_version,
                )
            else:
                self._client = AsyncOpenAI(
                    api_key=self.settings.openai_api_key.get_secret_value()
                )
        return self._client

    async def generate_response(
        self,
        user_message: str,
        conversation_history: list[ChatMessage] | None = None,
        session_id: UUID | None = None,
    ) -> ChatResponse:
        """
        Generate an AI response to a user message.

        Args:
            user_message: The user's input message
            conversation_history: Previous messages in the conversation
            session_id: Existing session ID or None to create new

        Returns:
            ChatResponse with the AI's response and analysis
        """
        session_id = session_id or uuid4()
        history = conversation_history or []

        # Build messages for the API call
        messages = self._build_messages(user_message, history)

        try:
            # Call the LLM
            completion: ChatCompletion = await self.client.chat.completions.create(
                model=self._get_model_name(),
                messages=messages,
                temperature=self.settings.llm_temperature,
                max_tokens=self.settings.llm_max_tokens,
            )

            response_text = completion.choices[0].message.content or ""

            # Analyze the conversation for sentiment and risk
            sentiment = await self._analyze_sentiment(user_message)
            risk_level, show_crisis = await self._assess_risk(user_message, response_text)

            logger.info(
                "chat_response_generated",
                session_id=str(session_id),
                sentiment=sentiment.value if sentiment else None,
                risk_level=risk_level.value if risk_level else None,
                tokens_used=completion.usage.total_tokens if completion.usage else None,
            )

            return ChatResponse(
                session_id=session_id,
                message=response_text,
                sentiment=sentiment,
                risk_level=risk_level,
                show_crisis_resources=show_crisis,
            )

        except Exception as e:
            logger.error(
                "chat_generation_failed",
                session_id=str(session_id),
                error=str(e),
            )
            raise

    def _build_messages(
        self, user_message: str, history: list[ChatMessage]
    ) -> list[dict]:
        """Build the messages list for the OpenAI API."""
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Add conversation history
        for msg in history[-10:]:  # Keep last 10 messages for context
            messages.append({
                "role": msg.role.value,
                "content": msg.content,
            })

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        return messages

    def _get_model_name(self) -> str:
        """Get the appropriate model name based on configuration."""
        if self.settings.use_azure_openai:
            return self.settings.azure_openai_deployment_name
        return self.settings.llm_model

    async def _analyze_sentiment(self, text: str) -> SentimentLevel | None:
        """
        Analyze the sentiment of the user's message.

        This is a simplified implementation. In production, you might use
        a dedicated sentiment analysis model or service.
        """
        # Simple keyword-based sentiment for demonstration
        # In production, use a proper sentiment analysis model
        text_lower = text.lower()

        very_negative_keywords = [
            "hopeless", "worthless", "suicidal", "kill myself", "end it all",
            "no point", "want to die", "can't go on"
        ]
        negative_keywords = [
            "sad", "depressed", "anxious", "worried", "scared", "angry",
            "frustrated", "lonely", "tired", "exhausted", "stressed"
        ]
        positive_keywords = [
            "happy", "better", "good", "hopeful", "grateful", "excited",
            "calm", "peaceful", "proud", "accomplished"
        ]
        very_positive_keywords = [
            "amazing", "wonderful", "fantastic", "thrilled", "overjoyed",
            "incredible", "blessed"
        ]

        if any(kw in text_lower for kw in very_negative_keywords):
            return SentimentLevel.VERY_NEGATIVE
        if any(kw in text_lower for kw in very_positive_keywords):
            return SentimentLevel.VERY_POSITIVE
        if any(kw in text_lower for kw in negative_keywords):
            return SentimentLevel.NEGATIVE
        if any(kw in text_lower for kw in positive_keywords):
            return SentimentLevel.POSITIVE

        return SentimentLevel.NEUTRAL

    async def _assess_risk(
        self, user_message: str, ai_response: str
    ) -> tuple[RiskLevel | None, bool]:
        """
        Assess the risk level based on the user's message.

        Returns:
            Tuple of (risk_level, should_show_crisis_resources)
        """
        text_lower = user_message.lower()

        # Critical risk indicators - immediate crisis
        critical_keywords = [
            "kill myself", "suicide", "end my life", "want to die",
            "better off dead", "no reason to live", "self harm",
            "hurt myself"
        ]

        # High risk indicators
        high_risk_keywords = [
            "hopeless", "worthless", "can't go on", "no point",
            "giving up", "nothing matters", "no one cares"
        ]

        # Moderate risk indicators
        moderate_keywords = [
            "depressed", "really struggling", "can't cope",
            "falling apart", "breaking down"
        ]

        if any(kw in text_lower for kw in critical_keywords):
            return RiskLevel.CRITICAL, True

        if any(kw in text_lower for kw in high_risk_keywords):
            return RiskLevel.HIGH, True

        if any(kw in text_lower for kw in moderate_keywords):
            return RiskLevel.MODERATE, False

        return RiskLevel.LOW, False


# Singleton instance
_chat_service: ChatService | None = None


def get_chat_service() -> ChatService:
    """Get the chat service singleton."""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
