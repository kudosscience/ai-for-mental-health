"""Tests for risk assessment."""

import pytest

from mindwell.core.risk import RiskAssessor, get_risk_assessor
from mindwell.schemas import RiskLevel


class TestRiskAssessor:
    """Tests for the RiskAssessor class."""

    @pytest.fixture
    def assessor(self):
        """Create a risk assessor instance."""
        return RiskAssessor()

    def test_low_risk_message(self, assessor):
        """Test that normal messages are low risk."""
        result = assessor.assess("I'm having a regular day at work.")
        assert result.overall_level == RiskLevel.LOW

    def test_moderate_risk_message(self, assessor):
        """Test detection of moderate risk."""
        result = assessor.assess("I'm really struggling to cope with everything.")
        assert result.overall_level == RiskLevel.MODERATE

    def test_high_risk_message(self, assessor):
        """Test detection of high risk."""
        result = assessor.assess("I feel completely hopeless. Nothing will ever get better.")
        assert result.overall_level == RiskLevel.HIGH
        assert result.crisis_resources_shown

    def test_critical_risk_suicide_ideation(self, assessor):
        """Test detection of critical risk with suicidal ideation."""
        result = assessor.assess("I want to kill myself.")
        assert result.overall_level == RiskLevel.CRITICAL
        assert result.crisis_resources_shown
        assert len(result.indicators) > 0

    def test_critical_risk_self_harm(self, assessor):
        """Test detection of critical risk with self-harm mention."""
        result = assessor.assess("I've been thinking about hurting myself.")
        assert result.overall_level == RiskLevel.CRITICAL

    def test_recommendations_generated(self, assessor):
        """Test that recommendations are generated."""
        result = assessor.assess("I feel hopeless and worthless.")
        assert len(result.recommended_actions) > 0

    def test_crisis_message_generation(self, assessor):
        """Test crisis message is properly formatted."""
        crisis_msg = assessor.get_crisis_message()
        assert "988" in crisis_msg  # Crisis hotline
        assert "741741" in crisis_msg  # Text line
        assert "911" in crisis_msg  # Emergency

    def test_context_escalation(self, assessor):
        """Test that escalating context is detected."""
        context = [
            "I'm feeling a bit sad today",
            "Things aren't getting better",
            "I feel completely hopeless",
            "Nobody cares about me",
            "I can't go on like this",
        ]
        result = assessor.assess("Everything is pointless", context=context)
        # Should detect escalating pattern
        assert result.overall_level in [RiskLevel.MODERATE, RiskLevel.HIGH]

    def test_get_risk_assessor_singleton(self):
        """Test that get_risk_assessor returns singleton."""
        assessor1 = get_risk_assessor()
        assessor2 = get_risk_assessor()
        assert assessor1 is assessor2
