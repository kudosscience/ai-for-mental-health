"""Sentiment analysis service for mental health conversations."""

from dataclasses import dataclass
from enum import Enum

import structlog

from mindwell.schemas import SentimentLevel

logger = structlog.get_logger()


class EmotionCategory(str, Enum):
    """Categories of emotions detected in text."""

    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    TRUST = "trust"
    ANTICIPATION = "anticipation"


@dataclass
class EmotionScore:
    """Score for a detected emotion."""

    emotion: EmotionCategory
    confidence: float
    keywords_found: list[str]


@dataclass
class SentimentResult:
    """Complete sentiment analysis result."""

    overall_sentiment: SentimentLevel
    confidence: float
    emotions: list[EmotionScore]
    dominant_emotion: EmotionCategory | None


class SentimentAnalyzer:
    """
    Sentiment analysis service for mental health conversations.
    
    This provides keyword-based sentiment analysis suitable for a prototype.
    In production, consider integrating with:
    - Azure Cognitive Services Text Analytics
    - Google Cloud Natural Language API
    - Custom fine-tuned transformer models
    """

    # Emotion keyword mappings with associated sentiment weights
    EMOTION_KEYWORDS = {
        EmotionCategory.JOY: {
            "keywords": [
                "happy", "joyful", "excited", "glad", "pleased", "delighted",
                "cheerful", "content", "grateful", "thankful", "blessed",
                "wonderful", "amazing", "fantastic", "great", "good", "nice",
                "love", "loving", "caring", "hopeful", "optimistic"
            ],
            "sentiment_weight": 1.0,
        },
        EmotionCategory.SADNESS: {
            "keywords": [
                "sad", "unhappy", "miserable", "depressed", "down", "low",
                "heartbroken", "grief", "mourning", "loss", "lonely", "alone",
                "empty", "numb", "hopeless", "helpless", "worthless", "useless",
                "crying", "tears", "sobbing", "melancholy", "despair"
            ],
            "sentiment_weight": -0.8,
        },
        EmotionCategory.ANGER: {
            "keywords": [
                "angry", "furious", "rage", "mad", "annoyed", "irritated",
                "frustrated", "resentful", "bitter", "hostile", "hate",
                "disgusted", "outraged", "enraged", "livid", "fuming"
            ],
            "sentiment_weight": -0.6,
        },
        EmotionCategory.FEAR: {
            "keywords": [
                "afraid", "scared", "frightened", "terrified", "anxious",
                "worried", "nervous", "panicked", "panic", "dread", "horror",
                "alarmed", "uneasy", "tense", "stressed", "overwhelmed",
                "paranoid", "phobia", "fearful"
            ],
            "sentiment_weight": -0.7,
        },
        EmotionCategory.SURPRISE: {
            "keywords": [
                "surprised", "shocked", "amazed", "astonished", "stunned",
                "startled", "unexpected", "sudden", "wow"
            ],
            "sentiment_weight": 0.0,  # Neutral - context dependent
        },
        EmotionCategory.DISGUST: {
            "keywords": [
                "disgusted", "revolted", "sickened", "repulsed", "gross",
                "nauseated", "appalled"
            ],
            "sentiment_weight": -0.5,
        },
        EmotionCategory.TRUST: {
            "keywords": [
                "trust", "faith", "confident", "secure", "safe", "reliable",
                "believe", "believing", "comfortable", "assured"
            ],
            "sentiment_weight": 0.6,
        },
        EmotionCategory.ANTICIPATION: {
            "keywords": [
                "excited", "eager", "looking forward", "anticipating",
                "expecting", "hoping", "curious", "interested"
            ],
            "sentiment_weight": 0.4,
        },
    }

    # Intensity modifiers
    INTENSIFIERS = {
        "very": 1.5,
        "really": 1.4,
        "extremely": 1.8,
        "incredibly": 1.7,
        "so": 1.3,
        "super": 1.4,
        "absolutely": 1.6,
        "completely": 1.5,
        "totally": 1.4,
        "deeply": 1.5,
    }

    DIMINISHERS = {
        "slightly": 0.5,
        "somewhat": 0.6,
        "a bit": 0.5,
        "a little": 0.5,
        "kind of": 0.6,
        "sort of": 0.6,
        "barely": 0.3,
    }

    NEGATIONS = ["not", "no", "never", "don't", "doesn't", "didn't", "won't", "wouldn't", "can't", "couldn't"]

    def analyze(self, text: str) -> SentimentResult:
        """
        Analyze the sentiment and emotions in a text.

        Args:
            text: The text to analyze

        Returns:
            SentimentResult with overall sentiment and emotion breakdown
        """
        text_lower = text.lower()
        words = text_lower.split()
        
        emotion_scores: list[EmotionScore] = []
        total_sentiment_score = 0.0
        total_weight = 0.0

        # Detect emotions
        for emotion, config in self.EMOTION_KEYWORDS.items():
            keywords_found = []
            base_confidence = 0.0

            for keyword in config["keywords"]:
                if keyword in text_lower:
                    keywords_found.append(keyword)
                    # Check for intensifiers/diminishers near the keyword
                    intensity = self._get_intensity_modifier(text_lower, keyword)
                    # Check for negation
                    if self._is_negated(text_lower, keyword):
                        intensity *= -1
                    base_confidence += 0.2 * intensity

            if keywords_found:
                confidence = min(base_confidence, 1.0)
                emotion_scores.append(EmotionScore(
                    emotion=emotion,
                    confidence=confidence,
                    keywords_found=keywords_found,
                ))
                total_sentiment_score += config["sentiment_weight"] * confidence
                total_weight += confidence

        # Calculate overall sentiment
        if total_weight > 0:
            normalized_score = total_sentiment_score / total_weight
        else:
            normalized_score = 0.0

        overall_sentiment = self._score_to_sentiment_level(normalized_score)
        confidence = min(total_weight / 2, 1.0)  # Cap at 1.0

        # Find dominant emotion
        dominant_emotion = None
        if emotion_scores:
            dominant = max(emotion_scores, key=lambda x: x.confidence)
            if dominant.confidence > 0.3:
                dominant_emotion = dominant.emotion

        logger.debug(
            "sentiment_analyzed",
            overall_sentiment=overall_sentiment.value,
            confidence=confidence,
            emotion_count=len(emotion_scores),
            dominant_emotion=dominant_emotion.value if dominant_emotion else None,
        )

        return SentimentResult(
            overall_sentiment=overall_sentiment,
            confidence=confidence,
            emotions=emotion_scores,
            dominant_emotion=dominant_emotion,
        )

    def _get_intensity_modifier(self, text: str, keyword: str) -> float:
        """Get intensity modifier for a keyword based on surrounding words."""
        # Find position of keyword
        keyword_pos = text.find(keyword)
        if keyword_pos == -1:
            return 1.0

        # Get words before the keyword (within 3 words)
        prefix = text[:keyword_pos].split()[-3:]
        prefix_text = " ".join(prefix)

        # Check for intensifiers
        for intensifier, multiplier in self.INTENSIFIERS.items():
            if intensifier in prefix_text:
                return multiplier

        # Check for diminishers
        for diminisher, multiplier in self.DIMINISHERS.items():
            if diminisher in prefix_text:
                return multiplier

        return 1.0

    def _is_negated(self, text: str, keyword: str) -> bool:
        """Check if a keyword is negated."""
        keyword_pos = text.find(keyword)
        if keyword_pos == -1:
            return False

        # Check for negations in the 4 words before the keyword
        prefix = text[:keyword_pos].split()[-4:]

        for negation in self.NEGATIONS:
            if negation in prefix:
                return True

        return False

    def _score_to_sentiment_level(self, score: float) -> SentimentLevel:
        """Convert a numeric score to a sentiment level."""
        if score <= -0.6:
            return SentimentLevel.VERY_NEGATIVE
        if score <= -0.2:
            return SentimentLevel.NEGATIVE
        if score >= 0.6:
            return SentimentLevel.VERY_POSITIVE
        if score >= 0.2:
            return SentimentLevel.POSITIVE
        return SentimentLevel.NEUTRAL


# Singleton instance
_sentiment_analyzer: SentimentAnalyzer | None = None


def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Get the sentiment analyzer singleton."""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentAnalyzer()
    return _sentiment_analyzer
