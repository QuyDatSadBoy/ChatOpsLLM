import litellm
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from .chat_completion import conversation_router
from .dependencies import shutdown, startup
from .middleware import setup_middleware
from .websocket.ws_handler import handle_ws_chat

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app
app = FastAPI(
    title='ChatOpsLLM',
    description='Production LLMOps platform – FastAPI · LiteLLM · Celery · Qdrant · Redis',
    version='1.0.0',
    redoc_url=None,
    openapi_url='/api/v1/openapi.json',
)

# Set up rate limiter middleware
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Event handlers for startup and shutdown
app.add_event_handler('startup', startup)
app.add_event_handler('shutdown', shutdown)

# Middleware setup
setup_middleware(app)


# Exception handler for rate limiting
@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(status_code=429, content={'detail': 'Rate Limited!'})


# Set up callbacks for litellm
litellm.success_callback = ['langfuse']
litellm.failure_callback = ['langfuse']

# Include application router(s)
app.include_router(conversation_router)


@app.get('/health', tags=['system'])
async def health_check() -> dict[str, str]:
    return {'status': 'ok'}


@app.get('/ready', tags=['system'])
async def readiness_check() -> dict[str, str]:
    return {'status': 'ready'}


# ---------------------------------------------------------------------------
# WebSocket – real-time streaming chat (consumed by Next.js UI)
# ---------------------------------------------------------------------------

@app.websocket('/ws/chat')
async def websocket_chat(websocket: WebSocket) -> None:
    await handle_ws_chat(websocket)


# ---------------------------------------------------------------------------
# Async task endpoint – enqueues a chat request via Celery + RabbitMQ
# ---------------------------------------------------------------------------

class AsyncChatRequest(BaseModel):
    prompt: str
    model: str = 'gemini-flash'
    system_prompt: str = ''
    history: list = []


@app.post('/api/v1/chat/async', tags=['chat'])
async def enqueue_chat(data: AsyncChatRequest) -> dict:
    """
    Enqueue a chat generation task via RabbitMQ → Celery worker → LiteLLM.
    Returns the Celery task ID so the caller can poll /api/v1/chat/async/{task_id}.
    """
    from .worker.tasks import generate_chat_response_task

    task = generate_chat_response_task.apply_async(
        kwargs={
            'prompt': data.prompt,
            'model': data.model,
            'system_prompt': data.system_prompt,
            'history': data.history,
        }
    )
    return {'task_id': task.id, 'status': 'queued'}


@app.get('/api/v1/chat/async/{task_id}', tags=['chat'])
async def get_async_chat_result(task_id: str) -> dict:
    """Poll the status/result of an async chat task."""
    from .worker.celery_app import celery_app

    result = celery_app.AsyncResult(task_id)
    if result.state == 'PENDING':
        return {'task_id': task_id, 'status': 'pending'}
    if result.state == 'FAILURE':
        return {'task_id': task_id, 'status': 'failed', 'detail': str(result.info)}
    if result.ready():
        return {'task_id': task_id, 'status': 'completed', 'result': result.get()}
    return {'task_id': task_id, 'status': result.state.lower()}


# ---------------------------------------------------------------------------
# RAG ingest endpoint
# ---------------------------------------------------------------------------

class IngestRequest(BaseModel):
    texts: list[str]
    metadatas: list[dict] = []


@app.post('/api/v1/rag/ingest', tags=['rag'])
async def rag_ingest(data: IngestRequest) -> dict:
    """Embed and store document chunks in Qdrant."""
    from .rag.retriever import QdrantRetriever

    retriever = QdrantRetriever()
    metadatas = data.metadatas or [{'text': t} for t in data.texts]
    ids = await retriever.ingest(texts=data.texts, metadatas=metadatas)
    return {'ingested': len(ids), 'ids': ids}


# Entry point for the application
if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='0.0.0.0', port=8000)
