"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient

from mindwell.api.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_chat_message():
    """Sample chat message for testing."""
    return {
        "message": "I've been feeling anxious lately about work."
    }


@pytest.fixture
def crisis_message():
    """Sample crisis message for testing risk detection."""
    return {
        "message": "I feel like I want to end it all. Nothing matters anymore."
    }


@pytest.fixture
def positive_message():
    """Sample positive message for testing sentiment."""
    return {
        "message": "I'm feeling so much better today! Things are looking up."
    }
