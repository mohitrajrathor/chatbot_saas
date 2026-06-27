# RAG Chatbot SaaS Platform

A multi-user SaaS platform to create and deploy RAG-powered AI chatbots backed by custom document knowledge bases. Users manage chatbots via a web dashboard and expose them via a REST API for third-party integrations.

---

## Features

- Create multiple chatbots, each with its own documents and LLM instructions
- Upload PDF, DOCX, TXT files or index URLs as knowledge sources
- Stateless RAG query pipeline with context-aware responses
- Input/output safety filtering via a HuggingFace guardrails classifier
- API key generation for third-party REST access
- Web chatbot with public or restricted access control
- RAG quality evaluation using RAGAS (upload a test set, get scored results)
- Asynchronous document ingestion and evaluation via Celery

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vue 3, PrimeVue 4, TailwindCSS, Pinia, Axios |
| Backend | FastAPI, SQLAlchemy, Alembic, Pydantic |
| Worker | Celery, Redis |
| Database | PostgreSQL 15 |
| Vector Store | Pinecone (Starter) |
| LLM | Groq API (`llama-3.3-70b-versatile`) / NVIDIA NIM |
| Embeddings | HuggingFace `BAAI/bge-small-en-v1.5` (local) |
| Guardrails | HuggingFace `unitary/toxic-bert` (local) |
| RAG Framework | LangChain |
| Evaluation | RAGAS |
| Deployment | Docker, GCP Cloud Run, Cloud SQL, Memorystore |

---

## Prerequisites

- Docker and Docker Compose
- A [Pinecone](https://www.pinecone.io/) account (Starter plan)
- A [Groq](https://console.groq.com/) API key **or** an [NVIDIA NIM](https://build.nvidia.com/) API key
- GCP project (for production deployment only)

---

## Local Development Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/rag-saas.git
cd rag-saas
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in the required values:

```env
SECRET_KEY=your-random-secret-key

DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/ragdb
REDIS_URL=redis://redis:6379/0

PINECONE_API_KEY=your-pinecone-api-key
PINECONE_INDEX_NAME=rag-saas

LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key

EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
GUARDRAILS_MODEL=unitary/toxic-bert
GUARDRAILS_THRESHOLD=0.7
```

### 3. Start all services

```bash
docker compose up --build
```

This starts:

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

### 4. Run database migrations

```bash
docker compose exec backend alembic upgrade head
```

---

## Project Structure

```
rag-saas/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # Route handlers
│   │   ├── core/            # Config, security, DB session
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic (RAG, ingestion, eval)
│   │   ├── tasks/           # Celery task definitions
│   │   └── main.py
│   ├── alembic/             # Database migrations
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── views/           # Page components
│   │   ├── components/      # Reusable UI components
│   │   ├── stores/          # Pinia state stores
│   │   ├── services/        # Axios API wrappers
│   │   └── router/          # Vue Router config
│   ├── Dockerfile
│   └── package.json
│
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
└── README.md
```

---

## API Reference

### Authentication

All dashboard API routes require a JWT Bearer token obtained from `/api/v1/auth/login`.

Chat endpoints for third-party integrations use an API key:

```
Authorization: Bearer <api_key>
```

### Chat Endpoint

```
POST /api/v1/chat/{chatbot_id}
Authorization: Bearer <api_key>
Content-Type: application/json

{
  "query": "What is the refund policy?"
}
```

Response:

```json
{
  "answer": "The refund policy allows returns within 30 days...",
  "sources": ["policy_document.pdf", "faq.txt"]
}
```

Full API documentation is available at `/docs` (Swagger UI) when running locally.

---

## RAG Evaluation

1. Go to the dashboard → select a chatbot → open the **Evaluation** tab.
2. Upload a CSV file with two columns: `question`, `ground_truth`.
3. Click **Run Evaluation**.
4. The system runs each question through the RAG pipeline and scores using RAGAS:
   - `faithfulness`
   - `answer_relevancy`
   - `context_recall`
   - `context_precision`
5. Results appear in the dashboard when the run completes.

---

## Production Deployment (GCP)

### 1. Build and push Docker images

```bash
# Authenticate with GCP
gcloud auth configure-docker

# Build and push
docker build -t gcr.io/<project-id>/rag-backend ./backend
docker push gcr.io/<project-id>/rag-backend

docker build -t gcr.io/<project-id>/rag-frontend ./frontend
docker push gcr.io/<project-id>/rag-frontend
```

### 2. Provision GCP infrastructure

- **Cloud SQL:** PostgreSQL 15 instance
- **Memorystore:** Redis instance
- **Secret Manager:** Store all environment variables as secrets
- **Artifact Registry:** Store Docker images
- **VPC Connector:** Connect Cloud Run services to Cloud SQL and Memorystore

### 3. Deploy to Cloud Run

```bash
gcloud run deploy rag-backend \
  --image gcr.io/<project-id>/rag-backend \
  --platform managed \
  --region asia-south1 \
  --set-env-vars LLM_PROVIDER=groq \
  --set-secrets GROQ_API_KEY=groq-api-key:latest \
  --allow-unauthenticated

gcloud run deploy rag-frontend \
  --image gcr.io/<project-id>/rag-frontend \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated
```

### 4. Run migrations in production

```bash
gcloud run jobs execute migrate --region asia-south1
```

---

## Environment Variables Reference

| Variable | Description | Required |
|---|---|---|
| `SECRET_KEY` | JWT signing key (random, long string) | Yes |
| `DATABASE_URL` | PostgreSQL connection string (asyncpg) | Yes |
| `REDIS_URL` | Redis connection URL | Yes |
| `PINECONE_API_KEY` | Pinecone API key | Yes |
| `PINECONE_INDEX_NAME` | Pinecone index name | Yes |
| `LLM_PROVIDER` | `groq` or `nim` | Yes |
| `GROQ_API_KEY` | Groq API key (if using Groq) | Conditional |
| `NIM_API_KEY` | NVIDIA NIM API key (if using NIM) | Conditional |
| `NIM_BASE_URL` | NIM base URL | Conditional |
| `EMBEDDING_MODEL` | HuggingFace model name for embeddings | Yes |
| `GUARDRAILS_MODEL` | HuggingFace model name for classifier | Yes |
| `GUARDRAILS_THRESHOLD` | Classification confidence threshold (0–1) | Yes |
| `TOP_K` | Number of chunks retrieved per query | Yes |
| `CHUNK_SIZE` | Chunk size in tokens | Yes |
| `CHUNK_OVERLAP` | Chunk overlap in tokens | Yes |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT access token TTL | Yes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | JWT refresh token TTL | Yes |

---

## Planned for Stage 2

- WhatsApp integration via Twilio / Meta Cloud API
- Google Chat app integration
- Streaming API responses
- Semantic chunking
- OAuth login (Google)
- Rate limiting on API keys
- Email notifications for async task completion

---

## Contributing

1. Create a feature branch from `main`.
2. Follow the existing folder structure and naming conventions.
3. Add Alembic migrations for any schema changes — do not modify the DB directly.
4. Test ingestion and RAG pipeline changes against a local Pinecone-compatible mock or a dedicated test namespace.
5. Open a pull request with a clear description of the change.

---

## License

MIT