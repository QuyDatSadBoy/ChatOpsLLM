# ChatOpsLLM

> A production-grade **LLMOps platform** for serving conversational AI on Kubernetes — built end-to-end from infrastructure provisioning to real-time streaming chat.

**Author:** Trần Quý Đạt &nbsp;·&nbsp; [tranquydat.work@gmail.com](mailto:tranquydat.work@gmail.com)

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)
![Kubernetes](https://img.shields.io/badge/Kubernetes-K8s-326CE5?logo=kubernetes&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Architecture

![ChatOpsLLM Architecture](./assets/images/architecture.png)

---

## System Overview

### Request Flow

```
User ──► Kong Gateway ──► Next.js UI ──WebSocket──► FastAPI
                                                        │
                                          ┌─────────────┴─────────────┐
                                     Redis Cache               RabbitMQ (miss)
                                     (hit → return)                    │
                                                               Celery Worker
                                                                       │
                                                               LiteLLM Proxy
                                                          ┌────────────┴────────────┐
                                                   API Provider             API Selfhost
                                              Gemini · OpenAI           BentoML · vLLM
                                               · Anthropic
```

### Data Ingestion Pipeline

```
Raw Data ──► MinIO ──► Airflow DAG ──► Chunk ──► Embed ──► Qdrant (vector store)
```

---

## Key Components

| Layer | Technology | Role |
|---|---|---|
| **API** | FastAPI + Uvicorn | REST + WebSocket endpoint, rate limiting, CORS |
| **Prompt Enhancement** | Custom `PromptEnhancer` | Rewrites user input before sending to LLM |
| **Async Queue** | Celery + RabbitMQ | Non-blocking LLM task processing |
| **Semantic Cache** | Redis (cosine similarity) | Avoids redundant LLM calls for similar prompts |
| **LLM Gateway** | LiteLLM Proxy | Unified routing to Gemini, GPT-4, Claude, vLLM, BentoML |
| **RAG** | Qdrant + Embeddings | Vector search to augment prompts with document context |
| **Database** | PostgreSQL | Conversation history, user management |
| **Frontend** | Next.js 14 + TypeScript | Real-time streaming chat UI over WebSocket |
| **API Gateway** | Kong Gateway | Auth, rate-limit, routing for all Kubernetes traffic |
| **Data Pipeline** | Apache Airflow + MinIO | Scheduled ingestion: raw docs → chunk → embed → Qdrant |
| **Observability** | Langfuse | LLM cost, latency, and quality tracing |
| **Monitoring** | Prometheus + Grafana | Cluster and app metrics, alerting |
| **Alerting** | AlertManager + Discord | Automated incident notifications |
| **Logging** | Filebeat → Logstash → Elasticsearch → Kibana | Centralised log pipeline |
| **CI/CD** | Jenkins + Helm | Webhook-triggered build → push → Kubernetes deploy |
| **IaC** | Terraform + Ansible | GKE cluster provisioning + Jenkins bootstrap |

---

## Project Structure

```
apps/
├── api/                        # FastAPI service
│   └── chatopsllm_api/
│       ├── cache/              # Redis semantic cache
│       ├── worker/             # Celery app + RabbitMQ tasks
│       ├── rag/                # Qdrant vector store + retriever
│       ├── websocket/          # WebSocket handler (/ws/chat)
│       ├── chat_completion/    # Conversation handler + prompt enhancer
│       ├── llms/               # LiteLLM async client
│       └── configs/            # LiteLLM, prompt templates
├── web/                        # Next.js 14 chat UI
│   ├── app/                    # App Router (pages + layout)
│   ├── components/             # ChatbotUI, ChatInput, MessageBubble
│   └── lib/                    # WebSocket client, REST helpers
└── data_pipeline/              # Airflow data-ingestion pipeline
    ├── dags/                   # DAG: raw → chunk → embed → Qdrant
    ├── chunks/                 # Text chunker (sliding window + overlap)
    ├── embeddings/             # Embedding via LiteLLM proxy
    └── storage/                # MinIO reader + Qdrant uploader
ci/
└── Jenkinsfile                 # CI/CD: test → build → push → deploy
deployments/
├── kong/                       # Kong Gateway Helm chart
├── litellm/                    # LiteLLM Helm chart
├── redis/                      # Redis Helm chart
├── monitoring/                 # kube-prometheus-stack
└── ELK/                        # Elasticsearch · Logstash · Kibana
iac/
├── terraform/                  # GKE cluster (Terraform)
└── ansible/                    # Jenkins bootstrap (Ansible)
tests/
└── test_chunker.py             # Data pipeline unit tests
```

---

## Quick Start

```bash
# 1. Start all backend services
cd apps/api
docker compose up -d          # FastAPI · LiteLLM · Redis · RabbitMQ · Qdrant

# 2. Start Celery worker
celery -A chatopsllm_api.worker.celery_app worker --loglevel=info

# 3. Start Next.js UI
cd apps/web && npm install && npm run dev   # http://localhost:3000

# 4. Run tests (26 tests, all passing)
cd apps/api && pytest -v
```

---

## Test Coverage

```
tests/test_semantic_cache.py   8 passed   Redis cache · cosine similarity
tests/test_rag.py              5 passed   Qdrant store · RAG retriever
tests/test_celery_tasks.py     2 passed   Celery task · cache integration
tests/test_websocket.py        3 passed   WebSocket streaming · cache hit
tests/test_system.py           3 passed   Health · LLM error handling
tests/test_chunker.py          5 passed   Data pipeline chunker
─────────────────────────────────────────
Total                         26 passed
```

---

## License

MIT © 2025 Trần Quý Đạt · [tranquydat.work@gmail.com](mailto:tranquydat.work@gmail.com)


# ChatOpsLLM
