# MindWell AI - Mental Health Support Platform

An AI-powered mental health support platform designed for collaboration between patients and healthcare professionals.

## 🎯 Project Overview

MindWell AI is a conversational AI system that provides:
- **Supportive Conversations**: AI-powered chat for mental health support
- **Sentiment Analysis**: Real-time emotional state detection
- **Healthcare Collaboration**: Tools for clinicians to review sessions and provide oversight
- **Session Analytics**: Insights and trends for treatment planning

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Web Client    │────▶│   FastAPI       │────▶│   PostgreSQL    │
│   (Future)      │     │   Backend       │     │   Database      │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                        ┌────────▼────────┐
                        │  AI Services    │
                        │  - LLM Chat     │
                        │  - Sentiment    │
                        │  - Risk Assess  │
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │  OpenAI/Azure   │
                        │  API            │
                        └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- OpenAI API key or Azure OpenAI endpoint

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/mindwell-ai.git
cd mindwell-ai

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -e ".[dev]"

# Copy environment template
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac

# Edit .env with your configuration
```

### Configuration

Edit `.env` file with your settings:
```env
OPENAI_API_KEY=your-api-key
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/mindwell
```

### Running the Application

```bash
# Start the API server
uvicorn mindwell.api.main:app --reload

# Run tests
pytest

# Run with coverage
pytest --cov=mindwell
```

## 📁 Project Structure

```
ai-for-mental-health/
├── src/mindwell/
│   ├── api/              # FastAPI application
│   │   ├── routes/       # API endpoints
│   │   ├── middleware/   # Custom middleware
│   │   └── dependencies/ # Dependency injection
│   ├── core/             # Core business logic
│   │   ├── chat/         # Conversation handling
│   │   ├── sentiment/    # Sentiment analysis
│   │   └── risk/         # Risk assessment
│   ├── models/           # Database models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # External service integrations
│   └── utils/            # Utilities and helpers
├── tests/                # Test suite
├── docs/                 # Documentation
│   └── delivery/         # Project delivery docs
├── alembic/              # Database migrations
└── scripts/              # Utility scripts
```

## 🔒 Security & Compliance

This project is designed with healthcare compliance in mind:
- **Data Encryption**: All sensitive data encrypted at rest and in transit
- **Audit Logging**: Comprehensive logging for compliance requirements
- **Access Control**: Role-based access for healthcare professionals
- **Data Retention**: Configurable retention policies

> ⚠️ **Note**: This is a prototype. For production use in healthcare settings, 
> additional compliance measures (HIPAA, GDPR, etc.) must be implemented and verified.

## 🤝 Healthcare Collaboration Features

### For Clinicians
- Review patient conversation summaries
- Set custom safety thresholds
- Receive alerts for high-risk indicators
- Access analytics dashboards

### For Patients
- 24/7 supportive AI conversations
- Mood tracking and journaling
- Crisis resource access
- Session history review

## 📊 API Documentation

Once running, access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_chat.py

# Run with verbose output
pytest -v

# Run integration tests only
pytest tests/integration/
```

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for GPT models
- FastAPI framework
- Healthcare professionals who provided domain expertise
