---
name: rag-chatbot-saas-coding
description: >-
  Coding standards, architecture guidelines, design philosophy, and implementation rules for the RAG Chatbot SaaS project.
  Use this skill whenever writing, refactoring, or reviewing backend (FastAPI/Python), frontend (Vue 3/JS), background worker (Celery), or database (PostgreSQL/pgvector) code for this repository.
---

# RAG Chatbot SaaS — Coding & Implementation Skill

This skill defines the coding standards, architectural rules, and implementation practices for the **RAG-Based Chatbot SaaS Platform**. All code written or modified in this repository must strictly adhere to these guidelines.

---

## 1. Core Engineering Philosophy

- **Simple & Readable over Clever**: If a line or block of code requires a pause to understand, rewrite it flatly and clearly.
- **No Over-Engineering**: Do not build factories, generic plugin systems, or unnecessary abstraction layers. Build single, concrete implementations for current requirements (e.g., one chatbot service, one retriever).
- **Working First, Perfect Never**: Focus on clean, working functionality over gold-plating.
- **Flat Over Nested**: Avoid deep nesting. Prefer early returns, guard clauses, and flat control flow.

---

## 2. Python & FastAPI Backend Standards (`/backend` or `/app`)

### Naming Conventions
- Variables & Functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private / Internal Helpers: `_leading_underscore`

### Type Hints & Function Structure
- Add clear type hints to all function signatures using built-ins (`list[str]`, `dict`, `str | None`). Avoid overly complex generics.
- Keep functions short (< 30 lines). Each function must perform exactly **one job**.
- Use early returns to keep logic flat.

### Classes vs Functions
- Use classes **only when managing internal state** (e.g., `EmbeddingModel` holding a loaded model in memory).
- Use plain functions for stateless logic (e.g., text validation, prompt formatting).

### Error Handling & Logging
- Wrap all external network/DB calls (LLM API, pgvector queries, file reads) in `try/except`.
- Catch specific exceptions (e.g., `groq.APIError`, `SQLAlchemyError`). Never use bare `except:`.
- Log failures with context and return standard HTTP exceptions (`HTTPException`).

### FastAPI Route Handlers
- Keep route handlers **thin**: validate input, delegate business logic to `services/`, and return response models.
- Always use Pydantic models for request and response serialization.
- Use `async def` for route handlers and I/O-bound functions (database, external HTTP calls).

---

## 3. Vue 3 & JavaScript Frontend Standards (`/frontend`)

### Naming Conventions
- Variables & Functions: `camelCase`
- Components: `PascalCase` (both filename and component name, e.g., `ChatWindow.vue`)
- Constants: `UPPER_SNAKE_CASE`

### Vue Component Architecture
- Always use Vue 3 Composition API with `<script setup>`. Do NOT use Options API.
- Keep components focused (< 150 lines). Split large components into smaller, single-responsibility components.
- Always define typed props with `defineProps`.

### API & State Management
- Never call API endpoints (e.g. `axios`) directly inside Vue components. Place all HTTP calls in `services/` (e.g., `services/chatbot.js`).
- Always handle `loading` and `error` states explicitly in the UI.
- Use **Pinia stores** only for global state shared across multiple routes (e.g., user auth, active token). Use component-local `ref()` for UI state (e.g., modal visibility, form fields).

---

## 4. Architectural & Component Guidelines

### RAG Pipeline & Ingestion Scope
- **Text Extraction**: PDF, DOCX, TXT, and Web URLs. Flag scanned PDFs as unsupported.
- **Chunking**: Use `RecursiveCharacterTextSplitter` (default: `chunk_size=512`, `chunk_overlap=50`).
- **Embeddings**: Local HuggingFace sentence transformer (`BAAI/bge-small-en-v1.5`, 384 dimensions).
- **Vector Storage**: Self-hosted PostgreSQL with `pgvector` (`chunks` table). Query via cosine similarity (`<=>`) filtered by `chatbot_id` UUID with HNSW index.
- **LLM Abstraction**: Wrap LLM calls behind an `LLMProvider` interface to support switching between `groq` (`llama-3.3-70b-versatile`) and `nim` (`meta/llama-3.1-70b-instruct`) via environment variables (`LLM_PROVIDER`).
- **Guardrails**: Apply input and output toxicity classification using HuggingFace (`unitary/toxic-bert`) loaded in memory at app startup.
- **Stateless RAG Queries**: Query pipeline does not maintain or pass past conversation context to the LLM.

### Async Background Tasks
- Use Celery with Redis for long-running processes: document ingestion (`ingest_document`) and RAGAS evaluation (`run_eval`).
- Frontend polls task status endpoints rather than blocking on API calls.

### Security & Access Controls
- Store password hashes with `bcrypt`.
- Hash API keys with SHA-256 before saving to DB. Show plaintext keys to users only once.
- Enforce strict user data isolation at the service layer (users can only query/modify their own chatbots and documents).

---

## 5. Project-Wide Strict Rules

1. **Zero Hardcoding**: All secrets, model names, API keys, URLs, and thresholds must come from environment variables (`core/config.py` / `.env`).
2. **Clean Debugging**: Remove all `print()` statements and `console.log()` before committing code.
3. **Modular File Structure**: One file per logical unit (e.g., `extractor.py`, `chunker.py`, `embedder.py`).
4. **No Dead Code**: Remove unused functions or draft code immediately.
5. **Forbidden Anti-Patterns**:
   - Do NOT implement repository patterns over SQLAlchemy for v1.
   - Do NOT create factory-of-factories, metaclasses, or custom decorator protocols.
   - Do NOT add redundant docstrings or `__repr__` methods to every class.
