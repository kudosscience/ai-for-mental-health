"""Tests for sentiment analysis."""

import pytest

from mindwell.core.sentiment import SentimentAnalyzer, get_sentiment_analyzer
from mindwell.schemas import SentimentLevel


class TestSentimentAnalyzer:
    """Tests for the SentimentAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create a sentiment analyzer instance."""
        return SentimentAnalyzer()

    def test_positive_sentiment(self, analyzer):
        """Test detection of positive sentiment."""
        result = analyzer.analyze("I'm feeling happy and grateful today!")
        assert result.overall_sentiment in [SentimentLevel.POSITIVE, SentimentLevel.VERY_POSITIVE]
        assert result.confidence > 0

    def test_negative_sentiment(self, analyzer):
        """Test detection of negative sentiment."""
        result = analyzer.analyze("I feel sad and lonely.")
        assert result.overall_sentiment in [SentimentLevel.NEGATIVE, SentimentLevel.VERY_NEGATIVE]

    def test_neutral_sentiment(self, analyzer):
        """Test detection of neutral sentiment."""
        result = analyzer.analyze("The weather is cloudy today.")
        assert result.overall_sentiment == SentimentLevel.NEUTRAL

    def test_very_negative_sentiment(self, analyzer):
        """Test detection of very negative sentiment."""
        result = analyzer.analyze("I feel completely hopeless and worthless.")
        assert result.overall_sentiment == SentimentLevel.VERY_NEGATIVE

    def test_intensifier_detection(self, analyzer):
        """Test that intensifiers increase confidence."""
        regular = analyzer.analyze("I'm happy")
        intensified = analyzer.analyze("I'm very happy")
        # Intensified should have higher confidence
        assert intensified.confidence >= regular.confidence

    def test_negation_handling(self, analyzer):
        """Test that negations are handled correctly."""
        result = analyzer.analyze("I'm not happy at all")
        # Negated positive should not be positive
        assert result.overall_sentiment != SentimentLevel.VERY_POSITIVE

    def test_emotion_detection(self, analyzer):
        """Test that specific emotions are detected."""
        result = analyzer.analyze("I'm feeling very anxious and scared about the future")
        emotions = [e.emotion.value for e in result.emotions]
        assert "fear" in emotions

    def test_get_sentiment_analyzer_singleton(self):
        """Test that get_sentiment_analyzer returns singleton."""
        analyzer1 = get_sentiment_analyzer()
        analyzer2 = get_sentiment_analyzer()
        assert analyzer1 is analyzer2
