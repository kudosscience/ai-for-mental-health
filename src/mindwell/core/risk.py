"""Risk assessment service for mental health safety monitoring."""

from dataclasses import dataclass, field
from datetime import datetime

import structlog

from mindwell.config import get_settings
from mindwell.schemas import RiskAssessment, RiskIndicator, RiskLevel

logger = structlog.get_logger()


@dataclass
class RiskPattern:
    """A pattern indicating potential risk."""

    keywords: list[str]
    category: str
    severity: RiskLevel
    description: str
    requires_attention: bool = False


@dataclass
class CrisisResources:
    """Crisis intervention resources."""

    hotline: str
    text_line: str
    emergency: str
    additional_resources: list[str] = field(default_factory=list)


class RiskAssessor:
    """
    Risk assessment service for identifying mental health concerns.
    
    This service analyzes user messages for indicators of:
    - Suicidal ideation
    - Self-harm
    - Crisis situations
    - Severe distress
    
    IMPORTANT: This is a supportive tool and should NOT replace
    professional clinical assessment. Always encourage users to
    seek professional help when appropriate.
    """

    # Risk patterns organized by severity
    RISK_PATTERNS: list[RiskPattern] = [
        # CRITICAL - Immediate danger
        RiskPattern(
            keywords=[
                "kill myself", "suicide", "suicidal", "end my life",
                "want to die", "better off dead", "no reason to live",
                "end it all", "take my own life", "commit suicide"
            ],
            category="suicidal_ideation",
            severity=RiskLevel.CRITICAL,
            description="Expression of suicidal thoughts or intent",
            requires_attention=True,
        ),
        RiskPattern(
            keywords=[
                "hurt myself", "self harm", "cut myself", "cutting",
                "burn myself", "harm myself", "injure myself"
            ],
            category="self_harm",
            severity=RiskLevel.CRITICAL,
            description="Expression of self-harm thoughts or behaviors",
            requires_attention=True,
        ),
        RiskPattern(
            keywords=[
                "plan to die", "suicide plan", "method to",
                "pills to", "gun to", "rope to", "bridge to jump"
            ],
            category="suicide_planning",
            severity=RiskLevel.CRITICAL,
            description="Indication of specific suicide planning",
            requires_attention=True,
        ),
        # HIGH - Serious concern
        RiskPattern(
            keywords=[
                "hopeless", "no hope", "never get better",
                "nothing will help", "pointless", "no point in trying"
            ],
            category="hopelessness",
            severity=RiskLevel.HIGH,
            description="Expression of persistent hopelessness",
            requires_attention=True,
        ),
        RiskPattern(
            keywords=[
                "worthless", "burden to everyone", "everyone hates me",
                "no one cares", "better without me", "don't deserve"
            ],
            category="worthlessness",
            severity=RiskLevel.HIGH,
            description="Expression of severe worthlessness or being a burden",
            requires_attention=True,
        ),
        RiskPattern(
            keywords=[
                "can't go on", "can't take it anymore", "giving up",
                "done with everything", "had enough"
            ],
            category="desperation",
            severity=RiskLevel.HIGH,
            description="Expression of desperation or giving up",
            requires_attention=True,
        ),
        # MODERATE - Requires monitoring
        RiskPattern(
            keywords=[
                "really struggling", "falling apart", "breaking down",
                "can't cope", "overwhelmed", "drowning"
            ],
            category="severe_distress",
            severity=RiskLevel.MODERATE,
            description="Expression of severe emotional distress",
            requires_attention=False,
        ),
        RiskPattern(
            keywords=[
                "haven't slept", "can't sleep", "not eating",
                "stopped eating", "can't get out of bed"
            ],
            category="functional_impairment",
            severity=RiskLevel.MODERATE,
            description="Signs of significant functional impairment",
            requires_attention=False,
        ),
        RiskPattern(
            keywords=[
                "isolated", "all alone", "no friends", "no one to talk to",
                "completely alone", "abandoned"
            ],
            category="social_isolation",
            severity=RiskLevel.MODERATE,
            description="Expression of severe social isolation",
            requires_attention=False,
        ),
    ]

    def __init__(self):
        """Initialize the risk assessor."""
        settings = get_settings()
        self.crisis_resources = CrisisResources(
            hotline=settings.crisis_hotline_number,
            text_line=settings.crisis_text_line,
            emergency=settings.emergency_number,
            additional_resources=[
                "International Association for Suicide Prevention: https://www.iasp.info/resources/Crisis_Centres/",
                "Crisis Text Line: Text HOME to 741741",
                "Veterans Crisis Line: 1-800-273-8255, Press 1",
            ],
        )

    def assess(self, text: str, context: list[str] | None = None) -> RiskAssessment:
        """
        Assess the risk level of a user's message.

        Args:
            text: The user's message to assess
            context: Optional list of previous messages for context

        Returns:
            RiskAssessment with identified indicators and recommendations
        """
        text_lower = text.lower()
        indicators: list[RiskIndicator] = []
        highest_severity = RiskLevel.LOW

        # Check for risk patterns
        for pattern in self.RISK_PATTERNS:
            if any(keyword in text_lower for keyword in pattern.keywords):
                indicator = RiskIndicator(
                    category=pattern.category,
                    description=pattern.description,
                    severity=pattern.severity,
                    requires_attention=pattern.requires_attention,
                )
                indicators.append(indicator)

                # Track highest severity
                if self._severity_rank(pattern.severity) > self._severity_rank(highest_severity):
                    highest_severity = pattern.severity

        # Check context for escalating patterns
        if context:
            context_risk = self._analyze_context(context)
            if context_risk and self._severity_rank(context_risk) > self._severity_rank(highest_severity):
                highest_severity = context_risk
                indicators.append(RiskIndicator(
                    category="escalating_pattern",
                    description="Conversation shows escalating distress patterns",
                    severity=context_risk,
                    requires_attention=context_risk in [RiskLevel.CRITICAL, RiskLevel.HIGH],
                ))

        # Generate recommendations
        recommendations = self._generate_recommendations(highest_severity, indicators)
        show_crisis = highest_severity in [RiskLevel.CRITICAL, RiskLevel.HIGH]

        logger.info(
            "risk_assessed",
            risk_level=highest_severity.value,
            indicator_count=len(indicators),
            show_crisis_resources=show_crisis,
        )

        return RiskAssessment(
            overall_level=highest_severity,
            indicators=indicators,
            recommended_actions=recommendations,
            crisis_resources_shown=show_crisis,
        )

    def _severity_rank(self, level: RiskLevel) -> int:
        """Get numeric rank for severity comparison."""
        ranks = {
            RiskLevel.LOW: 0,
            RiskLevel.MODERATE: 1,
            RiskLevel.HIGH: 2,
            RiskLevel.CRITICAL: 3,
        }
        return ranks.get(level, 0)

    def _analyze_context(self, context: list[str]) -> RiskLevel | None:
        """
        Analyze conversation context for escalating patterns.

        Looks for:
        - Increasing negative sentiment over time
        - Repeated expressions of distress
        - Progression toward more severe language
        """
        if len(context) < 3:
            return None

        negative_count = 0
        severe_count = 0

        severe_words = ["hopeless", "worthless", "can't", "never", "always", "nobody"]
        negative_words = ["sad", "depressed", "anxious", "worried", "scared", "angry"]

        for message in context[-5:]:  # Look at last 5 messages
            msg_lower = message.lower()
            if any(word in msg_lower for word in negative_words):
                negative_count += 1
            if any(word in msg_lower for word in severe_words):
                severe_count += 1

        # Escalating pattern detection
        if severe_count >= 3:
            return RiskLevel.HIGH
        if negative_count >= 4:
            return RiskLevel.MODERATE

        return None

    def _generate_recommendations(
        self, risk_level: RiskLevel, indicators: list[RiskIndicator]
    ) -> list[str]:
        """Generate recommended actions based on risk assessment."""
        recommendations = []

        if risk_level == RiskLevel.CRITICAL:
            recommendations.extend([
                f"If you're in immediate danger, please call {self.crisis_resources.emergency}",
                f"National Suicide Prevention Lifeline: {self.crisis_resources.hotline}",
                f"Crisis Text Line: {self.crisis_resources.text_line}",
                "Please reach out to a trusted person - you don't have to face this alone",
                "Consider going to your nearest emergency room",
            ])
        elif risk_level == RiskLevel.HIGH:
            recommendations.extend([
                f"Please consider calling the crisis line: {self.crisis_resources.hotline}",
                "Reaching out to a mental health professional is recommended",
                "Talk to someone you trust about how you're feeling",
                "You deserve support - please don't hesitate to ask for help",
            ])
        elif risk_level == RiskLevel.MODERATE:
            recommendations.extend([
                "Consider scheduling an appointment with a mental health professional",
                "Practice self-care and reach out to supportive people in your life",
                "Remember that seeking help is a sign of strength",
            ])
        else:
            recommendations.extend([
                "Continue taking care of your mental well-being",
                "Regular check-ins with a mental health professional can be beneficial",
            ])

        return recommendations

    def get_crisis_message(self) -> str:
        """Get a formatted crisis resources message."""
        return f"""
I'm concerned about what you've shared, and I want you to know that help is available.

**If you're in immediate danger:**
- Emergency: {self.crisis_resources.emergency}

**Crisis Support Lines (24/7):**
- National Suicide Prevention Lifeline: {self.crisis_resources.hotline}
- Crisis Text Line: {self.crisis_resources.text_line}

You're not alone, and there are people who want to help. Please reach out.
"""


# Singleton instance
_risk_assessor: RiskAssessor | None = None


def get_risk_assessor() -> RiskAssessor:
    """Get the risk assessor singleton."""
    global _risk_assessor
    if _risk_assessor is None:
        _risk_assessor = RiskAssessor()
    return _risk_assessor
