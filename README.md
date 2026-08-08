# RAG Chatbot SaaS Platform

A multi-user SaaS platform for creating, managing, and deploying AI-powered chatbots backed by custom document knowledge bases using Retrieval-Augmented Generation (RAG). Users can upload documents, configure chatbot behavior, test RAG pipelines, and integrate chatbots into external applications via REST API.

---

## Key Features

- **Multi-Tenant Chatbot Management**: Create and configure multiple chatbots with custom system prompts and isolated knowledge bases.
- **Document Ingestion Pipeline**: Ingest PDF, DOCX, TXT files, or web URLs with automated text extraction, chunking, and vector embedding.
- **Vector Search with pgvector**: Self-hosted PostgreSQL database using `pgvector` for fast cosine-similarity context retrieval.
- **Safety Guardrails**: Input/output toxicity classification powered by HuggingFace `unitary/toxic-bert`.
- **LLM Abstraction**: Flexible support for Groq (`llama-3.3-70b-versatile`) and NVIDIA NIM (`meta/llama-3.1-70b-instruct`).
- **Async Task Worker**: Background document ingestion and RAGAS evaluation processing via Celery and Redis.
- **API Key & Web Access Control**: Generate API keys for third-party REST integration or share public/restricted web chat links.
- **RAG Evaluation (RAGAS)**: Score chatbot accuracy (faithfulness, relevancy, recall, precision) using uploaded test sets.

---

## Tech Stack

- **Frontend**: Vue 3 (Composition API), PrimeVue 4, Tailwind CSS, Pinia, Vue Router, Axios
- **Backend**: Python 3.13, FastAPI, SQLModel / SQLAlchemy (AsyncSession), Pydantic v2
- **Vector Database**: PostgreSQL 16 with `pgvector` extension
- **Background Tasks**: Celery, Redis
- **Embedding Model**: `BAAI/bge-small-en-v1.5` (local HuggingFace sentence transformer, 384 dimensions)
- **Guardrails**: `unitary/toxic-bert` (local HuggingFace classifier)
- **LLM Providers**: Groq API, NVIDIA NIM API

---

## System Architecture

```
                                +-------------------+
                                |   Vue 3 Web App   |
                                +---------+---------+
                                          |
                                    HTTP / REST API
                                          |
                                          v
                                 +-----------------+
                                 | FastAPI Backend |
                                 +----+-------+----+
                                      |       |
                 +--------------------+       +--------------------+
                 |                                                 |
                 v                                                 v
      +---------------------+                           +--------------------+
      | PostgreSQL pgvector |                           |   Redis + Celery   |
      |   (Chunks & Data)   |                           | (Async Processing) |
      +---------------------+                           +--------------------+
```

---

## Getting Started

### Prerequisites

- Docker and Docker Compose (recommended)
- Python 3.11+ and Node.js 18+ (if running locally without Docker)
- A [Groq API Key](https://console.groq.com/) or [NVIDIA NIM Key](https://build.nvidia.com/)

---

### Running with Docker (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/chatbot_saas.git
   cd chatbot_saas
   ```

2. **Configure Environment Variables**:
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   Add your `GROQ_API_KEY` to `.env`.

3. **Launch Containers**:
   ```bash
   docker compose up --build
   ```

4. **Access the Services**:
   - **Frontend Dashboard**: `http://localhost:5173`
   - **Backend API**: `http://localhost:8000`
   - **Interactive API Docs (Swagger UI)**: `http://localhost:8000/docs`

---

### Running Locally (Without Docker)

1. **Backend Setup**:
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```

2. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

## Core API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Register a new user account |
| `POST` | `/api/v1/auth/login` | Authenticate and retrieve JWT token |
| `GET` | `/api/v1/chatbots` | List user's chatbots |
| `POST` | `/api/v1/chatbots` | Create a new chatbot |
| `POST` | `/api/v1/chatbots/{id}/documents` | Upload document for ingestion |
| `POST` | `/api/v1/chatbots/{id}/api-keys` | Generate API key for third-party access |
| `POST` | `/api/v1/chat/{chatbot_id}` | Execute RAG query (Bearer Token / API Key) |
| `GET` | `/health` | Service health status check |

---

## Project Structure

```
chatbot_saas/
├── backend/
│   ├── app/
│   │   ├── api/          # Route handlers & endpoints
│   │   ├── core/         # DB connection, settings, security
│   │   ├── models/       # SQLModel database models
│   │   ├── schemas/      # Pydantic request/response validation
│   │   ├── services/     # Ingestion, RAG query pipeline, guardrails
│   │   ├── tasks/        # Celery background workers
│   │   └── main.py       # FastAPI app & lifespan initialization
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # Reusable Vue components
│   │   ├── views/        # Dashboard & chat pages
│   │   ├── services/     # Axios API wrappers
│   │   └── stores/       # Pinia state management
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── .env.example
```

---

## License

This project is open-source under the [MIT License](LICENSE).