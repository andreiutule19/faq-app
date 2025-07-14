# FAQ API - AI-Powered Question Answering System

A sophisticated FAQ system that combines semantic search with AI-powered responses. The system intelligently routes questions between a local knowledge base and OpenAI's GPT models for comprehensive IT support assistance.

## 🚀 Features

- **Intelligent Question Routing**: Automatically determines whether to use local FAQ database or OpenAI
- **Semantic Search**: Vector-based similarity matching using OpenAI embeddings
- **AI Fallback**: OpenAI integration for questions not covered in the local database
- **Async Processing**: Celery-based background tasks for embedding computation
- **Rate Limiting**: Built-in API rate limiting for production use
- **PostgreSQL + pgvector**: Efficient vector storage and similarity search
- **RESTful API**: Clean, documented API endpoints
- **Docker Support**: Containerized deployment ready

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with pgvector extension
- **AI/ML**: OpenAI API, vector embeddings
- **Task Queue**: Celery with Redis/RabbitMQ
- **Containerization**: Docker & Docker Compose
- **API Documentation**: Automatic OpenAPI/Swagger docs

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL with pgvector extension
- Redis (for Celery)
- OpenAI API key
- Docker (optional, for containerized deployment)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd faq-api
```

### 2. Environment Setup

Create a `.env` file in the root directory:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/faq_db

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# API Configuration
DEBUG=True
SECRET_KEY=your_secret_key_here
```

### 3. Installation Options

#### Option A: Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# Initialize database
docker-compose exec app python init_db.py
```

#### Option B: Manual Installation

```bash

# Create enviroment 
pipenv shell

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL and Redis services
# Run database initialization
python init_db.py

# Start Celery worker (in separate terminal)
celery -A app.core.celery_app worker --loglevel=info

# Start FastAPI server
python main.py
```

## 📖 API Documentation

Once the server is running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

### Key Endpoints

#### Ask a Question
```http
POST /api/v1/ask-question
Content-Type: application/json

{
  "user_question": "How do I reset my password?"
}
```

**Response:**
```json
{
  "source": "local",
  "matched_question": "What steps do I take to reset my password?",
  "answer": "Go to account settings, select 'Change Password'...",
  "similarity_score": 0.95
}
```

#### Compute Embeddings
```http
POST /api/v1/embeddings?collection=default
```

**Response:**
```json
{
  "message": "Embedding computation started for collection: default",
  "task_id": "abc123-def456-ghi789"
}
```

## 🏗️ Project Structure

```
app/
├── api/
│   └── endpoints.py          # API route definitions
├── core/
│   ├── celery_app.py        # Celery configuration
│   ├── rate_limiter.py      # Rate limiting logic
│   └── settings.py          # Application settings
├── models/
│   ├── db.py               # Database models
│   └── schemas.py          # Pydantic schemas
└── services/
    ├── embeddings_service.py   # Embedding computation
    ├── openai_service.py      # OpenAI integration
    └── similarity_service.py   # Similarity matching
```

## 💡 How It Works

1. **Question Processing**: User submits a question via API
2. **Similarity Search**: System searches local FAQ database using vector similarity
3. **Intelligent Routing**: 
   - **High similarity match** → Return local FAQ answer
   - **Low/no similarity** → Route to OpenAI for response
4. **Response Generation**: Return structured response with source attribution
5. **Logging**: All interactions logged for analysis and improvement


### OpenAI Integration

The system uses GPT-4o-mini with a specialized system prompt for IT support:
- Provides helpful IT guidance
- Politely redirects non-IT questions
- Maintains professional, actionable responses


## 🐳 Docker Deployment

```yaml
# docker-compose.yaml includes:
# - FastAPI application
# - PostgreSQL with pgvector
# - Redis for Celery
# - Celery worker
```

## 📈 Performance & Scaling

- **Response Times**: 1.4-6.1 seconds for typical queries
- **Vector Search**: Optimized with IVFFLAT indexes
- **Async Processing**: Background embedding computation
- **Rate Limiting**: Configurable API limits
- **Horizontal Scaling**: Stateless design supports multiple instances

## 🔗 Related Documentation

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Celery Documentation](https://docs.celeryproject.org/)

## 📞 Support

For questions, please:
- Open an issue on GitHub
- Check the API documentation at `Documentation.pdf`
- Review the test collection within documentationfor usage examples

